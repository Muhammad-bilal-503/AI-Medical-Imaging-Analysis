"""
Grad-CAM (Gradient-weighted Class Activation Mapping) — shows doctors
which regions of the X-ray drove the model's top prediction, per the
spec's Explainable AI requirement.

Reference: Selvaraju et al., "Grad-CAM: Visual Explanations from Deep
Networks via Gradient-based Localization" (2017).
"""

import io

import numpy as np
import torch
import torch.nn.functional as F
from matplotlib import colormaps
from PIL import Image

from app.ai.chest_xray_model import get_model


class GradCAM:
    def __init__(self, model, target_layer: torch.nn.Module):
        self.model = model
        self.activations: torch.Tensor | None = None
        # Only a forward hook is used (not register_full_backward_hook):
        # this DenseNet applies an in-place ReLU right after this layer,
        # which conflicts with the autograd bookkeeping a backward hook
        # adds. retain_grad() on the captured activation sidesteps that.
        self.hook_handle = target_layer.register_forward_hook(self._save_activation)

    def _save_activation(self, module, inputs, output):
        output.retain_grad()
        self.activations = output

    def remove_hook(self):
        """MUST be called after generate() — otherwise this hook stays
        registered on the shared model forever, and fires again on the
        next plain (no_grad) prediction call, where output.retain_grad()
        crashes with "can't retain_grad on Tensor that has
        requires_grad=False". One GradCAM instance = one hook = one use."""
        self.hook_handle.remove()

    def generate(self, input_tensor: torch.Tensor, target_index: int) -> np.ndarray:
        self.model.zero_grad()
        output = self.model(input_tensor)
        score = output[0, target_index]
        score.backward()

        gradients = self.activations.grad[0]      # [C, H, W]
        activations = self.activations.detach()[0]  # [C, H, W]
        weights = gradients.mean(dim=(1, 2))  # global-average-pool the gradients

        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = F.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.numpy()


def generate_heatmap_overlay(
    display_image: Image.Image, input_tensor: torch.Tensor, target_index: int
) -> bytes:
    """Returns a PNG (as bytes) of the original image with the Grad-CAM
    heatmap overlaid — this is what gets stored and shown to doctors."""
    model = get_model()
    target_layer = model.features  # last conv block, before global pooling

    input_tensor = input_tensor.clone().requires_grad_(True)
    cam_engine = GradCAM(model, target_layer)
    try:
        cam = cam_engine.generate(input_tensor, target_index)
    finally:
        cam_engine.remove_hook()

    cam_img = Image.fromarray(np.uint8(cam * 255)).resize(display_image.size, Image.BILINEAR)
    cam_arr = np.array(cam_img).astype(np.float32) / 255.0

    colormap = colormaps.get_cmap("jet")
    heat_rgba = (colormap(cam_arr) * 255).astype(np.uint8)
    heat_rgb = Image.fromarray(heat_rgba).convert("RGB")

    base = display_image.convert("RGB")
    overlay = Image.blend(base, heat_rgb, alpha=0.45)

    buf = io.BytesIO()
    overlay.save(buf, format="PNG")
    return buf.getvalue()

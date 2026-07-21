"""
Chest X-ray disease detection.

Uses torchxrayvision's DenseNet121, pretrained on a combination of NIH,
CheXpert, MIMIC-CXR, PadChest, Google, OpenI, and Kaggle chest X-ray
datasets (https://github.com/mlmed/torchxrayvision). Training a
comparable model from scratch needs tens of thousands of labeled
images and days of GPU time — using vetted pretrained weights is the
standard approach here, same as most published chest X-ray CAD tools.

Note on disease coverage: this model's label set does not include
COVID-19 or Tuberculosis (the datasets it was trained on predate/omit
those labels). If those are required, that's a separate fine-tuning
effort — flagging that as a known gap against the original spec.
"""

import threading

import torch
import torchxrayvision as xrv

from app.ai.preprocessing import load_and_preprocess

_model = None
_model_lock = threading.Lock()

MODEL_NAME = "torchxrayvision-densenet121"
MODEL_VERSION = "densenet121-res224-all"


def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                m = xrv.models.DenseNet(weights=MODEL_VERSION)
                m.eval()
                _model = m
    return _model


def predict_chest_xray(image_bytes: bytes) -> dict:
    """
    Returns:
        {
            "display_image": PIL.Image (RGB, resized — for storage/preview),
            "predictions": [{"label": str, "confidence": float}, ...] sorted desc,
            "top_prediction": str,
            "top_confidence": float,
            "input_tensor": torch.Tensor (for Grad-CAM reuse),
            "target_index": int (index of top prediction in model.pathologies),
        }
    """
    model = get_model()
    display_image, model_array = load_and_preprocess(image_bytes)

    # torchxrayvision expects [-1024, 1024]-normalized single-channel input
    normalized = xrv.datasets.normalize(model_array, 255)
    tensor = torch.from_numpy(normalized[None, None, ...]).float()

    with torch.no_grad():
        raw_output = model(tensor)

    probs = raw_output[0].numpy()
    pathologies = model.pathologies

    predictions = [
        {"label": label, "confidence": round(float(prob) * 100, 2)}
        for label, prob in zip(pathologies, probs)
        if label  # torchxrayvision pads with empty-string labels for unused slots
    ]
    predictions.sort(key=lambda p: p["confidence"], reverse=True)

    top = predictions[0]
    target_index = pathologies.index(top["label"])

    return {
        "display_image": display_image,
        "predictions": predictions,
        "top_prediction": top["label"],
        "top_confidence": top["confidence"],
        "input_tensor": tensor,
        "target_index": target_index,
    }

import io

import numpy as np
from PIL import Image, ImageFilter, ImageOps

TARGET_SIZE = 224


class InvalidImageError(Exception):
    pass


def load_and_preprocess(image_bytes: bytes) -> tuple[Image.Image, np.ndarray]:
    """
    Validates the image, then applies the preprocessing pipeline the spec
    calls for (resize / normalize / contrast enhancement / noise reduction)
    before handing off to the model-specific normalization.

    Returns (display_image, model_ready_array):
      - display_image: RGB PIL image, resized, for storing/showing in the UI
      - model_ready_array: float32 grayscale array, contrast-enhanced and
        denoised, ready for the DenseNet's own normalization step
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))  # re-open after verify()
    except Exception as e:
        raise InvalidImageError(f"Could not read image: {e}") from e

    grayscale = img.convert("L")

    # Noise reduction
    denoised = grayscale.filter(ImageFilter.MedianFilter(size=3))

    # Contrast enhancement (histogram-stretch autocontrast)
    enhanced = ImageOps.autocontrast(denoised, cutoff=1)

    # Resize to model input size
    resized = enhanced.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

    display_image = resized.convert("RGB")
    model_array = np.array(resized).astype(np.float32)

    return display_image, model_array

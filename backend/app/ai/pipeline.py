from app.ai.chest_xray_model import MODEL_NAME, MODEL_VERSION, predict_chest_xray
from app.ai.gradcam import generate_heatmap_overlay
from app.ai.llm_report import generate_radiology_report


def run_chest_xray_pipeline(image_bytes: bytes, patient_context: dict) -> dict:
    """
    End-to-end: preprocess -> DenseNet121 inference -> Grad-CAM -> LLM report draft.

    Returns everything the caller needs to persist:
        {
            "model_name", "model_version",
            "predictions", "top_prediction", "top_confidence",
            "heatmap_png_bytes",
            "report": {examination, clinical_findings, ...},
        }
    """
    vision_result = predict_chest_xray(image_bytes)

    heatmap_png_bytes = generate_heatmap_overlay(
        vision_result["display_image"],
        vision_result["input_tensor"],
        vision_result["target_index"],
    )

    report = generate_radiology_report(
        predictions=vision_result["predictions"],
        scan_type="chest_xray",
        patient_context=patient_context,
    )

    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "predictions": vision_result["predictions"],
        "top_prediction": vision_result["top_prediction"],
        "top_confidence": vision_result["top_confidence"],
        "heatmap_png_bytes": heatmap_png_bytes,
        "report": report,
    }

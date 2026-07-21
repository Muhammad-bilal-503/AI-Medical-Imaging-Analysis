"""
Runs after image upload, as a FastAPI BackgroundTask (see images.py).
Uses the service-role Supabase client, since this executes outside any
single user's request context and needs to write across
ai_predictions/reports regardless of RLS.
"""

import logging

from app.ai.pipeline import run_chest_xray_pipeline
from app.core.config import get_settings
from app.db.supabase_client import get_service_client

logger = logging.getLogger(__name__)
settings = get_settings()


def process_chest_xray_image(image_id: str) -> None:
    client = get_service_client()

    try:
        image_row = (
            client.table("medical_images").select("*").eq("id", image_id).single().execute()
        )
        if not image_row.data:
            logger.error("process_chest_xray_image: image %s not found", image_id)
            return
        image = image_row.data

        patient_row = (
            client.table("patients")
            .select("date_of_birth, sex")
            .eq("id", image["patient_id"])
            .single()
            .execute()
        )
        patient = patient_row.data or {}
        patient_context = {"sex": patient.get("sex", "unknown"), "age": "unknown"}

        # Download the original image bytes from Storage.
        image_bytes = client.storage.from_(settings.BUCKET_MEDICAL_IMAGES).download(
            image["storage_path"]
        )

        result = run_chest_xray_pipeline(image_bytes, patient_context)

        # Upload the Grad-CAM heatmap.
        heatmap_path = f"{image['patient_id']}/{image_id}_heatmap.png"
        client.storage.from_(settings.BUCKET_HEATMAPS).upload(
            heatmap_path,
            result["heatmap_png_bytes"],
            {"content-type": "image/png"},
        )

        # Store the prediction.
        prediction_row = (
            client.table("ai_predictions")
            .insert(
                {
                    "image_id": image_id,
                    "model_name": result["model_name"],
                    "model_version": result["model_version"],
                    "predictions": result["predictions"],
                    "top_prediction": result["top_prediction"],
                    "top_confidence": result["top_confidence"],
                    "heatmap_storage_path": heatmap_path,
                }
            )
            .execute()
        )
        prediction_id = prediction_row.data[0]["id"]

        # Store the AI-drafted report (status="ai_generated" — NOT finalized;
        # a doctor must review before it's used clinically).
        report = result["report"]
        client.table("reports").insert(
            {
                "patient_id": image["patient_id"],
                "image_id": image_id,
                "prediction_id": prediction_id,
                "status": "ai_generated",
                "severity": report.get("severity_level"),
                "examination": report.get("examination"),
                "clinical_findings": report.get("clinical_findings"),
                "image_findings": report.get("image_findings"),
                "impression": report.get("impression"),
                "recommendation": report.get("recommendation"),
                "suggested_followup": report.get("suggested_followup"),
                "confidence_summary": report.get("confidence_summary"),
                "llm_model": "llama-3.1-8b-instant",
            }
        ).execute()

        logger.info("process_chest_xray_image: completed for image %s", image_id)

    except Exception:
        logger.exception("process_chest_xray_image failed for image %s", image_id)
        # TODO(next phase): write a failure status somewhere the doctor's
        # dashboard can surface, and/or push a notification, instead of
        # just logging — right now a failed pipeline run is silent to the
        # end user beyond the report never appearing.

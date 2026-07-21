"""
Turns structured vision-model output into a professional radiology
report draft using Llama 3.1 8B via the Groq API.

IMPORTANT: this produces a *draft* for a licensed doctor to review and
sign off on — the report rows this writes are stored with
status="ai_generated", not "finalized". See reports.py for the review
workflow.
"""

import json

from groq import Groq

from app.core.config import get_settings

settings = get_settings()

MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a radiology report drafting assistant. You are \
given AI vision-model disease predictions (label + confidence %) for a \
chest X-ray, plus basic patient context. Draft a professional radiology \
report DRAFT for a licensed radiologist to review, edit, and sign off on.

Rules:
- Write in standard radiology report register: precise, hedged where the \
  model's confidence is not high, never definitive about diagnosis — you \
  are producing decision support, not a diagnosis.
- Do not invent clinical history, patient symptoms, or findings not \
  supported by the provided predictions.
- If the top confidence is low (under ~40%), say findings are \
  indeterminate / low-confidence and recommend clinical correlation.
- Output ONLY a JSON object (no markdown fences, no commentary) with \
  exactly these keys, all string values:
  examination, clinical_findings, image_findings, impression, \
  recommendation, suggested_followup, severity_level (one of: low, \
  moderate, high, critical), confidence_summary."""


def build_user_prompt(predictions: list[dict], scan_type: str, patient_context: dict) -> str:
    top5 = predictions[:5]
    findings_text = "\n".join(f"- {p['label']}: {p['confidence']}%" for p in top5)
    age = patient_context.get("age", "unknown")
    sex = patient_context.get("sex", "unknown")
    return f"""Scan type: {scan_type}
Patient: age {age}, sex {sex}

AI vision model findings (top 5, by confidence):
{findings_text}

Draft the radiology report JSON now."""


def generate_radiology_report(
    predictions: list[dict], scan_type: str, patient_context: dict
) -> dict:
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set — add it to .env to enable report generation."
        )

    client = Groq(api_key=settings.GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(predictions, scan_type, patient_context)},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = completion.choices[0].message.content
    report = json.loads(raw)

    top = predictions[0] if predictions else {"label": "unknown", "confidence": 0}
    report.setdefault(
        "confidence_summary",
        f"Top AI-flagged finding: {top['label']} ({top['confidence']}% confidence).",
    )
    return report

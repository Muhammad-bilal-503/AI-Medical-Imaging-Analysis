"""
Generates the professional PDF radiology report from a finalized (or
in-review) report row. Pulls the original scan + Grad-CAM heatmap from
Storage, lays out patient/doctor info, findings, and a QR code, and
uploads the result to the `reports` bucket.
"""

import io
from datetime import datetime, timezone

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings
from app.db.supabase_client import get_service_client

settings = get_settings()

HOSPITAL_NAME = "AI Medical Imaging Platform"  # TODO: make configurable per deployment
PAGE_MARGIN = 18 * mm

styles = getSampleStyleSheet()
STYLE_H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=4)
STYLE_H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=4)
STYLE_BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13)
STYLE_SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)


def _fetch_bytes(client, bucket: str, path: str) -> bytes | None:
    if not path:
        return None
    try:
        return client.storage.from_(bucket).download(path)
    except Exception:
        return None


def _make_qr(data: str) -> RLImage:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=25 * mm, height=25 * mm)


def _predictions_table(predictions: list[dict]) -> Table:
    rows = [["Finding", "Confidence"]]
    for p in predictions[:8]:
        rows.append([p.get("label", ""), f"{p.get('confidence', 0)}%"])
    table = Table(rows, colWidths=[100 * mm, 40 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def generate_report_pdf(report_id: str) -> bytes:
    client = get_service_client()

    report_row = client.table("reports").select("*").eq("id", report_id).single().execute()
    if not report_row.data:
        raise ValueError(f"Report {report_id} not found")
    report = report_row.data

    patient_row = (
        client.table("patients").select("*").eq("id", report["patient_id"]).single().execute()
    )
    patient = patient_row.data or {}

    doctor = {}
    if report.get("doctor_id"):
        doctor_row = client.table("users").select("*").eq("id", report["doctor_id"]).single().execute()
        doctor = doctor_row.data or {}

    prediction = {}
    if report.get("prediction_id"):
        pred_row = (
            client.table("ai_predictions")
            .select("*")
            .eq("id", report["prediction_id"])
            .single()
            .execute()
        )
        prediction = pred_row.data or {}

    image_row = client.table("medical_images").select("*").eq("id", report["image_id"]).single().execute()
    image = image_row.data or {}

    scan_bytes = _fetch_bytes(client, settings.BUCKET_MEDICAL_IMAGES, image.get("storage_path", ""))
    heatmap_bytes = _fetch_bytes(
        client, settings.BUCKET_HEATMAPS, prediction.get("heatmap_storage_path", "")
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
    )
    story = []

    # --- Header ---
    story.append(Paragraph(HOSPITAL_NAME, STYLE_H1))
    story.append(Paragraph("Radiology Report — AI-Assisted Draft", STYLE_BODY))
    story.append(Spacer(1, 6))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_note = (
        "FINALIZED — reviewed and signed off by the attending physician"
        if report.get("status") == "finalized"
        else "DRAFT — pending physician review. Not for clinical use until finalized."
    )
    story.append(Paragraph(f"<b>Status:</b> {status_note}", STYLE_SMALL))
    story.append(Paragraph(f"<b>Generated:</b> {generated_at}", STYLE_SMALL))
    story.append(Spacer(1, 10))

    # --- Patient / Doctor info ---
    info_rows = [
        ["Patient", patient.get("full_name", "—"), "Patient Code", patient.get("patient_code", "—")],
        ["Date of Birth", str(patient.get("date_of_birth", "—")), "Sex", patient.get("sex", "—")],
        [
            "Reviewing Doctor",
            doctor.get("full_name", "Pending assignment"),
            "Specialty",
            doctor.get("specialty", "—"),
        ],
        ["Scan Type", image.get("scan_type", "—"), "Report ID", report_id[:8]],
    ]
    info_table = Table(info_rows, colWidths=[32 * mm, 58 * mm, 32 * mm, 48 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 12))

    # --- Images ---
    if scan_bytes or heatmap_bytes:
        story.append(Paragraph("Imaging", STYLE_H2))
        img_cells = []
        if scan_bytes:
            img_cells.append(RLImage(io.BytesIO(scan_bytes), width=70 * mm, height=70 * mm))
        if heatmap_bytes:
            img_cells.append(RLImage(io.BytesIO(heatmap_bytes), width=70 * mm, height=70 * mm))
        img_table = Table([img_cells], colWidths=[75 * mm] * len(img_cells))
        story.append(img_table)
        caption_cells = [Paragraph("Original scan", STYLE_SMALL)]
        if heatmap_bytes:
            caption_cells.append(Paragraph("Grad-CAM heatmap (AI attention regions)", STYLE_SMALL))
        story.append(Table([caption_cells], colWidths=[75 * mm] * len(caption_cells)))
        story.append(Spacer(1, 10))

    # --- AI findings table ---
    predictions = prediction.get("predictions") or []
    if predictions:
        story.append(Paragraph("AI Vision Model Findings", STYLE_H2))
        story.append(_predictions_table(predictions))
        story.append(Spacer(1, 10))

    # --- Report narrative sections ---
    sections = [
        ("Examination", report.get("examination")),
        ("Clinical Findings", report.get("clinical_findings")),
        ("Image Findings", report.get("image_findings")),
        ("Impression", report.get("impression")),
        ("Recommendation", report.get("recommendation")),
        ("Suggested Follow-up", report.get("suggested_followup")),
        ("Severity", report.get("severity")),
        ("Confidence Summary", report.get("confidence_summary")),
    ]
    for title, text in sections:
        if text:
            story.append(Paragraph(title, STYLE_H2))
            story.append(Paragraph(str(text), STYLE_BODY))

    story.append(Spacer(1, 16))

    # --- QR + signature footer ---
    qr_img = _make_qr(f"report:{report_id}")
    sig_text = (
        f"Digitally reviewed by: {doctor.get('full_name')}"
        if report.get("status") == "finalized" and doctor.get("full_name")
        else "Signature: ______________________  (pending physician sign-off)"
    )
    footer_table = Table(
        [[qr_img, Paragraph(sig_text, STYLE_BODY)]],
        colWidths=[30 * mm, 130 * mm],
    )
    footer_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(footer_table)

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "This report was drafted with AI assistance and is intended as clinical "
            "decision support, not a standalone diagnosis. It must be reviewed by a "
            "licensed physician before being acted upon.",
            STYLE_SMALL,
        )
    )

    doc.build(story)
    return buf.getvalue()


def generate_and_store_report_pdf(report_id: str) -> str:
    """Generates the PDF, uploads it to the `reports` bucket, updates the
    report row's pdf_storage_path, and returns that path."""
    client = get_service_client()
    pdf_bytes = generate_report_pdf(report_id)

    storage_path = f"{report_id}/report.pdf"
    client.storage.from_(settings.BUCKET_REPORTS).upload(
        storage_path,
        pdf_bytes,
        {"content-type": "application/pdf", "x-upsert": "true"},
    )
    client.table("reports").update({"pdf_storage_path": storage_path}).eq("id", report_id).execute()
    return storage_path

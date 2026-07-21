from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.supabase_client import get_user_client
from app.dependencies.auth import get_current_token, get_current_user, require_roles
from app.models.schemas import CurrentUser, ReportOut, ReportStatus, UserRole
from app.services.pdf_service import generate_and_store_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


class ReportUpdate(BaseModel):
    doctor_notes: str | None = None
    impression: str | None = None
    recommendation: str | None = None
    status: ReportStatus | None = None


@router.get("", response_model=list[ReportOut])
def list_reports(
    patient_id: str | None = None,
    status: ReportStatus | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    query = client.table("reports").select("*")
    if patient_id:
        query = query.eq("patient_id", patient_id)
    if status:
        query = query.eq("status", status.value)
    result = query.order("created_at", desc=True).limit(50).execute()
    return [ReportOut(**row) for row in result.data]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = client.table("reports").select("*").eq("id", report_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut(**result.data)


@router.patch("/{report_id}", response_model=ReportOut)
def update_report(
    report_id: str,
    payload: ReportUpdate,
    current_user: CurrentUser = Depends(
        require_roles(UserRole.doctor, UserRole.radiologist, UserRole.admin)
    ),
    token: str = Depends(get_current_token),
):
    """Doctor reviews/edits the AI-generated draft. Finalizing (status=
    finalized) should be treated as a clinical sign-off — RLS restricts
    this to the assigned doctor or an admin."""
    client = get_user_client(token)
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    existing = client.table("reports").select("doctor_id").eq("id", report_id).single().execute()
    if existing.data and existing.data.get("doctor_id") is None:
        updates["doctor_id"] = current_user.id  # claim it on first edit

    result = client.table("reports").update(updates).eq("id", report_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found or not permitted")
    return ReportOut(**result.data[0])


@router.post("/{report_id}/generate-pdf")
def generate_pdf(
    report_id: str,
    current_user: CurrentUser = Depends(
        require_roles(UserRole.doctor, UserRole.radiologist, UserRole.admin)
    ),
):
    """Renders the report to PDF and stores it in the `reports` bucket.
    Works for draft (ai_generated) reports too, marked accordingly in the
    PDF, so a doctor can print/share a working copy while reviewing."""
    try:
        storage_path = generate_and_store_report_pdf(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"pdf_storage_path": storage_path}


@router.get("/{report_id}/pdf-url")
def get_pdf_signed_url(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = client.table("reports").select("pdf_storage_path").eq("id", report_id).single().execute()
    if not result.data or not result.data.get("pdf_storage_path"):
        raise HTTPException(
            status_code=404, detail="No PDF generated yet — call generate-pdf first"
        )
    signed = client.storage.from_(settings.BUCKET_REPORTS).create_signed_url(
        result.data["pdf_storage_path"], expires_in=300
    )
    return {"url": signed.get("signedURL") or signed.get("signed_url")}

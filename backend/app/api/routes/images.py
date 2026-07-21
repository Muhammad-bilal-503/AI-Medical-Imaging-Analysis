import hashlib
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.db.supabase_client import get_user_client
from app.dependencies.auth import get_current_token, get_current_user
from app.models.schemas import AIPredictionOut, CurrentUser, MedicalImageOut, ScanType
from app.services.inference_service import process_chest_xray_image

router = APIRouter(prefix="/images", tags=["images"])
settings = get_settings()

ALLOWED_FORMATS = {"jpg", "jpeg", "png", "dcm", "dicom"}
MAX_FILE_SIZE_MB = 50


@router.post("/upload", response_model=MedicalImageOut, status_code=201)
async def upload_image(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(...),
    scan_type: ScanType = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {sorted(ALLOWED_FORMATS)}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    checksum = hashlib.sha256(contents).hexdigest()
    storage_path = f"{patient_id}/{uuid.uuid4()}.{ext}"

    client = get_user_client(token)

    # Upload to Supabase Storage bucket (private — access via signed URLs only).
    client.storage.from_(settings.BUCKET_MEDICAL_IMAGES).upload(
        storage_path,
        contents,
        {"content-type": file.content_type or "application/octet-stream"},
    )

    row = {
        "patient_id": patient_id,
        "uploaded_by": current_user.id,
        "scan_type": scan_type.value,
        "storage_path": storage_path,
        "original_filename": file.filename,
        "file_format": ext,
        "checksum": checksum,
    }
    result = client.table("medical_images").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Could not record image metadata")

    image_row = MedicalImageOut(**result.data[0])

    if scan_type == ScanType.chest_xray:
        background_tasks.add_task(process_chest_xray_image, image_row.id)
    # TODO(next phase): brain_mri / CT pipelines aren't built yet — those
    # uploads are stored but won't get an AI prediction/report yet.

    return image_row


@router.get("/patient/{patient_id}", response_model=list[MedicalImageOut])
def list_patient_images(
    patient_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = (
        client.table("medical_images")
        .select("*")
        .eq("patient_id", patient_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    return [MedicalImageOut(**row) for row in result.data]


@router.get("/{image_id}/signed-url")
def get_signed_url(
    image_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    img = client.table("medical_images").select("storage_path").eq("id", image_id).single().execute()
    if not img.data:
        raise HTTPException(status_code=404, detail="Image not found")

    signed = client.storage.from_(settings.BUCKET_MEDICAL_IMAGES).create_signed_url(
        img.data["storage_path"], expires_in=300
    )
    return {"url": signed.get("signedURL") or signed.get("signed_url")}


@router.get("/{image_id}/prediction", response_model=AIPredictionOut)
def get_prediction(
    image_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = (
        client.table("ai_predictions")
        .select("*")
        .eq("image_id", image_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No prediction yet for this image")
    return AIPredictionOut(**result.data[0])


@router.get("/{image_id}/heatmap-url")
def get_heatmap_signed_url(
    image_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    pred = (
        client.table("ai_predictions")
        .select("heatmap_storage_path")
        .eq("image_id", image_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not pred.data or not pred.data[0].get("heatmap_storage_path"):
        raise HTTPException(status_code=404, detail="No heatmap available for this image")

    signed = client.storage.from_(settings.BUCKET_HEATMAPS).create_signed_url(
        pred.data[0]["heatmap_storage_path"], expires_in=300
    )
    return {"url": signed.get("signedURL") or signed.get("signed_url")}

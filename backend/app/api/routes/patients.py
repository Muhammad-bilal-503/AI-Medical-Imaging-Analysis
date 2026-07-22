from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.supabase_client import get_user_client
from app.dependencies.auth import get_current_token, get_current_user, require_roles
from app.models.schemas import CurrentUser, PatientCreate, PatientOut, UserRole

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    payload: PatientCreate,
    current_user: CurrentUser = Depends(require_roles(UserRole.doctor, UserRole.radiologist)),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    data = payload.model_dump(mode="json")
    data["created_by"] = current_user.id
    result = client.table("patients").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Could not create patient")

    new_patient = result.data[0]
    client.table("patient_access").insert(
        {"patient_id": new_patient["id"], "doctor_id": current_user.id, "granted_via": "owner"}
    ).execute()

    return PatientOut(**new_patient)


@router.get("", response_model=list[PatientOut])
def search_patients(
    q: str | None = Query(default=None, description="Search by name or patient code"),
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    query = client.table("patients").select("*")
    if q:
        query = query.or_(f"full_name.ilike.%{q}%,patient_code.ilike.%{q}%")
    result = query.order("created_at", desc=True).limit(50).execute()
    return [PatientOut(**row) for row in result.data]


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = client.table("patients").select("*").eq("id", patient_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientOut(**result.data)

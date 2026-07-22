from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import get_service_client, get_user_client
from app.dependencies.auth import get_current_token, get_current_user
from app.models.schemas import CurrentUser, ReferralCreate, ReferralOut, UserRole

router = APIRouter(prefix="/referrals", tags=["referrals"])


def _enrich(client, referral: dict) -> dict:
    """Fills in display names — the DB row only has IDs."""
    patient = (
        client.table("patients").select("full_name").eq("id", referral["patient_id"]).single().execute()
    )
    from_doc = (
        client.table("users")
        .select("full_name")
        .eq("id", referral["referring_doctor_id"])
        .single()
        .execute()
    )
    to_doc = (
        client.table("users")
        .select("full_name")
        .eq("id", referral["referred_to_doctor_id"])
        .single()
        .execute()
    )
    referral["patient_name"] = patient.data["full_name"] if patient.data else None
    referral["referring_doctor_name"] = from_doc.data["full_name"] if from_doc.data else None
    referral["referred_to_doctor_name"] = to_doc.data["full_name"] if to_doc.data else None
    return referral


@router.post("", response_model=ReferralOut, status_code=201)
def create_referral(
    payload: ReferralCreate,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)

    # Must actually have access to this patient to refer them.
    access = (
        client.table("patient_access")
        .select("patient_id")
        .eq("patient_id", payload.patient_id)
        .eq("doctor_id", current_user.id)
        .execute()
    )
    if not access.data and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="You don't have access to this patient.")

    # Resolve the target doctor by email — service client, since RLS on
    # users only lets you read your own row otherwise.
    db = get_service_client()
    target = (
        db.table("users")
        .select("id, role")
        .eq("email", payload.to_email)
        .execute()
    )
    if not target.data:
        raise HTTPException(
            status_code=404, detail="No staff account found with that email."
        )
    target_user = target.data[0]
    if target_user["role"] not in ("doctor", "radiologist"):
        raise HTTPException(status_code=400, detail="Can only refer to a doctor or radiologist.")
    if target_user["id"] == current_user.id:
        raise HTTPException(status_code=400, detail="You can't refer a patient to yourself.")

    already_has_access = (
        client.table("patient_access")
        .select("patient_id")
        .eq("patient_id", payload.patient_id)
        .eq("doctor_id", target_user["id"])
        .execute()
    )
    if already_has_access.data:
        raise HTTPException(
            status_code=400, detail="That doctor already has access to this patient."
        )

    result = (
        client.table("patient_referrals")
        .insert(
            {
                "patient_id": payload.patient_id,
                "referring_doctor_id": current_user.id,
                "referred_to_doctor_id": target_user["id"],
                "note": payload.note,
            }
        )
        .execute()
    )
    return ReferralOut(**_enrich(client, result.data[0]))


@router.get("/incoming", response_model=list[ReferralOut])
def list_incoming(
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = (
        client.table("patient_referrals")
        .select("*")
        .eq("referred_to_doctor_id", current_user.id)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return [ReferralOut(**_enrich(client, row)) for row in result.data]


@router.get("/outgoing", response_model=list[ReferralOut])
def list_outgoing(
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    result = (
        client.table("patient_referrals")
        .select("*")
        .eq("referring_doctor_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return [ReferralOut(**_enrich(client, row)) for row in result.data]


@router.post("/{referral_id}/accept", response_model=ReferralOut)
def accept_referral(
    referral_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    referral = client.table("patient_referrals").select("*").eq("id", referral_id).single().execute()
    if not referral.data:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.data["referred_to_doctor_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="This referral isn't addressed to you.")
    if referral.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="This referral has already been responded to.")

    client.table("patient_access").insert(
        {
            "patient_id": referral.data["patient_id"],
            "doctor_id": current_user.id,
            "granted_via": "referral",
        }
    ).execute()

    updated = (
        client.table("patient_referrals")
        .update({"status": "accepted", "responded_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", referral_id)
        .execute()
    )
    return ReferralOut(**_enrich(client, updated.data[0]))


@router.post("/{referral_id}/decline", response_model=ReferralOut)
def decline_referral(
    referral_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)
    referral = client.table("patient_referrals").select("*").eq("id", referral_id).single().execute()
    if not referral.data:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.data["referred_to_doctor_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="This referral isn't addressed to you.")
    if referral.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="This referral has already been responded to.")

    updated = (
        client.table("patient_referrals")
        .update({"status": "declined", "responded_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", referral_id)
        .execute()
    )
    return ReferralOut(**_enrich(client, updated.data[0]))

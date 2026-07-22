from fastapi import APIRouter, Depends, HTTPException, status

from app.db.supabase_client import get_legacy_admin_client, get_service_client
from app.dependencies.auth import require_roles
from app.models.schemas import AdminCreateUserRequest, CurrentUser, UserProfile, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminCreateUserRequest,
    current_user: CurrentUser = Depends(require_roles(UserRole.admin)),
):
    """
    Admin-only account creation. Creates the auth user pre-confirmed
    (no email link needed — the admin hands the password to the staff
    member directly) via the legacy service_role JWT client, then the
    matching public.users profile row via the normal service client.
    """
    admin_auth = get_legacy_admin_client()

    try:
        auth_result = admin_auth.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {"full_name": payload.full_name, "role": payload.role.value},
                "app_metadata": {"role": payload.role.value},
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = auth_result.user.id
    db = get_service_client()
    result = (
        db.table("users")
        .insert(
            {
                "id": user_id,
                "email": payload.email,
                "full_name": payload.full_name,
                "role": payload.role.value,
                "specialty": payload.specialty,
                "license_number": payload.license_number,
                "hospital_affiliation": payload.hospital_affiliation,
            }
        )
        .execute()
    )
    return UserProfile(**result.data[0])


@router.get("/users", response_model=list[UserProfile])
def list_users(current_user: CurrentUser = Depends(require_roles(UserRole.admin))):
    db = get_service_client()
    result = db.table("users").select("*").order("created_at", desc=True).execute()
    return [UserProfile(**row) for row in result.data]


@router.patch("/users/{user_id}/active", response_model=UserProfile)
def set_user_active(
    user_id: str,
    is_active: bool,
    current_user: CurrentUser = Depends(require_roles(UserRole.admin)),
):
    """Deactivate/reactivate a staff account (e.g. offboarding) without
    deleting their history — reports/images they created stay intact."""
    db = get_service_client()
    result = db.table("users").update({"is_active": is_active}).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**result.data[0])


@router.get("/stats")
def get_stats(current_user: CurrentUser = Depends(require_roles(UserRole.admin))):
    """High-level counts for the admin overview panel."""
    db = get_service_client()

    def count(table: str) -> int:
        res = db.table(table).select("id", count="exact").execute()
        return res.count or 0

    return {
        "total_users": count("users"),
        "total_patients": count("patients"),
        "total_scans": count("medical_images"),
        "total_reports": count("reports"),
    }

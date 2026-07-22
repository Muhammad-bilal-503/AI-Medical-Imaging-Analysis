from fastapi import APIRouter, Depends, HTTPException, status

from app.db.supabase_client import get_service_client
from app.dependencies.auth import get_current_user
from app.models.schemas import CurrentUser, LoginRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])

# NOTE: there is no public /auth/signup route. Accounts are provisioned
# only by an admin, via POST /api/v1/admin/users (see admin.py) — a
# hospital deployment shouldn't let anyone self-register as a doctor.
# The very first admin account is created by the one-time bootstrap
# script: backend/scripts/create_first_admin.py.


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    client = get_service_client()
    try:
        session = client.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    profile = (
        client.table("users")
        .select("is_active")
        .eq("id", session.user.id)
        .single()
        .execute()
    )
    if profile.data and profile.data.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated."
        )

    return TokenResponse(
        access_token=session.session.access_token,
        refresh_token=session.session.refresh_token,
    )


@router.get("/me", response_model=UserProfile)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    client = get_service_client()
    result = client.table("users").select("*").eq("id", current_user.id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User profile not found")
    return UserProfile(**result.data)

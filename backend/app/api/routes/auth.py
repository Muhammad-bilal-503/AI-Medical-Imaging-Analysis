from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client

from app.core.config import get_settings
from app.db.supabase_client import get_service_client
from app.dependencies.auth import get_current_user
from app.models.schemas import (
    CurrentUser,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    """
    Creates the Supabase auth user via standard self-registration
    (auth.sign_up), then a matching row in public.users.

    NOTE: this intentionally does NOT use client.auth.admin.create_user().
    That call requires the Auth Admin API to recognize the caller as
    service_role — which the old JWT-format service_role key encoded
    directly in its claims. Supabase's newer opaque secret key isn't a
    JWT, so the Auth Admin API currently rejects it with "User not
    allowed" even though the exact same key correctly bypasses/satisfies
    RLS for ordinary database and storage calls. Using sign_up() sidesteps
    the Admin API entirely — it's the same endpoint a real self-registering
    user would hit.

    This requires "Confirm email" to be OFF in Supabase Dashboard ->
    Authentication -> Sign In / Providers -> Email, otherwise sign_up()
    won't return a session until the user clicks a confirmation link, and
    this endpoint will 400.

    In production, gate this behind an admin invite flow rather than open
    signup — clinical staff accounts shouldn't self-register.
    """
    anon_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)

    try:
        result = anon_client.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
                "options": {
                    "data": {"full_name": payload.full_name, "role": payload.role.value}
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.session or not result.user:
        raise HTTPException(
            status_code=400,
            detail=(
                "Signup succeeded but no session was returned — this usually means "
                "'Confirm email' is enabled in Supabase Auth settings. Disable it "
                "(Authentication > Sign In / Providers > Email) for this flow, or "
                "confirm the account via the emailed link and then log in."
            ),
        )

    user_id = result.user.id
    anon_client.postgrest.auth(result.session.access_token)
    anon_client.table("users").insert(
        {
            "id": user_id,
            "full_name": payload.full_name,
            "role": payload.role.value,
            "specialty": payload.specialty,
            "license_number": payload.license_number,
        }
    ).execute()

    return TokenResponse(
        access_token=result.session.access_token,
        refresh_token=result.session.refresh_token,
    )


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

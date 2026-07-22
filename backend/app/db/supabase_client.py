from functools import lru_cache
from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_service_client() -> Client:
    """
    Uses the secret key — bypasses RLS. Only use for trusted
    server-side operations (e.g. writing audit logs, admin tasks).
    NEVER expose this client or key to the frontend.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)


def get_user_client(access_token: str) -> Client:
    """
    Uses the publishable key + the caller's access token, so Postgres RLS
    policies are enforced as that user. Prefer this for normal
    request-scoped reads/writes.

    NOTE: postgrest.auth() only authenticates the Postgrest (database)
    sub-client. The Storage sub-client is created lazily from
    client.options.headers, so we set the Authorization header there too
    — otherwise storage.objects RLS policies see this as an anonymous
    request and reject uploads with "new row violates row-level security
    policy" even though the database calls work fine.
    """
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
    client.options.headers["Authorization"] = f"Bearer {access_token}"
    client.postgrest.auth(access_token)
    return client


@lru_cache
def get_legacy_admin_client() -> Client:
    """
    Client authenticated with the LEGACY JWT-format service_role key,
    used ONLY for Supabase Auth Admin API calls (auth.admin.create_user,
    auth.admin.delete_user, etc). The new opaque secret key is rejected
    by those specific endpoints with "User not allowed" even though it
    works fine for ordinary database/storage calls — this is a
    Supabase-side gap in the new key rollout, not a bug in this app.
    Do not use this client for table/storage operations; use
    get_service_client() for those.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_LEGACY_SERVICE_ROLE_JWT)

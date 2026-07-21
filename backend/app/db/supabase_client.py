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

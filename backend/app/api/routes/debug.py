"""
TEMPORARY diagnostic route — delete this file once the patients-insert
RLS issue is resolved. Not meant to ship in a real deployment (it
leaks internal auth-context details).
"""

from fastapi import APIRouter, Depends

from app.db.supabase_client import get_user_client
from app.dependencies.auth import get_current_token, get_current_user
from app.models.schemas import CurrentUser

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/whoami")
def whoami(
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_current_token),
):
    client = get_user_client(token)

    # Ask Postgres, via PostgREST, what auth.role()/auth.uid() resolve to
    # for THIS exact request — this is what RLS policies actually see.
    pg_result = client.rpc("debug_whoami", {}).execute()

    return {
        "app_layer_current_user": {
            "id": current_user.id,
            "role": current_user.role,
            "email": current_user.email,
        },
        "postgres_rls_layer": pg_result.data,
    }

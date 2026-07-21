from functools import lru_cache

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings

settings = get_settings()


class InvalidTokenError(Exception):
    pass


@lru_cache
def _fetch_jwks() -> list[dict]:
    """Fetch and cache the project's JSON Web Key Set. Supabase's new
    asymmetric-key projects sign user tokens with a private key and
    publish the matching public keys here — we verify against those,
    there's no shared secret to keep on the server."""
    resp = httpx.get(settings.SUPABASE_JWKS_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()["keys"]


def _get_signing_key(kid: str | None) -> dict:
    keys = _fetch_jwks()
    match = next((k for k in keys if k.get("kid") == kid), None)
    if match is None:
        # Key rotated since our cache was populated — refresh once and retry.
        _fetch_jwks.cache_clear()
        keys = _fetch_jwks()
        match = next((k for k in keys if k.get("kid") == kid), None)
    if match is None:
        raise InvalidTokenError("Signing key not found in JWKS")
    return match


def decode_supabase_jwt(token: str) -> dict:
    """Verify and decode a Supabase-issued access token against the
    project's published JWKS (asymmetric signing — ES256 by default
    on new Supabase projects)."""
    try:
        header = jwt.get_unverified_header(token)
        signing_key = _get_signing_key(header.get("kid"))
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[signing_key.get("alg", "ES256")],
            audience="authenticated",
        )
        return payload
    except (JWTError, httpx.HTTPError, KeyError) as e:
        raise InvalidTokenError(str(e)) from e

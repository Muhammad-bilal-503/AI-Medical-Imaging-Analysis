from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str   # client-safe key, replaces old "anon" key
    SUPABASE_SECRET_KEY: str        # server-side key, replaces old "service_role" key
    SUPABASE_JWKS_URL: str          # new asymmetric-key projects expose this instead of a JWT secret
    SUPABASE_LEGACY_SERVICE_ROLE_JWT: str  # Settings > API > Legacy API Keys > service_role
    # ^ ONLY the legacy JWT-format service_role key can call the Auth
    # Admin API (auth.admin.create_user etc). The new secret key is
    # rejected by that specific API with "User not allowed" — see
    # app/db/supabase_client.py get_legacy_admin_client().

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"
    RATE_LIMIT_PER_MINUTE: int = 60

    BUCKET_MEDICAL_IMAGES: str = "medical-images"
    BUCKET_HEATMAPS: str = "heatmaps"
    BUCKET_REPORTS: str = "reports"

    GROQ_API_KEY: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

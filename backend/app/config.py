import os

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRETS = frozenset(
    {
        "",
        "change-me-phase-1",
        "dev-only-not-for-prod",
        "dev-compose-secret",
    }
)

LOCAL_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def normalize_origin(value: str) -> str:
    item = value.strip().rstrip("/")
    if not item:
        return ""
    if "://" not in item:
        item = f"https://{item}"
    return item


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./nasalter.db"
    xai_api_key: str = ""
    openai_api_key: str = ""
    xai_model: str = "grok-3"
    openai_vision_model: str = "gpt-4o-mini"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "nova"
    jwt_secret: str = "change-me-phase-1"
    cors_origins: str = ",".join(LOCAL_ORIGINS)
    frontend_origin: str = ""
    environment: str = "development"
    upload_dir: str = "./uploads"
    master_key: str = "dev-only-not-for-prod"
    document_retention_hours: int = 48

    @property
    def is_deployed(self) -> bool:
        if os.environ.get("RENDER", "").lower() in {"true", "1"}:
            return True
        return self.environment.lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> list[str]:
        origins: list[str] = []
        for raw in (*self.cors_origins.split(","), self.frontend_origin, *LOCAL_ORIGINS):
            origin = normalize_origin(raw)
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    def ensure_deploy_secrets(self) -> None:
        if not self.is_deployed:
            return
        if self.jwt_secret in INSECURE_SECRETS or len(self.jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET must be a unique production value (32+ characters). "
                "Do not use change-me / compose defaults."
            )
        if self.master_key in INSECURE_SECRETS or len(self.master_key) < 32:
            raise RuntimeError(
                "MASTER_KEY must be a unique production value (32+ characters). "
                "Do not use dev-only-not-for-prod."
            )


settings = Settings()

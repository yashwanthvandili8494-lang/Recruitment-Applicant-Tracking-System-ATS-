"""
Application configuration using Pydantic Settings.

All settings are loaded from environment variables or a .env file.
Sensitive values must be provided via environment variables in production.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Application ----------
    APP_NAME: str = "RecruitFlow"
    APP_ENV: str = "development"
    DEBUG: bool = False
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # ---------- Database ----------
    DATABASE_URL: str = "postgresql+asyncpg://recruitflow:recruitflow_dev@localhost:5432/recruitflow"
    DATABASE_URL_SYNC: str = "postgresql://recruitflow:recruitflow_dev@localhost:5432/recruitflow"

    # ---------- Authentication ----------
    JWT_SECRET_KEY: str = "change-this-to-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- Email ----------
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = False
    EMAIL_FROM: str = "noreply@recruitflow.dev"
    EMAIL_FROM_NAME: str = "RecruitFlow"

    # ---------- File Uploads ----------
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ---------- Redis ----------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---------- Logging ----------
    LOG_LEVEL: str = "INFO"

    # ---------- Demo ----------
    DEMO_ADMIN_EMAIL: str = "admin@recruitflow.dev"
    DEMO_ADMIN_PASSWORD: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB limit to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v == "change-this-to-a-random-64-char-string":
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is using the default value. "
                "Set a strong random secret in production!",
                stacklevel=2,
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

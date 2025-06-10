from __future__ import annotations

from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Core settings
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    DATABASE_URL: str = "sqlite:///./filemaster.db"

    # File handling
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {"pdf", "png", "jpg", "jpeg", "gif", "heic"}

    # Security
    SESSION_TIMEOUT: int = 7200  # 2 hours
    TOKEN_EXPIRY_DAYS: int = 7
    CLEANUP_GRACE_HOURS: int = 48

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour

    # Business rules
    MAX_MODULES_PER_REQUEST: int = 20
    DEFAULT_REQUEST_EXPIRY_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


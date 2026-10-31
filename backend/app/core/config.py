
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Locate .env file inside the backend directory.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):

    # PostgreSQL configuration
    db_user: str = "brightloop_app"
    db_password: str
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "brightloop_db"

    # JWT configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    # IMPORTANT: JWT token expiry configuration
    access_token_expire_minutes: int = 30

    # Password reset configuration
    reset_token_expire_minutes: int = 15

    # SMTP configuration for password reset emails
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Frontend URL for reset link
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

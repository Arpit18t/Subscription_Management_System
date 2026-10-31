
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Always locate .env inside the backend folder.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):

    # Database configuration
    db_user: str = "brightloop_app"
    db_password: str
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "brightloop_db"

    # JWT configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

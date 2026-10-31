
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_user: str = "brightloop_app"
    db_password: str
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "brightloop_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()

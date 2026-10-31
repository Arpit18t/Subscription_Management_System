"""Application configuration management using Pydantic Settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Brightloop Billing & Payments Engine"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL Database URL (psycopg2 driver)
    DATABASE_URL: str = "postgresql+psycopg2://testuser:testpass@localhost:5432/brightloop"
    TEST_DATABASE_URL: Optional[str] = "postgresql+psycopg2://testuser:testpass@localhost:5432/brightloop_test"

    # Security & Tokens
    SECRET_KEY: str = "brightloop-default-insecure-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

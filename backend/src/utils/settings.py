from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DB_CONNECTION: str

    # Auth / JWT
    SECRET_KEY: str
    ALGORITHM: str
    EXP_TIME: int  # Token expiry in minutes

    # Email (FastAPI-Mail)
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    # AI — Gemini API (optional: if not set, falls back to simulation mode)
    GEMINI_API_KEY: Optional[str] = None

    # Deployment — Vercel API
    VERCEL_TOKEN: Optional[str] = None
    VERCEL_PROJECT_ID: Optional[str] = None

    # Firebase Config for generated sites
    FIREBASE_API_KEY: Optional[str] = None
    FIREBASE_AUTH_DOMAIN: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = None
    FIREBASE_APP_ID: Optional[str] = None

settings = Settings()


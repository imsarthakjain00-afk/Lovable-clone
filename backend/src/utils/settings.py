from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # CORS Allowed Origins
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

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

    # AI — Groq API (optional: if not set, falls back to simulation mode)
    GROQ_API_KEY: Optional[str] = None

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

    # Path to the Firebase Admin SDK service account JSON (for backend token verification)
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None
    
    # Raw JSON string for the Firebase Service Account (used in Railway/production)
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    
    # Supabase Settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

settings = Settings()


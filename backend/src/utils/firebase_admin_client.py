import firebase_admin
from firebase_admin import auth, credentials
from src.utils.settings import settings

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None and settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verifies a Firebase ID token and returns the decoded claims.
    Returns None if verification fails or Firebase Admin is not configured.
    """
    if not _get_firebase_app():
        return None

    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None

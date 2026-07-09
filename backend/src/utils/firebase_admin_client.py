import firebase_admin
from firebase_admin import auth, credentials
from src.utils.settings import settings

_firebase_app = None


import json

def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
            try:
                cert_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(cert_dict)
                _firebase_app = firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Failed to load Firebase from JSON: {e}")
        elif settings.FIREBASE_SERVICE_ACCOUNT_PATH:
            try:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                _firebase_app = firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Failed to load Firebase from PATH: {e}")
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

from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from jwt.exceptions import InvalidTokenError
from src.Users.models import UserModel
from src.Users.dtos import UserSchema, LoginSchema
from src.Users.db_queries import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user_query
)
from src.utils.settings import settings
from src.utils.mail import send_email
from src.utils.firebase_admin_client import verify_firebase_id_token

password_hash = PasswordHash.recommended()

def get_password_hash(password: str):
    return password_hash.hash(password)

def verify_password(plain_password: str, hash_password: str):
    return password_hash.verify(
        plain_password,
        hash_password
    )

async def register_service(
    user_data: UserSchema,
    db: Session
):
    username_user = get_user_by_username(
        user_data.username,
        db
    )
    if username_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exist..."
        )

    email_user = get_user_by_email(
        user_data.email,
        db
    )
    if email_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exist..."
        )

    hash_password = get_password_hash(
        user_data.password
    )

    new_user = UserModel(
        name=user_data.name,
        username=user_data.username,
        email=user_data.email,
        hash_password=hash_password,
        mobile_number=user_data.mobile_number
    )

    new_user = create_user_query(
        new_user,
        db
    )

    try:
        await send_email(
            [new_user.email]
        )
    except Exception as e:
        print(f"Email sending failed: {e}")

    return new_user

def login_user_service(
    user_data: LoginSchema,
    db: Session
):
    user = get_user_by_username(
        user_data.username,
        db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found..."
        )   

    if not verify_password(
        user_data.password,
        user.hash_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials..."
        )

    return {"token": _build_jwt_token(user.id)}

def is_authenticated_service(
    request: Request,
    db: Session
):
    try:
        token = request.headers.get(
            "Authorization"
        )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Token provided..."
            )

        token = token.split(" ")[-1]

        data = jwt.decode(
            token,
            settings.SECRET_KEY,
            settings.ALGORITHM
        )

        user_id = data.get("_id")

        user = get_user_by_id(
            user_id,
            db
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found..."
            )

        return user

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token..."
        )


def _build_jwt_token(user_id: int) -> str:
    exp_time = datetime.now(timezone.utc) + timedelta(minutes=settings.EXP_TIME)
    return jwt.encode(
        {"_id": user_id, "exp": exp_time.timestamp()},
        settings.SECRET_KEY,
        settings.ALGORITHM,
    )


def google_login_service(id_token: str, db: Session):
    try:
        claims = verify_firebase_id_token(id_token)
        if not claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Google token."
            )

        email = claims.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google token has no email.")

        name = claims.get("name", email.split("@")[0])
        user = get_user_by_email(email, db)

        if not user:
            username = email.split("@")[0]
            existing = get_user_by_username(username, db)
            if existing:
                username = f"{username}_{secrets.token_hex(3)}"

            user = UserModel(
                name=name,
                username=username,
                email=email,
                hash_password=get_password_hash(secrets.token_hex(16)),
            )
            user = create_user_query(user, db)

        return {"token": _build_jwt_token(user.id)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("GOOGLE LOGIN CRASH:", error_trace)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend crash: {str(e)}"
        )

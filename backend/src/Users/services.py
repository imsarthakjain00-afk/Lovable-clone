from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
import jwt
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

    exp_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.EXP_TIME
    )

    token = jwt.encode(
        {
            "_id": user.id,
            "exp": exp_time.timestamp()
        },
        settings.SECRET_KEY,
        settings.ALGORITHM
    )

    return {
        "token": token
    }

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

from fastapi import APIRouter, Depends, status, Request
from src.Users.dtos import UserSchema, UserResponseSchema, LoginSchema, GoogleLoginSchema
from src.Users import controller
from sqlalchemy.orm import Session
from src.utils.db import get_db

user_routes = APIRouter(prefix="/users")


@user_routes.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserSchema, db: Session = Depends(get_db)):
    return await controller.register(user_data, db)


@user_routes.post("/login", status_code=status.HTTP_200_OK)
def login_user(user_data: LoginSchema, db: Session = Depends(get_db)):
    return controller.login_user(user_data, db)


@user_routes.get("/is_auth", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
def is_auth(request: Request, db: Session = Depends(get_db)):
    return controller.is_authenticated(request, db)


@user_routes.post("/google-login", status_code=status.HTTP_200_OK)
def google_login(request_body: GoogleLoginSchema, db: Session = Depends(get_db)):
    return controller.google_login(request_body.id_token, db)

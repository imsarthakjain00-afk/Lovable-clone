from src.Users.services import (
    register_service,
    login_user_service,
    is_authenticated_service,
    google_login_service,
)


async def register(user_data, db):
    return await register_service(user_data, db)


def login_user(user_data, db):
    return login_user_service(user_data, db)


def is_authenticated(request, db):
    return is_authenticated_service(request, db)


def google_login(id_token: str, db):
    return google_login_service(id_token, db)

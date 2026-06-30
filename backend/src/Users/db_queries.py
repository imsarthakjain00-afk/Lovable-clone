from sqlalchemy.orm import Session
from src.Users.models import UserModel

def get_user_by_username(username: str, db: Session):
    return (
        db.query(UserModel)
        .filter(UserModel.username == username)
        .first()
    )

def get_user_by_email(email: str, db: Session):
    return (
        db.query(UserModel)
        .filter(UserModel.email == email)
        .first()
    )

def get_user_by_id(user_id: int, db: Session):
    return (
        db.query(UserModel)
        .filter(UserModel.id == user_id)
        .first()
    )

def create_user_query(user: UserModel, db: Session):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

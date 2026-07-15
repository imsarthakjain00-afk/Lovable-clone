from pydantic import BaseModel

from typing import Optional

class UserSchema(BaseModel):
    name: str
    username: str
    email: str
    password: str
    mobile_number: Optional[int] = None

class UserResponseSchema(BaseModel):
    id: int
    name: str
    username: str
    email: str
    mobile_number: Optional[int] = None

class LoginSchema(BaseModel):
    username: str
    password: str


class GoogleLoginSchema(BaseModel):
    id_token: str

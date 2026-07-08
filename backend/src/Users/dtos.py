from pydantic import BaseModel

class UserSchema(BaseModel):
    name: str
    username: str
    email: str
    password: str
    mobile_number: int

class UserResponseSchema(BaseModel):
    id: int
    name: str
    username: str
    email: str
    mobile_number: int

class LoginSchema(BaseModel):
    username: str
    password: str


class GoogleLoginSchema(BaseModel):
    id_token: str

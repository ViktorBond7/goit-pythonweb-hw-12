from pydantic import BaseModel, ConfigDict, EmailStr
from src.models.user import Role


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    avatar: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    confirmed: bool
    avatar: str | None = None
    role: Role


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class RequestPasswordReset(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str

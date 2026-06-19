from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str
    region: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    region: Optional[str]
    is_admin: bool
    created_at: datetime


class TokenResponse(BaseModel):
    token: str
    user: UserResponse

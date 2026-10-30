"""Authentication request and response schemas."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class SignupRequest(BaseModel):
    email: EmailStr = Field(max_length=150)
    password: str = Field(min_length=10, max_length=200)
    password_confirmation: str = Field(min_length=10, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)
    role: Literal["administrator", "retail_manager", "analyst", "quality_user"]


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=10, max_length=200)


class UserRead(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str



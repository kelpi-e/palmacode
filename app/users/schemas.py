from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from users.models import RoleEnum


class SRegister(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")
    role: str = Field(default="user", description="Роль пользователя (admin или user)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in [RoleEnum.admin.value, RoleEnum.user.value]:
            raise ValueError(f"Роль должна быть 'admin' или 'user', получено: {v}")
        return v


class SLogin(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль")


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SUpdateUser(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = Field(None, description="Email пользователя")
    password: Optional[str] = Field(None, min_length=6, description="Пароль (минимум 6 символов)")
    role: Optional[str] = Field(None, description="Роль пользователя (admin или user)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in [RoleEnum.admin.value, RoleEnum.user.value]:
            raise ValueError(f"Роль должна быть 'admin' или 'user', получено: {v}")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
        if v is not None and not v.strip():
            raise ValueError("Email не может быть пустым")
        return v


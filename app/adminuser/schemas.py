from pydantic import BaseModel, Field
from typing import Optional


class SCreateInvitation(BaseModel):
    """Схема для создания приглашения"""
    pass


class SInvitationResponse(BaseModel):
    """Схема ответа с пригласительным кодом"""
    link: str
    admin_id: int


class SJoinAdmin(BaseModel):
    """Схема для присоединения к админу"""
    code: str = Field(..., description="Пригласительный код")


class SAdminUserResponse(BaseModel):
    """Схема связи админ-пользователь"""
    admin_id: int
    user_id: int

    class Config:
        from_attributes = True


class SAdminInfo(BaseModel):
    """Информация об админе"""
    id: int
    email: str

    class Config:
        from_attributes = True


class SUserInfo(BaseModel):
    """Информация о пользователе"""
    id: int
    email: str

    class Config:
        from_attributes = True




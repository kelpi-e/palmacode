from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional


class SAddVideo(BaseModel):
    """Схема для добавления видео"""
    url: str = Field(..., description="URL видео", min_length=1, max_length=500)
    name: str = Field(..., description="Название видео", min_length=1, max_length=120)


    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация названия"""
        if not v or not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()


class SUpdateVideo(BaseModel):
    """Схема для обновления видео"""
    url: Optional[str] = Field(None, description="URL видео", max_length=500)
    name: Optional[str] = Field(None, description="Название видео", max_length=120)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Валидация названия при обновлении"""
        if v is not None and not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip() if v else v


class SVideo(BaseModel):
    """Схема для отображения видео"""
    id: int
    url: str
    name: str
    uploaded_by: int

    class Config:
        from_attributes = True


class SVideoCreateResponse(BaseModel):
    """Схема ответа при создании видео"""
    id: int
    url: str
    name: str
    uploaded_by: int
    message: str = "Видео успешно создано"

    class Config:
        from_attributes = True

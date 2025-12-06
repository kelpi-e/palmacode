from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SCreateUser(BaseModel):
    email: EmailStr
    role: str = Field(..., enum=['admin', 'tester'])
    password: str = Field(min_length=8, max_length=16)

class SLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)

class SUserResponse(BaseModel):
    id: int
    email: EmailStr
    token: str
    class Config:
        orm_mode = True
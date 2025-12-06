from enum import Enum as enum
from sqlalchemy import Column, Enum, Integer, String
from database.database import Base

class RoleEnum(enum):
    admin = 'admin'
    user = 'user'

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True)
    role = Column(Enum(RoleEnum, name='role_enum'), default=RoleEnum.user)
    password = Column(String(120))

    
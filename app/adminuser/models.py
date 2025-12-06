from enum import Enum as enum
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, UniqueConstraint
from database.database import Base


class Invitation(Base):
    __tablename__ = 'invitations'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    link = Column(String(120), unique=True, nullable=False)


class UserToAdmin(Base):
    __tablename__ = 'user_to_admin'
    admin_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)


    



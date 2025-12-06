from enum import Enum as enum
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from database.database import Base


class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    url = Column(String(120))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)


    
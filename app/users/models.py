from sqlalchemy import Column, Enum, Integer, String, Text

from database.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    role = Column(Enum("admin", "user"), default="user")
    email = Column(String, unique=True)
    hashPassword = Column(String)



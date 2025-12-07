from sqlalchemy import Column, ForeignKey, Integer, DateTime
from database.database import Base
from datetime import datetime


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    end_time = Column(DateTime, nullable=False)

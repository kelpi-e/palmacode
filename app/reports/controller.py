from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.database import async_session_maker
from reports.models import Report


class ReportController:

    @classmethod
    async def create_report(
        cls,
        start_time: datetime,
        video_id: int
    ) -> Report:
        """Создать отчет"""
        async with async_session_maker() as session:
            try:
                report = Report(
                    start_time=start_time,
                    video_id=video_id,
                )
                session.add(report)
                await session.commit()
                await session.refresh(report)
                return report
            except IntegrityError:
                await session.rollback()
                raise ValueError("Ошибка при создании отчета")

    @classmethod
    async def update_report(cls, id: int, end_time: datetime) -> Optional[Report]:
        async with async_session_maker() as session:
            report = ReportController.get_report_by_id(id)
            if not report:
                return None
            report.end_time = end_time
            await session.commit()
            await session.refresh(report)  
            return report
    
    @classmethod
    async def get_report_by_id(cls, report_id: int) -> Optional[Report]:
        """Получить отчет по ID"""
        async with async_session_maker() as session:
            query = select(Report).where(Report.id == report_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()


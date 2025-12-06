from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.database import async_session_maker
from videos.models import Video


class VideoController:
    """Контроллер для работы с видео"""

    @classmethod
    async def get_all_videos(cls) -> List[Video]:
        """Получить все видео"""
        async with async_session_maker() as session:
            query = select(Video)
            result = await session.execute(query)
            return list(result.scalars().all())
        
    @classmethod
    async def get_videos_by_user(cls, user_id: int) -> List[Video]:
        """Получить все видео пользователя"""
        async with async_session_maker() as session:
            query = select(Video).where(Video.uploaded_by == user_id)
            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def get_video_by_id(cls, video_id: int) -> Optional[Video]:
        """Получить видео по ID"""
        async with async_session_maker() as session:
            query = select(Video).where(Video.id == video_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_video_by_url(cls, url: str) -> Optional[Video]:
        """Найти видео по URL"""
        async with async_session_maker() as session:
            query = select(Video).where(Video.url == url)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def create_video(
        cls, 
        name: str, 
        url: str, 
        uploaded_by: int
    ) -> Video:
        """Создать новое видео"""
        async with async_session_maker() as session:
            try:
                video = Video(
                    name=name,
                    url=url,
                    uploaded_by=uploaded_by
                )
                session.add(video)
                await session.commit()
                await session.refresh(video)
                return video
            except IntegrityError:
                await session.rollback()
                raise ValueError("Видео с таким URL уже существует")

    @classmethod
    async def update_video(
        cls,
        video_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None
    ) -> Optional[Video]:
        """Обновить видео"""
        async with async_session_maker() as session:
            query = select(Video).where(Video.id == video_id)
            result = await session.execute(query)
            video = result.scalar_one_or_none()
            
            if not video:
                return None
            
            if name is not None:
                video.name = name
            if url is not None:
                # Проверка на дубликат URL
                existing_query = select(Video).where(Video.url == url)
                existing_result = await session.execute(existing_query)
                existing_video = existing_result.scalar_one_or_none()
                if existing_video and existing_video.id != video_id:
                    raise ValueError("Видео с таким URL уже существует")
                video.url = url
            
            await session.commit()
            await session.refresh(video)
            return video

    @classmethod
    async def delete_video(cls, video_id: int) -> bool:
        """Удалить видео по ID"""
        async with async_session_maker() as session:
            query = select(Video).where(Video.id == video_id)
            result = await session.execute(query)
            video = result.scalar_one_or_none()
            
            if not video:
                return False
            
            await session.delete(video)
            await session.commit()
            return True

    @classmethod
    async def check_video_ownership(cls, video_id: int, user_id: int) -> bool:
        """Проверить, принадлежит ли видео пользователю"""
        video = await cls.get_video_by_id(video_id)
        if not video:
            return False
        return video.uploaded_by == user_id
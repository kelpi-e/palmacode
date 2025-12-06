import os
from typing import Optional, List
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.database import async_session_maker
from videos.models import Video
from adminuser.controller import AdminUserController

UPLOADS_DIR = Path("uploads")


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
    async def get_videos_by_users(cls, user_ids: List[int]) -> List[Video]:
        """Получить все видео по списку пользователей"""
        async with async_session_maker() as session:
            if not user_ids:
                return []
            query = select(Video).where(Video.uploaded_by.in_(user_ids))
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

    @classmethod
    async def get_user_accessible_ids(cls, user_id: int, admin_ids: List[int]) -> List[int]:
        """Получить список ID пользователей, видео которых доступны текущему пользователю"""
        user_ids = [user_id]
        user_ids.extend(admin_ids)
        return user_ids

    @classmethod
    async def check_video_access(cls, video_id: int, user_id: int) -> bool:
        """Проверить, есть ли у пользователя доступ к видео"""
        video = await cls.get_video_by_id(video_id)
        if not video:
            return False
        
        user_ids = [user_id]
        connections = await AdminUserController.get_user_admins(user_id)
        admin_ids = [conn.admin_id for conn in connections]
        user_ids.extend(admin_ids)
        
        return video.uploaded_by in user_ids

    @classmethod
    async def get_accessible_videos(cls, user_id: int) -> List[Video]:
        """Получить все доступные видео для пользователя"""
        user_ids = [user_id]
        connections = await AdminUserController.get_user_admins(user_id)
        admin_ids = [conn.admin_id for conn in connections]
        user_ids.extend(admin_ids)
        
        return await cls.get_videos_by_users(user_ids)

    @classmethod
    async def get_accessible_video(cls, video_id: int, user_id: int) -> Optional[Video]:
        """Получить видео по ID с проверкой доступа"""
        has_access = await cls.check_video_access(video_id, user_id)
        if not has_access:
            return None
        return await cls.get_video_by_id(video_id)

    @classmethod
    async def create_video_with_validation(
        cls,
        name: str,
        url: str,
        uploaded_by: int
    ) -> Video:
        """Создать видео с валидацией файла"""
        file_path = url
        
        if not os.path.isabs(file_path):
            file_path = str(UPLOADS_DIR / file_path)
        
        if not os.path.exists(file_path):
            raise ValueError(f"Файл не найден: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError("Указанный путь не является файлом")
        
        existing_video = await cls.find_video_by_url(file_path)
        if existing_video:
            raise ValueError("Видео с таким URL уже существует")
        
        return await cls.create_video(name=name, url=file_path, uploaded_by=uploaded_by)

    @classmethod
    async def update_video_with_permission(
        cls,
        video_id: int,
        user_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None
    ) -> Optional[Video]:
        """Обновить видео с проверкой прав"""
        video = await cls.get_video_by_id(video_id)
        if not video:
            return None
        
        if video.uploaded_by != user_id:
            raise ValueError("Нет прав для обновления этого видео")
        
        return await cls.update_video(video_id=video_id, name=name, url=url)

    @classmethod
    async def delete_video_with_permission(cls, video_id: int, user_id: int) -> bool:
        """Удалить видео с проверкой прав"""
        video = await cls.get_video_by_id(video_id)
        if not video:
            return False
        
        if video.uploaded_by != user_id:
            raise ValueError("Нет прав для удаления этого видео")
        
        return await cls.delete_video(video_id)

    @classmethod
    async def get_video_file_path(cls, video_id: int, user_id: int) -> Optional[str]:
        """Получить путь к файлу видео с проверкой доступа"""
        has_access = await cls.check_video_access(video_id, user_id)
        if not has_access:
            return None
        
        video = await cls.get_video_by_id(video_id)
        if not video:
            return None
        
        file_path = video.url
        
        if not os.path.isabs(file_path):
            file_path = str(file_path)
        
        if not os.path.exists(file_path):
            raise ValueError(f"Файл не найден по указанному пути: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError("Указанный путь не является файлом")
        
        return file_path
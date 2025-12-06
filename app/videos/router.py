import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from services.usersDepends import get_current_user
from users.models import User
from videos.schemas import (
    SAddVideo, 
    SVideo, 
    SUpdateVideo, 
    SVideoCreateResponse
)
from videos.controller import VideoController


router = APIRouter(
    prefix="/video",
    tags=["VIDEO"]
)


@router.get(
    "/",
    response_model=List[SVideo],
    status_code=status.HTTP_200_OK,
    summary="Получить все видео пользователя",
    description="Возвращает список всех видео пользователя и его админов"
)
async def get_all_videos(
    current_user: User = Depends(get_current_user)
) -> List[SVideo]:
    """Получить все видео текущего пользователя и его админов"""
    videos = await VideoController.get_accessible_videos(current_user.id)
    return [
        SVideo(
            id=video.id,
            url=video.url,
            name=video.name,
            uploaded_by=video.uploaded_by
        )
        for video in videos
    ]


@router.get(
    "/{video_id}",
    response_model=SVideo,
    status_code=status.HTTP_200_OK,
    summary="Получить видео по ID",
    description="Возвращает информацию о конкретном видео"
)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user)
) -> SVideo:
    """Получить видео по ID"""
    video = await VideoController.get_accessible_video(video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Видео не найдено или нет доступа"
        )
    
    return SVideo(
        id=video.id,
        url=video.url,
        name=video.name,
        uploaded_by=video.uploaded_by
    )


@router.post(
    "/",
    response_model=SVideoCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое видео",
    description="Добавляет новое видео"
)
async def create_video(
    video: SAddVideo,
    current_user: User = Depends(get_current_user)
) -> SVideoCreateResponse:
    """Создать новое видео"""
    try:
        new_video = await VideoController.create_video_with_validation(
            name=video.name,
            url=video.url,
            uploaded_by=current_user.id
        )
        return SVideoCreateResponse(
            id=new_video.id,
            url=new_video.url,
            name=new_video.name,
            uploaded_by=new_video.uploaded_by,
            message="Видео успешно создано"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{video_id}",
    response_model=SVideo,
    status_code=status.HTTP_200_OK,
    summary="Обновить видео",
    description="Обновляет инф о видео"
)
async def update_video(
    video_id: int,
    video_data: SUpdateVideo,
    current_user: User = Depends(get_current_user)
) -> SVideo:
    """Обновить видео"""
    try:
        updated_video = await VideoController.update_video_with_permission(
            video_id=video_id,
            user_id=current_user.id,
            name=video_data.name,
            url=video_data.url
        )
        
        if not updated_video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Видео не найдено"
            )
        
        return SVideo(
            id=updated_video.id,
            url=updated_video.url,
            name=updated_video.name,
            uploaded_by=updated_video.uploaded_by
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "прав" in str(e) else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить видео",
    description="Удаляет видео"
)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить видео"""
    try:
        deleted = await VideoController.delete_video_with_permission(
            video_id=video_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Видео не найдено"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    return None


@router.get(
    "/file/{video_id}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Скачать файл видео",
    description="Отдает файл видео по пути из базы данных"
)
async def download_video_file(
    video_id: int,
    current_user: User = Depends(get_current_user)
):
    """Скачать файл видео"""
    try:
        file_path = await VideoController.get_video_file_path(video_id, current_user.id)
        
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Видео не найдено или нет доступа"
            )
        
        video = await VideoController.get_video_by_id(video_id)
        
        return FileResponse(
            path=file_path,
            filename=video.name or os.path.basename(file_path),
            media_type='application/octet-stream'
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

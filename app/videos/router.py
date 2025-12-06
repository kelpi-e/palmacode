from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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
    description="Возвращает список всех видео, загруженных текущим пользователем"
)
async def get_all_videos(
    current_user: User = Depends(get_current_user)
) -> List[SVideo]:
    """Получить все видео текущего пользователя"""
    videos = await VideoController.get_videos_by_user(current_user.id)
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
    video = await VideoController.get_video_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Видео не найдено"
        )
    
    # можно видеть только свои видео
    if video.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому видео"
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
    existing_video = await VideoController.find_video_by_url(video.url)
    if existing_video:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Видео с таким URL уже существует"
        )
    
    try:
        new_video = await VideoController.create_video(
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
    video = await VideoController.get_video_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Видео не найдено"
        )
    
    if video.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для обновления этого видео"
        )
    
    try:
        updated_video = await VideoController.update_video(
            video_id=video_id,
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
            status_code=status.HTTP_400_BAD_REQUEST,
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
    video = await VideoController.get_video_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Видео не найдено"
        )
    
    if video.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления этого видео"
        )
    
    deleted = await VideoController.delete_video(video_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Видео не найдено"
        )
    
    return None

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from users.controller import UserController
from users.schemas import UserResponse, SUpdateUser
from users.models import User, RoleEnum
from services.usersDepends import get_current_user
from users.auth import get_password_hash


router = APIRouter(
    prefix="/users",
    tags=["USERS"]
)


@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить всех пользователей",
    description="Возвращает список всех пользователей"
)
async def get_all_users() -> List[UserResponse]:
    """Получить всех пользователей"""
    users = await UserController.get_all_users()
    return [
        UserResponse(id=user.id, email=user.email, role=user.role.value)
        for user in users
    ]


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить текущего пользователя",
    description="Возвращает информацию о текущем пользователе"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Получить информацию о текущем пользователе"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить пользователя по ID",
    description="Возвращает информацию о пользователе по его ID"
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Получить пользователя по ID"""
    user = await UserController.find_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить пользователя",
    description="Обновляет информацию о пользователе"
)
async def update_user(
    user_id: int,
    user_data: SUpdateUser,
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Обновить пользователя"""
    user = await UserController.find_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # пользователь может обновлять только свой профиль,
    if user.id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для обновления этого пользователя"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя изменить свою роль"
        )
    
    try:
        hashed_password = None
        if user_data.password:
            hashed_password = get_password_hash(user_data.password)
        
        updated_user = await UserController.update_user(
            user_id=user_id,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            role=updated_user.role.value
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Удаляет пользователя из системы"
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Удалить пользователя"""
    # Проверка существования пользователя
    user = await UserController.find_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # пользователь может удалить только свой профиль,ё
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления"
        )
    
    deleted = await UserController.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return None
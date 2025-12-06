from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from services.usersDepends import get_current_user
from users.models import User, RoleEnum
from adminuser.schemas import (
    SCreateInvitation,
    SInvitationResponse,
    SJoinAdmin,
    SAdminUserResponse,
    SAdminInfo
)
from adminuser.controller import AdminUserController
from users.controller import UserController


router = APIRouter(
    prefix="/adminuser",
    tags=["ADMINUSER"]
)


@router.post(
    "/invitation",
    response_model=SInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пригласительный код",
    description="Создает пригласительный код для админа"
)
async def create_invitation(
    current_user: User = Depends(get_current_user)
) -> SInvitationResponse:
    """Создать пригласительный код"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ может создавать приглашения"
        )
    
    invitation_link = await AdminUserController.create_invitation(current_user.id)
    return SInvitationResponse(
        link=invitation_link,
        admin_id=current_user.id
    )


@router.post(
    "/join",
    response_model=SAdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Присоединиться к админу",
    description="Присоединяет пользователя к админу по пригласительному коду"
)
async def join_admin(
    join_data: SJoinAdmin,
    current_user: User = Depends(get_current_user)
) -> SAdminUserResponse:
    """Присоединиться к админу"""
    if current_user.role == RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Админ не может присоединяться к другому админу"
        )
    
    try:
        user_to_admin = await AdminUserController.join_admin(
            current_user.id,
            join_data.code
        )
        return SAdminUserResponse(
            admin_id=user_to_admin.admin_id,
            user_id=user_to_admin.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/my-admins",
    response_model=List[SAdminInfo],
    status_code=status.HTTP_200_OK,
    summary="Получить моих админов",
    description="Возвращает список админов, к которым привязан пользователь"
)
async def get_my_admins(
    current_user: User = Depends(get_current_user)
) -> List[SAdminInfo]:
    """Получить моих админов"""
    connections = await AdminUserController.get_user_admins(current_user.id)
    admin_ids = [conn.admin_id for conn in connections]
    
    admins = []
    for admin_id in admin_ids:
        admin = await UserController.find_user_by_id(admin_id)
        if admin and admin.role == RoleEnum.admin:
            admins.append(SAdminInfo(id=admin.id, email=admin.email))
    
    return admins


@router.get(
    "/my-users",
    response_model=List[SAdminInfo],
    status_code=status.HTTP_200_OK,
    summary="Получить моих пользователей",
    description="Возвращает список пользователей, привязанных к админу"
)
async def get_my_users(
    current_user: User = Depends(get_current_user)
) -> List[SAdminInfo]:
    """Получить моих пользователей"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ может просматривать своих пользователей"
        )
    
    connections = await AdminUserController.get_admin_users(current_user.id)
    user_ids = [conn.user_id for conn in connections if conn.user_id != current_user.id]
    
    users = []
    for user_id in user_ids:
        user = await UserController.find_user_by_id(user_id)
        if user:
            users.append(SAdminInfo(id=user.id, email=user.email))
    
    return users


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отвязать пользователя",
    description="Отвязывает пользователя от админа"
)
async def remove_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отвязать пользователя"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ может отвязывать пользователей"
        )
    
    deleted = await AdminUserController.delete_connection(
        current_user.id,
        user_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь не найдена"
        )
    
    return None


@router.delete(
    "/leave/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отвязаться от админа",
    description="Отвязывает пользователя от админа"
)
async def leave_admin(
    admin_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отвязаться от админа"""
    deleted = await AdminUserController.delete_connection(
        admin_id,
        current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь не найдена"
        )
    
    return None




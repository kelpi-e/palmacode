import secrets
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from database.database import async_session_maker
from adminuser.models import UserToAdmin, Invitation
from users.models import User, RoleEnum


class AdminUserController:

    @classmethod
    async def create_invitation(cls, admin_id: int) -> str:
        """Создать пригласительный код для админа"""
        async with async_session_maker() as session:
            invitation_link = secrets.token_urlsafe(32)
            
            try:
                invitation = Invitation(
                    admin_id=admin_id,
                    link=invitation_link
                )
                session.add(invitation)
                await session.commit()
                return invitation_link
            except IntegrityError:
                await session.rollback()
                raise ValueError("Ошибка при создании приглашения")

    @classmethod
    async def find_invitation_by_link(cls, link: str) -> Optional[Invitation]:
        """Найти приглашение по ссылке"""
        async with async_session_maker() as session:
            query = select(Invitation).where(Invitation.link == link)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def join_admin(cls, user_id: int, invitation_link: str) -> UserToAdmin:
        """Присоединить пользователя к админу по invitation ссылке"""
        invitation = await cls.find_invitation_by_link(invitation_link)
        if not invitation:
            raise ValueError("Пригласительная ссылка не найдена")
        
        admin_id = invitation.admin_id
        
        if admin_id == user_id:
            raise ValueError("Нельзя присоединиться к самому себе")
        
        existing = await cls.get_connection(admin_id, user_id)
        if existing:
            raise ValueError("Пользователь уже привязан к этому админу")
        
        async with async_session_maker() as session:
            try:
                user_to_admin = UserToAdmin(
                    admin_id=admin_id,
                    user_id=user_id
                )
                session.add(user_to_admin)
                await session.commit()
                await session.refresh(user_to_admin)
                return user_to_admin
            except IntegrityError:
                await session.rollback()
                raise ValueError("Пользователь уже привязан к этому админу")

    @classmethod
    async def get_connection(cls, admin_id: int, user_id: int) -> Optional[UserToAdmin]:
        """Получить связь админ-пользователь"""
        async with async_session_maker() as session:
            query = select(UserToAdmin).where(
                and_(UserToAdmin.admin_id == admin_id, UserToAdmin.user_id == user_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_user_admins(cls, user_id: int) -> List[UserToAdmin]:
        """Получить всех админов пользователя"""
        async with async_session_maker() as session:
            query = select(UserToAdmin).where(UserToAdmin.user_id == user_id)
            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def get_admin_users(cls, admin_id: int) -> List[UserToAdmin]:
        """Получить всех пользователей админа (исключая самого админа)"""
        async with async_session_maker() as session:
            query = select(UserToAdmin).where(
                and_(
                    UserToAdmin.admin_id == admin_id,
                    UserToAdmin.user_id != admin_id
                )
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def delete_connection(cls, admin_id: int, user_id: int) -> bool:
        """Удалить связь админ-пользователь"""
        async with async_session_maker() as session:
            query = select(UserToAdmin).where(
                and_(UserToAdmin.admin_id == admin_id, UserToAdmin.user_id == user_id)
            )
            result = await session.execute(query)
            user_to_admin = result.scalar_one_or_none()
            
            if not user_to_admin:
                return False
            
            await session.delete(user_to_admin)
            await session.commit()
            return True

    @classmethod
    async def check_user_has_access(cls, user_id: int, admin_id: int) -> bool:
        """Проверить, есть ли у пользователя доступ к админу"""
        connection = await cls.get_connection(admin_id, user_id)
        return connection is not None


from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.database import async_session_maker
from users.models import User, RoleEnum


class UserController:
    """Контроллер для работы с пользователями"""

    @classmethod
    async def get_all_users(cls) -> List[User]:
        """Получить всех пользователей"""
        async with async_session_maker() as session:
            query = select(User)
            result = await session.execute(query)
            return list(result.scalars().all())
        
    @classmethod
    async def find_user_by_email(cls, user_email: str) -> Optional[User]:
        """Найти пользователя по email"""
        async with async_session_maker() as session:
            query = select(User).where(User.email == user_email)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_user_by_id(cls, user_id: int) -> Optional[User]:
        """Найти пользователя по ID"""
        async with async_session_maker() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
    @classmethod
    async def create_user(
        cls, 
        email: str, 
        password: str, 
        role: str = RoleEnum.user.value
    ) -> User:
        """Создать нового пользователя"""
        async with async_session_maker() as session:
            try:
                # Валидация и преобразование роли
                try:
                    role_enum = RoleEnum(role)
                except ValueError:
                    role_enum = RoleEnum.user
                
                user = User(
                    email=email,
                    password=password,
                    role=role_enum
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError:
                await session.rollback()
                raise ValueError("Пользователь с таким email уже существует")
            except ValueError as e:
                await session.rollback()
                raise e

    @classmethod
    async def update_user(
        cls,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[User]:
        """Обновить пользователя"""
        async with async_session_maker() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            try:
                if email is not None:
                    # Проверка на дубликат email
                    existing_query = select(User).where(User.email == email, User.id != user_id)
                    existing_result = await session.execute(existing_query)
                    existing_user = existing_result.scalar_one_or_none()
                    if existing_user:
                        raise ValueError("Пользователь с таким email уже существует")
                    user.email = email
                
                if password is not None:
                    user.password = password
                
                if role is not None:
                    try:
                        user.role = RoleEnum(role)
                    except ValueError:
                        user.role = RoleEnum.user
                
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError:
                await session.rollback()
                raise ValueError("Пользователь с таким email уже существует")
            except ValueError as e:
                await session.rollback()
                raise e

    @classmethod
    async def delete_user(cls, user_id: int) -> bool:
        """Удалить пользователя по ID"""
        async with async_session_maker() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            await session.delete(user)
            await session.commit()
            return True

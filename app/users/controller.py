# app/users/crud.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from app.users.models import User
from app.security.security import hash_password, create_access_token, verify_password
from app.users.schemas import SCreateUser, SLogin, SUserResponse



class UsersController:

    @classmethod
    async def register(cls, user: SCreateUser) -> SUserResponse:
        h_password = hash_password(user.password)
        async with AsyncSession() as session:
            async with session.begin():
                try:
                    query = (
                        insert(User)
                        .values(email=user.email, role=user.role, hashPassword=user.password)
                        .returning(User)
                    )
                    rslt = await session.execute(query)
                    new_user = rslt.scalar_one()
                except:
                    return HTTPException(status_code=400, detail="Email already registered")
            await session.commit()
        return SUserResponse.model_validate(new_user)
    
    @classmethod
    async def login(cls, user: SLogin) -> SUserResponse:
        async with AsyncSession() as session:
            async with session.begin():
                try:
                    query = select(User).where(User.email == user.email)
                    rslt = await session.execute(query)
                    usr = rslt.scalar_one_or_none()
                    if not user or not verify_password(usr.hashPassword, user.password):
                        return HTTPException(status_code=400, detail="Error")
                except:
                    return HTTPException(status_code=500)
            await session.commit()
        access_token = create_access_token(str(user.))
        return SUserResponse.model_validate(usr)





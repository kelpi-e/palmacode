from fastapi import APIRouter, Form
from app.users.schemas import SCreateUser, SUserResponse
from users.controller import UsersController


router = APIRouter(
    prefix="/users",
    tags=["Пользователи"]
)


@router.post("/register")
async def register(user: SCreateUser) -> SUserResponse:
    return await UsersController.register(user)

@router.post("/register")
async def register(user: SCreateUser) -> SUserResponse:
    return await UsersController.register(user)
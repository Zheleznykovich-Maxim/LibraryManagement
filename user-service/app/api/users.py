from typing import List

from app.api import db_manager
from app.api.models import UserIn, UserOut, User
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status
import jwt


# Секретный ключ для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users = FastAPI()

# Зависимость для проверки токена
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        user = await db_manager.get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


@users.get('/')
async def get_users(current_user: User = Depends(oauth2_scheme)):
    users_list = await db_manager.get_all_users()
    return users_list


@users.get("/search")
async def search_users(
        email: str,  # Параметр для поиска по email
        current_user: User = Depends(oauth2_scheme)
):
    user = await db_manager.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

@users.get('/{id}/', response_model=UserOut)
async def get_user(
        id: int,
        current_user: User = Depends(oauth2_scheme)):

    user = await db_manager.get_user(id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

# Эндпоинт для получения профиля
@users.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

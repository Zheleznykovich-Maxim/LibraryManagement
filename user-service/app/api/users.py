from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status
import jwt
import json  # Для сериализации/десериализации
from app.api import db_manager
from app.api.models import UserIn, UserOut, User
import aioredis

# Секретный ключ для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
users = APIRouter()

# Подключение к Redis
REDIS_HOST = "redis"
REDIS_PORT = 6379
redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

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
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# Получение всех пользователей с кэшированием
@users.get('/')
async def get_users(current_user: User = Depends(oauth2_scheme)):
    # Проверка кэша
    cached_users = await redis.get("users:all")
    if cached_users:
        users_list = json.loads(cached_users)
        return {"data": users_list, "source": "cache"}

    # Если данных нет в кэше, получаем их из базы
    users_list = await db_manager.get_all_users()
    users_serialized = [dict(user) for user in users_list]

    # Сохраняем данные в кэше
    await redis.set("users:all", json.dumps(users_serialized), ex=3600)  # Кэш на 1 час
    return {"data": users_serialized, "source": "database"}


# Поиск пользователя по email с кэшированием
@users.get("/search/{email}", response_model=UserOut)
async def search_users(
    email: str,
    current_user: User = Depends(oauth2_scheme)
):
    cache_key = f"user:email:{email}"
    cached_user = await redis.get(cache_key)
    if cached_user:
        user = json.loads(cached_user)
        return UserOut(**user)  # Убедимся, что структура соответствует модели

    # Если данных нет в кэше, выполняем запрос
    user = await db_manager.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Кэшируем результат
    user_serialized = dict(user)
    await redis.set(cache_key, json.dumps(user_serialized), ex=3600)
    return UserOut(**user_serialized)  # Преобразуем данные в объект модели


# Получение пользователя по ID с кэшированием
@users.get('/{id}/', response_model=UserOut)
async def get_user(
    id: int,
    current_user: User = Depends(oauth2_scheme)
):
    cache_key = f"user:id:{id}"
    cached_user = await redis.get(cache_key)
    if cached_user:
        user = json.loads(cached_user)
        return UserOut(**user)  # Убедимся, что структура соответствует модели

    # Если данных нет в кэше, выполняем запрос
    user = await db_manager.get_user(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Кэшируем результат
    user_serialized = dict(user)
    await redis.set(cache_key, json.dumps(user_serialized), ex=3600)
    return UserOut(**user_serialized)  # Преобразуем данные в объект модели


# Эндпоинт для получения профиля
@users.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

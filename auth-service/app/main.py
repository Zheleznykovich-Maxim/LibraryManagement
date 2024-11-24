import aioredis
from fastapi import FastAPI
from app.api.db import metadata, database, engine
from app.api.users import users  # Импортируем маршруты для аутентификации

# Инициализация базы данных
metadata.create_all(engine)

# Создаём приложение FastAPI
app = FastAPI(openapi_url="/api/v1/auth/openapi.json", docs_url="/api/v1/auth/docs")

# Переменные для подключения к Redis
REDIS_HOST = "redis"
REDIS_PORT = 6379

# Подключение Redis
redis = None


@app.on_event("startup")
async def startup():
    global redis
    # Подключение к Redis
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)
    # Подключение к базе данных
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    # Закрытие подключения к Redis
    if redis:
        await redis.close()
    # Отключение от базы данных
    await database.disconnect()

# Регистрируем маршруты для аутентификации
app.include_router(users, prefix='/api/v1/auth', tags=['auth'])

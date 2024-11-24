from fastapi import FastAPI, Depends, HTTPException
import aioredis
from app.api.books import books
from app.api.db import metadata, database, engine

# Создание таблиц базы данных
metadata.create_all(engine)

# Инициализация FastAPI
app = FastAPI(openapi_url="/api/v1/books/openapi.json", docs_url="/api/v1/books/docs")

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


# Маршрут для проверки подключения к Redis
@app.get("/api/v1/books/cache-status", tags=["cache"])
async def cache_status():
    try:
        pong = await redis.ping()
        return {"status": "Redis is connected", "ping": pong}
    except Exception as e:
        return {"status": "Redis connection failed", "error": str(e)}


# Интеграция роутера книг
app.include_router(books, prefix="/api/v1/books", tags=["books"])

import aioredis
from fastapi import FastAPI
from app.api.orders import orders
from app.api.db import metadata, database, engine

metadata.create_all(engine)

app = FastAPI(openapi_url="/api/v1/orders/openapi.json", docs_url="/api/v1/orders/docs")


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

app.include_router(orders, prefix='/api/v1/orders', tags=['orders'])
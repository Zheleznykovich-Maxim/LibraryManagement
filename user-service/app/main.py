from fastapi import FastAPI
from app.api.db import metadata, database, engine
from app.api.users import users
import aioredis

metadata.create_all(engine)

app = FastAPI(openapi_url="/api/v1/users/openapi.json", docs_url="/api/v1/users/docs")

# Подключение к Redis
REDIS_HOST = "redis"
REDIS_PORT = 6379
redis = None


@app.on_event("startup")
async def startup():
    global redis
    # Подключение к базе данных и Redis
    await database.connect()
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    # Отключение от базы данных и Redis
    await database.disconnect()
    if redis:
        await redis.close()


# Подключение роутеров
app.include_router(users, prefix='/api/v1/users', tags=['users'])

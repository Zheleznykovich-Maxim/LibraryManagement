import aioredis
from app.api.db import metadata, database, engine
from app.api.users import users
from fastapi import FastAPI

metadata.create_all(engine)

app = FastAPI(openapi_url="/api/v1/users/openapi.json", docs_url="/api/v1/users/docs")

REDIS_HOST = "redis"
REDIS_PORT = 6379
redis = None


@app.on_event("startup")
async def startup():
    global redis

    await database.connect()
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    if redis:
        await redis.close()


app.include_router(users, prefix='/api/v1/users', tags=['users'])

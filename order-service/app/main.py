import aioredis
from app.api.db import metadata, database, engine
from app.api.orders import orders
from fastapi import FastAPI

metadata.create_all(engine)

app = FastAPI(openapi_url="/api/v1/orders/openapi.json", docs_url="/api/v1/orders/docs")

REDIS_HOST = "redis"
REDIS_PORT = 6379

redis = None


@app.on_event("startup")
async def startup():
    global redis

    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    if redis:
        await redis.close()

    await database.disconnect()


app.include_router(orders, prefix='/api/v1/orders', tags=['orders'])

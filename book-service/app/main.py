import aioredis
from app.api.books import books
from app.api.db import metadata, database, engine
from fastapi import FastAPI

metadata.create_all(engine)

app = FastAPI(openapi_url="/api/v1/books/openapi.json", docs_url="/api/v1/books/docs")

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


@app.get("/api/v1/books/cache-status", tags=["cache"])
async def cache_status():
    try:
        pong = await redis.ping()
        return {"status": "Redis is connected", "ping": pong}
    except Exception as e:
        return {"status": "Redis connection failed", "error": str(e)}


app.include_router(books, prefix="/api/v1/books", tags=["books"])

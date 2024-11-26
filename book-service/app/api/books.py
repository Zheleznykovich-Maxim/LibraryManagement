import json

import aioredis
import jwt
from app.api import db_manager
from app.api.models import BookOut, BookIn, BookUpdate
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status

books = APIRouter()

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

REDIS_HOST = "redis"
REDIS_PORT = 6379
redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)


@books.post('/', response_model=BookOut, status_code=201)
async def create_book(payload: BookIn):
    book_id = await db_manager.add_book(payload)

    response = {
        'id': book_id,
        **payload.dict()
    }

    await redis.delete("books:all")
    return response


@books.get('/')
async def get_books(current_user: str = Depends(oauth2_scheme)):
    cached_books = await redis.get("books:all")
    if cached_books:
        books_list = json.loads(cached_books)
        return {"data": books_list, "source": "cache"}

    books_list = await db_manager.get_all_books()

    books_serialized = [dict(book) for book in books_list]

    await redis.set("books:all", json.dumps(books_serialized), ex=3600)
    return {"data": books_serialized, "source": "database"}


@books.get('/{id}/', response_model=BookOut)
async def get_book(
        id: int,
        current_user: str = Depends(oauth2_scheme)
):

    cache_key = f"book:{id}"
    await redis.delete(cache_key)
    cached_book = await redis.get(cache_key)
    if cached_book:
        book = json.loads(cached_book)
        return BookOut(**book)

    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book_serialized = dict(book)

    await redis.set(cache_key, json.dumps(book_serialized), ex=3600)
    return BookOut(**book_serialized)


@books.put('/{id}/', response_model=BookOut)
async def update_book(id: int, payload: BookUpdate):
    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = payload.dict(exclude_unset=True)
    book_in_db = BookIn(**book)
    updated_book = book_in_db.copy(update=update_data)

    result = await db_manager.update_book(id, updated_book)

    cache_key = f"book:{id}"
    await redis.set(cache_key, str(updated_book), ex=3600)

    await redis.delete("books:all")
    return result


@books.delete('/{id}/', response_model=None)
async def delete_book(id: int):
    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    result = await db_manager.delete_book(id)

    cache_key = f"book:{id}"
    await redis.delete(cache_key)

    await redis.delete("books:all")
    return result


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
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

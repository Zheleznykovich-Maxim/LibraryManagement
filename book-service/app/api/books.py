import jwt
from fastapi import APIRouter, HTTPException
from typing import List

from app.api.models import BookOut, BookIn, BookUpdate
from app.api import db_manager
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.testing.pickleable import User
from starlette import status

books = APIRouter()

# Секретный ключ для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@books.post('/', response_model=BookOut, status_code=201)
async def create_book(payload: BookIn):
    book_id = await db_manager.add_book(payload)

    response = {
        'id': book_id,
        **payload.dict()
    }

    return response

@books.get('/')
async def get_books(current_user: User = Depends(oauth2_scheme)):
    books_list = await db_manager.get_all_books()
    return books_list

@books.get('/{id}/', response_model=BookOut)
async def get_book(id: int):
    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="book not found")
    return book

@books.put('/{id}/', response_model=BookOut)
async def update_book(id: int, payload: BookUpdate):
    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = payload.dict(exclude_unset=True)

    book_in_db = BookIn(**book)

    updated_book = book_in_db.copy(update=update_data)

    return await db_manager.update_book(id, updated_book)

@books.delete('/{id}/', response_model=None)
async def delete_book(id: int):
    book = await db_manager.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return await db_manager.delete_book(id)

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

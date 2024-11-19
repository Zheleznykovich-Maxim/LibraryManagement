import jwt
from fastapi import APIRouter, HTTPException
from typing import List

from app.api.models import OrderOut, OrderIn, OrderUpdate
from app.api import db_manager
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.testing.pickleable import User
from starlette import status
from app.api.service import is_book_present

orders = APIRouter()

# Секретный ключ для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@orders.post('/', response_model=OrderOut, status_code=201)
async def create_order(payload: OrderIn):
    for book_id in payload.books_id:
        if not is_book_present(book_id):
            raise HTTPException(status_code=404, detail=f"Book with given id:{book_id} not found")

    order_id = await db_manager.add_order(payload)
    response = {
        'id': order_id,
        **payload.dict()
    }

    return response

@orders.get('/')
async def get_orders(current_user: User = Depends(oauth2_scheme)):
    orders_list = await db_manager.get_all_orders()
    return orders_list

@orders.get('/{id}/', response_model=OrderOut)
async def get_order(id: int):
    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order

@orders.put('/{id}/', response_model=OrderOut)
async def update_order(id: int, payload: OrderUpdate):
    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    update_data = payload.dict(exclude_unset=True)

    order_in_db = OrderIn(**order)

    updated_order = order_in_db.copy(update=update_data)

    return await db_manager.update_order(id, updated_order)

@orders.delete('/{id}/', response_model=None)
async def delete_order(id: int):
    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return await db_manager.delete_order(id)

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

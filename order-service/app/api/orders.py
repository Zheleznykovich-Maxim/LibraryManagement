import json
from datetime import datetime

import aioredis
import jwt
from app.api import db_manager
from app.api.models import OrderOut, OrderIn, OrderUpdate
from app.api.service import is_book_present
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

REDIS_HOST = "redis"
REDIS_PORT = 6379
redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
orders = APIRouter()


@orders.post('/', response_model=OrderOut, status_code=201)
async def create_order(payload: OrderIn):
    for book_id in payload.books_id:
        if not is_book_present(book_id):
            raise HTTPException(status_code=404, detail=f"Book with given id:{book_id} not found")

    order_id = await db_manager.add_order(payload)
    order = await db_manager.get_order(order_id)

    order_dict = serialize_record(dict(order))

    cache_key = f"order:id:{order_id}"
    await redis.set(cache_key, json.dumps(order_dict), ex=3600)

    await redis.delete("orders:all")

    return order_dict


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@orders.get('/')
async def get_orders(current_user: str = Depends(oauth2_scheme)):
    cached_orders = await redis.get("orders:all")
    if cached_orders:
        orders_list = json.loads(cached_orders)
        return {"data": orders_list, "source": "cache"}

    orders_list = await db_manager.get_all_orders()

    orders_serialized = [dict(order) for order in orders_list]
    for order_item in orders_serialized:
        if 'order_date' in order_item and isinstance(order_item['order_date'], datetime):
            order_item['order_date'] = order_item['order_date'].isoformat()

    await redis.set("orders:all", json.dumps(orders_serialized, default=serialize_datetime), ex=3600)
    return {"data": orders_serialized, "source": "database"}


@orders.get('/{id}/', response_model=OrderOut)
async def get_order(id: int):
    cached_order = await redis.get(f"order:{id}")

    if cached_order:
        order = json.loads(cached_order)
        return OrderOut(**order)

    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_dict = dict(order)
    if 'order_date' in order_dict and isinstance(order_dict['order_date'], datetime):
        order_dict['order_date'] = order_dict['order_date'].isoformat()

    await redis.set(f"order:{id}", json.dumps(order_dict), ex=3600)

    return OrderOut(**order_dict)


@orders.put('/{id}/', response_model=OrderOut)
async def update_order(id: int, payload: OrderUpdate):
    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = payload.dict(exclude_unset=True)
    order_in_db = OrderIn(**order)
    updated_order = order_in_db.copy(update=update_data)

    result = await db_manager.update_order(id, updated_order)

    cache_key = f"order:id:{id}"
    await redis.set(cache_key, json.dumps(result, default=serialize_datetime), ex=3600)

    return result


@orders.delete('/{id}/', response_model=None)
async def delete_order(id: int):
    order = await db_manager.get_order(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db_manager.delete_order(id)

    cache_key = f"order:id:{id}"
    await redis.delete(cache_key)

    await redis.delete("orders:all")

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


def serialize_record(obj):
    """Преобразует объект Record в обычный словарь с сериализацией даты."""
    if isinstance(obj, dict):
        return {key: serialize_record(value) for key, value in obj.items()}

    if isinstance(obj, datetime):
        return obj.isoformat()

    return obj

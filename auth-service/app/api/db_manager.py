
from app.api.models import UserIn, UserOut
from app.api.db import database, users
from datetime import datetime, timedelta
import jwt

from passlib.context import CryptContext

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Функция для проверки пароля при авторизации
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Функция для создания токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

async def get_user_password(email):
    query = users.select().where(users.c.email == email)
    return await database.fetch_one(query)['password']

async def get_user_by_email(email):
    query = users.select(users.c.email==email)
    return await database.fetch_one(query=query)

async def create_user(payload: UserIn):
    query = users.insert().values(payload.dict())

    return await database.execute(query=query)
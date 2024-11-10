from app.api import db_manager
from app.api.models import UserIn, UserOut, User
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status
import jwt


# Секретный ключ для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users = FastAPI()

# Эндпоинт для регистрации
@users.post("/register", response_model=UserOut, status_code=201)
async def register_user(payload: UserIn):
    db_user = await db_manager.get_user_by_email(payload.email)
    if db_user:
        raise HTTPException(
            status_code=404,
            detail="Email already registered",
        )
    hashed_password = db_manager.get_password_hash(payload.password)
    payload.password = hashed_password
    user_id = await db_manager.create_user(payload)

    response = {
        'id': user_id,
        'email': payload.email,
        **payload.dict()
    }

    return response

# Эндпоинт для авторизации
@users.post("/login")
async def login(payload: UserIn):
    user = await db_manager.get_user_by_email(payload.email)
    if not user or not db_manager.verify_password(
            payload.password,
            user['password']):
        raise HTTPException(
            status_code=404,
            detail="Incorrect email or password",
        )
    access_token = db_manager.create_access_token(data={"sub": user['email']})
    return {"access_token": access_token, "token_type": "bearer"}


# Зависимость для проверки токена
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

# Эндпоинт для получения профиля
@users.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
from pydantic import BaseModel, EmailStr, validate_email


class UserIn(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True

# Модель пользователя для работы с аутентификацией
class User(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True  # Для работы с ORM

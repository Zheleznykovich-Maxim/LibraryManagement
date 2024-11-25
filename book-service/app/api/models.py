from typing import Optional

from pydantic import BaseModel


class BookIn(BaseModel):
    title: str
    author: str
    genre: str
    price: float
    description: str


class BookOut(BookIn):
    id: int
    title: str
    author: str
    genre: str
    price: float
    description: str


class BookUpdate(BookIn):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None

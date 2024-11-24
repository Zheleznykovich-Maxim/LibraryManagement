from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class OrderIn(BaseModel):
    status: str
    books_id: List[int]


class OrderOut(OrderIn):
    id: int
    status: str
    books_id: List[int]
    order_date: datetime


class OrderUpdate(OrderIn):
    status: Optional[str]
    books_id: List[int]

import os
from datetime import date, datetime

from sqlalchemy import (Column, Integer, MetaData, String, Table,
                        create_engine, ARRAY, Float, DateTime, func)

from databases import Database
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.util import timezone

DATABASE_URI = os.getenv('DATABASE_URI')

engine = create_engine(DATABASE_URI)
metadata = MetaData()

orders = Table(
    'orders2',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('order_date', DateTime(timezone=True), default=func.now()),
    Column('status', String(30)),
    Column('books_id', ARRAY(Integer))
)
# orders.drop(engine)
database = Database(DATABASE_URI)
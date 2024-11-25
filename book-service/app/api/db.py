import os

from databases import Database
from sqlalchemy import (Column, Integer, MetaData, String, Table,
                        create_engine, Float)

DATABASE_URI = os.getenv('DATABASE_URI')

engine = create_engine(DATABASE_URI)
metadata = MetaData()

books = Table(
    'books',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(50)),
    Column('author', String(30)),
    Column('genre', String(30)),
    Column('price', Float),
    Column('description', String(60))
)

database = Database(DATABASE_URI)

import os

from sqlalchemy import (Column, Integer, MetaData, String, Table,
                        create_engine, ARRAY, Float)

from databases import Database

DATABASE_URI = os.getenv('DATABASE_URI')

engine = create_engine(DATABASE_URI)
metadata = MetaData()

users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('email', String, unique=True, index=True),
    Column('password', String)
)

database = Database(DATABASE_URI)
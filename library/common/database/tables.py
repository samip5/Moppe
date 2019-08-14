# This file will have the database tables in code so it's easier to reference from other places.

from sqlalchemy import MetaData, Table, Column, Integer, String

metadata = MetaData()


Test = Table(
    "test",
    metadata,
    Column('id', Integer, primary_key=True)
)

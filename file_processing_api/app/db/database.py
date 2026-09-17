from typing_extensions import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session


DATABASE_URL = "postgresql+psycopg://postgres:F%40sil3105@localhost:5432/file_processing_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    print("Database connected successfully!")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
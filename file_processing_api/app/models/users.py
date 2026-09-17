from datetime import datetime

from sqlmodel import Field, SQLModel


class Users(SQLModel, table=True):
    id : int | None = Field(default = None, primary_key=True)
    name : str
    email : str
    password_hash : str
    created_at : datetime = Field(default_factory= datetime.now, index = True)
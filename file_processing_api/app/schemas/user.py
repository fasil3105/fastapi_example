from datetime import datetime

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    name : str
    email : str
    password : str

class UserResponse(SQLModel):
    id : int
    name : str
    email : str
    created_at : datetime

class LoginUser(SQLModel):
    email : str
    password : str

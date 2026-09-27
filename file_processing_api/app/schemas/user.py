from datetime import datetime
from re import S
from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    name : str
    email : EmailStr
    password : str

    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
             raise ValueError("Password must be at least 8 characters long")

        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")

        if not any(char in "!@#$%^&*()_+-=[]{}|;:',.<>?/`~" for char in value):
            raise ValueError("Password must contain at least one special character")


        return value


class UserResponse(SQLModel):
    id : int
    name : str
    email : str
    created_at : datetime

class LoginUser(SQLModel):
    email : str
    password : str


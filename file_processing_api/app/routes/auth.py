from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlmodel import Session
from app.db.database import get_session, SessionDep
from app.schemas.user import UserCreate, UserResponse
from app.models.users import Users
from app.core.security import hash_password

router = APIRouter()

@router.post("/register", response_model = UserResponse)
async def create_user(user : UserCreate, session : SessionDep):

    existing_user =  session.exec(select(Users).where(Users.email == user.email)).first()

    if existing_user:
        raise HTTPException(status_code=409,
                            detail = "Email already exist")

    pwd_hash = hash_password(user.password)

    user_data = Users(
        name = user.name,
        email = user.email,
        password_hash = pwd_hash
    )

    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    return  user_data
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException
from app.core.config import ALGORITHM, SECRET_KEY
from sqlmodel import select
from sqlmodel import Session
from app.db.database import get_session, SessionDep
from app.schemas.user import LoginUser, UserCreate, UserResponse
from app.models.users import Users
from app.core.security import hash_password, verify_password

router = APIRouter()

@router.post("/register", response_model = UserResponse)
async def create_user(user : UserCreate, session : SessionDep): # type: ignore

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


@router.post("/login")
async def user_login(user : LoginUser,session : SessionDep): # type: ignore

    existing_user =  session.exec(select(Users).where(Users.email == user.email)).first()
    
    if not existing_user:
        raise HTTPException(status_code=401,
                            detail = "Invalid email or password")
    

    auth_user = verify_password(user.password, existing_user.password_hash)


    if not auth_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    

    sub = str(existing_user.id)
    exp = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {

        "sub" : sub,
        "exp" : exp
    }


    access_token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm = ALGORITHM
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
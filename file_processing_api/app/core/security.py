from fastapi import Depends, HTTPException
import jwt
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer

from app.core.config import ALGORITHM, SECRET_KEY
from app.db.database import SessionDep
from app.models.users import Users

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def get_current_user(session: SessionDep,
                     token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")

        if not user_id:
                    raise HTTPException(status_code=401,detail = "Could not validate credentials")

        user = session.get(Users, int(user_id))

        if not user:
            raise HTTPException(status_code=401,detail = "Could not validate credentials")

        return user

    except Exception:
        
        raise HTTPException(status_code = 401,detail = "Could not validate credentials")
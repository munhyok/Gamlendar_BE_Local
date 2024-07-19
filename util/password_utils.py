from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
import secrets
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
SALT_NUM = int(os.getenv("SALT_NUM"))

def create_access_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return access_token

def create_refresh_token(data: dict, UUID: str):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    to_encode.update({"uuid": UUID})
    
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user_id: str = payload.get("sub")
        device_id: str = payload.get("uuid")
        
        
        return user_id, device_id
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"message":"Invalid refresh token"})
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(SALT_NUM).decode('utf-8'))


from fastapi import APIRouter, HTTPException, status, Depends, Header, Form

from config.mongo import userDB, userDB_Log
from config.redis import reDB
from util.password_utils import get_password_hash, verify_password
from util.password_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS, decode_token, create_uuid
from datetime import timedelta




# 클라이언트에서 UUID 생성 후 받은 UUID 기반으로 받아오는 과정 (이전 버전 유저를 위한 코드)
async def login_service(form_data, device_id):
    user = await authenticate_user(form_data.username, form_data.password)
    #device_id = create_uuid()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user['_id'])}
    )
    
    await reDB.delete(f"refresh_token:{str(user['_id'])}:{device_id}")
    refresh_token = create_refresh_token(
        data={"sub": str(user['_id'])}, UUID=device_id
    )
    
    await reDB.setex(f"refresh_token:{str(user['_id'])}:{device_id}", timedelta(days = REFRESH_TOKEN_EXPIRE_DAYS), refresh_token)
    
    return {"access_token": access_token, "refresh_token":refresh_token, "uuid":device_id, "token_type": "bearer"}

# 백엔드에서 UUID 생성 후 Resp에 담아주고 클라이언트에서 저장하는과정
async def access_token_service(form_data):
    user = await authenticate_user(form_data.username, form_data.password)
    device_id = str(create_uuid())
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user['_id'])}
    )
    
    await reDB.delete(f"refresh_token:{str(user['_id'])}:{device_id}")
    refresh_token = create_refresh_token(
        data={"sub": str(user['_id'])}, UUID=device_id
    )
    
    await reDB.setex(f"refresh_token:{str(user['_id'])}:{device_id}", timedelta(days = REFRESH_TOKEN_EXPIRE_DAYS), refresh_token)
    
    return {"access_token": access_token, "refresh_token":refresh_token, "uuid":device_id, "token_type": "bearer"}


async def refresh_token_service(refresh_token):
    user_id, uuid = decode_token(refresh_token)
    
    stored_refresh_token = await reDB.get(f"refresh_token:{user_id}:{uuid}")

    
    if stored_refresh_token == refresh_token:

        new_access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id}, UUID=uuid)
        
        await reDB.delete(f"refresh_token:{user_id}:{uuid}")
        await reDB.setex(f"refresh_token:{user_id}:{uuid}", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), new_refresh_token)
        
        return {"access_token": new_access_token, "refresh_token":new_refresh_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"message":"refresh token이 일치하지 않습니다"})


async def authenticate_user(username: str, password: str):
    user = await userDB.find_one({"username": username, "account_provider": "gamlendar"})
    if not user or not verify_password(password, user['password']):
        return False
    return user
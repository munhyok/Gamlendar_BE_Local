from config.mongo import userDB, gameDB
from config.redis import reDB
import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.user import Register
from bson import ObjectId
from schemas.user_serializer import users_serializer
from passlib.context import CryptContext

from util.password_utils import get_password_hash, verify_password
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
SALT_NUM = int(os.getenv("SALT_NUM"))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(register):
    
    verify_string = await reDB.get(f"email_verify:{register.username}")
    
    if verify_string != 'Verify':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="잘못된 요청입니다. 다시 시도하세요")
    
    
    register.password = pwd_context.hash(register.password)
    
    isUsernameExist = await userDB.find_one({"username":register.username})
    
    if isUsernameExist:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="이미 가입되어있는 계정입니다.")
    
    isNicknameExist = await userDB.find_one({"nickname":register.nickname})
    
    if isNicknameExist:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="중복된 닉네임입니다.")
    
    _id = await userDB.insert_one(dict(register))
    
    db_cursor = userDB.find({"_id": _id.inserted_id})
    db_data = await db_cursor.to_list(length=None)
    db_serialize = users_serializer(db_data)
    user = jsonable_encoder(db_serialize)
    
    await reDB.delete(f"email_verify:{register.username}")
    
async def search_account(account):
    
    isAccountExist = await userDB.find_one({"username":account.username})
    
    if isAccountExist:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="이미 가입되어있는 계정입니다.")
    
    
async def search_nickname(nickname):
    
    isNicknameExist = await userDB.find_one({'nickname': nickname.nickname})
    
    if isNicknameExist:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="중복되는 닉네임이 존재합니다.")
    
    
async def authenticate_user(username: str, password: str):
    user = await userDB.find_one({"username": username})
    if not user or not verify_password(password, user['password']):
        return False
    return user


async def fetch_gamlendar_yearmonth(user_id: ObjectId, yearmonth: str):
    result = []
    pipeline = [
        {"$match": {"_id": user_id}},
        {"$lookup": {
            "from": "Gamlendar_game",
            "localField": "myGamlendar",
            "foreignField": "_id",
            "as": "gamlendarDetails"
        }},
        {"$unwind": "$gamlendarDetails"},
        {"$match": {"gamlendarDetails.yearmonth": yearmonth}},
        
        {"$project": {"gamlendarDetails.date": 1}}
    ]
    
    aggCursor = userDB.aggregate(pipeline)
    
    async for doc in await aggCursor:
        result.append(doc)
        
        
    return result

async def delete_user(user_objectID):
    try:
        await userDB.delete_one({"_id":ObjectId(user_objectID)})
    except:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="유저를 찾을 수 없습니다.")
    
    
    

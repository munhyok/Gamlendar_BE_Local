from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from config.mongo import userDB
from util.password_utils import SECRET_KEY,ALGORITHM
from typing import Optional
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowPassword


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_user_by_id(id: str):
    objectId = ObjectId(id)
    user = await userDB.find_one({"_id": objectId})

    if user:
        user["id"] = str(user['_id'])
        user['_id'] = str(user['_id'])
        
        return user
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        if id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_id(id)
    if user is None:
        raise credentials_exception
    return user


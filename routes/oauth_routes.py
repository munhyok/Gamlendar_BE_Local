from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from models.oauth import AppleSignIn
from services.oauth_service import google_login_service, apple_login_service, apple_account_revoke
from util.dependencies import get_current_user
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL")

oauth = APIRouter(tags=['OAuth'])




@oauth.get('/oauth/google', status_code=status.HTTP_200_OK)
async def oauth_google(code: str):
    result = await google_login_service(code)
    return result

@oauth.post('/oauth/apple', status_code=status.HTTP_200_OK)
async def oauth_apple(requset_data: AppleSignIn):
    result = await apple_login_service(requset_data)
    return result


@oauth.get('/oauth/google/callback', status_code=status.HTTP_200_OK)
async def oauth_google_callback():
    return {"result": 'ok'}


# apple 로그인은 callback URL을 /login/callback으로 설정해야 하더라...
@oauth.get('/login/callback', status_code=status.HTTP_200_OK)
async def oauth_apple_callback():
    return {"result": 'ok'}


@oauth.post('/oauth/apple/revoke', status_code=status.HTTP_200_OK, description="애플 계정 Revoke API")
async def oauth_apple_revoke(current_user = Depends(get_current_user)):

    result = await apple_account_revoke(current_user)
    
    
    return result

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
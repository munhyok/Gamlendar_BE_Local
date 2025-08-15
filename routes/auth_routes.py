from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from models.user import UserResponse, MyGamlendar, AddGame
from schemas.game_serializer import games_serializer
from bson import ObjectId
from services.user_service import create_user, search_account, search_nickname, fetch_gamlendar_yearmonth, delete_matching_key
from services.auth_service import login_service, access_token_service ,refresh_token_service
from util.password_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS, decode_token
from util.dependencies import get_current_user
from util.email_util import send_password_recovery_code, verify_code, send_email_verify_code


from models.user import Register, Token, FindAccount, FindNickname, RefreshToken
from dotenv import load_dotenv

auth = APIRouter(tags=['Auth'])

load_dotenv()

        
        
    
@auth.post("/login", status_code=status.HTTP_200_OK, response_model= Token, 
           description='로그인 후 access_token과 refresh_token을 발급받습니다. UUID를 앱에서 생성해 백엔드로 받아옵니다. 이전 버전을 사용하는 유저를 위한 코드입니다.')
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 device_id: str = Form(...)
) -> Token:

    
    token = await login_service(form_data, device_id)
    
    return token
    
    
@auth.post("/auth/token", status_code=status.HTTP_200_OK, response_model=Token,
           description='로그인 후 access_token과 refresh_token을 발급받습니다. UUID를 백엔드에서 생성해 앱으로 보내줍니다.')
async def get_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    
    token = await access_token_service(form_data)
    
    return token



@auth.post("/refresh", status_code=status.HTTP_200_OK, response_model=RefreshToken)
async def refresh_token(refresh_token: str = Form(...)):
    
    refresh_token = await refresh_token_service(refresh_token)
    
    return refresh_token
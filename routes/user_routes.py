import json

from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from fastapi.encoders import jsonable_encoder
from models.user import UserResponse, MyGamlendar
from schemas.game_serializer import games_serializer
from bson import ObjectId
from service.user.user_service import create_user

from models.user import Register, Token
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from service.user.user_service import authenticate_user
from util.password_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS, decode_token
from util.dependencies import get_current_user
from util.email_util import send_password_recovery_code, verify_code
from datetime import timedelta
from typing import Annotated
from datetime import datetime
from config.mongo import userDB, gameDB
from config.redis import reDB
import os
from dotenv import load_dotenv

user = APIRouter(tags=['User'])

load_dotenv()

        
        

@user.post("/create",response_model=Register, status_code=status.HTTP_201_CREATED)
async def user_create(register: Register):
    await create_user(register)
    return {"status": "Ok", "data": register}
    
    
@user.post("/login", status_code=status.HTTP_200_OK, response_model= Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 device_id: str = Form(...)
) -> Token:
    
    
    
    user = await authenticate_user(form_data.username, form_data.password)
    
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
    
    return {"access_token": access_token, "refresh_token":refresh_token, "token_type": "bearer"}

@user.post("/refresh", status_code=status.HTTP_200_OK, response_model=Token)
async def refresh_token(refresh_token: str = Form(...)):
    
    user_id, uuid = decode_token(refresh_token)
    
    stored_refresh_token = await reDB.get(f"refresh_token:{user_id}:{uuid}")

    
    if stored_refresh_token == refresh_token:

        new_access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id}, UUID=uuid)
        
        await reDB.delete(f"refresh_token:{user_id}:{uuid}")
        await reDB.setex(f"refresh_token:{user_id}:{uuid}", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), new_refresh_token)
        
        return {"access_token": new_access_token, "refresh_token":new_refresh_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"message":"refresh token이 일치하지 않습니다"})


@user.post("/account/recovery",status_code=status.HTTP_200_OK)
async def recovery_password(email: str = Form(...)):
    
    await send_password_recovery_code(email)
    
    return {"message":"복구번호 전송완료"}


@user.post("/account/recovery/verify/", status_code=status.HTTP_200_OK)
async def verify_recovery_code(email: str = Form(...), code: str = Form(...)):
    await verify_code(email, code)
    
    return {"message":"이메일 인증완료"}


@user.post("/profile/gamlendar/add/", status_code=status.HTTP_200_OK)
async def add_game_myGamlendar(game_id:str , current_user = Depends(get_current_user)):
    
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    find = await userDB.find_one(
        {"_id": obj_user_id},
        {"myGamlendar":{"$elemMatch": {"$eq": obj_game_id}}}
    )
    
    if find:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="이미 등록된 게임입니다.")
    
    game = await userDB.update_one(
        {"_id": obj_user_id},
        {"$push": {"myGamlendar": obj_game_id}}
    )
    
    if game.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 발견하지 못했습니다. 게임 추가 실패")
    
    return {"message":"내 겜린더에 등록되었습니다."}


@user.get("/profile/gamlendar/find/", status_code=status.HTTP_200_OK)
async def find_game_myGamlendar(game_id: str, current_user = Depends(get_current_user)):
    
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    find = await userDB.find_one(
        {"_id": obj_user_id},
        {"myGamlendar":{"$elemMatch": {"$eq": obj_game_id}}}
        # $match 는 aggregate에서만 쓸 수 있다고한다
        # $elemMatch 배열에 지정된 요소 중 하나가 "지정된 조건"과 일치하는지 확인
        # "지정된 조건" $eq 값이 일치하는지 확인
    )
    
    if not find:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약한 게임이 아닙니다.")
    
    return {"message": game_id}
    
    


@user.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
def user_profile(current_user: UserResponse = Depends(get_current_user)):
    
    return current_user


@user.get("/profile/gamlendar/date/", response_model=MyGamlendar, status_code=status.HTTP_200_OK)
async def my_gamlendar_date(date: str, current_user: MyGamlendar = Depends(get_current_user)):
    
    user_id = current_user["id"]
    
    obj_user_id = ObjectId(user_id)

    # 사용자 정보 가져오기
    user = await userDB.find_one(
        {"_id": obj_user_id},
        {"_id": 1, "myGamlendar": 1}
    )
    

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 특정 날짜로 필터링할 날짜
    specific_date = date

    # myGamlendar에서 관련 데이터 필터링
    filtered_data_cursor = gameDB.find(
        {"_id": {"$in": user["myGamlendar"]}, "date": specific_date},
        {"_id": 0}  # 필요한 필드를 여기에 추가 (0은 제외, 1은 포함) 
    )

    # 필터링된 데이터를 리스트로 변환
    filtered_data = await filtered_data_cursor.to_list(length=None)

    # myGamlendar 필드 요소들을 문자열로 변환
    my_gamlendar = [str(item) for item in user["myGamlendar"]]

    # MyGamlendar 모델 인스턴스로 변환
    gamlendar_data = MyGamlendar(
        id= user_id,
        myGamlendar=my_gamlendar,
        gamlendarDetails=filtered_data
    )

    return gamlendar_data

    
    
    

@user.get("/profile/gamlendar/yearmonth/", response_model=MyGamlendar, status_code=status.HTTP_200_OK)
async def my_gamlendar_yearmonth(yearmonth: str, current_user: MyGamlendar = Depends(get_current_user)):
    user_id = current_user["id"]
    
    obj_user_id = ObjectId(user_id)

    # 사용자 정보 가져오기
    user = await userDB.find_one(
        {"_id": obj_user_id},
        {"_id": 1, "myGamlendar": 1}
    )
    

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    specific_yearmonth = yearmonth

    
    filtered_data_cursor = gameDB.find(
        {"_id": {"$in": user["myGamlendar"]}, "yearmonth": specific_yearmonth},
        {"_id": 0} 
    )

    
    filtered_data = await filtered_data_cursor.to_list(length=None)

    
    my_gamlendar = [str(item) for item in user["myGamlendar"]]

    
    gamlendar_data = MyGamlendar(
        id= user_id,
        myGamlendar=my_gamlendar,
        gamlendarDetails=filtered_data
    )

    return gamlendar_data



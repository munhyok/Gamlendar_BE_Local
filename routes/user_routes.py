import json

from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from fastapi.encoders import jsonable_encoder
from models.user import UserResponse, MyGamlendar
from schemas.game_serializer import games_serializer
from bson import ObjectId
from services.user_service import create_user, search_account, search_nickname,fetch_gamlendar_yearmonth

from models.user import Register, Token, FindAccount, FindNickname
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from services.user_service import authenticate_user
from util.password_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS, decode_token
from util.dependencies import get_current_user
from util.email_util import send_password_recovery_code, verify_code, send_email_verify_code
from datetime import timedelta
from typing import Annotated
from datetime import datetime
from config.mongo import userDB, gameDB
from config.redis import reDB
import os
from dotenv import load_dotenv


user = APIRouter(tags=['User'])

load_dotenv()

        
        

@user.post("/register", status_code=status.HTTP_201_CREATED)
async def user_create(register: Register):
    await create_user(register)
    return {"status": 201, "msg":'가입완료', "data":register}


@user.post("/find/account", status_code=status.HTTP_200_OK)
async def find_account(account: FindAccount):
    await search_account(account)
    return {'status': 200, "detail": '사용할 수 있는 계정입니다.'}


@user.post("/find/nickname", status_code=status.HTTP_200_OK)
async def find_nickname(nickname: FindNickname):
    await search_nickname(nickname)
    return {'status': 200, "detail": '사용할 수 있는 별명입니다.'}
    
@user.post("/account/authcode", status_code=status.HTTP_200_OK)
async def auth_account(email: str = Form(...)):
    await send_email_verify_code(email)
    return {'status': 200, 'msg':'인증번호 전송완료'}

@user.post("/account/authcode/verify", status_code=status.HTTP_200_OK)
async def verify_auth_account(email: str = Form(...), code: str = Form(...)):
    await verify_code('email_verify',email,code)
    return {'status': 200, 'msg':'인증완료'}
    
    
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
    
    return {"status_code": 200,"msg":"복구번호 전송완료"}


@user.post("/account/recovery/verify", status_code=status.HTTP_200_OK)
async def verify_recovery_code(email: str = Form(...), code: str = Form(...)):
    await verify_code("recovery_password",email, code)
    
    return {"status_code": 200,"message":"이메일 인증완료"}





@user.post("/profile/gamlendar/add", status_code=status.HTTP_200_OK)
async def add_game_myGamlendar(game_id:str,game_date: str, game_name: str, current_user = Depends(get_current_user)):
    
    str_user_id = current_user["id"]
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    
    try:
        find = await userDB.find_one(
            {"_id": obj_user_id, "myGamlendar": {"$elemMatch": {"$eq": obj_game_id}}},
            {"_id": 1}
        )
    

        if find:
            raise HTTPException(status_code=status.HTTP_302_FOUND, detail="이미 등록된 게임입니다.")
    
        
        
        game = await userDB.update_one(
        
            {"_id": obj_user_id},

            {"$addToSet": {"myGamlendar": obj_game_id}}

        )
        
        await reDB.hset(f"{game_date}:{str_user_id}",game_id, game_name)
        
        await reDB.delete(f"yearmonth:{str_user_id}")

        return {"message":"내 겜린더에 등록되었습니다."}
    
    except:
        HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 추가 실패")
        
    


    
    


@user.get("/profile/gamlendar/find", status_code=status.HTTP_200_OK)
async def find_game_myGamlendar(game_id: str, current_user = Depends(get_current_user)):
    
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    
    
    find = await userDB.find_one(
        {"_id": obj_user_id, "myGamlendar": obj_game_id},
        {"_id": 1}
    )
    
    if find:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="이미 등록된 게임입니다.")
    
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약한 게임이 아닙니다.")
    
    
    #return {"message": '게임이 존재합니다'}
    


@user.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
def user_profile(current_user: UserResponse = Depends(get_current_user)):
    
    return current_user


@user.get("/profile/gamlendar/date",  status_code=status.HTTP_200_OK)
async def my_gamlendar_date(date: str, current_user: MyGamlendar = Depends(get_current_user)):
    
    user_id = current_user["id"]
    result = []
    
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
        #{"_id": 0}  # 필요한 필드를 여기에 추가 (0은 제외, 1은 포함) 
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
    
    
    
    
    for games in gamlendar_data.gamlendarDetails:
        games['id'] = str(games["_id"])
        del(games["_id"])
        result.append(games)
    
    

    return result

    
    
    

@user.get("/profile/gamlendar/yearmonth", status_code=status.HTTP_200_OK)
async def my_gamlendar_yearmonth(yearmonth: str, current_user: MyGamlendar = Depends(get_current_user)):
    user_id = ObjectId(current_user["id"])
    
    cache_data = await reDB.get(f"yearmonth:{current_user['id']}")
    
    if cache_data:
        
        return json.loads(cache_data)
    
    user_data = await fetch_gamlendar_yearmonth(user_id, yearmonth)
    result = {item["gamlendarDetails"]["date"] for item in user_data}


    await reDB.set(f"yearmonth:{current_user['id']}", json.dumps(list(result)))
    return result
    
    


@user.delete('/profile/gamlendar/remove', status_code=status.HTTP_200_OK)
async def remove_game_myGamlendar(game_id: str, game_date: str, current_user = Depends(get_current_user)):
    
    str_user_id = current_user['id']
    
    obj_user_id = ObjectId(current_user['id'])
    obj_game_id = ObjectId(game_id)
    
    try:
        
        
        game = await userDB.update_one(

            {"_id": obj_user_id},
            {"$pull":{"myGamlendar": obj_game_id}},

        )
        
        # 푸시 알림 데이터 삭제
        await reDB.hdel(f"{game_date}:{str_user_id}",game_id)
        
        # 달력 캐시 삭제
        await reDB.delete(f"yearmonth:{str_user_id}")
    
        return '삭제완료'
    except:
        raise HTTPException(status_code=404, detail='이미 삭제되었거나 없는 게임입니다.')


@user.delete('/account', status_code=status.HTTP_200_OK)
async def account_delete(current_user=Depends(get_current_user)):
    str_user_id = current_user['id']
    obj_user_id = ObjectId(current_user['id'])
    
    try:
        await reDB.delete(f"refresh_token:{str_user_id}:*")
        
        await userDB.delete_one(
            {"_id": obj_user_id}
        )
        
        return '계정 삭제 완료'
    except:
        raise HTTPException(status_code=404, detail='계정 삭제를 실패하였습니다.')
    
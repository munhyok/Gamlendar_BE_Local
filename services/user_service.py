from config.mongo import userDB, userDB_Log, gameDB, myGamlendarDB
from config.redis import reDB
import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.user import Register, AddGame, MyGamlendar
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
SALT_NUM = os.getenv("SALT_NUM")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(register):
    
    verify_string = await reDB.get(f"email_verify:{register.username}")
    
    if verify_string != 'Verify':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="잘못된 요청입니다. 다시 시도하세요")
    
    register.password = pwd_context.hash(register.password)
    #register['account_provider'] = 'gamlendar'
    
    
    
    isUsernameExist = await userDB.find_one({"username":register.username})
    
    if isUsernameExist:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="이미 가입되어있는 계정입니다.")
    
    isNicknameExist = await userDB.find_one({"nickname":register.nickname})
    
    if isNicknameExist:
        raise HTTPException(status_code=status.HTTP_200_OK, detail="중복된 닉네임입니다.")
    
    _id = await userDB.insert_one(dict(register))
    _id_Log = await userDB_Log.insert_one(dict(register))
    
    db_cursor = userDB.find({"_id": _id.inserted_id})
    db_data = await db_cursor.to_list(length=None)
    db_serialize = users_serializer(db_data)
    user = jsonable_encoder(db_serialize)
    
    
    await reDB.delete(f"email_verify:{register.username}")
    
async def search_account(account):
    
    isAccountExist = await userDB.find_one({"username":account.username})
    
    if isAccountExist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입되어있는 계정입니다.")
    
    
async def search_nickname(nickname):
    
    isNicknameExist = await userDB.find_one({'nickname': nickname.nickname})
    
    if isNicknameExist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="중복되는 닉네임이 존재합니다.")
        #이거 다음 업데이트 때 confilct 로 고쳐
    


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


async def add_game_gamlendar(add_game: AddGame, current_user):
    game_id = add_game.game_id
    game_name = add_game.game_name
    game_date = add_game.game_date
    
    
    str_user_id = current_user["id"]
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    
    try: # relational db에 추가 v1 호환하기 위한 사전작업
        game_new = await myGamlendarDB.insert_one({
            "user_id": obj_user_id,
            "game_id": obj_game_id
        })
        
    except Exception as e:
        # 일단 추가만 하게 합니다. 데이터 일치를 위해
        
        pass
    
    
    
    find = await userDB.find_one(
            {"_id": obj_user_id, "myGamlendar": obj_game_id},
            {"_id": 1}
        )
    

    if find:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 게임입니다.")
    
    try:
        
        game = await userDB.update_one(
        
            {"_id": obj_user_id},

            {"$addToSet": {"myGamlendar": obj_game_id}}

        )
        
        await reDB.hset(f"{game_date}:{str_user_id}",game_id, game_name)
        
        await delete_matching_key(f"yearmonth:{str_user_id}:*")

        return {"message":"내 겜린더에 등록되었습니다."}
    
    except:
        HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 추가 실패")

async def find_game_gamlendar(game_id, current_user):
    obj_user_id = ObjectId(current_user["id"])
    obj_game_id = ObjectId(game_id)
    
    
    
    find = await userDB.find_one(
        {"_id": obj_user_id, "myGamlendar": obj_game_id},
        {"_id": 1}
    )
    
    if find:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 게임입니다.")
    
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약한 게임이 아닙니다.")
    
    
async def myGamlendar_date(date: str, current_user: MyGamlendar):
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


async def myGamlendar_yearmonth(yearmonth: str, current_user: MyGamlendar):
    user_id = ObjectId(current_user["id"])
    
    cache_data = await reDB.get(f"yearmonth:{current_user['id']}:{yearmonth}")
    
    if cache_data != None:
        
        return json.loads(cache_data)
    
    
    user_data = await fetch_gamlendar_yearmonth(user_id, yearmonth)
    result = {item["gamlendarDetails"]["date"] for item in user_data}

    await reDB.set(f"yearmonth:{current_user['id']}:{yearmonth}", json.dumps(list(result)), 86400)
    return result


async def remove_game_Gamlendar(game_id: str, game_date: str, current_user):
    str_user_id = current_user['id']
    
    obj_user_id = ObjectId(current_user['id'])
    obj_game_id = ObjectId(game_id)
    
    game_new = await myGamlendarDB.find_one_and_delete(
        {"user_id": obj_user_id, "game_id": obj_game_id}
    )
    
    try:

        game = await userDB.update_one(

            {"_id": obj_user_id},
            {"$pull":{"myGamlendar": obj_game_id}},

        )
        
        # 푸시 알림 데이터 삭제
        await reDB.hdel(f"{game_date}:{str_user_id}",game_id)
        
        # 달력 캐시 삭제
        await delete_matching_key(f"yearmonth:{str_user_id}:*")
    
        return '삭제완료'
    except:
        raise HTTPException(status_code=404, detail='이미 삭제되었거나 없는 게임입니다.')
    
    

async def update_nickname(nickname, current_user):
    obj_user_id = ObjectId(current_user["id"])
    
    
    isNicknameExist = await userDB.find_one({'nickname': nickname})
    
    if isNicknameExist:
        
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="중복되는 닉네임이 존재합니다.")
    
    
    await userDB.update_one(
        {"_id": obj_user_id},
        {"$set": {"nickname": nickname}}
    )
    
    
    return {"status_code": status.HTTP_200_OK, "detail": "닉네임이 변경되었습니다."}



async def remove_account(current_user):
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
    
async def delete_matching_key(pattern: str):
    async for key in reDB.scan_iter(pattern):
        await reDB.delete(key)
        
    
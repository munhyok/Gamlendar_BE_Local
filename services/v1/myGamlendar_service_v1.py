from config.mongo import userDB, userDB_Log, gameDB, myGamlendarDB
from config.redis import reDB
import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.user import Register, AddGame, MyGamlendar
from bson import ObjectId
from schemas.user_serializer import users_serializer
from passlib.context import CryptContext

from models.v1.response.CommonResponse import CommonResponseModel

from util.redis_utils import delete_matching_key
from util.password_utils import (
    get_password_hash, verify_password, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, SALT_NUM
)

import os



async def addToMyGamlendar(add_game: AddGame, current_user):
    
    game_id = add_game.game_id
    
    
    str_user_id = current_user["id"]
    obj_user_id = ObjectId(str_user_id)
    obj_game_id = ObjectId(game_id)
    
    try:
        
        relationDB_find = myGamlendarDB.find_one(
            {
                "user_id": obj_user_id,
                "game_id": obj_game_id
            }
        )
        
        if relationDB_find:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 게임입니다.")
        
        game_insert = await myGamlendarDB.insert_one(
            {
                "user_id": obj_user_id,
                "game_id": obj_game_id
            }
        )
        
        game_find = await gameDB.find_one(
            {"_id": obj_game_id}
        )
        
        
        game_name = game_find['name']
        game_date = game_find['date']
        
        await reDB.hset(f"{game_date}:{str_user_id}",game_id, game_name)
        
        await delete_matching_key(f"yearmonth:{str_user_id}:*")
        
        response = CommonResponseModel(status='Created',status_code=201)
    
        return response
    
    except HTTPException as http_except:
        raise http_except

    except Exception as e:
        #print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")
    
    
    
async def removeFromMyGamlendar(game_id: str, current_user): #
    str_user_id = current_user['id']
    
    obj_user_id = ObjectId(current_user['id'])
    obj_game_id = ObjectId(game_id)
    

    try:

        game_find = await gameDB.find_one(
            {"_id": obj_game_id}
        )
        #print(game_find)
        if not game_find:
            raise HTTPException(status_code=404, detail='없는 게임')
        
        game_date = game_find['date']
        
        await reDB.hdel(f"{game_date}:{str_user_id}",game_id)
        
        game_del= await myGamlendarDB.find_one_and_delete(
            {"user_id": obj_user_id, "game_id": obj_game_id}
        )
        
        #print(game_del)
        
        if not game_del:
            raise HTTPException(status_code=404, detail='이미 삭제되었거나 없는 게임입니다.')
        
        # 달력 캐시 삭제
        await delete_matching_key(f"yearmonth:{str_user_id}:*")
    
        response = CommonResponseModel()
        return response.model_dump()
    
    except HTTPException as http_except:
        raise http_except
    
    except Exception as e:
        #print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")
        
    
async def isGameInMyGamlendar(game_id: str, current_user): #달력에 등록된 게임인지 확인
    obj_user_id = ObjectId(current_user['id'])
    obj_game_id = ObjectId(game_id)
    
    try:
        found = await myGamlendarDB.find_one(
            {"user_id": obj_user_id, "game_id": obj_game_id},
        )
        
        if found:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 게임입니다.")
        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약한 게임이 아닙니다.")
    
    except HTTPException as http_except:
        raise http_except
        
    
    except Exception as e:    
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")

async def getMyGamlendarYearMonth(yearmonth: str, current_user: MyGamlendar):
    
    obj_user_id = ObjectId(current_user["id"])
    cache_data = await reDB.get(f"yearmonth:{current_user['id']}:{yearmonth}")
    
    if cache_data:
        return json.loads(cache_data)
    
    try:
        result = []
        yearmonth_cursor = myGamlendarDB.find(
            {"user_id": obj_user_id}
        )
        
        # 사용자가 겜린더에 등록한 게임 조회
        user_all_games = await yearmonth_cursor.to_list(length=None)
        
        for game in user_all_games:
            
            find = await gameDB.find_one(
                {"_id": game['game_id'], "yearmonth":yearmonth}
            )
            
            if find:
                date = find['date']
                result.append(date)
        
        response = CommonResponseModel(data= set(result))
        
        return response.model_dump()
    
    except HTTPException as http_except:
        raise http_except
    
    except Exception as e:
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")
            

async def getMyGamlendarDate(date: str, current_user: MyGamlendar):
    user_id = current_user["id"]
    obj_user_id = ObjectId(user_id)
    
    try: 
        user_game_list = []
        
        user_game = myGamlendarDB.find(
            {"user_id": obj_user_id}
        )
        
       
        
        game_list = await user_game.to_list(length=None)
        
        
        for game in game_list:
            find_game = await gameDB.find_one(
                {"_id": game['game_id'], "date":date},
                
            )
            
            
            if find_game:
                find_game['id'] = str(find_game['_id'])
                find_game.pop('_id')
            
                user_game_list.append(find_game)
            
        
        

        response = CommonResponseModel(data=user_game_list)

        return response.model_dump()
    
    except HTTPException as http_except:
        raise http_except
    
    except Exception as e:
        #print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")
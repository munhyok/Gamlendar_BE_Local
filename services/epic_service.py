from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from config.mongo import epicDB
from pymongo.errors import DuplicateKeyError
from datetime import datetime

async def get_epic_free_games_service():
    result = []
    current_time = datetime.now()
    #print(current_time)
    pipeline = [
        {"$match": {"end_date": {"$gte": current_time}}},
        #{"start_date": {"$gte": datetimeIso}},
    ]
    
    cursor = epicDB.aggregate(pipeline)
    
    async for freeGame in await cursor:
        #print(freeGame)
        freeGame['id'] = str(freeGame['_id'])
        del freeGame['_id']
        
        result.append(freeGame)
        
    return result
        
        
        
    
    
    
    

async def post_epic_free_games_service(epic_game):
    
    epic_game = dict(epic_game)
    
    try:
        result = await epicDB.insert_one(epic_game)
        
    except DuplicateKeyError as duplicateErr:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='중복 데이터가 존재합니다.')
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="알 수 없는 오류가 발생하였습니다.")
    
    return {"status": "Ok", "data": str(result.inserted_id)}
    
    
    
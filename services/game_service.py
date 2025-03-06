import json

from fastapi import APIRouter, HTTPException, status, Query
from config.redis import reDB
from config.mongo import gameDB
from config.tags_metadata import tags_metadata

from typing import List, Annotated
from datetime import date
from pymongoexplain import ExplainableCollection
from bson import ObjectId
from schemas.game_serializer import games_serializer
from models.game import gameForm, GameListForm



async def post_game_service(game):
    
    result = await gameDB.insert_one(dict(game))
    inserted_id = result.inserted_id
    
    db_cursor = gameDB.find({"_id": inserted_id})
    
    db_data = await db_cursor.to_list(length=None)
    
    # 직렬화 작업
    serialized_game = games_serializer(db_data) 

    #Crawling BOT에서 POST할 때 수집된 키워드를 Redis에 보내는 작업
    autokwd_dict = dict()
    
    for text in range(len(serialized_game[0]["autokwd"])):
        autokwd_dict[serialized_game[0]["autokwd"][text]] = 0
        
    await reDB.zadd('autocomplete', autokwd_dict)
    
    
    return {"status": "Ok", "data": serialized_game}


async def get_games_service(start_date:date, page, page_size, platform, tag):
    filters = {"date": {"$gte": start_date.isoformat()}}
    result = []
    
    if platform:
        filters['platform'] = {"$in": platform}
        
    if tag:
        filters['tag'] = {"$in": tag}

    
    skip = (page - 1) * page_size
    pipeline = [
        {"$match": filters},
        {"$sort": {"date": 1, "_id": 1}},
        {"$skip": skip},
        {"$limit": page_size}
    ]
    
    game_cursor = gameDB.aggregate(pipeline)
    
    #explain = await ExplainableCollection(gameDB).aggregate(pipeline)
    #print(explain)
    
    async for games in await game_cursor:
        raw = []
        
        raw.append(games)
        
        
        serialize = games_serializer(raw)
        result.append(serialize[0])
    
        
    if not result:
        raise HTTPException(status_code=404, detail="게임이 더이상 없습니다")
    
    return result

async def get_game_service(name):
    
    cache_data = await reDB.get("game:"+name)
    
    if cache_data == None:
        db_cursor = gameDB.find({"name":name})
        db_data = await db_cursor.to_list(length=None)
        
        db_serialize = games_serializer(db_data)
        
        
        await reDB.set("game:"+name, json.dumps(db_serialize), ex=120)
        
        return db_serialize
    
    return json.loads(cache_data)

async def get_date_service(date):
    
    cache_data = await reDB.get("date:"+date)
    
    if cache_data == None:
        
        db_cursor = gameDB.find({"date":date})
        db_data = await db_cursor.to_list(length=None)
        
        db_serialize = games_serializer(db_data)
        
        await reDB.set("date:"+date, json.dumps(db_serialize), ex=60)
        
        return db_serialize
    
    return json.loads(cache_data)

async def get_yearmonth_service(yearmonth):
    
    #yearmonth expire time: 60sec
    cache_data = await reDB.get("yearmonth:"+yearmonth)
    dateList = []
    
    
    if cache_data == None:
        
        db_cursor = gameDB.find({"yearmonth": yearmonth})
        db_data = await db_cursor.to_list(length=None)
        
    
        for num in range(len(db_data)):
            dateList.append(db_data[num]["date"])
        
        set_data = list(set(dateList))
        await reDB.set("yearmonth:"+yearmonth, json.dumps(set_data),ex=60)
        
        return set_data
    
    return json.loads(cache_data)

async def get_gindie_service(gindie):
    db_cursor = gameDB.find({"gindie":gindie})
    db_data = await db_cursor.to_list(length=None)
    
    result = games_serializer(db_data)
    
    return result

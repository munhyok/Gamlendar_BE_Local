import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.game import gameForm
from schemas.game_schema import games_serializer
from bson import ObjectId
from config.mongo import collection
from config.tags_metadata import tags_metadata
from config.redis import reCache



search = APIRouter(tags=['Search'])



@search.get("/search/autocomplete/{text}", status_code=status.HTTP_200_OK,
            description='검색창에 text를 입력하면 자동완성 키워드 데이터를 받아옵니다.')
async def get_text(text: str):
    
    text_bytes = text.encode('utf-8')
    
    
    min = b'[' + text_bytes
    max = b'[' + text_bytes + b"\xff"
    
    
    result = reCache.execute_command('zrange', 'autocomplete', min, max, 'BYLEX')

    return result


@search.get("/search/game/{keyword}", status_code=status.HTTP_200_OK,
            description='검색 결과 데이터를 받아옵니다.')
async def get_game_result(keyword: str):
    
    cache_data = reCache.get("search:"+keyword)
    db_data = list()
    
    if cache_data == None:
        for data in games_serializer(collection.find({"$text":{"$search":keyword}})):
            db_data.append(data)
        
        reCache.set("search:"+keyword, json.dumps(db_data), ex=300)
        return db_data
    
    
    return json.loads(cache_data)
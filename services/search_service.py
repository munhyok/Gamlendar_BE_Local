import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.game import gameForm
from schemas.game_serializer import games_serializer
from bson import ObjectId
from config.mongo import gameDB
from config.tags_metadata import tags_metadata
from config.redis import reDB


async def get_text_service(text):
    
    text_bytes = text.encode('utf-8')
    
    
    min = b'[' + text_bytes
    max = b'[' + text_bytes + b"\xff"
    
    
    result = await reDB.execute_command('zrange', 'autocomplete', min, max, 'BYLEX')
    

    
    return result

async def get_game_result_service(keyword):
    cache_data = reDB.get("search:"+keyword)
    cache_data = None
    if cache_data == None:
        db_cursor = gameDB.find({"$text": {"$search":keyword}},
                                {"score": {"$meta":'textScore'}}
                                ).sort({ "score": { "$meta": "textScore" } })
        db_data = await db_cursor.to_list(length=None)

        
        db_serialize = games_serializer(db_data)
        #print(db_serialize)
        await reDB.set("search:"+keyword, json.dumps(db_serialize), ex=300)
        
        return db_serialize
    
    
    return json.loads(cache_data)
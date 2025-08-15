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
    
    #text_bytes = text.encode('utf-8')
    #
    #
    #min = b'[' + text_bytes
    #max = b'[' + text_bytes + b"\xff"
    #
    #
    #result = await reDB.execute_command('zrange', 'autocomplete', min, max, 'BYLEX')
    #
#
    #
    #return result
    
    
    
    result = []
    pipeline = [
            {"$match": {"$text": {"$search": text}}},
            {"$sort": {"score": {"$meta": "textScore"}}}
    ]
    
    search_cursor = gameDB.aggregate(pipeline)
        
    async for games in await search_cursor:
        raw = []
        raw.append(games)
        serialize = games_serializer(raw)
        result.append(serialize[0])
        
    
        
    
    return result
    

async def get_game_result_service(name):
    
    
    result = await gameDB.find_one({"name": name})
    
    result['id'] = str(result['_id'])
    
    del result['_id']
    
    
    return result
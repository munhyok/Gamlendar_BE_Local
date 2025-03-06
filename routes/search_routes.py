import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.game import gameForm
from schemas.game_serializer import games_serializer
from bson import ObjectId
from config.mongo import gameDB
from config.tags_metadata import tags_metadata
from config.redis import reDB

from services.search_service import (
    get_text_service, get_game_result_service
)

search = APIRouter(tags=['Search'])



@search.get("/search/autocomplete/{text}", status_code=status.HTTP_200_OK,
            description='검색창에 text를 입력하면 자동완성 키워드 데이터를 받아옵니다.')
async def get_text(text: str):
    
    result = await get_text_service(text)
    
    return result

@search.get("/search/game/{keyword}", status_code=status.HTTP_200_OK,
            description='검색 결과 데이터를 받아옵니다.')
async def get_game_result(keyword: str):
    
    result = await get_game_result_service(keyword)
    
    return result
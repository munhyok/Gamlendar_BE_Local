import json
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from models.game import gameForm, GameListForm
from schemas.game_serializer import games_serializer
from bson import ObjectId
from config.mongo import gameDB
from config.tags_metadata import tags_metadata
from config.redis import reDB
from typing import List, Annotated
from datetime import date


from services.game_service import (
    post_game_service, get_games_service, 
    get_game_service, get_date_service,
    get_yearmonth_service, get_gindie_service
    
)

game = APIRouter(tags=['Game'])

#Update는 추후 관리페이지 제작할 때 같이 제작

### Create
@game.post("/admin/games", status_code=status.HTTP_201_CREATED,
           description='게임 정보를 DB에 업로드하기 위한 post입니다.')
async def post_game(game: gameForm):
    
    result = await post_game_service(game)
    
    return result



### Read
@game.get("/games", status_code=status.HTTP_200_OK, response_model=List[GameListForm],
          description='날짜를 기준으로 게임을 출력해줍니다.')
async def get_games(
    start_date: date,
    page: int = 1,
    page_size: int = 15,
    platform: Annotated[list[str], Query()]=None,
    tag: Annotated[list[str], Query()]= None ):
    
    
    result = await get_games_service(start_date, page, page_size, platform, tag)
    
    return result


@game.get("/games/{name}", status_code=status.HTTP_200_OK,
          description='게임 이름으로 정보을 얻어올 수 있습니다.')
async def get_game(name: str):
    # game expire time : 10min
    
    result = await get_game_service(name)
    
    return result


@game.get("/games/date/{date}", status_code=status.HTTP_200_OK,
          description='YYYY-MM-DD 형식으로 입력하고 해당 날짜의 게임들을 불러옵니다.')
async def get_date(date: str):
    
    result = await get_date_service(date)
    
    return result
    
    



@game.get("/games/yearmonth/{yearmonth}", status_code=status.HTTP_200_OK,
          description='YYYY-MM 형식으로 입력하면 해당 년-월에 출시하는 날짜(YYYY-MM-DD) 정보를 모아서 불러옵니다. 달력에 표시하기 위함')
async def get_yearmonth(yearmonth: str):
    
    result = await get_yearmonth_service(yearmonth)
    
    return result



@game.get("/games/gindie/{gindie}", status_code=status.HTTP_200_OK,
          description='겜린더 등록페이지에 수동으로 등록한 게임 조회')
async def get_gindie(gindie: str):
    
    result = await get_gindie_service(gindie)
    
    return result



### Delete
@game.delete("/admin/games/{id}", status_code=status.HTTP_204_NO_CONTENT,
             description='ObjectID로 삭제')
async def delete_game_obj(id: str):
    await gameDB.find_one_and_delete({"_id":ObjectId(id)})
    return {"status":"Delete Complete"}


@game.delete("/admin/games/{name}", status_code=status.HTTP_204_NO_CONTENT,
             description='게임 이름으로 삭제')
async def delete_game(name: str):
    await gameDB.find_one_and_delete({"name":name})
    return {"status": "Delete Complete"}





import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.game import gameForm, GameListForm
from schemas.game_serializer import games_serializer
from bson import ObjectId
from config.mongo import gameDB
from config.tags_metadata import tags_metadata
from config.redis import reDB
from typing import List
from datetime import date

game = APIRouter(tags=['Game'])

#Update는 추후 관리페이지 제작할 때 같이 제작

### Create
@game.post("/games", status_code=status.HTTP_201_CREATED,
           description='게임 정보를 DB에 업로드하기 위한 post입니다.')
async def post_game(game: gameForm):
    
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



### Read
@game.get("/games/", status_code=status.HTTP_200_OK, response_model=List[GameListForm],
          description='날짜를 기준으로 10개씩 게임 출력해줍니다.')
async def get_games(start_date: date, page: int = 1, page_size: int = 10):
    
    cache_data = await reDB.get("gameList:"+str(start_date)+'_'+str(page))
    
    if cache_data is None:
        skip = (page - 1) * page_size
        query = {"date": {"$gte": start_date.isoformat()}}
        
        cursor = gameDB.find(query).sort("date", 1).skip(skip).limit(page_size)
        games = []
        
        async for game in cursor:
            games.append(game)
        
        if not games:
            raise HTTPException(status_code=404, detail="No games found")
        
        # Serialize the games
        serialize = games_serializer(games)

        # Cache the serialized data
        await reDB.set("gameList:"+str(start_date)+'_'+str(page), json.dumps(serialize), ex=600)

        return serialize
    
    return json.loads(cache_data)


@game.get("/games/{name}", status_code=status.HTTP_200_OK,
          description='게임 이름으로 정보을 얻어올 수 있습니다.')
async def get_game(name: str):
    # game expire time : 10min
    cache_data = await reDB.get("game:"+name)
    
    if cache_data == None:
        db_cursor = gameDB.find({"name":name})
        db_data = await db_cursor.to_list(length=None)
        
        db_serialize = games_serializer(db_data)
        
        
        await reDB.set("game:"+name, json.dumps(db_serialize), ex=120)
        
        return db_serialize
    
    return json.loads(cache_data)


@game.get("/games/date/{date}", status_code=status.HTTP_200_OK,
          description='YYYY-MM-DD 형식으로 입력하고 해당 날짜의 게임들을 불러옵니다.')
async def get_date(date: str):
    # date expire time : 60sec
    cache_data = await reDB.get("date:"+date)
    
    if cache_data == None:
        
        db_cursor = gameDB.find({"date":date})
        db_data = await db_cursor.to_list(length=None)
        
        db_serialize = games_serializer(db_data)
        
        await reDB.set("date:"+date, json.dumps(db_serialize), ex=60)
        
        return db_serialize
    
    return json.loads(cache_data)



@game.get("/games/yearmonth/{yearmonth}", status_code=status.HTTP_200_OK,
          description='YYYY-MM 형식으로 입력하면 해당 년-월에 출시하는 날짜(YYYY-MM-DD) 정보를 모아서 불러옵니다. 달력에 표시하기 위함')
async def get_yearmonth(yearmonth: str):
    
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



@game.get("/games/gindie/{gindie}", status_code=status.HTTP_200_OK,
          description='겜린더 등록페이지에 수동으로 등록한 게임 조회')
async def get_gindie(gindie: str):
    
    db_cursor = gameDB.find({"gindie":gindie})
    db_data = await db_cursor.to_list(length=None)
    
    result = games_serializer(db_data)
    
    return result



### Delete
@game.delete("/games/{id}", status_code=status.HTTP_204_NO_CONTENT,
             description='ObjectID로 삭제')
async def delete_game_obj(id: str):
    await gameDB.find_one_and_delete({"_id":ObjectId(id)})
    return {"status":"Delete Complete"}


@game.delete("/games/{name}", status_code=status.HTTP_204_NO_CONTENT,
             description='게임 이름으로 삭제')
async def delete_game(name: str):
    await gameDB.find_one_and_delete({"name":name})
    return {"status": "Delete Complete"}





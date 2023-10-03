import json
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from models.game import gameForm
from schemas.game_schema import games_serializer
from bson import ObjectId
from config.mongo import collection
from config.tags_metadata import tags_metadata
from config.redis import reCache


game = APIRouter(tags=['Game'])

#Update는 추후 관리페이지 제작할 때 같이 제작

### Create
@game.post("/games", status_code=status.HTTP_201_CREATED,
           description='게임 정보를 DB에 업로드하기 위한 post입니다.')
async def post_game(game: gameForm):
    
    _id = collection.insert_one(dict(game))
    game = games_serializer(collection.find({"_id": _id.inserted_id}))
    game = jsonable_encoder(game)

    #Crawling BOT에서 POST할 때 수집된 키워드를 Redis에 보내는 작업
    autokwd_dict = dict()
    
    for text in range(len(game[0]["autokwd"])):
        autokwd_dict[game[0]["autokwd"][text]] = 0
    
    reCache.zadd('autocomplete', autokwd_dict)
    
    return {"status": "Ok", "data": game}



### Read
@game.get("/games/{name}", status_code=status.HTTP_200_OK,
          description='게임 이름으로 정보을 얻어올 수 있습니다.')
async def get_game(name: str):
    # game expire time : 10min
    
    if reCache.get("game:"+name) == None:
        db_data = games_serializer(collection.find({"name":name}))
        reCache.set("game:"+name,json.dumps(db_data), ex=120)
        
        return json.loads(reCache.get("game:"+name))
    
    return json.loads(reCache.get("game:"+name))


@game.get("/games/date/{date}", status_code=status.HTTP_200_OK,
          description='YYYY-MM-DD 형식으로 입력하고 해당 날짜의 게임들을 불러옵니다.')
async def get_date(date: str):
    # date expire time : 60sec
    
    if reCache.get("date:"+date) == None:
        db_data = games_serializer(collection.find({"date":date}))
        reCache.set("date:"+date, json.dumps(db_data), ex=60)
        
        return json.loads(reCache.get("date:"+date))
    
    return json.loads(reCache.get("date:"+date))



@game.get("/games/yearmonth/{yearmonth}", status_code=status.HTTP_200_OK,
          description='YYYY-MM 형식으로 입력하면 해당 년-월에 출시하는 날짜(YYYY-MM-DD) 정보를 모아서 불러옵니다. 달력에 표시하기 위함')
async def get_yearmonth(yearmonth: str):
    
    #yearmonth expire time: 60sec
    
    dateList = []
    
    if reCache.get("yearmonth:"+yearmonth) == None:
        db_data = games_serializer(collection.find({"yearmonth":yearmonth}))
    
        for num in range(len(db_data)):
            dateList.append(db_data[num]["date"])
        
        tmp = list(set(dateList))
        reCache.set("yearmonth:"+yearmonth, json.dumps(tmp),ex=60)
        
        return json.loads(reCache.get("yearmonth:"+yearmonth))
        
    
    return json.loads(reCache.get("yearmonth:"+yearmonth))



@game.get("/games/gindie/{gindie}", status_code=status.HTTP_200_OK,
          description='겜린더 등록페이지에 수동으로 등록한 게임 조회')
async def get_gindie(gindie: str):
    return games_serializer(collection.find({"gindie": gindie}))



### Delete
@game.delete("/games/{id}", status_code=status.HTTP_204_NO_CONTENT,
             description='ObjectID로 삭제')
async def delete_game_obj(id: str):
    collection.find_one_and_delete({"_id":ObjectId(id)})
    return {"status":"Delete Complete"}


@game.delete("/games/{name}", status_code=status.HTTP_204_NO_CONTENT,
             description='게임 이름으로 삭제')
async def delete_game(name: str):
    collection.find_one_and_delete({"name":name})
    return {"status": "Delete Complete"}
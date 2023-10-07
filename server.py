from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pymongo import MongoClient

import redis
from redis_om import get_redis_connection
from routes.game_routes import game
from routes.search_routes import search
from config.tags_metadata import tags_metadata


app = FastAPI(title='겜린더 API', openapi_tags=tags_metadata)

origins = [ 'http://localhost',
            'http://localhost:5200' ]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_methods=['*'],
    allow_headers=['*'],
    allow_credentials=True, 
)


app.include_router(game)
app.include_router(search)

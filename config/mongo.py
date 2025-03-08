from pymongo import MongoClient, AsyncMongoClient, pool_options
import pymongo
import asyncio
from dotenv import load_dotenv
import os
import uvicorn


load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST")





db_connection = AsyncMongoClient(MONGODB_HOST, 
                                 maxconnecting=4,
                                 maxpoolsize=250,
                                 minpoolsize=20,
                                 maxidletimems=300000,
                                 waitqueuetimeoutms=5000,
                                 
                                 )
#print(db_connection.options.pool_options.max_connecting)
#print(db_connection.options.pool_options.max_pool_size)
#print(db_connection.options.pool_options.min_pool_size)
#print(db_connection.options.pool_options.max_idle_time_seconds)
#print(db_connection.options.pool_options.wait_queue_timeout)


db = db_connection.Gamlendar



async def create_collections():
    
    collection_list = ["Gamlendar_game", "User"]


    mongo_collectionList = await db.list_collection_names()

    for collection in collection_list:
        if collection not in mongo_collectionList:
            db.create_collection(collection)



gameDB = db["Gamlendar_game"]
userDB = db["User"]

async def main():
    await gameDB.create_index([
        ("date", pymongo.ASCENDING),
        ("platform", pymongo.ASCENDING)
    ])
    await gameDB.create_index([
        ("date", pymongo.ASCENDING),
        ("tag", pymongo.ASCENDING)
    ])

    
    index_info = await gameDB.index_information()
    
    await create_collections()
    
    

    
try:
    loop = asyncio.get_running_loop()
    task = loop.create_task(main())
    task
except:
    asyncio.run(main())
    




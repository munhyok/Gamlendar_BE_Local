from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os


load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST")

db_connection = AsyncIOMotorClient(MONGODB_HOST)
db = db_connection.Gamlendar

async def create_collections():
    
    collection_list = ["Gamlendar_game", "User"]


    mongo_collectionList = await db.list_collection_names()

    for collection in collection_list:
        if collection not in mongo_collectionList:
            db.create_collection(collection)

gameDB = db["Gamlendar_game"]
userDB = db["User"]




from pymongo import MongoClient
db_connection = MongoClient("mongodb://localhost:27017")
db = db_connection.Gamlendar

collection = db["Gamlendar_game"]
collection.create_index([('autokwd','text')])

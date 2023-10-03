
from pydantic import BaseModel, Field
import time
from bson import ObjectId

class gameForm(BaseModel):
    
    timestamp: str = str(time.time())
    path: str = 'game'
    gindie: str = 'gamlendar'
    name: str
    autokwd: list[str]
    company: str
    yearmonth: str
    date: str
    description: str 
    platform: list[str]
    gameurl: str
    imageurl: str
    yturl: str | None = None
    
    screenshots: list[str] | None = None
    
    adult: bool
    
    class Config:
        json_encoders = {ObjectId: str}

from pydantic import BaseModel, Field
import time
from bson import ObjectId
from typing import List

class Game(BaseModel):
    id: str
    timestamp: str
    path: str
    gindie: str
    name: str
    autokwd: List[str]
    company: str
    yearmonth: str
    date: str
    description: str
    platform: List[str]
    gameurl: str
    imageurl: str
    yturl: str
    screenshots: List[str]
    adult: bool

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
    gameurl: dict[str, str]
    imageurl: str
    yturl: str = None
    
    screenshots: list[str] = None
    tag: list[str]
    
    adult: bool
    
    class Config:
        json_encoders = {ObjectId: str}
        
        

        
class GameListForm(BaseModel):
    
    id: str
    timestamp: str
    path: str
    gindie: str
    name: str
    autokwd: List[str]
    company: str
    yearmonth: str
    date: str
    description: str
    platform: List[str]
    gameurl: dict[str, str]
    imageurl: str
    yturl: str
    screenshots: List[str]
    tag: List[str]
    adult: bool
    
    
    class Config:
        json_encoders = {ObjectId: str}
    
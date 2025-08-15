from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from typing import List

class EpicFreeGameForm(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime
    image_url: str
    url: str
    
    

class EpicFreeGame(BaseModel):
    id: str
    title: str
    start_date: datetime
    end_date: datetime
    image_url: str
    url: str
    

class EpicFreeGameResponse(BaseModel):
    status: str = Field(default="Ok")
    status_code: int = Field(default=200)
    data: List[EpicFreeGame] = Field(default_factory=list)
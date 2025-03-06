from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from beanie import Document
from .game import Game, gameForm

class Register(BaseModel):
    username: str
    nickname: str
    password: str
    myGamlendar: list[str] = []
    
    @validator('username', 'nickname', 'password')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('빈 값은 허용되지 않습니다.')
        return v
    
    
class Login(BaseModel):
    username: EmailStr
    password: str
    
    
class UserResponse(BaseModel):
    id: str
    username: EmailStr
    nickname: str
    
    
    

class MyGamlendar(BaseModel):
    id: str
    myGamlendar: list[str]
    gamlendarDetails: list
    
    
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class FindAccount(BaseModel):
    username: EmailStr
    
class FindNickname(BaseModel):
    nickname: str
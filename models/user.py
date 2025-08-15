from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from beanie import Document
from .game import Game, gameForm
from bson import ObjectId

class Register(BaseModel):
    username: str
    nickname: str
    password: str
    
    account_provider: str = 'gamlendar'
    myGamlendar: list[str] = []
    
    @validator('username', 'nickname', 'password')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('빈 값은 허용되지 않습니다.')
        return v
    
class OauthRegister(BaseModel):
    username: str
    nickname: str
    
    account_provider: str
    apple_token: str
    myGamlendar: list[str] = []
    @validator('username', 'nickname', 'account_provider')
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
    account_provider: str
    

class MyGamlendar(BaseModel):
    id: str
    myGamlendar: list[str]
    gamlendarDetails: list
    
    
class Token(BaseModel):
    access_token: str
    refresh_token: str
    uuid: str
    token_type: str
    
    
    
class RefreshToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class AddGame(BaseModel):
    game_id: str
    game_date: Optional[str] = None
    game_name: Optional[str] = None
    


class FindAccount(BaseModel):
    username: EmailStr
    
class FindNickname(BaseModel):
    nickname: str
    
class MyGamlendarRelatedForm(BaseModel):
    user_id: str
    game_id: str
    
    
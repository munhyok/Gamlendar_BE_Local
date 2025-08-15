from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from models.epicstore import EpicFreeGame, EpicFreeGameForm, EpicFreeGameResponse
from services.epic_service import (
    get_epic_free_games_service, post_epic_free_games_service
)



epic = APIRouter(tags=['EpicStore'])



@epic.post('/admin/epic/free-games', status_code=status.HTTP_201_CREATED,
           description='에픽스토어 무료 게임 목록을 추가합니다.')
async def post_epic_free_games(epic_game: EpicFreeGameForm):
    result = await post_epic_free_games_service(epic_game)
    return result

@epic.get('/epic/free-games', status_code=status.HTTP_200_OK, response_model=EpicFreeGameResponse,
           description='에픽스토어 무료 게임 목록을 가져옵니다.')
async def get_epic_free_games():
    result = await get_epic_free_games_service()
    response = EpicFreeGameResponse(data=result)
    return response



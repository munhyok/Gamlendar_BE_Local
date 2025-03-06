import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from services.game_service import get_games_service

@pytest.fixture
def mock_game_data():
    return [
        {
          "_id": '123123',
          "timestamp": "1741280398.011619",
          "path": "game",
          "gindie": "gamlendar",
          "name": "string",
          "autokwd": [
            "string"
          ],
          "company": "string",
          "yearmonth": "string",
          "date": "2025-03-07",
          "description": "string",
          "platform": [
            "string"
          ],
          "gameurl": "string",
          "imageurl": "string",
          "yturl": "string",
          "screenshots": [
            "string"
          ],
          
          "tag": [
              
          ],
          
          "adult": True
        }
    ]
    
@pytest.mark.asyncio # async def 테스트 함수 실행
@patch("services.game_service.gameDB.aggregate", new_callable=AsyncMock)
async def test_get_games_service(mock_aggregate, mock_game_data):
    
    # 비동기 커서 객체처럼 동작하도록 설정
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = iter(mock_game_data)  # 비동기 순회 가능 객체 설정
    mock_aggregate.return_value = mock_cursor 
    
    
    start_date = date(2025, 3, 7) #date 객체로 설정
    
    
    result = await get_games_service(start_date=start_date, page=1, page_size=10, platform=None, tag=None)
    
    assert len(result) == 1
    assert result[0]["name"] == "string"
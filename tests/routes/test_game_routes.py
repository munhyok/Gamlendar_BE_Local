import pytest
from server import app
from fastapi.testclient import TestClient
from routes.game_routes import get_games
from datetime import date

client = TestClient(app)



# GET
def test_get_games():
    date_ = date(2025,1,1)
    response = client.get("/games/", params={"start_date": date_, "page": 1, "page_size": 10})
    
    
    assert response.status_code == 200
    
def test_get_game():
    game_name = "string"
    response = client.get(f"/games/{game_name}")
    
    assert response.status_code == 200
    
    
    
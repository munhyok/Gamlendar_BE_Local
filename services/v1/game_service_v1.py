import json

from fastapi import APIRouter, HTTPException, status, Query
from config.redis import reDB
from config.mongo import gameDB, myGamlendarDB
from config.tags_metadata import tags_metadata
from schemas.game_serializer import games_serializer
from models.game import gameForm, GameListForm

from typing import List, Annotated
from datetime import date
from bson import ObjectId



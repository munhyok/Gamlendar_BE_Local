from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, Field, StrictStr, Strict
from typing import Optional, List, Union
from beanie import Document



class CommonResponseModel(BaseModel):
    status: str = Field(default='Ok')
    status_code: int = Field(default=200)
    data: list = Field(default=[])
    msg: str = Field(default='정상적으로 처리되었습니다')

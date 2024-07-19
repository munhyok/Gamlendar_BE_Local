from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from beanie import Document


class CommonResponse(BaseModel):
    pass
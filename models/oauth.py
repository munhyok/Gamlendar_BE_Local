from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AppleSignIn(BaseModel):
    
    authorization_code: str = Field(..., alias='authorizationCode')
    identity_token: str = Field(..., alias='identityToken')
    
    platform: str = Field(..., description="Platform from which the request is made, e.g., 'ios', 'android', 'web'")
    myGamlendar: list[str] = []
    #user_info: Optional[str] = Field(None, alias='user')
from fastapi import HTTPException, status

class CommonExceptionResponse(HTTPException):
    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        super().__init__(self, status_code=status_code, detail=detail, headers=headers)
        
class GameConflictError(CommonExceptionResponse):
    pass
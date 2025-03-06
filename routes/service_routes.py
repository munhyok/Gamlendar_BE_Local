import uvicorn
from fastapi import APIRouter,FastAPI, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates


service = APIRouter(tags=['Service'])

templates = Jinja2Templates(directory='templates')

@service.get('/terms-of-service')
async def terms_of_service(request: Request):
    return templates.TemplateResponse(
        name="Terms-Of-Service.html", context={'request':request}
    )
    
@service.get('/privacy-policy')
async def privacy_policy(request: Request):
    return templates.TemplateResponse(
        name="Privacy-Policy.html", context={'request':request}
    )
    
    
@service.get('/version')
async def version():
    return {"service_version":"1.0.5"}
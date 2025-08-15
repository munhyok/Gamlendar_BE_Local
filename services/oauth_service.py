from fastapi import APIRouter, HTTPException, status, Depends, Header, Form
from models.oauth import AppleSignIn
from config.mongo import userDB, userDB_Log
from config.redis import reDB
from models.user import Register, OauthRegister
from util.password_utils import create_uuid, create_access_token, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
from util.apple_auth_utils import generate_client_secret, verify_apple_id_token
from bson import ObjectId
from datetime import timedelta
import httpx
import os
from dotenv import load_dotenv

import logging
import json

from config.apple import APPLE_PRIVATE_KEY_CONTENT


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL")

GOOGLE_IOS_CLIENT_ID = os.getenv("GOOGLE_IOS_CLIENT_ID")
GOOGLE_ANDROID_CLIENT_ID = os.getenv("GOOGLE_ANDROID_CLIENT_ID")
GOOGLE_IOS_REDIRECT_URI = os.getenv("GOOGLE_IOS_REDIRECT_URI")
GOOGLE_ANDROID_REDIRECT_URI = os.getenv("GOOGLE_ANDROID_REDIRECT_URI")


APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
APPLE_SERVICE_ID = os.getenv("APPLE_SERVICE_ID")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_AUTH_KEY_FILE = os.getenv("APPLE_AUTH_KEY_FILE")  
APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI")




oauth = APIRouter(tags=['OAuth'])


async def get_access_refresh_token(user: dict):
    
        #print(user)

        device_id = str(create_uuid())
        access_token = create_access_token(data={"sub": str(user['_id'])})
        
        await reDB.delete(f"refresh_token:{str(user['_id'])}:{device_id}")
        refresh_token = create_refresh_token(data={"sub": str(user['_id'])}, UUID=device_id)
        await reDB.setex(f"refresh_token:{str(user['_id'])}:{device_id}", timedelta(days = REFRESH_TOKEN_EXPIRE_DAYS), refresh_token)
        
        return {"access_token": access_token, "refresh_token":refresh_token, "uuid":device_id, "token_type": "bearer"}
    
async def new_user_register(email_from_provider, email_id, provider, apple_token):
    register_data = {
        "username": email_from_provider,
        "nickname": email_id,
        "account_provider": provider,
        "apple_token": apple_token,
        "myGamlendar": [],
    }
    # ValueError Check 용도..
    register = OauthRegister(**register_data)
    
    
    # 회원가입
    user = await userDB.insert_one(register.dict())
    user_Log = await userDB_Log.insert_one(register.dict())
    findUser = await userDB.find_one({"username":email_from_provider})
    result = await get_access_refresh_token(findUser)
    
    return result


async def google_login_service(code):
    token_url = "https://accounts.google.com/o/oauth2/token"
    
    data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }  
    
    
    headers = {"Accept": "application/json"}
    
    try:
    
        async with httpx.AsyncClient() as client: 
            response = await client.post(token_url, data=data, headers= headers)

            #print(response)
            #print(f"DEBUG: Google Token Exchange Status Code: {response.status_code}")
            #print(f"DEBUG: Google Token Exchange Response Body: {response.text}")
            respJson = response.json()

            token = respJson['access_token']
            #print(token)



        async with httpx.AsyncClient() as client:
            # get email info from google

            #print('token:', token)
            headers.update({'Authorization': f"Bearer {token}"})
            response = await client.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)


            data_from_google = response.json()
            #print(data_from_google)

            email_from_google = data_from_google['email']

            email_id = email_from_google.split('@')


            # find email from gamlendar userdb
            isUsernameExist = await userDB.find_one({"username":email_from_google})

            if isUsernameExist: # 기존 가입한 유저를 찾았을 경우 Access, Refresh Token 발급
                if isUsernameExist['account_provider'] == 'google':
                    result = await get_access_refresh_token(isUsernameExist)
                    return result

                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="구글 계정으로 가입된 유저가 아닙니다.")
            else:
                #신규 가입 로직
                # Generate Register Data
                result = await new_user_register(email_from_google, email_id[0], 'google', '')
                

                return result
    except httpx.HTTPStatusError as e:
        #print(e)
        logger.error(f"Google API response error: {e.response.status_code}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Google API 오류: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Network error: {e}")
        raise HTTPException(status_code=500, detail="네트워크 오류: 구글 API에 연결할 수 없습니다.")
    except KeyError as e:
        logger.error(f"Missing expected key in Google API response: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Google 응답에서 필수 정보가 누락되었습니다: {e}")
    except json.JSONDecodeError: # json 임포트 필요
        logger.error("Failed to decode JSON from Google API response.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google 응답을 처리할 수 없습니다.")
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.exception("An unexpected error occurred during Google login service.") # 전체 스택 트레이스 로깅
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    
async def apple_login_service(request_data: AppleSignIn):
    
    APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
    APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
    
    client_id = None
    
    auth_code = request_data.authorization_code
    id_token_from_app = request_data.identity_token
    platform = request_data.platform
    #user_info_str_from_app = request_data.user_info
    
    if platform == 'ios':
        client_id = APPLE_CLIENT_ID
    elif platform == 'android':
        client_id = APPLE_SERVICE_ID
    elif platform == 'web':
        client_id = APPLE_SERVICE_ID
        
    
    client_secret = await generate_client_secret(client_id, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY_CONTENT)
    
    
    
    token_exchange_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": APPLE_REDIRECT_URI,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(APPLE_TOKEN_URL, data=token_exchange_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Apple로부터 받은 ID 토큰
            server_id_token = tokens.get("id_token")
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token") #revoke용 토큰이라 DB에 저장해야합니다...
            
            #print(f"DEBUG: Apple Token Exchange Response: {tokens}")
            
            platform_refresh_token = f"{platform}:{refresh_token}"
            

            if not server_id_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID Token not received from Apple after code exchange.")

            # 3. 서버에서 받은 ID 토큰 검증
            # (앱에서 nonce를 사용했다면, 여기 verify_apple_id_token에 nonce를 전달하여 추가 검증합니다.)
            id_token_claims = await verify_apple_id_token(server_id_token, client_id)

            # 4. 사용자 정보 추출
            apple_user_id = id_token_claims.get("sub") # Apple 고유 사용자 ID
            email = id_token_claims.get("email")
            email_verified = id_token_claims.get("email_verified") == True # Apple은 불리언 값으로 보냄

            first_name = None
            last_name = None

            email_id = email.split('@')

            isUsernameExist = await userDB.find_one({"username":email})

            if isUsernameExist: # 기존 가입한 유저를 찾았을 경우 Access, Refresh Token 발급
                if isUsernameExist['account_provider'] == 'apple':
                    result = await get_access_refresh_token(isUsernameExist)
                    return result
                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="애플 계정으로 가입된 유저가 아닙니다.")
            else:
                #신규 가입 로직
                # Generate Register Data
                result = await new_user_register(email, email_id[0], 'apple', apple_token=platform_refresh_token)

                return result
    except httpx.HTTPStatusError as e:
        logger.error(f"Apple token exchange failed: {e.response.status_code}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Apple API 오류: {e.response.text}")
    
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.exception("An unexpected error occurred during Google login service.") # 전체 스택 트레이스 로깅
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    
async def apple_account_revoke(current_user):
    
    APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke"
    
    obj_user_id = ObjectId(current_user['_id'])
    
    user = await userDB.find_one({"_id": obj_user_id})
    if not user or user['account_provider'] != 'apple':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apple 계정이 아닙니다.")
    
    platform_token = user['apple_token'].split(':')
    
    platform = platform_token[0]
    refresh_token = platform_token[1]
    
    client_id = None
    if platform == 'ios':
        client_id = APPLE_CLIENT_ID
    elif platform == 'android':
        client_id = APPLE_SERVICE_ID
    elif platform == 'web':
        client_id = APPLE_SERVICE_ID
    
    
    
    
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        
    }
    
    data = {
        'client_id': client_id,
        'client_secret': await generate_client_secret(client_id, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY_CONTENT),
        'token': refresh_token,
        'token_type_hint': 'refresh_token',
    }
    
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(APPLE_REVOKE_URL, headers=headers, data=data)
            
            return {"message": "Apple 계정이 성공적으로 해지되었습니다."}
    except httpx.HTTPStatusError as e:
        logger.error(f"Apple account revoke failed: {e.response.status_code}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Apple API 오류: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Network error during Apple account revoke: {e}")
        raise HTTPException(status_code=500, detail="네트워크 오류: 애플 API에 연결할 수 없습니다.")
    except Exception as e:
        logger.exception("An unexpected error occurred during Apple account revoke.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            
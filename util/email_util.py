
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from config.redis import reDB
from config.mongo import userDB
from fastapi import APIRouter, HTTPException, status

import aiosmtplib

from dotenv import load_dotenv
import os
import secrets


load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")


async def send_email(msg):
    try:
        smtp = aiosmtplib.SMTP(hostname='smtp.gmail.com', port=587, use_tls=False)
        await smtp.connect()
        await smtp.ehlo()
        if smtp.supports_extension("STARTTLS"):
            await smtp.starttls()
            await smtp.ehlo()
            
        await smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        
        await smtp.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"message": "이메일 전송 중 오류가 발생했습니다."})
    finally:
        await smtp.quit()


async def send_email_verify_code(to_email: str):
    
    
    subject = '[겜린더] 이메일 인증번호 입니다.'
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    
    verify_code = await random_code_generator("email_verify", to_email)
    
    msg.attach(MIMEText(f"이메일 인증 코드: {verify_code}\n5분안에 입력해주세요", 'plain'))
    
    msg.as_string()
    
    await send_email(msg)
    
    
    

async def send_password_recovery_code(to_email:str):
    
    user_email = await userDB.find_one({"username":to_email})
    
    if not user_email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message":"계정을 찾을 수 없습니다."})
    
    subject = "[겜린더] 비밀번호 복구 인증번호 입니다."

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    
    recovery_code = await random_code_generator("recovery_password",to_email)
    
    # 이메일 본문 추후 HTML로 만들든 뭐든 해야겠다.
    msg.attach(MIMEText(f"비밀번호 복구 코드: {recovery_code}\n5분안에 입력해주세요", 'plain'))
    
    msg.as_string()
    
    await send_email(msg)
    
    
async def verify_code(email_type: str ,to_email: str, code: str):
    
    stored_code = await reDB.get(f"{email_type}:{to_email}")
    if code != stored_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message":"인증번호가 틀립니다"})
    
    
    await reDB.setex(f"{email_type}:{to_email}", 300, "Verify")
    
    
    
async def random_code_generator(email_type: str, email: str):
    
    code = '{:06d}'.format(secrets.randbelow(900000) + 100000)
    #code = '007622'
    
    await reDB.delete(f"{email_type}:{email}")
    await reDB.setex(f"{email_type}:{email}", 300, code)
    
    return code
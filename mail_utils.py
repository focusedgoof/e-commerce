from typing import List
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from dotenv import dotenv_values
from models import *
import jwt

config_credentials = dotenv_values(".env")

conf = ConnectionConfig(
    MAIL_USERNAME=config_credentials["EMAIL"],
    MAIL_PASSWORD=config_credentials["PASS"],
    MAIL_FROM=config_credentials["EMAIL"],
    MAIL_FROM_NAME="ShopShip", 
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,   
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_email(email:List, instance: User):  
  token_data ={
    "id": instance.id,
    "username": instance.username
  }

  token = jwt.encode(token_data, config_credentials["SECRET"], algorithm="HS256")
  template = f"""
    <html>
      <head>
          <meta charset="UTF-8">
          <title>Email Verification</title>
      </head>
      <body>
          <div class="container">
              <h2>Email Verification</h2>
              <p>Hello <strong>{instance.username}</strong>,</p>
              <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
              <a class="button" href="http://localhost:8000/verification?token={token}">Verify Email</a>
              <p>If you did not create an account, you can ignore this email.</p>
              <p>Best Regards,<br>ShopShip</p>
          </div>
      </body>
      </html>
    """
  
  message = MessageSchema(
    subject ="ShopShip Account verification Email",
    recipients= email,
    body = template,
    subtype="html"
  )

  fm = FastMail(conf)
  await fm.send_message(message=message)

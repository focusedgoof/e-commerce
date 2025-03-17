from passlib.context import CryptContext
import jwt
from dotenv import dotenv_values
from models import User
from fastapi.exceptions import HTTPException
from fastapi import status


config_credentials= dotenv_values(".env")

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

#hashing password
def get_hashed_password(password):
  return pwd_context.hash(password)

#verify password
def verify(plain_password: str, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#verification of token
async def very_token(token:str):
  try: 
      payload = jwt.decode(token, config_credentials["SECRET"], algorithms = ['HS256'])
      user = await User.get(id = payload.get("id"))
  except:
     raise HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid token",
        headers ={"WWW.Autenticate": "Bearer"}
     )
  return user


async def authenticate_user(username, password):
   user =await User.get(username= username)

   if user and verify(password, user.password):
      return user
   return False

async def token_generator(username:str, password:str):
  user = await authenticate_user(username, password)

  if not user:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "Invalid token",
      headers ={"WWW.Autenticate": "Bearer"}
    )
  token_data ={
    "id":user.id,
    "username": user.username
  }
  token = jwt.encode(token_data, config_credentials["SECRET"])
  return token

   

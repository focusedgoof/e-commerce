from fastapi import FastAPI, Request
from tortoise.contrib.fastapi import register_tortoise
from mail_utils import send_email
from models import *
from authentication import *
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

#signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient




app= FastAPI()


@post_save(User)
async def create_business(
  sender: "Type[User]",
  instance: User,
  created: bool,
  using_db: "Optional[BaseDBAsyncClient]",
  update_fields: List[str]
) -> None:
  
  if created:
    business_obj  = await Business.create(
      business_name =instance.username, owner =instance
    )
    await business_pydentic.from_tortoise_orm(business_obj)
    #send email to the user
    await send_email([instance.email], instance)

#registration
@app.post("/registration")
async def user_registration(user: user_pydenticIn):
  user_info =user.dict(exclude_unset= True)
  existing_user = await User.filter(email=user_info["email"]).first()
  if existing_user:
    raise HTTPException(status_code=400, detail="Email already exists")

  user_info["password"] = get_hashed_password(user_info["password"])
  user_obj =await User.create(**user_info)
  new_user = await user_pydentic.from_tortoise_orm(user_obj)
  return {
      "status": "ok",
      "data": f"Hello {new_user.username}, thanks for choosing our services. Please check your mailbox to confirm your email for registration."
  }


templates =Jinja2Templates(directory="templates")
#verification
@app.get("/verification", response_class=HTMLResponse )
async def email_verification(request: Request, token: str):
  user= await very_token(token)

  if user and not user.is_verified:
    user.is_verified=True
    await user.save()
    return templates.TemplateResponse("verification.html", {"request":request, "username":user.username})
  
  raise HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid token or expired token",
        headers ={"WWW.Autenticate": "Bearer"}
     )

@app.get("/")
def index():
  return {"Message":"Hello World"}


register_tortoise(
  app,
  db_url="sqlite://database.sqlite3",
  modules= {"models": ["models"]},
  generate_schemas=True,
  add_exception_handlers=True
)


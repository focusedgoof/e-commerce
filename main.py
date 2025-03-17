from fastapi import Depends, FastAPI, Request
from tortoise.contrib.fastapi import register_tortoise
from mail_utils import send_email
from models import *
from authentication import *
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image
from datetime import datetime



app= FastAPI()

oath2_scheme =OAuth2PasswordBearer(tokenUrl='token')

#static file setup
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/token")
async def generate_token(request_form:OAuth2PasswordRequestForm = Depends()):
  token = await token_generator(request_form.username, request_form.password)
  return {"access_token":token, "token_type": "bearer"}

async def get_current_user(token:str =Depends(oath2_scheme)):
  try:
    payload = jwt.decode(token,config_credentials["SECRET"],algorithms = ['HS256'])
    user= await User.get(id= payload.get("id"))
  
  except:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "Invalid token",
      headers ={"WWW.Autenticate": "Bearer"}
    )
  return await user


@app.post("/user/me")
async def user_login(user: user_pydenticIn= Depends(get_current_user)):
  business =await Business.get(owner =user)
  logo = business.logo
  logo_path = "localhost:8000/static/images/" + logo


  return{
      "status": "ok",
      "data": 
      {
        "username": user.username,
        "email":user.email,
        "verified":user.is_verified,
        "joining_date":user.join_date.strftime("%d %d %Y"),
        "logo": logo_path
      }
  }
  
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

@app.post("/uploadfile/profile")
async def create_upload_file(file:UploadFile = File(...),
                             user:user_pydentic = Depends(get_current_user)):
  FILEPATH = "./static/images/"
  filename = file.filename
  extension = filename.split(".")[1]

  if extension not in["png","jpeg","jpg"]:
    return {
      "status": "error",
      "detail": "File extension not valid"
    }
  token_name =secrets.token_hex(10) + "." + extension
  generate_name = FILEPATH + token_name
  file_content =await file.read()

  with open(generate_name, "wb") as file:
    file.write(file_content)

  img =Image.open(generate_name)
  img =img.resize(size=(200,200))
  img.save(generate_name)

  file.close()

  business =await Business.get(owner =user)
  owner= await business.owner

  if owner == user:
    business.logo = token_name
    await business.save()

  else:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "not authenticated to perform the action",
      headers ={"WWW.Autenticate": "Bearer"}
    )
  
  file_url = "localhost:8000" + generate_name[1:]
  return {"status": "ok", "filename":file_url}

@app.post("/uploadfile/product/{id}")
async def create_upload_file(id:int, file: UploadFile =File(...),
                             user: user_pydenticIn =Depends(get_current_user)):
  FILEPATH = "./static/images/"
  filename = file.filename
  extension = filename.split(".")[1]

  if extension not in["png","jpeg","jpg"]:
    return {
      "status": "error",
      "detail": "File extension not valid"
    }
  token_name =secrets.token_hex(10) + "." + extension
  generate_name = FILEPATH + token_name
  file_content =await file.read()

  with open(generate_name, "wb") as file:
    file.write(file_content)

  img =Image.open(generate_name)
  img =img.resize(size=(200,200))
  img.save(generate_name)

  file.close()

  product = await Product.get(id=id)
  business = await product.business
  owner = await business.owner

  if owner == user:
    product.product_image= token_name
    await product.save()

  else:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "not authenticated to perform the action",
      headers ={"WWW.Autenticate": "Bearer"}
    )
  
  file_url = "localhost:8000" + generate_name[1:]
  return {"status": "ok", "filename":file_url}

#crud operations
@app.post("/products")
async def add_new_product(product: product_pydenticIn, user: user_pydentic = Depends(get_current_user)):
    product_data = product.dict(exclude_unset=True)
    
    business = await Business.get(owner=user)
    
    if product_data["orignal_price"] > 0:
        product_data["percentage_discount"] = ((product_data["orignal_price"] - product_data["new_price"]) / product_data["orignal_price"]) * 100
        product_obj = await Product.create(**product_data, business=business)
        product_obj = await product_pydentic.from_tortoise_orm(product_obj)
        return {"status": "ok", "data": product_obj}
    else:
        return {"status": "error"}
  

@app.get("/product")
async def get_product():
  response = await product_pydentic.from_queryset(Product.all())
  return {"status": "ok", "data":response}

@app.get("/product/{id}")
async def get_product(id: int):
  product = await Product.get(id =id)
  business = await product.business
  owner =await business.owner
  response = await product_pydentic.from_tortoise_orm(await Product.get(id=id))
  response_dict = response.dict()
  response_dict["orignal_price"] = float(response_dict["orignal_price"])
  response_dict["new_price"] = float(response_dict["new_price"])
  response_dict["percentage_discount"] = float(response_dict["percentage_discount"])

  return {"status": "ok", "data":{
    "product_details":response,
    "business_details": {
      "name": business.business_name,
      "city":business.city,
      "region": business.region,
      "description": business.business_description,
      "logo": business.logo,
      "owner_id": owner.id,
      "email":owner.email,
      "joining_date": owner.join_date.strftime("%d %d %Y")
    },
  }}

@app.delete("/product/{id}")
async def delete_product(id: int, user: user_pydentic = Depends(get_current_user)):
    product = await Product.get(id=id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    
    business = await product.business
    owner = await business.owner
    
    if user == owner:
        await product.delete()
        return {"status": "ok", "message": "Product deleted successfully"}
    else:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated to perform this action",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.put("/product/{id}")
async def update_product(id: int, update_info: product_pydenticIn, user: user_pydentic= Depends(get_current_user)):
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner

    if user != owner:
        raise HTTPException(
          status_code=401,
          detail="Not authenticated to perform this action",
          headers={"WWW-Authenticate": "Bearer"}
        )

    update_data = update_info.dict(exclude_unset=True)

    if "orignal_price" in update_data and update_data["orignal_price"] > 0:
        update_data["percentage_discount"] = (
            (update_data["orignal_price"] - update_data["new_price"]) / update_data["orignal_price"]
        ) * 100

    update_data["date_added"] = datetime.utcnow().date() 

    await product.update_from_dict(update_data)
    await product.save() 

    updated_product = await product_pydentic.from_tortoise_orm(product)
    return {"status": "ok", "data": updated_product}

@app.put("/business/{id}")
async def update_business(id: int, update_business: business_pydenticIn, user: user_pydentic = Depends(get_current_user)):
    business = await Business.get(id=id)    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business_owner = await business.owner
    if user != business_owner:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized to update this business")

    update_data = update_business.dict(exclude_unset=True)
    await business.update_from_dict(update_data)
    await business.save()

    response = await business_pydentic.from_tortoise_orm(business)
    return {"status": "ok", "data": response}

  
   
@app.post("/order")
async def create_order(order_data: List[order_item_pydanticIn], user: user_pydentic = Depends(get_current_user)):
    if not order_data:
        raise HTTPException(status_code=400, detail="Order cannot be empty")

    first_product = await Product.get(id=order_data[0].product_id)
    if not first_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    business = await first_product.business

    order = await Order.create(user=user, business=business, total_price=0.00)
    
    total_price = 0
    for item in order_data:
        product = await Product.get(id=item.product_id)

        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")

        if product.business != business:
            raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} does not belong to the same business")

        order_item = await OrderItem.create(
            order=order,
            product=product,
            business=business,
            quantity=item.quantity,
            price=product.new_price
        )
        
        total_price += product.new_price * item.quantity

    order.total_price = total_price
    await order.save()

    return {"status": "ok", "message": "Order placed successfully", "order_id": order.id}


@app.get("/orders")
async def get_orders(user: user_pydentic = Depends(get_current_user)):
    orders = await order_pydantic.from_queryset(Order.filter(user=user))
    return {"status": "ok", "data": orders}


@app.get("/business/orders")
async def get_business_orders(user: user_pydentic = Depends(get_current_user)):
    businesses = await Business.filter(owner=user).values_list("id", flat=True)
    if not businesses:
        raise HTTPException(status_code=403, detail="You do not own any businesses")
    
    orders = await order_pydantic.from_queryset(Order.filter(business_id__in=businesses))
    return {"status": "ok", "data": orders}


@app.get("/order/{id}")
async def get_order(id: int, user: user_pydentic = Depends(get_current_user)):
    order = await Order.get_or_none(id=id).prefetch_related("items", "user", "business")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if user != order.user and user != order.business.owner:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    order_data = await order_pydantic.from_tortoise_orm(order)
    items = await order_item_pydantic.from_queryset(OrderItem.filter(order=order))

    return {"status": "ok", "order": order_data, "items": items}


@app.put("/order/{id}/status")
async def update_order_status(id: int, status: str, user: user_pydentic = Depends(get_current_user)):
    order = await Order.get_or_none(id=id).prefetch_related("business")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if user != order.business.owner:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")

    order.status = status
    await




register_tortoise(
  app,
  db_url="sqlite://database.sqlite3",
  modules= {"models": ["models"]},
  generate_schemas=True,
  add_exception_handlers=True
)


from tortoise import Model, fields
from pydantic import BaseModel
from datetime import datetime, timezone
from tortoise.contrib.pydantic import pydantic_model_creator

class User(Model):
  id= fields.IntField(pk=True, index= True)
  username=fields.CharField(max_length=20, null=False, unique= True)
  email = fields.CharField(max_length=200, null =False, unique=True)
  password= fields.CharField(max_length= 70, null =False)
  is_verified = fields.BooleanField(default=False)
  join_date = fields.DatetimeField(default=lambda: datetime.now(timezone.utc))

class Business(Model):
  id= fields.IntField(pk = True, index= True)
  business_name =fields.CharField(max_length= 20, null = False, unique =True)
  city = fields.CharField( max_length =100, null =False, default= "Unspecified")
  region = fields.CharField(max_length =100, null =False, default= "Unspecified")
  business_description =fields.TextField(null=True)
  logo =fields.CharField(max_length =200, null=False, default="default.jpg")
  owner =fields.ForeignKeyField("models.User", related_name="business")

class Product(Model):
  id= fields.IntField(pk = True, index= True)
  name= fields.CharField(max_length =100, null =False, index =True)
  category= fields.CharField(max_length=30, index=True)
  orignal_price =fields.DecimalField(max_digits =12, decimal_places =2)
  new_price = fields.DecimalField(max_digits = 12, decimal_places=2)
  percentage_discount= fields.IntField(null=True)
  offer_expiration_date =fields.DateField(default=lambda: datetime.now(timezone.utc))
  product_image=fields.CharField(max_length =200, null=False, default="productDefault.jpg")
  date_added = fields.DateField(default=lambda: datetime.now(timezone.utc).date())
  business= fields.ForeignKeyField("models.Business", related_name="products")

class Order(Model):
    id = fields.IntField(pk=True, index=True)
    user = fields.ForeignKeyField("models.User", related_name="orders", on_delete=fields.CASCADE) 
    business = fields.ForeignKeyField("models.Business", related_name="orders", on_delete=fields.CASCADE) 
    total_price = fields.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = fields.CharField(max_length=20, default="Pending")
    created_at = fields.DatetimeField(auto_now_add=True)

class OrderItem(Model):
    id = fields.IntField(pk=True, index=True)
    order = fields.ForeignKeyField("models.Order", related_name="items", on_delete=fields.CASCADE)r
    product = fields.ForeignKeyField("models.Product", related_name="order_items", on_delete=fields.CASCADE)  
    business = fields.ForeignKeyField("models.Business", related_name="order_items", on_delete=fields.CASCADE) 
    quantity = fields.IntField(default=1)
    price = fields.DecimalField(max_digits=12, decimal_places=2)

#Creating a Pydantic model from a Tortoise model
user_pydentic = pydantic_model_creator(User, name="User", exclude = ("is_verified"))
user_pydenticIn = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=("is_verified", "join_date"))
user_pydenticOut = pydantic_model_creator(User, name="UserOut", exclude = ("ipassword"))

business_pydentic = pydantic_model_creator(Business, name="Business")
business_pydenticIn= pydantic_model_creator(Business, name="BusinessIn", exclude_readonly=True)

product_pydentic = pydantic_model_creator(Product, name="Product", exclude = ("is_verified"))
product_pydenticIn= pydantic_model_creator(Product, name="ProductIn", exclude_readonly=True, exclude=("id", "percentage_discount","product_image", "date_added"))

order_pydantic = pydantic_model_creator(Order, name="Order")
order_pydanticIn = pydantic_model_creator(Order, name="OrderIn", exclude_readonly=True, exclude=("id", "total_price", "created_at"))

order_item_pydantic = pydantic_model_creator(OrderItem, name="OrderItem")
order_item_pydanticIn = pydantic_model_creator(OrderItem, name="OrderItemIn", exclude_readonly=True, exclude=("id"))



from fastapi import FastAPI, Request, Depends, Response, APIRouter
from typing import Optional
from fastapi_users import models
from fastapi_users.db import MongoDBUserDatabase
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from pydantic import EmailStr
import motor.motor_asyncio


SECRET = 'SECRET'

auth_backends = []

jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds = 12000
)

auth_backends.append(jwt_authentication)

router = APIRouter()

class User(models.BaseUser):
    username: str
    password: str
    email: Optional[str]
    name: Optional[str]
    agency: Optional[str]
    role: Optional[str]
    expert_for: Optional[str]

class UserCreate(models.BaseUserCreate):
    username: str
    password: str
    email: str
    name: str
    agency: str
    role: str
    expert_for: str

class UserUpdate(User, models.BaseUserUpdate):
    pass

class UserDB(User, models.BaseUserDB):
    pass

DATABASE_URL = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, uuidRepresentation="standard"
)

db = client['fastapi_users']
collection = db['users']

app = FastAPI(
    title="Cervical Cancer Application",
    description="Rest API Backend for CCA"
)

user_db = MongoDBUserDatabase(UserDB, collection)

fastapi_users = FastAPIUsers(
    user_db,
    auth_backends,
    User,
    UserCreate,
    UserUpdate,
    UserDB
)

app = FastAPI()

##### ROUTERS #####

# Auth Router
app.include_router(
    fastapi_users.get_auth_router(jwt_authentication),
    prefix="/auth/jwt",
    tags = ['auth']
)

# Register Router
def on_after_register(user:UserDB, request: Request):
    print(f"User {user.id} has registered.")

app.include_router(
    fastapi_users.get_register_router(on_after_register),
    prefix='/auth',
    tags=['auth']
)

# User Oprations
def on_after_user_process(request: Request):
    print("Success.")

app.include_router(fastapi_users.get_users_router(jwt_authentication), prefix="/users", tags=["users"])


# Reset Password
def on_after_forgot_password(user:UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")

app.include_router(
    fastapi_users.get_reset_password_router("SECRET", after_forgot_password=on_after_forgot_password),
    prefix="/auth",
    tags=['auth']
)


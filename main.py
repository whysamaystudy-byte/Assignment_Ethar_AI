from fastapi import FastAPI
import models
from database import engine
from routers import auth, users

models.Base.metadata.create_all(bind=engine)
#all the tables written in models.py with base as the parent class
#they all will be created if these do not exist in the database


app = FastAPI()

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)
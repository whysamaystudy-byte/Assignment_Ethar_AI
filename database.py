from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./project_task.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# we are connecting sql db to engine and checksamethread is used to safely allow multiple
#users to acces the same db at the same time

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#whenever session local is called, we will get a session object
#this session object is used to perform crud operations on the db
#autocommit false means commit when db.commit 

Base = declarative_base()
#parent class for all the models


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#used to create new sessions
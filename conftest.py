import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base 
from main import app
from database import get_db 

# using a pecific SQLite database for testing 
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# db creation stuff
@pytest.fixture(scope="function") 
def db_setup():
    """creates table before each test and drops them afterwards for clean isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine) 

# db dependency override
def override_get_db():
    """provides a fresh session for each dependency call, WITHOUT wiping the tables."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the override to the main application instance
app.dependency_overrides[get_db] = override_get_db

# test client creation
@pytest.fixture(scope="function") 
def client(db_setup): 
    """A fixture to provide a test client for making requests."""
    with TestClient(app) as c:
        yield c

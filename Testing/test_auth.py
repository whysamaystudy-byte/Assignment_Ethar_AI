
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

#data for testing

Test_user_1 = {
    "email" : "abcd@gmail.com",
    "phone_number" : '101010',
    "password" : "password",
    "role" : "user"
}

Test_user_2 = {
    "email": "efgh@example.com",
    "password": "anotherpassword",
    "phone_number": "010101",
    "role": "user"
}

#registaration
def test_register_success(client: TestClient):
    """Tests successful user registration (HTTP 201)."""
    response = client.post('/auth/register', json=Test_user_1)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == Test_user_1["email"]
    assert "id" in data

    assert "hashed_password" not in data
    assert "password" not in data

def test_register_duplicate_email(client: TestClient):
    """Tests failure when trying to register the same email twice (HTTP 400)."""
    # 1. Register first user (ensure success)
    res = client.post("/auth/register", json=Test_user_2)
    assert res.status_code == 201 
    
    # 2. Try to register with the same email
    response = client.post("/auth/register", json=Test_user_2)
    
    # 3. Check for specific error message
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_register_invalid_data(client: TestClient):
    """Tests failure when required data is missing (HTTP 422)."""
    invalid_data = Test_user_1.copy()
    del invalid_data["email"] # Remove required field
    
    response = client.post("/auth/register", json=invalid_data)
    
    # Check for Pydantic validation error
    assert response.status_code == 422


#token
def authenticate_test_user(client: TestClient, user_data: dict = Test_user_1):
    """Utility function to register and log in a user, returning the token."""
    # Ensure user exists first
    res = client.post("/auth/register", json=user_data)
    assert res.status_code == 201
    
    # Credentials must be sent as form data for the /token endpoint
    form_data = {
        "username": user_data["email"],
        "password": user_data["password"],
    }
    
    token_response = client.post("/auth/token", data=form_data)
    
    return token_response

def test_login_success(client: TestClient):
    """Tests successful login and token issue (HTTP 200)."""
    token_response = authenticate_test_user(client)
    
    assert token_response.status_code == 200
    data = token_response.json()
    
    # Check token schema compliance
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Tests failure with correct email but wrong password (HTTP 401)."""
    # ensure user exists
    client.post("/auth/register", json=Test_user_1)
    
    form_data = {
        "username": Test_user_1["email"],
        "password": "wrong-password", # incorrect password
    }
    
    response = client.post("/auth/token", data=form_data)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "incorrect username or password"
    # Check for WWW-Authenticate header compliance
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_nonexistent_user(client: TestClient):
    """Tests failure when user email is not found (HTTP 401)."""
    form_data = {
        "username": "nonexistent@user.com",
        "password": "anypassword",
    }
    
    response = client.post("/auth/token", data=form_data)
    
    # Must return the same 401 error as wrong password
    assert response.status_code == 401
    assert response.json()["detail"] == "incorrect username or password"
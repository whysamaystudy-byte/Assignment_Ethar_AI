import pytest
from fastapi.testclient import TestClient
from test_auth import Test_user_1
from security import verify_password
import models


def get_token_for_user(client: TestClient, user_data: dict):
    """function help a user to login and get token"""
    client.post("/auth/register", json=user_data)
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/auth/token", data=login_data)
    return response.json()["access_token"]


def test_read_own_profile(client: TestClient):
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/users/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == Test_user_1["email"]
    assert "id" in response.json()

def test_update_profile(client: TestClient):
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {"phone_number": "999-9999"}
    response = client.put("/users/me", json=update_data, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["phone_number"] == "999-9999"

def test_change_password(client: TestClient):
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    password_payload = {
        "old_password": Test_user_1["password"],
        "new_password": "newly_secure_password"
    }
    
    #change it
    response = client.put("/users/me/password", json=password_payload, headers=headers)
    assert response.status_code == 204
    
    # login w old password fail
    login_old = {"username": Test_user_1["email"], "password": Test_user_1["password"]}
    assert client.post("/auth/token", data=login_old).status_code == 401
    
    # login w new password sucess
    login_new = {"username": Test_user_1["email"], "password": "newly_secure_password"}
    assert client.post("/auth/token", data=login_new).status_code == 200

# admin access
def test_list_all_users_forbidden_for_regular_user(client: TestClient):
    # register a user
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    # attempt to access admin route
    response = client.get("/users/", headers=headers)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to view all users"

def test_list_all_users_allowed_for_admin(client: TestClient):
    # Register an admin user
    admin_data = Test_user_1.copy()
    admin_data["email"] = "admin@example.com"
    admin_data["role"] = "admin"
    
    token = get_token_for_user(client, admin_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/users/", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

# delete-
def test_delete_own_account(client: TestClient):
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    # delete
    response = client.delete("/users/me", headers=headers)
    assert response.status_code == 204
    
    # account delete verify
    login_data = {"username": Test_user_1["email"], "password": Test_user_1["password"]}
    assert client.post("/auth/token", data=login_data).status_code == 401
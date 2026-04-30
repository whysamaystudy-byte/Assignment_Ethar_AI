import pytest
from fastapi.testclient import TestClient
from test_auth import Test_user_1

# Re-use the token helper
def get_token_for_user(client: TestClient, user_data: dict):
    client.post("/auth/register", json=user_data)
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/auth/token", data=login_data)
    return response.json()["access_token"]

Test_admin = {
    "email": "admin_dash@example.com",
    "phone_number": "555555",
    "password": "password",
    "role": "admin"
}

def test_dashboard_access_member(client: TestClient):
    """Testing regular user can access dashboard"""
    token = get_token_for_user(client, Test_user_1)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/dashboard/", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "total_tasks" in data
    assert "pending_tasks" in data
    assert "in_progress_tasks" in data
    assert "completed_tasks" in data
    assert "overdue_tasks_count" in data
    
    # A fresh user should have 0 tasks
    assert data["total_tasks"] == 0

def test_dashboard_access_admin(client: TestClient):
    """Test that an admin can access the dashboard."""
    token = get_token_for_user(client, Test_admin)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/dashboard/", headers=headers)
    assert response.status_code == 200

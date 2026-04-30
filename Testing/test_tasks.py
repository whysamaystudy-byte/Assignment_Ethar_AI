import pytest
from fastapi.testclient import TestClient
from test_projects import Test_admin, get_auth_headers
from test_auth import Test_user_1

@pytest.fixture
def task_setup(client: TestClient):
    """Fixture to set up users, project, and initial task for tests."""
    admin_headers = get_auth_headers(client, Test_admin)
    user_headers = get_auth_headers(client, Test_user_1)
    
    # Admin creates a project
    proj_res = client.post("/projects/", json={"title": "Task Test Project"}, headers=admin_headers)
    project_id = proj_res.json()["id"]

    # Get the member's user id
    user_me = client.get("/users/me", headers=user_headers)
    user_id = user_me.json()["id"]

    # Admin creates a task and assigns it to member
    task_payload = {
        "title": "First Test Task",
        "priority": 1,
        "project_id": project_id,
        "assignee_id": user_id
    }
    task_res = client.post("/tasks/", json=task_payload, headers=admin_headers)
    task_id = task_res.json()["id"]
    
    return {
        "admin_headers": admin_headers,
        "user_headers": user_headers,
        "task_id": task_id
    }


def test_admin_create_and_assign_task(client: TestClient, task_setup):
    # Verifies the task created in the setup fixture was successful
    admin_headers = task_setup["admin_headers"]
    task_id = task_setup["task_id"]
    
    response = client.get(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "First Test Task"

def test_member_views_their_tasks(client: TestClient, task_setup):
    user_headers = task_setup["user_headers"]
    
    member_tasks_res = client.get("/tasks/", headers=user_headers)
    assert member_tasks_res.status_code == 200
    assert len(member_tasks_res.json()) >= 1

def test_member_updates_task_status(client: TestClient, task_setup):
    user_headers = task_setup["user_headers"]
    task_id = task_setup["task_id"]
    
    update_res = client.put(f"/tasks/{task_id}", json={"status": "In Progress"}, headers=user_headers)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "In Progress"

def test_member_cannot_update_priority(client: TestClient, task_setup):
    user_headers = task_setup["user_headers"]
    task_id = task_setup["task_id"]
    
    priority_res = client.put(f"/tasks/{task_id}", json={"priority": 5}, headers=user_headers)
    assert priority_res.status_code == 403

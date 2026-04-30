from fastapi import APIRouter, status, HTTPException, Path
from typing import List, Optional

import schemas
import models
from .auth import db_dependency, current_user_dependency

router = APIRouter(
    prefix='/tasks',
    tags=['tasks']
)

def require_admin(user: models.User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action (Admin only)"
        )
    return user

@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    user: current_user_dependency,
    task_request: schemas.TaskCreate,
    db: db_dependency
):
    require_admin(user)
    
    # check if project exist
    project = db.query(models.Project).filter(models.Project.id == task_request.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # check if user exist if provided
    if task_request.assignee_id:
        assignee = db.query(models.User).filter(models.User.id == task_request.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")

    db_task = models.Task(
        title=task_request.title,
        description=task_request.description,
        priority=task_request.priority,
        status=task_request.status,
        due_date=task_request.due_date,
        project_id=task_request.project_id,
        assignee_id=task_request.assignee_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task

@router.get('/', response_model=List[schemas.TaskOut])
async def list_tasks(
    user: current_user_dependency,
    db: db_dependency
):
    if user.role == "admin":
        tasks = db.query(models.Task).all()
    else:
        tasks = db.query(models.Task).filter(models.Task.assignee_id == user.id).all()
    return tasks

@router.get("/{task_id}", response_model=schemas.TaskOut)
async def get_task(
    task_id: int,
    user: current_user_dependency,
    db: db_dependency
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    if user.role != "admin" and task.assignee_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this task")
        
    return task


@router.put("/{task_id}", response_model=schemas.TaskOut)
async def update_task(
    task_id: int,
    task_request: schemas.TaskUpdate,
    user: current_user_dependency,
    db: db_dependency
):
    task_to_update = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # If member, only allow updating status of assigned tasks
    if user.role != "admin":
        if task_to_update.assignee_id != user.id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")
        # Check if they try to update something else than status
        # Using dict instead of model_dump for older pydantic versions compatibility
        update_data = task_request.model_dump(exclude_unset=True)
        if any(k != "status" for k in update_data.keys()):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Members can only update task status")

    if task_request.title is not None:
        task_to_update.title = task_request.title
    if task_request.description is not None:
        task_to_update.description = task_request.description
    if task_request.priority is not None:
        task_to_update.priority = task_request.priority
    if task_request.status is not None:
        if task_request.status not in ["Pending", "In Progress", "Completed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        task_to_update.status = task_request.status
    if task_request.due_date is not None:
        task_to_update.due_date = task_request.due_date
    if task_request.assignee_id is not None:
        task_to_update.assignee_id = task_request.assignee_id

    db.add(task_to_update)
    db.commit()
    db.refresh(task_to_update)
    
    return task_to_update

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    user: current_user_dependency,
    db: db_dependency
):
    require_admin(user)
    
    task_to_delete = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task_to_delete)
    db.commit()
    return

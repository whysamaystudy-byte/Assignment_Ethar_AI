from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

import models, schemas
from .auth import db_dependency, current_user_dependency

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

def require_admin(user: models.User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action (Admin only)"
        )
    return user

@router.post("/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    user: current_user_dependency,
    project_request: schemas.ProjectCreate,
    db: db_dependency
):
    require_admin(user)
    
    new_project = models.Project(
        title=project_request.title,
        description=project_request.description,
        owner_id=user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=List[schemas.ProjectOut])
async def list_projects(
    user: current_user_dependency,
    db: db_dependency
):
    projects = db.query(models.Project).all()
    return projects

@router.get("/{project_id}", response_model=schemas.ProjectOut)
async def get_project(
    project_id: int,
    user: current_user_dependency,
    db: db_dependency
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    user: current_user_dependency,
    db: db_dependency
):
    require_admin(user)
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
    # Delete associated tasks first
    db.query(models.Task).filter(models.Task.project_id == project_id).delete()
    
    db.delete(project)
    db.commit()
    return

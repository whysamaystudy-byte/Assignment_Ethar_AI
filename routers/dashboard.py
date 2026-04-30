from fastapi import APIRouter, Depends
from sqlalchemy import func
from datetime import datetime

import schemas
import models
from .auth import db_dependency, current_user_dependency

router = APIRouter(
    prefix='/dashboard',
    tags=['dashboard']
)

@router.get("/", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    user: current_user_dependency,
    db: db_dependency
):
    # Total task
    base_query = db.query(models.Task)
    if user.role != "admin":
        base_query = base_query.filter(models.Task.assignee_id == user.id)

    total_tasks = base_query.count()
    
    pending_tasks = base_query.filter(models.Task.status == "Pending").count()
    in_progress_tasks = base_query.filter(models.Task.status == "In Progress").count()
    completed_tasks = base_query.filter(models.Task.status == "Completed").count()
    
    # Overdue tasks
    current_time = datetime.utcnow()
    overdue_tasks = base_query.filter(
        models.Task.due_date < current_time,
        models.Task.status != "Completed"
    ).count()

    return schemas.DashboardStats(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks_count=overdue_tasks
    )

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

#schemas is used to validate the classes

#user class schema
class UserBase(BaseModel):
    phone_number: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str

#what we are returning
class UserOut(UserBase):
    id: int
    is_active: bool = True 

    class Config:
        from_attributes = True
    #when non dictionary object is passed, look for attributes on the object and not as key in dict ex: user.EmailStr

#project schema

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True



#task schema
class TaskBase(BaseModel):
    title: str
    description: str
    priority: int
    status: str = "pending"
    due_date: datetime

class TaskCreate(TaskBase):
    project_id: int
    assignee_id: int

class TaskUpdate(BaseModel):
    title: str
    description: str
    priority: int
    status: str
    due_date: datetime
    assignee_id: int


class TaskOut(TaskBase):
    id: int
    project_id: int
    assignee_id: Optional[int]

    class Config:
        from_attributes = True


#dashboard schema
class DashboardStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks_count: int
from _pytest.main import Session
from typing import Annotated
from routers.auth import get_current_user, db_dependency
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from security import hash_password
import schemas
from typing import List
from security import verify_password
import models

#db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter(
    prefix='/users',
    tags=['user management']
)

@router.get("/me", response_model=schemas.UserOut)
async def get_my_profile(user: current_user_dependency):
    """return profile of logged in user"""
    return user

@router.put("/me", response_model=schemas.UserOut)
async def update_profile(
    user_update: schemas.UserUpdate,
    db: db_dependency,
    current_user: current_user_dependency
):
    """update user email and number"""
    if user_update.email:
        # Check if the new email is already taken by someone else
        email_check = db.query(models.User).filter(models.User.email == user_update.email).first()
        if email_check and email_check.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = user_update.email
    
    if user_update.phone_number:
        current_user.phone_number = user_update.phone_number
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: schemas.UserPasswordUpdate,
    db: db_dependency,
    current_user: current_user_dependency,
):
    """set new password"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
    
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    db: db_dependency,
    current_user: current_user_dependency
):
    """delete current user details"""
    db.delete(current_user)
    db.commit()
    return None

@router.get("/", response_model=List[schemas.UserOut])
async def list_all_users(
    db: db_dependency,
    current_user: current_user_dependency
):
    """list all users, admin only access"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to view all users"
        )
    return db.query(models.User).all()
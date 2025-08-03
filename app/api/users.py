from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.crud import users
from app.schemas.schemas import User, UserCreate, UserUpdate, UserCategory
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, 
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_admin_user)):
    return users.get_users(db, skip=skip, limit=limit)

@router.post("/", response_model=User)
def create_user(user: UserCreate, 
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    db_user = users.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return users.create_user(db=db, user=user)

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, 
              db: Session = Depends(get_db),
              current_user: User = Depends(get_current_admin_user)):
    db_user = users.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user_update: UserUpdate,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    db_user = users.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    # 检查用户是否存在
    db_user = users.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查用户是否有关联的设备类别权限
    user_categories = users.get_user_categories(db, user_id)
    if user_categories:
        raise HTTPException(
            status_code=400, 
            detail="无法删除该用户，因为该用户还管理着设备类别。请先移除该用户的设备类别权限后再删除。"
        )
    
    # 删除用户
    success = users.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete user")
    
    return {"message": "User deleted successfully"}

@router.get("/{user_id}/categories", response_model=List[UserCategory])
def get_user_categories(user_id: int,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_admin_user)):
    return users.get_user_categories(db, user_id=user_id)

@router.post("/{user_id}/categories/{category_id}")
def assign_category_to_user(user_id: int, category_id: int,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_admin_user)):
    user_category = users.assign_category_to_user(db, user_id=user_id, category_id=category_id)
    return {"message": "Category assigned successfully", "user_category": user_category}

@router.put("/{user_id}/categories")
def update_user_categories(user_id: int, category_data: dict,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_admin_user)):
    category_ids = category_data.get("category_ids", [])
    success = users.update_user_categories(db, user_id=user_id, category_ids=category_ids)
    if success:
        return {"message": "User categories updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update user categories")
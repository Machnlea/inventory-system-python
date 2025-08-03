from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import User, UserCategory
from app.schemas.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from typing import Optional, List

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    # 检查用户是否存在
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    # 检查用户是否有关联的设备类别权限
    user_categories = db.query(UserCategory).filter(UserCategory.user_id == user_id).all()
    if user_categories:
        # 如果有关联的权限，不能删除用户
        return False
    
    # 如果没有关联权限，可以删除用户
    db.delete(db_user)
    db.commit()
    return True

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_user_categories(db: Session, user_id: int):
    return db.query(UserCategory).filter(UserCategory.user_id == user_id).all()

def assign_category_to_user(db: Session, user_id: int, category_id: int):
    # 检查是否已存在
    existing = db.query(UserCategory).filter(
        and_(UserCategory.user_id == user_id, UserCategory.category_id == category_id)
    ).first()
    
    if not existing:
        user_category = UserCategory(user_id=user_id, category_id=category_id)
        db.add(user_category)
        db.commit()
        db.refresh(user_category)
        return user_category
    return existing

def remove_category_from_user(db: Session, user_id: int, category_id: int):
    """移除用户的设备类别权限"""
    user_category = db.query(UserCategory).filter(
        and_(UserCategory.user_id == user_id, UserCategory.category_id == category_id)
    ).first()
    
    if user_category:
        db.delete(user_category)
        db.commit()
        return True
    return False

def update_user_categories(db: Session, user_id: int, category_ids: List[int]):
    """更新用户的设备类别权限"""
    # 删除现有权限
    db.query(UserCategory).filter(UserCategory.user_id == user_id).delete()
    
    # 添加新权限
    for category_id in category_ids:
        user_category = UserCategory(user_id=user_id, category_id=category_id)
        db.add(user_category)
    
    db.commit()
    return True
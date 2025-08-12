#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    
    # 检查是否已存在admin用户
    admin_user = db.query(User).filter(User.username == 'admin').first()
    
    if admin_user:
        print("Admin user already exists.")
        print(f"Username: {admin_user.username}")
        print(f"Full Name: {admin_user.full_name}")
        print(f"Email: {admin_user.email}")
        print(f"Role: {admin_user.role}")
        print(f"Is Active: {admin_user.is_active}")
        print(f"Is Admin: {admin_user.is_admin}")
    else:
        # 创建admin用户
        hashed_password = get_password_hash('admin123')
        admin_user = User(
            username='admin',
            hashed_password=hashed_password,
            full_name='系统管理员',
            email='admin@example.com',
            role='admin',
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Full Name: {admin_user.full_name}")
        print(f"Email: {admin_user.email}")
        print(f"Role: {admin_user.role}")
        print(f"Is Active: {admin_user.is_active}")
        print(f"Is Admin: {admin_user.is_admin}")
    
    db.close()

if __name__ == "__main__":
    create_admin_user()
#!/usr/bin/env python3
"""
检查默认用户是否存在
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import SQLALCHEMY_DATABASE_URL
from app.models.models import User
from app.core.security import get_password_hash

# 创建数据库连接
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 检查用户
    users = db.query(User).all()
    print(f"用户总数: {len(users)}")
    
    for user in users:
        print(f"用户: {user.username}, 管理员: {user.is_admin}")
    
    # 如果没有用户，创建默认用户
    if len(users) == 0:
        print("创建默认用户...")
        default_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(default_user)
        db.commit()
        print("默认用户创建成功")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
#!/usr/bin/env python3
"""
用户设备权限分配脚本
为用户分配特定设备类别的管理权限
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.models import User, EquipmentCategory, UserCategory
from app.crud import users, categories

def assign_equipment_management():
    """分配设备管理权限"""
    db = SessionLocal()
    
    try:
        print("=== 用户设备权限分配 ===\n")
        
        # 1. 检查并创建用户
        target_users = {
            "zmms": {"desc": "温湿度计管理员"},
            "zms": {"desc": "玻璃液体温度计管理员"}
        }
        
        for username, info in target_users.items():
            user = users.get_user_by_username(db, username)
            if not user:
                print(f"创建用户: {username} ({info['desc']})")
                from app.schemas.schemas import UserCreate
                user_data = UserCreate(
                    username=username,
                    password="123456",  # 默认密码
                    is_admin=False
                )
                user = users.create_user(db, user_data)
                print(f"✅ 用户 {username} 创建成功，默认密码: 123456")
            else:
                print(f"✅ 用户 {username} 已存在")
        
        # 2. 获取温度环境类别
        temp_category = db.query(EquipmentCategory).filter(EquipmentCategory.code == "TEM").first()
        if not temp_category:
            print("❌ 错误: 未找到温度环境类别 (TEM)")
            return
        
        print(f"✅ 找到设备类别: {temp_category.name} ({temp_category.code})")
        print(f"   预定义设备: {', '.join(temp_category.predefined_names[:5])}...")
        
        # 3. 为用户分配权限
        assignments = [
            ("zmms", "温湿度计管理权限"),
            ("zms", "玻璃液体温度计管理权限")
        ]
        
        for username, permission_desc in assignments:
            user = users.get_user_by_username(db, username)
            if user:
                # 检查是否已有权限
                existing_permission = db.query(UserCategory).filter(
                    UserCategory.user_id == user.id,
                    UserCategory.category_id == temp_category.id
                ).first()
                
                if not existing_permission:
                    # 分配权限
                    user_category = UserCategory(user_id=user.id, category_id=temp_category.id)
                    db.add(user_category)
                    db.commit()
                    print(f"✅ 为用户 {username} 分配 {permission_desc}")
                else:
                    print(f"✅ 用户 {username} 已有 {permission_desc}")
        
        # 4. 创建具体设备（如果需要）
        print(f"\n=== 创建设备示例 ===")
        
        # 检查是否已有温湿度计
        existing_devices = db.query(EquipmentCategory).join(Equipment).filter(
            EquipmentCategory.id == temp_category.id
        ).count()
        
        print(f"当前温度环境类设备数量: {existing_devices}")
        
        # 5. 显示权限分配结果
        print(f"\n=== 权限分配结果 ===")
        for username, info in target_users.items():
            user = users.get_user_by_username(db, username)
            if user:
                user_categories = users.get_user_categories(db, user.id)
                for uc in user_categories:
                    if uc.category_id == temp_category.id:
                        print(f"👤 {username} 可以管理:")
                        print(f"   - 类别: {uc.category.name}")
                        print(f"   - 代码: {uc.category.code}")
                        print(f"   - 可管理设备: {', '.join(uc.category.predefined_names[:3])}...")
                        break
                else:
                    print(f"❌ {username} 没有分配权限")
        
        print(f"\n=== 测试权限访问 ===")
        print("用户可以通过以下方式验证权限:")
        print("1. 登录系统后访问设备管理页面")
        print("2. 只能看到和管理自己权限范围内的设备")
        print("3. 温湿度计和玻璃液体温度计都属于温度环境类别")
        
        print(f"\n✅ 权限分配完成!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # 确保导入Equipment模型
    from app.models.models import Equipment
    assign_equipment_management()
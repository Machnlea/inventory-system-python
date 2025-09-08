#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门用户CRUD操作
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
from app.models.models import User, Department, Equipment, EquipmentCategory, DepartmentUserLog
from app.schemas.schemas import (
    DepartmentUserCreate, 
    DepartmentUserPasswordChange, 
    DepartmentUserPasswordReset,
    DepartmentEquipmentFilter
)
from app.core.security import get_password_hash, verify_password
from typing import List, Optional

def get_department_user_by_id(db: Session, user_id: int):
    """根据ID获取部门用户"""
    return db.query(User).filter(
        User.id == user_id,
        User.user_type == "department_user"
    ).options(joinedload(User.department)).first()

def get_department_user_by_username(db: Session, username: str):
    """根据用户名获取部门用户"""
    return db.query(User).filter(
        User.username == username,
        User.user_type == "department_user"
    ).options(joinedload(User.department)).first()

def get_department_user_by_department_id(db: Session, department_id: int):
    """根据部门ID获取部门用户"""
    return db.query(User).filter(
        User.department_id == department_id,
        User.user_type == "department_user"
    ).options(joinedload(User.department)).first()

def get_all_department_users(db: Session, skip: int = 0, limit: int = 100):
    """获取所有部门用户"""
    return db.query(User).filter(
        User.user_type == "department_user"
    ).options(joinedload(User.department)).offset(skip).limit(limit).all()

def create_department_user(db: Session, department_id: int, password: str = "sxyq123"):
    """为部门创建用户账户"""
    # 获取部门信息
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ValueError("部门不存在")
    
    # 检查是否已存在同名用户
    existing_user = db.query(User).filter(User.username == department.name).first()
    if existing_user:
        raise ValueError(f"用户名 '{department.name}' 已存在")
    
    # 检查该部门是否已有用户
    existing_dept_user = get_department_user_by_department_id(db, department_id)
    if existing_dept_user:
        raise ValueError(f"部门 '{department.name}' 已存在用户账户")
    
    # 创建用户
    hashed_password = get_password_hash(password)
    db_user = User(
        username=department.name,
        hashed_password=hashed_password,
        is_admin=False,
        user_type="department_user",
        department_id=department_id,
        is_active=True,
        created_at=datetime.now()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_department_user(db: Session, username: str, password: str):
    """验证部门用户登录"""
    user = get_department_user_by_username(db, username)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()
    
    return user

def change_department_user_password(
    db: Session, 
    user_id: int, 
    current_password: str, 
    new_password: str
):
    """部门用户修改密码"""
    user = get_department_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("当前密码错误")
    
    if current_password == new_password:
        raise ValueError("新密码不能与当前密码相同")
    
    # 更新密码
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_at = datetime.now()
    
    db.commit()
    db.refresh(user)
    return user

def admin_reset_department_user_password(db: Session, user_id: int, new_password: str):
    """管理员重置部门用户密码"""
    user = get_department_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    # 重置密码
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_at = datetime.now()
    
    db.commit()
    db.refresh(user)
    return user

def update_department_user_status(db: Session, user_id: int, is_active: bool):
    """更新部门用户状态"""
    user = get_department_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

def delete_department_user(db: Session, user_id: int):
    """删除部门用户"""
    user = get_department_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    db.delete(user)
    db.commit()
    return True

# ========== 部门设备相关操作 ==========

def get_department_equipment_count(db: Session, department_id: int):
    """获取部门设备总数"""
    return db.query(Equipment).filter(Equipment.department_id == department_id).count()

def get_department_equipment_stats(db: Session, department_id: int):
    """获取部门设备统计信息"""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    # 总设备数
    total_count = db.query(Equipment).filter(Equipment.department_id == department_id).count()
    
    # 在用设备数
    active_count = db.query(Equipment).filter(
        Equipment.department_id == department_id,
        Equipment.status == "在用"
    ).count()
    
    # 30天内到期设备数
    due_in_30_days = db.query(Equipment).filter(
        Equipment.department_id == department_id,
        Equipment.status == "在用",
        Equipment.valid_until <= thirty_days_later,
        Equipment.valid_until >= today
    ).count()
    
    # 已到期设备数
    overdue_count = db.query(Equipment).filter(
        Equipment.department_id == department_id,
        Equipment.status == "在用",
        Equipment.valid_until < today
    ).count()
    
    # 设备类别分布
    category_distribution = db.query(
        EquipmentCategory.name,
        EquipmentCategory.id,
        func.count(Equipment.id).label('count')
    ).join(Equipment).filter(
        Equipment.department_id == department_id,
        Equipment.status == "在用"
    ).group_by(EquipmentCategory.id, EquipmentCategory.name).all()
    
    category_dist = [
        {
            "name": item.name,
            "id": item.id,
            "count": item.count
        } for item in category_distribution
    ]
    
    return {
        "total_count": total_count,
        "active_count": active_count,
        "due_in_30_days": due_in_30_days,
        "overdue_count": overdue_count,
        "category_distribution": category_dist
    }

def get_department_equipment_list(
    db: Session,
    department_id: int,
    skip: int = 0,
    limit: int = 50,
    filters: Optional[DepartmentEquipmentFilter] = None
):
    """获取部门设备列表"""
    query = db.query(Equipment).filter(Equipment.department_id == department_id).options(
        joinedload(Equipment.category)
    )
    
    # 应用筛选条件
    if filters:
        if filters.equipment_name:
            query = query.filter(Equipment.name == filters.equipment_name)
        
        if filters.search:
            # 扩展搜索：设备名称、内部编号、厂家编号
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Equipment.name.contains(filters.search),
                    Equipment.internal_id.contains(filters.search),
                    Equipment.manufacturer_id.contains(filters.search)
                )
            )
        
        if filters.status:
            today = date.today()
            thirty_days_later = today + timedelta(days=30)
            
            if filters.status == "正常":
                query = query.filter(
                    Equipment.status == "在用",
                    Equipment.valid_until > thirty_days_later
                )
            elif filters.status == "即将到期":
                query = query.filter(
                    Equipment.status == "在用",
                    Equipment.valid_until <= thirty_days_later,
                    Equipment.valid_until >= today
                )
            elif filters.status == "已到期":
                query = query.filter(
                    Equipment.status == "在用",
                    Equipment.valid_until < today
                )
            else:
                query = query.filter(Equipment.status == filters.status)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

def get_department_equipment_by_id(db: Session, equipment_id: int, department_id: int):
    """获取部门的特定设备详情"""
    return db.query(Equipment).filter(
        Equipment.id == equipment_id,
        Equipment.department_id == department_id
    ).options(
        joinedload(Equipment.category),
        joinedload(Equipment.department)
    ).first()

def get_department_equipment_names(db: Session, department_id: int):
    """获取部门拥有的设备名称列表（用于筛选）"""
    equipment_names = db.query(Equipment.name).filter(
        Equipment.department_id == department_id
    ).distinct().all()
    
    # 返回排序后的设备名称列表
    return sorted([name[0] for name in equipment_names])

def get_department_categories(db: Session, department_id: int):
    """获取部门拥有的设备类别列表（用于筛选）"""
    categories = db.query(EquipmentCategory).join(Equipment).filter(
        Equipment.department_id == department_id
    ).distinct().all()
    
    return categories

# ========== 部门用户操作日志相关 ==========

def create_department_user_log(
    db: Session, 
    user_id: int, 
    action: str, 
    description: str,
    ip_address: str = None,
    user_agent: str = None
):
    """创建部门用户操作日志"""
    log = DepartmentUserLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_department_user_logs(db: Session, user_id: int, limit: int = 10):
    """获取部门用户的操作日志"""
    logs = db.query(DepartmentUserLog).filter(
        DepartmentUserLog.user_id == user_id
    ).order_by(DepartmentUserLog.created_at.desc()).limit(limit).all()
    
    return logs

def get_department_user_logs_by_department(db: Session, department_id: int, limit: int = 50):
    """获取部门所有用户的操作日志"""
    logs = db.query(DepartmentUserLog).join(User).filter(
        User.department_id == department_id,
        User.user_type == "department_user"
    ).options(joinedload(DepartmentUserLog.user)).order_by(
        DepartmentUserLog.created_at.desc()
    ).limit(limit).all()
    
    return logs
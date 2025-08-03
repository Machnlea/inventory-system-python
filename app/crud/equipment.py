from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select
from app.models.models import Equipment, UserCategory
from app.schemas.schemas import EquipmentCreate, EquipmentUpdate, EquipmentFilter
from datetime import date, timedelta, datetime
from typing import List, Optional

def calculate_next_calibration_date(calibration_date: date, calibration_cycle: str) -> date:
    """计算下次检定日期"""
    if calibration_cycle == "1年":
        next_date = calibration_date.replace(year=calibration_date.year + 1)
    elif calibration_cycle == "2年":
        next_date = calibration_date.replace(year=calibration_date.year + 2)
    else:
        raise ValueError("检定周期必须是'1年'或'2年'")
    
    # 减去1天
    return next_date - timedelta(days=1)

def get_equipments_count(db: Session, user_id: Optional[int] = None, is_admin: bool = False):
    """获取设备总数"""
    query = db.query(Equipment)
    
    # 如果不是管理员，只能看到被授权的设备类别
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    return query.count()

def get_equipments(db: Session, skip: int = 0, limit: int = 100, 
                  user_id: Optional[int] = None, is_admin: bool = False):
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    )
    
    # 如果不是管理员，只能看到被授权的设备类别
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    return query.offset(skip).limit(limit).all()

def get_equipments_paginated(db: Session, skip: int = 0, limit: int = 100, 
                           user_id: Optional[int] = None, is_admin: bool = False):
    """获取分页设备数据"""
    items = get_equipments(db, skip=skip, limit=limit, user_id=user_id, is_admin=is_admin)
    total = get_equipments_count(db, user_id=user_id, is_admin=is_admin)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

def get_equipment(db: Session, equipment_id: int, user_id: Optional[int] = None, 
                 is_admin: bool = False):
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    ).filter(Equipment.id == equipment_id)
    
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    return query.first()

def create_equipment(db: Session, equipment: EquipmentCreate):
    # 自动计算下次检定日期
    next_calibration_date = calculate_next_calibration_date(
        equipment.calibration_date, equipment.calibration_cycle
    )
    
    # 准备设备数据
    equipment_data = equipment.dict()
    equipment_data["next_calibration_date"] = next_calibration_date
    
    # 处理状态变更时间
    if hasattr(equipment, 'status') and equipment.status in ["停用", "报废"]:
        if hasattr(equipment, 'status_change_date') and equipment.status_change_date:
            # 如果提供了状态变更时间，将日期字符串转换为datetime对象（只保留日期部分）
            if isinstance(equipment.status_change_date, str):
                parsed_date = datetime.strptime(equipment.status_change_date, "%Y-%m-%d")
                equipment_data["status_change_date"] = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                equipment_data["status_change_date"] = equipment.status_change_date
        else:
            # 如果没有提供状态变更时间，使用当前日期（00:00:00）
            today = date.today()
            equipment_data["status_change_date"] = datetime.combine(today, datetime.min.time())
    
    db_equipment = Equipment(**equipment_data)
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def update_equipment(db: Session, equipment_id: int, equipment_update: EquipmentUpdate):
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if db_equipment:
        update_data = equipment_update.dict(exclude_unset=True)
        
        # 如果更新了检定日期或检定周期，重新计算下次检定日期
        if "calibration_date" in update_data or "calibration_cycle" in update_data:
            calibration_date = update_data.get("calibration_date", db_equipment.calibration_date)
            calibration_cycle = update_data.get("calibration_cycle", db_equipment.calibration_cycle)
            update_data["next_calibration_date"] = calculate_next_calibration_date(
                calibration_date, calibration_cycle
            )
        
        # 处理状态变更时间
        if "status" in update_data:
            if update_data["status"] in ["停用", "报废"]:
                # 如果提供了状态变更时间，使用提供的时间
                if "status_change_date" in update_data and update_data["status_change_date"]:
                    # 将日期字符串转换为datetime对象（只保留日期部分，时间设为00:00:00）
                    if isinstance(update_data["status_change_date"], str):
                        parsed_date = datetime.strptime(update_data["status_change_date"], "%Y-%m-%d")
                        update_data["status_change_date"] = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                elif db_equipment.status == "在用":
                    # 只有当设备原本是在用状态且没有提供状态变更时间时，才使用当前日期（00:00:00）
                    today = date.today()
                    update_data["status_change_date"] = datetime.combine(today, datetime.min.time())
                # 如果设备原本就是停用或报废状态且没有提供新的状态变更时间，保留原有时间
            else:
                # 如果状态改为在用，清除状态变更时间
                update_data["status_change_date"] = None
        elif "status_change_date" in update_data and update_data["status_change_date"]:
            # 单独更新状态变更时间
            if isinstance(update_data["status_change_date"], str):
                parsed_date = datetime.strptime(update_data["status_change_date"], "%Y-%m-%d")
                update_data["status_change_date"] = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for field, value in update_data.items():
            setattr(db_equipment, field, value)
        
        db.commit()
        db.refresh(db_equipment)
    return db_equipment

def delete_equipment(db: Session, equipment_id: int):
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if db_equipment:
        db.delete(db_equipment)
        db.commit()
        return True
    return False

def filter_equipments_count(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                           is_admin: bool = False):
    """获取筛选后的设备总数"""
    query = db.query(Equipment)
    
    # 权限控制
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 应用筛选条件
    if filters.department_id:
        query = query.filter(Equipment.department_id == filters.department_id)
    
    if filters.category_id:
        query = query.filter(Equipment.category_id == filters.category_id)
    
    if filters.status:
        query = query.filter(Equipment.status == filters.status)
    
    if filters.next_calibration_start:
        query = query.filter(Equipment.next_calibration_date >= filters.next_calibration_start)
    
    if filters.next_calibration_end:
        query = query.filter(Equipment.next_calibration_date <= filters.next_calibration_end)
    
    return query.count()

def filter_equipments(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                     is_admin: bool = False, skip: int = 0, limit: int = 100):
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    )
    
    # 权限控制
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 应用筛选条件
    if filters.department_id:
        query = query.filter(Equipment.department_id == filters.department_id)
    
    if filters.category_id:
        query = query.filter(Equipment.category_id == filters.category_id)
    
    if filters.status:
        query = query.filter(Equipment.status == filters.status)
    
    if filters.next_calibration_start:
        query = query.filter(Equipment.next_calibration_date >= filters.next_calibration_start)
    
    if filters.next_calibration_end:
        query = query.filter(Equipment.next_calibration_date <= filters.next_calibration_end)
    
    return query.offset(skip).limit(limit).all()

def filter_equipments_paginated(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                               is_admin: bool = False, skip: int = 0, limit: int = 100):
    """获取分页筛选设备数据"""
    items = filter_equipments(db, filters, user_id, is_admin, skip, limit)
    total = filter_equipments_count(db, filters, user_id, is_admin)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

def get_equipments_due_for_calibration(db: Session, start_date: date, end_date: date,
                                     user_id: Optional[int] = None, is_admin: bool = False):
    """获取指定日期范围内需要检定的设备"""
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    ).filter(
        and_(
            Equipment.next_calibration_date >= start_date,
            Equipment.next_calibration_date <= end_date,
            Equipment.status == "在用"
        )
    )
    
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    return query.all()

def get_overdue_equipments(db: Session, user_id: Optional[int] = None, is_admin: bool = False):
    """获取超期未检设备"""
    today = date.today()
    query = db.query(Equipment).filter(
        and_(
            Equipment.next_calibration_date < today,
            Equipment.status == "在用"
        )
    )
    
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    return query.all()
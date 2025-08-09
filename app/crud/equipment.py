from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select
from app.models.models import Equipment, UserCategory, Department, EquipmentCategory
from app.schemas.schemas import EquipmentCreate, EquipmentUpdate, EquipmentFilter, EquipmentSearch
from datetime import date, timedelta, datetime
from typing import List, Optional

def calculate_valid_until(calibration_date: date, calibration_cycle: str) -> date:
    """计算有效期至"""
    if calibration_cycle == "12个月":
        next_date = calibration_date.replace(year=calibration_date.year + 1)
    elif calibration_cycle == "24个月":
        next_date = calibration_date.replace(year=calibration_date.year + 2)
    elif calibration_cycle == "6个月":
        # 增加6个月
        if calibration_date.month + 6 > 12:
            next_date = calibration_date.replace(year=calibration_date.year + 1, month=calibration_date.month + 6 - 12)
        else:
            next_date = calibration_date.replace(month=calibration_date.month + 6)
    else:
        raise ValueError("检定周期必须是'6个月'、'12个月'或'24个月'")
    
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
                  sort_field: str = "valid_until", 
                  sort_order: str = "asc",
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
    
    # 添加排序
    if sort_field == "name":
        query = query.order_by(Equipment.name.asc() if sort_order == "asc" else Equipment.name.desc())
    elif sort_field == "department":
        query = query.join(Equipment.department).order_by(
            Department.name.asc() if sort_order == "asc" else Department.name.desc()
        )
    elif sort_field == "category":
        query = query.join(Equipment.category).order_by(
            EquipmentCategory.name.asc() if sort_order == "asc" else EquipmentCategory.name.desc()
        )
    elif sort_field == "valid_until":
        query = query.order_by(
            Equipment.valid_until.asc() if sort_order == "asc" else Equipment.valid_until.desc()
        )
    else:
        # 默认按有效期至排序
        query = query.order_by(Equipment.valid_until.asc())
    
    return query.offset(skip).limit(limit).all()

def get_equipments_paginated(db: Session, skip: int = 0, limit: int = 100,
                           sort_field: str = "valid_until", 
                           sort_order: str = "asc",
                           user_id: Optional[int] = None, is_admin: bool = False):
    """获取分页设备数据"""
    items = get_equipments(db, skip=skip, limit=limit, 
                          sort_field=sort_field, sort_order=sort_order,
                          user_id=user_id, is_admin=is_admin)
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
    # 验证证书形式字段
    if equipment.calibration_method == "外检" and equipment.certificate_form:
        if equipment.certificate_form not in ["校准证书", "检定证书"]:
            raise ValueError("证书形式必须是'校准证书'或'检定证书'")
    
    # 自动计算有效期至
    valid_until = calculate_valid_until(
        equipment.calibration_date, equipment.calibration_cycle
    )
    
    # 准备设备数据
    equipment_data = equipment.dict()
    equipment_data["valid_until"] = valid_until
    
    # 处理管理级别：如果检定方式为外检，管理级别设为"-"
    if equipment.calibration_method == "外检":
        equipment_data["management_level"] = "-"
    
    # 处理状态变更时间
    if hasattr(equipment, 'status') and equipment.status in ["停用", "报废"]:
        if hasattr(equipment, 'status_change_date') and equipment.status_change_date:
            # 如果提供了状态变更时间，使用提供的日期
            equipment_data["status_change_date"] = equipment.status_change_date
        else:
            # 如果没有提供状态变更时间，使用当前日期
            equipment_data["status_change_date"] = date.today()
    
    db_equipment = Equipment(**equipment_data)
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def update_equipment(db: Session, equipment_id: int, equipment_update: EquipmentUpdate):
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if db_equipment:
        update_data = equipment_update.dict(exclude_unset=True)
        
        # 验证证书形式字段
        if "certificate_form" in update_data:
            calibration_method = update_data.get("calibration_method", db_equipment.calibration_method)
            if calibration_method == "外检" and update_data["certificate_form"]:
                if update_data["certificate_form"] not in ["校准证书", "检定证书"]:
                    raise ValueError("证书形式必须是'校准证书'或'检定证书'")
        
        # 如果更新了检定日期或检定周期，重新计算有效期至
        if "calibration_date" in update_data or "calibration_cycle" in update_data:
            calibration_date = update_data.get("calibration_date", db_equipment.calibration_date)
            calibration_cycle = update_data.get("calibration_cycle", db_equipment.calibration_cycle)
            update_data["valid_until"] = calculate_valid_until(
                calibration_date, calibration_cycle
            )
        
        # 处理管理级别：如果检定方式为外检，管理级别设为"-"
        if "calibration_method" in update_data and update_data["calibration_method"] == "外检":
            update_data["management_level"] = "-"
        
        # 处理状态变更时间
        if "status" in update_data:
            if update_data["status"] in ["停用", "报废"]:
                # 如果提供了状态变更时间，使用提供的时间
                if "status_change_date" in update_data and update_data["status_change_date"]:
                    pass  # 使用提供的日期
                elif db_equipment.status == "在用":
                    # 只有当设备原本是在用状态且没有提供状态变更时间时，才使用当前日期
                    update_data["status_change_date"] = date.today()
                # 如果设备原本就是停用或报废状态且没有提供新的状态变更时间，保留原有时间
            else:
                # 如果状态改为在用，清除状态变更时间
                update_data["status_change_date"] = None
        
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
        query = query.filter(Equipment.valid_until >= filters.next_calibration_start)
    
    if filters.next_calibration_end:
        query = query.filter(Equipment.valid_until <= filters.next_calibration_end)
    
    return query.count()

def filter_equipments(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                     is_admin: bool = False, skip: int = 0, limit: int = 100,
                     sort_field: str = "next_calibration_date", 
                     sort_order: str = "asc"):
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
        query = query.filter(Equipment.valid_until >= filters.next_calibration_start)
    
    if filters.next_calibration_end:
        query = query.filter(Equipment.valid_until <= filters.next_calibration_end)
    
    # 添加排序
    if sort_field == "name":
        query = query.order_by(Equipment.name.asc() if sort_order == "asc" else Equipment.name.desc())
    elif sort_field == "department":
        query = query.join(Equipment.department).order_by(
            Department.name.asc() if sort_order == "asc" else Department.name.desc()
        )
    elif sort_field == "category":
        query = query.join(Equipment.category).order_by(
            EquipmentCategory.name.asc() if sort_order == "asc" else EquipmentCategory.name.desc()
        )
    elif sort_field == "valid_until":
        query = query.order_by(
            Equipment.valid_until.asc() if sort_order == "asc" else Equipment.valid_until.desc()
        )
    else:
        # 默认按有效期至排序
        query = query.order_by(Equipment.valid_until.asc())
    
    return query.offset(skip).limit(limit).all()

def filter_equipments_paginated(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                               is_admin: bool = False, skip: int = 0, limit: int = 100,
                               sort_field: str = "valid_until", 
                               sort_order: str = "asc"):
    """获取分页筛选设备数据"""
    items = filter_equipments(db, filters, user_id, is_admin, skip, limit,
                             sort_field=sort_field, sort_order=sort_order)
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
            Equipment.valid_until >= start_date,
            Equipment.valid_until <= end_date,
            Equipment.status == "在用"
        )
    )
    
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 按有效期至升序排序
    query = query.order_by(Equipment.valid_until.asc())
    
    return query.all()

def get_overdue_equipments(db: Session, user_id: Optional[int] = None, is_admin: bool = False):
    """获取超期未检设备"""
    today = date.today()
    query = db.query(Equipment).filter(
        and_(
            Equipment.valid_until < today,
            Equipment.status == "在用"
        )
    )
    
    if not is_admin and user_id:
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == user_id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 按有效期至升序排序（最早超期的排在前面）
    query = query.order_by(Equipment.valid_until.asc())
    
    return query.all()

def search_equipments_count(db: Session, search: EquipmentSearch, user_id: Optional[int] = None, 
                           is_admin: bool = False):
    """获取搜索结果总数"""
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
    
    # 构建搜索条件
    search_conditions = []
    if search.query:
        search_term = f"%{search.query}%"
        search_conditions.extend([
            Equipment.name.ilike(search_term),
            Equipment.model.ilike(search_term),
            Equipment.serial_number.ilike(search_term),
            Equipment.manufacturer.ilike(search_term),
            Equipment.installation_location.ilike(search_term),
            Equipment.notes.ilike(search_term),
            Equipment.accuracy_level.ilike(search_term),
            Equipment.measurement_range.ilike(search_term),
            Equipment.calibration_method.ilike(search_term)
        ])
    
    # 添加部门名称搜索
    if search.query:
        department_subquery = db.query(Department.id).filter(
            Department.name.ilike(f"%{search.query}%")
        )
        search_conditions.append(Equipment.department_id.in_(department_subquery))
    
    # 添加类别名称搜索
    if search.query:
        category_subquery = db.query(EquipmentCategory.id).filter(
            EquipmentCategory.name.ilike(f"%{search.query}%")
        )
        search_conditions.append(Equipment.category_id.in_(category_subquery))
    
    if search_conditions:
        query = query.filter(or_(*search_conditions))
    
    # 添加其他筛选条件
    if search.department_id:
        query = query.filter(Equipment.department_id == search.department_id)
    
    if search.category_id:
        query = query.filter(Equipment.category_id == search.category_id)
    
    if search.status:
        query = query.filter(Equipment.status == search.status)
    
    return query.count()

def search_equipments(db: Session, search: EquipmentSearch, user_id: Optional[int] = None, 
                     is_admin: bool = False, skip: int = 0, limit: int = 100):
    """全文本搜索设备"""
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
    
    # 构建搜索条件
    search_conditions = []
    if search.query:
        search_term = f"%{search.query}%"
        search_conditions.extend([
            Equipment.name.ilike(search_term),
            Equipment.model.ilike(search_term),
            Equipment.serial_number.ilike(search_term),
            Equipment.manufacturer.ilike(search_term),
            Equipment.installation_location.ilike(search_term),
            Equipment.notes.ilike(search_term),
            Equipment.accuracy_level.ilike(search_term),
            Equipment.measurement_range.ilike(search_term),
            Equipment.calibration_method.ilike(search_term)
        ])
    
    # 添加部门名称搜索
    if search.query:
        department_subquery = db.query(Department.id).filter(
            Department.name.ilike(f"%{search.query}%")
        )
        search_conditions.append(Equipment.department_id.in_(department_subquery))
    
    # 添加类别名称搜索
    if search.query:
        category_subquery = db.query(EquipmentCategory.id).filter(
            EquipmentCategory.name.ilike(f"%{search.query}%")
        )
        search_conditions.append(Equipment.category_id.in_(category_subquery))
    
    if search_conditions:
        query = query.filter(or_(*search_conditions))
    
    # 添加其他筛选条件
    if search.department_id:
        query = query.filter(Equipment.department_id == search.department_id)
    
    if search.category_id:
        query = query.filter(Equipment.category_id == search.category_id)
    
    if search.status:
        query = query.filter(Equipment.status == search.status)
    
    return query.offset(skip).limit(limit).all()

def search_equipments_paginated(db: Session, search: EquipmentSearch, user_id: Optional[int] = None, 
                               is_admin: bool = False, skip: int = 0, limit: int = 100):
    """获取分页搜索结果"""
    items = search_equipments(db, search, user_id, is_admin, skip, limit)
    total = search_equipments_count(db, search, user_id, is_admin)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
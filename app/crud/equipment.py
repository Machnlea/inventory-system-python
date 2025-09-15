from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, select, cast, String
from app.models.models import Equipment, UserEquipmentPermission, Department, EquipmentCategory
from app.schemas.schemas import EquipmentCreate, EquipmentUpdate, EquipmentFilter, EquipmentSearch
from datetime import date, timedelta
from typing import List, Optional

def get_equipments_for_external_api(
    db: Session,
    skip: int = 0,
    limit: int = 1000,
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Equipment]:
    """
    为外部API获取设备列表，无需用户权限验证
    专门用于外部系统调用
    """
    query = db.query(Equipment).options(
        joinedload(Equipment.category),
        joinedload(Equipment.department)
    )
    
    # 应用筛选条件
    if department_id:
        query = query.filter(Equipment.department_id == department_id)
    
    if category_id:
        query = query.filter(Equipment.category_id == category_id)
    
    if status:
        query = query.filter(Equipment.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(Equipment.created_at.desc())
    
    return query.offset(skip).limit(limit).all()

def get_equipments_by_category(db: Session, category_id: int) -> List[Equipment]:
    """获取指定类别下的所有设备"""
    return db.query(Equipment).filter(Equipment.category_id == category_id).all()

def calculate_valid_until(calibration_date: date, calibration_cycle: str) -> date | None:
    """计算有效期至"""
    if calibration_cycle == "随坏随换":
        return None  # 随坏随换不需要计算有效期
    elif calibration_cycle == "12个月":
        next_date = calibration_date.replace(year=calibration_date.year + 1)
    elif calibration_cycle == "24个月":
        next_date = calibration_date.replace(year=calibration_date.year + 2)
    elif calibration_cycle == "36个月":
        next_date = calibration_date.replace(year=calibration_date.year + 3)
    elif calibration_cycle == "6个月":
        # 增加6个月
        if calibration_date.month + 6 > 12:
            next_date = calibration_date.replace(year=calibration_date.year + 1, month=calibration_date.month + 6 - 12)
        else:
            next_date = calibration_date.replace(month=calibration_date.month + 6)
    else:
        raise ValueError("检定周期必须是'6个月'、'12个月'、'24个月'、'36个月'或'随坏随换'")
    
    # 减去1天
    return next_date - timedelta(days=1)

def get_equipments_count(db: Session, user_id: Optional[int] = None, is_admin: bool = False):
    """获取设备总数"""
    query = db.query(Equipment)
    
    # 如果不是管理员，只能看到被授权的设备
    if not is_admin and user_id:
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return 0
    
    return query.count()

def get_equipments(db: Session, skip: int = 0, limit: int = 100,
                  sort_field: str = "valid_until", 
                  sort_order: str = "asc",
                  user_id: Optional[int] = None, is_admin: bool = False):
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    )
    
    # 如果不是管理员，只能看到被授权的设备
    if not is_admin and user_id:
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return []
    
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
        # 特殊处理：确保随坏随换设备（valid_until为null）总是排在最后
        if sort_order == "asc":
            # 升序：非null值按升序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.asc().nulls_last()
            )
        else:
            # 降序：非null值按降序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.desc().nulls_last()
            )
    else:
        # 默认按有效期至升序排序，随坏随换设备排在最后
        query = query.order_by(Equipment.valid_until.asc().nulls_last())
    
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
        # 只使用设备权限检查
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return []
    
    return query.first()

def create_equipment(db: Session, equipment: EquipmentCreate):
    # 自动计算有效期至（如果检定周期不是"随坏随换"）
    valid_until = None
    if equipment.calibration_cycle != "随坏随换" and equipment.calibration_date:
        valid_until = calculate_valid_until(
            equipment.calibration_date, equipment.calibration_cycle
        )
    
    # 准备设备数据
    equipment_data = equipment.model_dump()
    equipment_data["valid_until"] = valid_until
    
    # 处理管理级别：如果检定方式为外检，管理级别设为"-"
    if equipment.calibration_method == "外检":
        equipment_data["management_level"] = "-"
    
    # 处理状态变更时间
    if equipment.status in ["停用", "报废"]:
        if equipment.status_change_date:
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
    from app.utils.auto_id import generate_internal_id
    
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if db_equipment:
        update_data = equipment_update.model_dump(exclude_unset=True)
        
        # 如果更新了设备名称或类别，需要重新生成内部编号
        if "name" in update_data or "category_id" in update_data:
            new_name = update_data.get("name", db_equipment.name)
            new_category_id = update_data.get("category_id", db_equipment.category_id)
            
            # 重新生成内部编号
            try:
                new_internal_id = generate_internal_id(
                    db, 
                    new_category_id, 
                    new_name, 
                    equipment_id=equipment_id
                )
                update_data["internal_id"] = new_internal_id
            except ValueError as e:
                raise ValueError(f"生成内部编号失败: {str(e)}")
        
        # 如果更新了检定日期或检定周期，重新计算有效期至
        if "calibration_date" in update_data or "calibration_cycle" in update_data:
            calibration_date = update_data.get("calibration_date", db_equipment.calibration_date)
            calibration_cycle = update_data.get("calibration_cycle", db_equipment.calibration_cycle)
            
            # 只有当检定周期不是"随坏随换"且有检定日期时才计算有效期
            if calibration_cycle != "随坏随换" and calibration_date:
                update_data["valid_until"] = calculate_valid_until(
                    calibration_date, calibration_cycle
                )
            else:
                update_data["valid_until"] = None
        
        # 处理管理级别：如果检定方式为外检，管理级别设为"-"
        if "calibration_method" in update_data and update_data["calibration_method"] == "外检":
            update_data["management_level"] = "-"
        
        # 处理状态变更时间
        if "status" in update_data:
            if update_data["status"] in ["停用", "报废"]:
                # 如果设备状态变为停用或报废，自动清空有效期至
                update_data["valid_until"] = None
                
                # 如果提供了状态变更时间，使用提供的时间
                if "status_change_date" in update_data and update_data["status_change_date"]:
                    pass  # 使用提供的日期
                elif str(db_equipment.status) == "在用":
                    # 只有当设备原本是在用状态且没有提供状态变更时间时，才使用当前日期
                    update_data["status_change_date"] = date.today()
                # 如果设备原本就是停用或报废状态且没有提供新的状态变更时间，保留原有时间
            else:
                # 如果状态改为在用，清除状态变更时间
                update_data["status_change_date"] = None
                
                # 如果设备从停用/报废状态恢复为在用，且检定周期不是"随坏随换"且有检定日期，重新计算有效期至
                if update_data["status"] == "在用" and db_equipment.status in ["停用", "报废"]:
                    if db_equipment.calibration_cycle != "随坏随换" and db_equipment.calibration_date:
                        update_data["valid_until"] = calculate_valid_until(
                            db_equipment.calibration_date, db_equipment.calibration_cycle
                        )
        
        for field, value in update_data.items():
            setattr(db_equipment, field, value)
        
        db.commit()
        db.refresh(db_equipment)
    return db_equipment

def delete_equipment(db: Session, equipment_id: int):
    import os
    from app.models.models import EquipmentAttachment, CalibrationHistory
    
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if db_equipment:
        # 先删除关联的附件文件
        attachments = db.query(EquipmentAttachment).filter(EquipmentAttachment.equipment_id == equipment_id).all()
        for attachment in attachments:
            try:
                # 删除物理文件
                file_path = str(attachment.file_path)  # 确保是字符串类型
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # 文件删除失败不影响数据库操作，只记录日志
                print(f"删除附件文件失败: {attachment.file_path}, 错误: {e}")
        
        # 删除数据库中的附件记录
        db.query(EquipmentAttachment).filter(EquipmentAttachment.equipment_id == equipment_id).delete()
        
        # 删除检定历史记录
        db.query(CalibrationHistory).filter(CalibrationHistory.equipment_id == equipment_id).delete()
        
        # 删除设备
        db.delete(db_equipment)
        db.commit()
        return True
    return False

def filter_equipments_count(db: Session, filters: EquipmentFilter, user_id: Optional[int] = None, 
                           is_admin: bool = False):
    """获取筛选后的设备总数"""
    query = db.query(Equipment)
    
    # 权限控制 - 临时简化以测试
    if not is_admin and user_id:
        try:
            result = db.execute(
                select(UserEquipmentPermission.equipment_name).filter(
                    UserEquipmentPermission.user_id == user_id
                )
            )
            authorized_equipment_names = [row[0] for row in result.fetchall()]
            
            if authorized_equipment_names:
                query = query.filter(Equipment.name.in_(authorized_equipment_names))
            else:
                # 如果没有权限，返回空结果
                return 0
        except Exception as e:
            # 如果权限查询出错，暂时允许所有权限用于调试
            print(f"权限查询错误: {e}")
            pass
    
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
                     sort_field: str = "valid_until", 
                     sort_order: str = "asc"):
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    )
    
    # 权限控制 - 临时简化以测试
    if not is_admin and user_id:
        try:
            result = db.execute(
                select(UserEquipmentPermission.equipment_name).filter(
                    UserEquipmentPermission.user_id == user_id
                )
            )
            authorized_equipment_names = [row[0] for row in result.fetchall()]
            
            if authorized_equipment_names:
                query = query.filter(Equipment.name.in_(authorized_equipment_names))
            else:
                # 如果没有权限，返回空结果
                return []
        except Exception as e:
            # 如果权限查询出错，暂时允许所有权限用于调试
            print(f"权限查询错误: {e}")
            pass
    
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
        # 特殊处理：确保随坏随换设备（valid_until为null）总是排在最后
        if sort_order == "asc":
            # 升序：非null值按升序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.asc().nulls_last()
            )
        else:
            # 降序：非null值按降序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.desc().nulls_last()
            )
    else:
        # 默认按有效期至升序排序，随坏随换设备排在最后
        query = query.order_by(Equipment.valid_until.asc().nulls_last())
    
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
        # 只使用设备权限检查
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return []
    
    # 按有效期至升序排序
    query = query.order_by(Equipment.valid_until.asc().nulls_last())
    
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
        # 只使用设备权限检查
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return []
    
    # 按有效期至升序排序（最早超期的排在前面）
    query = query.order_by(Equipment.valid_until.asc().nulls_last())
    
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
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return 0
    
    # 构建搜索条件
    search_conditions = []
    if search.query:
        search_term = f"%{search.query}%"
        search_conditions.extend([
            Equipment.name.ilike(search_term),
            Equipment.model.ilike(search_term),
            Equipment.internal_id.ilike(search_term),
            Equipment.manufacturer.ilike(search_term),
            Equipment.manufacturer_id.ilike(search_term),
            Equipment.installation_location.ilike(search_term),
            Equipment.notes.ilike(search_term),
            Equipment.accuracy_level.ilike(search_term),
            Equipment.measurement_range.ilike(search_term),
            Equipment.calibration_method.ilike(search_term)
        ])
        
        # 添加原值/元字段搜索支持
        # 尝试将搜索词转换为数字，如果成功则搜索原值字段
        try:
            # 移除可能的货币符号和空格
            clean_search_term = search.query.replace(',', '').replace('，', '').replace(' ', '').strip()
            if clean_search_term:
                # 尝试转换为浮点数
                search_value = float(clean_search_term)
                
                # 精确匹配
                search_conditions.append(Equipment.original_value == search_value)
                
                # 更精确的模糊匹配：只匹配包含完整搜索词的数值
                # 例如搜索"1500"会匹配"1500.0"但不会匹配"1000.0"
                search_conditions.append(
                    cast(Equipment.original_value, String).ilike(f"%{clean_search_term}.%")
                )
                search_conditions.append(
                    cast(Equipment.original_value, String).ilike(f"{clean_search_term}.%")
                )
        except ValueError:
            # 如果转换失败，只进行字符串匹配，但排除NULL值
            search_conditions.append(
                and_(
                    Equipment.original_value.isnot(None),
                    cast(Equipment.original_value, String).ilike(search_term)
                )
            )
    
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
    
    # 添加日期筛选条件
    if search.next_calibration_start:
        query = query.filter(Equipment.valid_until >= search.next_calibration_start)
    
    if search.next_calibration_end:
        query = query.filter(Equipment.valid_until <= search.next_calibration_end)
    
    return query.count()

def search_equipments(db: Session, search: EquipmentSearch, user_id: Optional[int] = None, 
                     is_admin: bool = False, skip: int = 0, limit: int = 100,
                     sort_field: str = "valid_until", sort_order: str = "asc"):
    """全文本搜索设备"""
    query = db.query(Equipment).options(
        joinedload(Equipment.department),
        joinedload(Equipment.category)
    )
    
    # 权限控制
    if not is_admin and user_id:
        authorized_equipment_names = db.execute(
            select(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == user_id
            )
        ).scalars().all()
        
        if authorized_equipment_names:
            query = query.filter(Equipment.name.in_(authorized_equipment_names))
        else:
            # 如果没有权限，返回空结果
            return []
    
    # 构建搜索条件
    search_conditions = []
    if search.query:
        search_term = f"%{search.query}%"
        search_conditions.extend([
            Equipment.name.ilike(search_term),
            Equipment.model.ilike(search_term),
            Equipment.internal_id.ilike(search_term),
            Equipment.manufacturer.ilike(search_term),
            Equipment.manufacturer_id.ilike(search_term),
            Equipment.installation_location.ilike(search_term),
            Equipment.notes.ilike(search_term),
            Equipment.accuracy_level.ilike(search_term),
            Equipment.measurement_range.ilike(search_term),
            Equipment.calibration_method.ilike(search_term)
        ])
        
        # 添加原值/元字段搜索支持
        # 尝试将搜索词转换为数字，如果成功则搜索原值字段
        try:
            # 移除可能的货币符号和空格
            clean_search_term = search.query.replace(',', '').replace('，', '').replace(' ', '').strip()
            if clean_search_term:
                # 尝试转换为浮点数
                search_value = float(clean_search_term)
                
                # 精确匹配
                search_conditions.append(Equipment.original_value == search_value)
                
                # 更精确的模糊匹配：只匹配包含完整搜索词的数值
                # 例如搜索"1500"会匹配"1500.0"但不会匹配"1000.0"
                search_conditions.append(
                    cast(Equipment.original_value, String).ilike(f"%{clean_search_term}.%")
                )
                search_conditions.append(
                    cast(Equipment.original_value, String).ilike(f"{clean_search_term}.%")
                )
        except ValueError:
            # 如果转换失败，只进行字符串匹配，但排除NULL值
            search_conditions.append(
                and_(
                    Equipment.original_value.isnot(None),
                    cast(Equipment.original_value, String).ilike(search_term)
                )
            )
    
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
    
    # 添加日期筛选条件
    if search.next_calibration_start:
        query = query.filter(Equipment.valid_until >= search.next_calibration_start)
    
    if search.next_calibration_end:
        query = query.filter(Equipment.valid_until <= search.next_calibration_end)
    
    # 添加排序逻辑
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
        # 特殊处理：确保随坏随换设备（valid_until为null）总是排在最后
        if sort_order == "asc":
            # 升序：非null值按升序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.asc().nulls_last()
            )
        else:
            # 降序：非null值按降序，null值排在最后
            query = query.order_by(
                Equipment.valid_until.desc().nulls_last()
            )
    else:
        # 默认按有效期至升序排序，随坏随换设备排在最后
        query = query.order_by(Equipment.valid_until.asc().nulls_last())
    
    return query.offset(skip).limit(limit).all()

def search_equipments_paginated(db: Session, search: EquipmentSearch, user_id: Optional[int] = None, 
                               is_admin: bool = False, skip: int = 0, limit: int = 100,
                               sort_field: str = "valid_until", sort_order: str = "asc"):
    """获取分页搜索结果"""
    items = search_equipments(db, search, user_id, is_admin, skip, limit, sort_field, sort_order)
    total = search_equipments_count(db, search, user_id, is_admin)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
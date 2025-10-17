"""
增强操作日志CRUD模块
支持完整的操作日志记录、查询和回滚功能
"""

import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import contains_eager

from app.models.models import AuditLog, Equipment, User, UserEquipmentPermission
from app.schemas.schemas import AuditLogCreate, AuditLogRollback


def create_audit_log(db: Session, log_data: AuditLogCreate,
                    ip_address: Optional[str] = None) -> AuditLog:
    """创建操作日志记录"""
    audit_log = AuditLog(
        user_id=log_data.user_id,
        equipment_id=log_data.equipment_id,
        action=log_data.action,
        description=log_data.description,
        old_value=log_data.old_value,
        new_value=log_data.new_value,
        operation_type=log_data.operation_type,
        target_table=log_data.target_table,
        target_id=log_data.target_id,
        parent_log_id=log_data.parent_log_id,
        is_rollback=log_data.is_rollback,
        rollback_reason=log_data.rollback_reason,
        ip_address=ip_address,
        user_agent=log_data.user_agent
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    action: Optional[str] = None,
    operation_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_rollback: Optional[bool] = None,
    current_user_id: Optional[int] = None,
    is_admin: bool = False
) -> Tuple[List[AuditLog], int]:
    """
    获取操作日志列表（支持权限控制）
    管理员可以查看所有日志，普通用户可以查看自己的操作日志
    """

    # 完全不加载任何关系，避免循环引用
    query = db.query(AuditLog)

    # 简化权限控制：管理员查看所有，普通用户查看自己的操作
    if not is_admin and current_user_id:
        # 普通用户只能查看自己的操作日志
        query = query.filter(AuditLog.user_id == current_user_id)

    # 应用筛选条件
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if equipment_id:
        query = query.filter(AuditLog.equipment_id == equipment_id)

    if action:
        query = query.filter(AuditLog.action == action)

    if operation_type:
        query = query.filter(AuditLog.operation_type == operation_type)

    if is_rollback is not None:
        query = query.filter(AuditLog.is_rollback == is_rollback)

    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    # 获取总数
    total = query.count()

    # 获取分页数据
    items = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    return items, total


def get_audit_log_by_id(db: Session, log_id: int,
                       current_user_id: Optional[int] = None,
                       is_admin: bool = False) -> Optional[AuditLog]:
    """根据ID获取操作日志（支持权限控制）"""
    # 完全不加载任何关系，避免循环引用
    query = db.query(AuditLog).filter(AuditLog.id == log_id)

    # 简化权限控制：管理员查看所有，普通用户查看自己的操作
    if not is_admin and current_user_id:
        query = query.filter(AuditLog.user_id == current_user_id)

    return query.first()


def get_equipment_audit_logs(
    db: Session,
    equipment_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user_id: Optional[int] = None,
    is_admin: bool = False
) -> Tuple[List[AuditLog], int]:
    """获取特定设备的操作日志"""

    # 检查设备是否存在和权限
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        return [], 0

    # 权限检查
    if not is_admin and current_user_id:
        if not has_equipment_permission(db, current_user_id, equipment.category_id, equipment.name):
            return [], 0

    query = db.query(AuditLog).filter(AuditLog.equipment_id == equipment_id)

    total = query.count()
    items = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    return items, total


def rollback_operation(db: Session, rollback_data: AuditLogRollback,
                      current_user_id: int, is_admin: bool = False,
                      ip_address: Optional[str] = None) -> Optional[AuditLog]:
    """
    回滚操作
    将设备状态恢复到指定操作之前的状态
    """
    # 直接查询原始日志，不使用权限过滤
    original_log = db.query(AuditLog).filter(AuditLog.id == rollback_data.log_id).first()
    if not original_log:
        print(f"DEBUG: 原始日志不存在，log_id={rollback_data.log_id}")
        return None

    print(f"DEBUG: 找到原始日志，log_id={original_log.id}, user_id={original_log.user_id}, action={original_log.action}, is_admin={is_admin}, current_user_id={current_user_id}")

    # 简化权限检查：管理员可以回滚任何操作，普通用户只能回滚自己的操作
    if not is_admin and original_log.user_id != current_user_id:
        print(f"DEBUG: 非管理员无法回滚他人操作，original_user_id={original_log.user_id}, current_user_id={current_user_id}")
        return None

    print(f"DEBUG: 权限检查通过，准备回滚操作，operation_type={original_log.operation_type}, equipment_id={original_log.equipment_id}")

    # 检查是否已经回滚过
    existing_rollback = db.query(AuditLog).filter(
        AuditLog.parent_log_id == original_log.id,
        AuditLog.is_rollback == True
    ).first()

    if existing_rollback:
        print(f"DEBUG: 操作已经回滚过，parent_log_id={original_log.id}")
        return None  # 已经回滚过了

    # 检查是否为回滚操作本身
    if original_log.is_rollback:
        print(f"DEBUG: 不能回滚回滚操作本身")
        return None

    print(f"DEBUG: 开始执行回滚操作，operation_type={original_log.operation_type}")

    # 执行回滚操作
    success = False
    if original_log.operation_type == "equipment" and original_log.equipment_id:
        print(f"DEBUG: 执行设备操作回滚")
        success = _rollback_equipment_operation(db, original_log)
    elif original_log.operation_type == "calibration" and original_log.equipment_id:
        print(f"DEBUG: 执行检定操作回滚")
        success = _rollback_calibration_operation(db, original_log)
    elif original_log.action in ["更新检定信息", "检定"] and original_log.equipment_id:
        print(f"DEBUG: 执行检定信息更新回滚")
        success = _rollback_calibration_operation(db, original_log)
    else:
        print(f"DEBUG: 尝试通用回滚，operation_type={original_log.operation_type}, action={original_log.action}")
        # 对于其他类型的操作，尝试通用回滚
        if original_log.equipment_id and original_log.old_value:
            success = _rollback_equipment_operation(db, original_log)
        else:
            print(f"DEBUG: 不支持的操作类型回滚，operation_type={original_log.operation_type}")

    print(f"DEBUG: 回滚操作执行结果，success={success}")

    if not success:
        print(f"DEBUG: 回滚操作执行失败")
        return None

    # 记录回滚操作日志
    rollback_log = create_audit_log(
        db,
        AuditLogCreate(
            user_id=current_user_id,
            equipment_id=original_log.equipment_id,
            action="回滚",
            description=f"回滚操作：{original_log.description}。原因：{rollback_data.rollback_reason}",
            old_value=original_log.new_value,
            new_value=original_log.old_value,
            operation_type=original_log.operation_type,
            target_table=original_log.target_table,
            target_id=original_log.target_id,
            parent_log_id=original_log.id,
            is_rollback=True,
            rollback_reason=rollback_data.rollback_reason,
            user_agent=None
        ),
        ip_address=ip_address
    )

    # 更新原始日志的回滚关联
    original_log.rollback_log_id = rollback_log.id
    db.commit()

    return rollback_log


def get_operation_history(db: Session, log_id: int,
                         current_user_id: Optional[int] = None,
                         is_admin: bool = False) -> Optional[Dict[str, Any]]:
    """获取操作的历史记录（包括回滚记录）"""
    # 直接查询，不使用权限过滤的函数
    original_log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not original_log:
        return None

    # 简化权限检查
    if not is_admin and current_user_id and original_log.user_id != current_user_id:
        return None

    # 查找所有相关的回滚记录，避免循环引用
    rollback_logs = db.query(AuditLog).filter(
        AuditLog.parent_log_id == log_id,
        AuditLog.is_rollback == True
    ).order_by(AuditLog.created_at).all()

    # 获取当前状态
    current_state = None
    if original_log.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == original_log.equipment_id).first()
        if equipment:
            current_state = {
                "status": equipment.status,
                "calibration_date": equipment.calibration_date.isoformat() if equipment.calibration_date else None,
                "valid_until": equipment.valid_until.isoformat() if equipment.valid_until else None,
                "current_calibration_result": equipment.current_calibration_result
            }

    return {
        "original_log": original_log,
        "rollback_logs": rollback_logs,
        "current_state": current_state
    }


def get_user_authorized_equipment_ids(db: Session, user_id: int) -> List[Tuple[int, str, int]]:
    """获取用户授权的设备ID列表（返回category_id, equipment_name, equipment_id三元组）"""
    permissions = db.query(
        UserEquipmentPermission.category_id,
        UserEquipmentPermission.equipment_name,
        Equipment.id
    ).join(
        Equipment,
        and_(
            Equipment.category_id == UserEquipmentPermission.category_id,
            Equipment.name == UserEquipmentPermission.equipment_name
        )
    ).filter(
        UserEquipmentPermission.user_id == user_id
    ).all()

    return permissions


def has_equipment_permission(db: Session, user_id: int, category_id: int, equipment_name: str) -> bool:
    """检查用户是否有特定设备的权限"""
    permission = db.query(UserEquipmentPermission).filter(
        UserEquipmentPermission.user_id == user_id,
        UserEquipmentPermission.category_id == category_id,
        UserEquipmentPermission.equipment_name == equipment_name
    ).first()

    return permission is not None


def _rollback_equipment_operation(db: Session, original_log: AuditLog) -> bool:
    """回滚设备操作"""
    try:
        print(f"DEBUG: 开始回滚设备操作，log_id={original_log.id}, equipment_id={original_log.equipment_id}")

        if not original_log.equipment_id:
            print(f"DEBUG: equipment_id为空，无法回滚")
            return False

        if not original_log.old_value:
            print(f"DEBUG: old_value为空，无法回滚")
            return False

        print(f"DEBUG: 查询设备，equipment_id={original_log.equipment_id}")
        equipment = db.query(Equipment).filter(Equipment.id == original_log.equipment_id).first()
        if not equipment:
            print(f"DEBUG: 设备不存在，equipment_id={original_log.equipment_id}")
            return False

        print(f"DEBUG: 找到设备，准备解析old_value: {original_log.old_value}")

        # 解析旧值JSON
        try:
            old_data = json.loads(original_log.old_value) if original_log.old_value else {}
            print(f"DEBUG: 成功解析old_value，得到{len(old_data)}个字段: {list(old_data.keys())}")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON解析失败: {e}")
            return False

        if not old_data:
            print(f"DEBUG: 解析后的old_data为空")
            return False

        # 只恢复简单的字段，避免复杂对象问题
        simple_fields = [
            'name', 'model', 'accuracy_level', 'measurement_range', 'calibration_cycle',
            'calibration_date', 'calibration_method', 'current_calibration_result',
            'certificate_number', 'verification_agency', 'certificate_form',
            'internal_id', 'manufacturer_id', 'installation_location', 'manufacturer',
            'manufacture_date', 'scale_value', 'management_level', 'original_value',
            'status', 'status_change_date', 'notes', 'valid_until'
        ]

        print(f"DEBUG: 准备恢复设备信息，支持的字段: {simple_fields}")

        restored_count = 0
        # 恢复设备信息
        for key, value in old_data.items():
            if key in simple_fields and hasattr(equipment, key):
                print(f"DEBUG: 恢复字段 {key}: {value} -> {getattr(equipment, key)}")

                # 处理日期字段
                if key in ['calibration_date', 'manufacture_date', 'valid_until', 'status_change_date']:
                    if value and isinstance(value, str):
                        try:
                            from datetime import datetime
                            if 'T' in value:  # ISO格式
                                value = datetime.fromisoformat(value).date()
                            else:  # 简单日期格式
                                value = datetime.strptime(value, '%Y-%m-%d').date()
                            print(f"DEBUG: 日期字段 {key} 转换后: {value}")
                        except Exception as date_error:
                            print(f"DEBUG: 日期解析失败，跳过字段 {key}: {date_error}")
                            continue  # 跳过无法解析的日期

                try:
                    setattr(equipment, key, value)
                    restored_count += 1
                    print(f"DEBUG: 成功设置字段 {key} = {value}")
                except Exception as set_error:
                    print(f"DEBUG: 设置字段失败 {key}: {set_error}")
            else:
                print(f"DEBUG: 跳过字段 {key} (不在支持列表或设备无此属性)")

        print(f"DEBUG: 总共恢复了 {restored_count} 个字段")

        if restored_count == 0:
            print(f"DEBUG: 没有字段被恢复，但仍然认为回滚成功（可能是空操作）")
            # 即使没有字段恢复，也认为回滚成功，避免阻止回滚日志的创建
            return True

        print(f"DEBUG: 准备提交数据库更改")
        db.commit()
        print(f"DEBUG: 数据库提交成功，回滚操作完成")
        return True

    except Exception as e:
        print(f"DEBUG: 回滚操作异常: {type(e).__name__}: {e}")
        import traceback
        print(f"DEBUG: 异常堆栈: {traceback.format_exc()}")
        db.rollback()
        return False


def _rollback_calibration_operation(db: Session, original_log: AuditLog) -> bool:
    """回滚检定操作"""
    try:
        if not original_log.equipment_id or not original_log.old_value:
            return False

        equipment = db.query(Equipment).filter(Equipment.id == original_log.equipment_id).first()
        if not equipment:
            return False

        # 解析检定相关的旧值
        old_data = json.loads(original_log.old_value) if original_log.old_value else {}

        # 恢复检定信息
        calibration_fields = ['calibration_date', 'valid_until', 'current_calibration_result',
                            'calibration_method', 'certificate_number', 'verification_agency']

        for field in calibration_fields:
            if field in old_data:
                field_value = old_data[field]
                if field_value and field in ['calibration_date', 'valid_until']:
                    from datetime import date
                    if isinstance(field_value, str):
                        field_value = datetime.fromisoformat(field_value).date()
                setattr(equipment, field, field_value)

        db.commit()
        return True

    except Exception:
        db.rollback()
        return False


def cleanup_old_audit_logs(db: Session, days: int = 365) -> int:
    """清理指定天数之前的��作日志"""
    from datetime import timedelta

    cutoff_date = datetime.now() - timedelta(days=days)

    # 删除超过指定天数的日志（保留重要的回滚记录）
    deleted_count = db.query(AuditLog).filter(
        and_(
            AuditLog.created_at < cutoff_date,
            AuditLog.is_rollback == False  # 保留回滚记录以便追踪
        )
    ).delete(synchronize_session=False)

    db.commit()
    return deleted_count


def get_audit_statistics(db: Session, current_user_id: Optional[int] = None,
                        is_admin: bool = False) -> Dict[str, Any]:
    """获取操作日志统计信息"""

    base_query = db.query(AuditLog)

    # 简化权限控制
    if not is_admin and current_user_id:
        base_query = base_query.filter(AuditLog.user_id == current_user_id)

    total_logs = base_query.count()

    # 按操作类型统计
    operation_stats = {}
    for op_type in ['equipment', 'calibration', 'attachment', 'user', 'system']:
        count = base_query.filter(AuditLog.operation_type == op_type).count()
        operation_stats[op_type] = count

    # 按动作统计
    action_stats = {}
    actions = ['创建', '更新', '删除', '检定', '状态变更', '回滚']
    for action in actions:
        count = base_query.filter(AuditLog.action == action).count()
        if count > 0:
            action_stats[action] = count

    # 回滚操作统计
    rollback_count = base_query.filter(AuditLog.is_rollback == True).count()

    # 最近7天的操作趋势
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_logs = base_query.filter(AuditLog.created_at >= seven_days_ago).count()

    return {
        "total_logs": total_logs,
        "operation_stats": operation_stats,
        "action_stats": action_stats,
        "rollback_count": rollback_count,
        "recent_logs": recent_logs
    }
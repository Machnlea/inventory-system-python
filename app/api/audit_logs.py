from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Any
from datetime import date, datetime
import json

from app.db.database import get_db
from app.schemas.schemas import (
    PaginatedAuditLog, AuditLogRollback,
    AuditLogHistory, AuditLogCreate, AuditLogResponse
)
from app.api.auth import get_current_admin_user, get_current_user
from app.models.models import AuditLog as AuditLogModel, User, Equipment
from app.crud.audit_logs import (
    create_audit_log, get_audit_logs, get_audit_log_by_id,
    get_equipment_audit_logs, rollback_operation, get_operation_history,
    get_audit_statistics, cleanup_old_audit_logs,
    get_user_authorized_equipment_ids, has_equipment_permission
)

router = APIRouter()


@router.get("/", response_model=PaginatedAuditLog)
def get_audit_logs_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    equipment_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    is_rollback: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取操作日志列表
    - 管理员可查看全部日志
    - 普通用户只能查看授权设备的日志
    """
    # 转换日期为datetime
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

    items, total = get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        equipment_id=equipment_id,
        action=action,
        operation_type=operation_type,
        start_date=start_datetime,
        end_date=end_datetime,
        is_rollback=is_rollback,
        current_user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    
    # 构建响应数据，为每个日志项单独查询用户和设备信息
    response_items = []
    for item in items:
        # 查询用户信息
        user_data = None
        if item.user_id:
            try:
                user = db.query(User).filter(User.id == item.user_id).first()
                if user:
                    user_data = {
                        "id": user.id,
                        "username": user.username,
                        "is_admin": user.is_admin
                    }
            except Exception as e:
                print(f"ERROR: 查询用户ID {item.user_id} 时出错: {e}")
        
        # 查询设备信息
        equipment_data = None
        if item.equipment_id:
            try:
                equipment = db.query(Equipment).filter(Equipment.id == item.equipment_id).first()
                if equipment:
                    equipment_data = {
                        "id": equipment.id,
                        "internal_id": equipment.internal_id,
                        "name": equipment.name
                    }
            except Exception as e:
                print(f"ERROR: 查询设备ID {item.equipment_id} 时出错: {e}")

        # 格式化时间，确保包含时区信息
        created_at_str = item.created_at.isoformat() + 'Z' if item.created_at else None

        response_item = {
            "id": item.id,
            "user_id": item.user_id,
            "equipment_id": item.equipment_id,
            "action": item.action,
            "description": item.description,
            "old_value": item.old_value,
            "new_value": item.new_value,
            "operation_type": item.operation_type,
            "target_table": item.target_table,
            "target_id": item.target_id,
            "parent_log_id": item.parent_log_id,
            "rollback_log_id": item.rollback_log_id,
            "is_rollback": item.is_rollback,
            "rollback_reason": item.rollback_reason,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "created_at": created_at_str,
            "user": user_data,
            "equipment": equipment_data
        }
        response_items.append(response_item)

    return {
        "items": response_items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/history/{log_id}")
def get_operation_history_api(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取操作的历史记录（包括回滚记录）"""
    history = get_operation_history(db, log_id, current_user.id, current_user.is_admin)

    if not history:
        raise HTTPException(status_code=404, detail="操作日志不存在或无权限访问")

    # 转换为响应模型，避免循环引用
    original_log = history["original_log"]
    rollback_logs = history["rollback_logs"]

    # 获取用户和设备信息，避免循环引用
    user_ids = set()
    equipment_ids = set()

    user_ids.add(original_log.user_id)
    if original_log.equipment_id:
        equipment_ids.add(original_log.equipment_id)

    for log in rollback_logs:
        user_ids.add(log.user_id)
        if log.equipment_id:
            equipment_ids.add(log.equipment_id)

    users = {user.id: user for user in db.query(User).filter(User.id.in_(list(user_ids))).all()} if user_ids else {}
    equipments = {eq.id: eq for eq in db.query(Equipment).filter(Equipment.id.in_(list(equipment_ids))).all()} if equipment_ids else {}

    # 手动序列化原始日志
    original_user = users.get(original_log.user_id)
    original_equipment = equipments.get(original_log.equipment_id) if original_log.equipment_id else None

    serialized_original_log = {
        "id": original_log.id,
        "user_id": original_log.user_id,
        "equipment_id": original_log.equipment_id,
        "action": original_log.action,
        "description": original_log.description,
        "old_value": original_log.old_value,
        "new_value": original_log.new_value,
        "operation_type": original_log.operation_type,
        "target_table": original_log.target_table,
        "target_id": original_log.target_id,
        "parent_log_id": original_log.parent_log_id,
        "rollback_log_id": original_log.rollback_log_id,
        "is_rollback": original_log.is_rollback,
        "rollback_reason": original_log.rollback_reason,
        "ip_address": original_log.ip_address,
        "user_agent": original_log.user_agent,
        "created_at": original_log.created_at,
        "user": {
            "id": original_user.id,
            "username": original_user.username,
            "is_admin": original_user.is_admin
        } if original_user else None,
        "equipment": {
            "id": original_equipment.id,
            "internal_id": original_equipment.internal_id,
            "name": original_equipment.name
        } if original_equipment else None
    }

    # 手动序列化回滚日志
    serialized_rollback_logs = []
    for log in rollback_logs:
        user = users.get(log.user_id)
        equipment = equipments.get(log.equipment_id) if log.equipment_id else None

        serialized_log = AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            equipment_id=log.equipment_id,
            action=log.action,
            description=log.description,
            old_value=log.old_value,
            new_value=log.new_value,
            operation_type=log.operation_type,
            target_table=log.target_table,
            target_id=log.target_id,
            parent_log_id=log.parent_log_id,
            rollback_log_id=log.rollback_log_id,
            is_rollback=log.is_rollback,
            rollback_reason=log.rollback_reason,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
            user={
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin
            } if user else None,
            equipment={
                "id": equipment.id,
                "internal_id": equipment.internal_id,
                "name": equipment.name
            } if equipment else None
        )
        serialized_rollback_logs.append(serialized_log)

    return AuditLogHistory(
        original_log=serialized_original_log,
        rollback_logs=serialized_rollback_logs,
        current_state=history["current_state"]
    )


@router.post("/rollback", response_model=AuditLogResponse)
def rollback_operation_api(
    rollback_data: AuditLogRollback,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    回滚操作
    - 管理员可回滚任何操作
    - 普通用户只能回滚自己的操作
    """
    print(f"DEBUG API: 收到回滚请求，log_id={rollback_data.log_id}, user_id={current_user.id}, is_admin={current_user.is_admin}")
    
    # 获取客户端IP地址
    client_ip = request.client.host if request.client else None

    rollback_log = rollback_operation(
        db=db,
        rollback_data=rollback_data,
        current_user_id=current_user.id,
        is_admin=current_user.is_admin,
        ip_address=client_ip
    )

    if not rollback_log:
        print(f"DEBUG API: 回滚操作失败，返回None")
        raise HTTPException(
            status_code=400,
            detail="回滚失败：操作不存在、已回滚过或无权限操作"
        )

    # 手动获取用户和设备信息，避免循环引用
    user = db.query(User).filter(User.id == rollback_log.user_id).first() if rollback_log.user_id else None
    equipment = db.query(Equipment).filter(Equipment.id == rollback_log.equipment_id).first() if rollback_log.equipment_id else None

    # 返回响应模型，避免循环引用
    return AuditLogResponse(
        id=rollback_log.id,
        user_id=rollback_log.user_id,
        equipment_id=rollback_log.equipment_id,
        action=rollback_log.action,
        description=rollback_log.description,
        old_value=rollback_log.old_value,
        new_value=rollback_log.new_value,
        operation_type=rollback_log.operation_type,
        target_table=rollback_log.target_table,
        target_id=rollback_log.target_id,
        parent_log_id=rollback_log.parent_log_id,
        rollback_log_id=rollback_log.rollback_log_id,
        is_rollback=rollback_log.is_rollback,
        rollback_reason=rollback_log.rollback_reason,
        ip_address=rollback_log.ip_address,
        user_agent=rollback_log.user_agent,
        created_at=rollback_log.created_at,
        user={
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        } if user else None,
        equipment={
            "id": equipment.id,
            "internal_id": equipment.internal_id,
            "name": equipment.name
        } if equipment else None
    )


@router.get("/statistics")
def get_audit_statistics_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取操作日志统计信息"""
    return get_audit_statistics(db, current_user.id, current_user.is_admin)


@router.get("/users")
def get_audit_users_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取有操作记录的用户列表
    - 管理员可查看全部用户
    - 普通用户只能看到与授权设备相关的用户
    """

    if current_user.is_admin:
        # 管理员可以查看所有有操作记录的用户
        users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).distinct().all()
    else:
        # 普通用户只能看到与授权设备相关的用户
        authorized_equipments = get_user_authorized_equipment_ids(db, current_user.id)
        equipment_ids = [eq[2] for eq in authorized_equipments if len(eq) > 2]

        if equipment_ids:
            users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).filter(
                or_(
                    AuditLogModel.equipment_id.in_(equipment_ids),
                    AuditLogModel.equipment_id == None
                )
            ).distinct().all()
        else:
            # 如果用户没有任何授权设备，只能看到系统级操作的用户
            users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).filter(
                AuditLogModel.equipment_id == None
            ).distinct().all()

    return [{"id": user.id, "username": user.username, "is_admin": user.is_admin} for user in users]


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log_by_id_api(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """根据ID获取操作日志详情"""
    log = get_audit_log_by_id(
        db, log_id, current_user.id, current_user.is_admin
    )

    if not log:
        raise HTTPException(status_code=404, detail="操作日志不存在")

    # 手动获取用户和设备信息，避免循环引用
    user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
    equipment = db.query(Equipment).filter(Equipment.id == log.equipment_id).first() if log.equipment_id else None

    # 返回响应模型，避免循环引用
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        equipment_id=log.equipment_id,
        action=log.action,
        description=log.description,
        old_value=log.old_value,
        new_value=log.new_value,
        operation_type=log.operation_type,
        target_table=log.target_table,
        target_id=log.target_id,
        parent_log_id=log.parent_log_id,
        rollback_log_id=log.rollback_log_id,
        is_rollback=log.is_rollback,
        rollback_reason=log.rollback_reason,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
        user={
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        } if user else None,
        equipment={
            "id": equipment.id,
            "internal_id": equipment.internal_id,
            "name": equipment.name
        } if equipment else None
    )


@router.post("/cleanup")
def cleanup_audit_logs_api(
    days: int = Query(365, ge=30, le=3650),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    手动清理操作日志
    - 仅管理员可用
    - 默认清理365天前的日志
    """
    cleaned_count = cleanup_old_audit_logs(db, days)

    return {
        "message": f"已清理 {cleaned_count} 条超过 {days} 天的操作日志",
        "cleaned_count": cleaned_count,
        "days": days
    }


def log_equipment_operation(
    db: Session,
    user_id: int,
    equipment_id: int,
    action: str,
    description: str,
    old_data: Optional[dict] = None,
    new_data: Optional[dict] = None,
    operation_type: str = "equipment",
    request: Optional[Request] = None
) -> AuditLogModel:
    """
    记录设备操作日志的辅助函数
    """
    # 获取客户端信息
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    # 转换数据为JSON字符串
    old_value = json.dumps(old_data, ensure_ascii=False, default=str) if old_data else None
    new_value = json.dumps(new_data, ensure_ascii=False, default=str) if new_data else None

    # 获取设备信息用于确定target_table和target_id
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    audit_log_data = AuditLogCreate(
        user_id=user_id,
        equipment_id=equipment_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
        operation_type=operation_type,
        target_table="equipments",
        target_id=equipment_id,
        user_agent=user_agent
    )

    return create_audit_log(db, audit_log_data, client_ip)


def log_system_operation(
    db: Session,
    user_id: int,
    action: str,
    description: str,
    details: Optional[dict] = None,
    request: Optional[Request] = None
) -> AuditLogModel:
    """
    记录系统操作日志的辅助函数
    """
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    new_value = json.dumps(details, ensure_ascii=False, default=str) if details else None

    audit_log_data = AuditLogCreate(
        user_id=user_id,
        action=action,
        description=description,
        new_value=new_value,
        operation_type="system",
        user_agent=user_agent
    )

    return create_audit_log(db, audit_log_data, client_ip)
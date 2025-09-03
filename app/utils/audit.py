"""
审计日志工具函数
处理系统操作的审计日志记录
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    description: str,
    equipment_id: Optional[int] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None
) -> AuditLog:
    """
    记录审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        action: 操作类型
        description: 操作描述
        equipment_id: 相关设备ID（可选）
        old_value: 旧值（可选）
        new_value: 新值（可选）
    
    Returns:
        创建的审计日志记录
    """
    
    audit_log = AuditLog(
        user_id=user_id,
        equipment_id=equipment_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log


def log_equipment_action(
    db: Session,
    user_id: int,
    equipment_id: int,
    action: str,
    description: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None
) -> AuditLog:
    """
    记录设备相关的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        equipment_id: 设备ID
        action: 操作类型
        description: 操作描述
        old_value: 旧值（可选）
        new_value: 新值（可选）
    
    Returns:
        创建的审计日志记录
    """
    return log_audit(
        db=db,
        user_id=user_id,
        equipment_id=equipment_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value
    )


def log_calibration_action(
    db: Session,
    user_id: int,
    equipment_id: int,
    calibration_result: str,
    calibration_date: str,
    valid_until: str
) -> AuditLog:
    """
    记录检定相关的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        equipment_id: 设备ID
        calibration_result: 检定结果
        calibration_date: 检定日期
        valid_until: 有效期至
    
    Returns:
        创建的审计日志记录
    """
    return log_equipment_action(
        db=db,
        user_id=user_id,
        equipment_id=equipment_id,
        action="检定信息更新",
        description=f"更新设备检定信息：结果={calibration_result}，检定日期={calibration_date}，有效期至={valid_until}",
        new_value=f"检定结果: {calibration_result}, 检定日期: {calibration_date}, 有效期至: {valid_until}"
    )


def log_status_change(
    db: Session,
    user_id: int,
    equipment_id: int,
    old_status: str,
    new_status: str,
    reason: Optional[str] = None
) -> AuditLog:
    """
    记录设备状态变更的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        equipment_id: 设备ID
        old_status: 原状态
        new_status: 新状态
        reason: 变更原因（可选）
    
    Returns:
        创建的审计日志记录
    """
    description = f"设备状态从'{old_status}'变更为'{new_status}'"
    if reason:
        description += f"，原因：{reason}"
    
    return log_equipment_action(
        db=db,
        user_id=user_id,
        equipment_id=equipment_id,
        action="状态变更",
        description=description,
        old_value=old_status,
        new_value=new_status
    )


def log_attachment_action(
    db: Session,
    user_id: int,
    equipment_id: int,
    action: str,
    filename: str,
    attachment_type: Optional[str] = None
) -> AuditLog:
    """
    记录附件相关的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        equipment_id: 设备ID
        action: 操作类型（上传/删除/下载等）
        filename: 文件名
        attachment_type: 附件类型（可选）
    
    Returns:
        创建的审计日志记录
    """
    description = f"{action}附件：{filename}"
    if attachment_type:
        description += f" (类型：{attachment_type})"
    
    return log_equipment_action(
        db=db,
        user_id=user_id,
        equipment_id=equipment_id,
        action=f"附件{action}",
        description=description,
        new_value=filename
    )


def log_batch_operation(
    db: Session,
    user_id: int,
    action: str,
    description: str,
    affected_count: int,
    equipment_ids: Optional[list] = None
) -> AuditLog:
    """
    记录批量操作的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        action: 操作类型
        description: 操作描述
        affected_count: 影响的记录数
        equipment_ids: 相关设备ID列表（可选）
    
    Returns:
        创建的审计日志记录
    """
    full_description = f"{description}，共影响 {affected_count} 条记录"
    if equipment_ids:
        full_description += f"，设备ID: {', '.join(map(str, equipment_ids[:10]))}"
        if len(equipment_ids) > 10:
            full_description += f" 等{len(equipment_ids)}个设备"
    
    return log_audit(
        db=db,
        user_id=user_id,
        action=action,
        description=full_description,
        new_value=f"影响记录数: {affected_count}"
    )


def log_system_action(
    db: Session,
    user_id: int,
    action: str,
    description: str,
    details: Optional[str] = None
) -> AuditLog:
    """
    记录系统级操作的审计日志
    
    Args:
        db: 数据库会话
        user_id: 操作用户ID
        action: 操作类型
        description: 操作描述
        details: 详细信息（可选）
    
    Returns:
        创建的审计日志记录
    """
    return log_audit(
        db=db,
        user_id=user_id,
        action=action,
        description=description,
        new_value=details
    )
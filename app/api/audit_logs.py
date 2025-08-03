from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.database import get_db
from app.schemas.schemas import AuditLog, PaginatedAuditLog
from app.api.auth import get_current_admin_user
from app.models.models import AuditLog as AuditLogModel, User, Equipment

router = APIRouter()

@router.get("/", response_model=PaginatedAuditLog)
def get_audit_logs(skip: int = 0, limit: int = 100,
                  user_id: Optional[int] = Query(None),
                  action: Optional[str] = Query(None),
                  start_date: Optional[date] = Query(None),
                  end_date: Optional[date] = Query(None),
                  db: Session = Depends(get_db),
                  current_user = Depends(get_current_admin_user)):
    """获取操作日志（仅管理员）"""
    query = db.query(AuditLogModel).join(User, AuditLogModel.user_id == User.id)
    
    # 应用筛选条件
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    
    if action:
        query = query.filter(AuditLogModel.action == action)
    
    if start_date:
        query = query.filter(AuditLogModel.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLogModel.created_at <= end_date)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据
    items = query.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/equipment/{equipment_id}", response_model=List[AuditLog])
def get_equipment_audit_logs(equipment_id: int,
                           db: Session = Depends(get_db),
                           current_user = Depends(get_current_admin_user)):
    """获取特定设备的操作日志"""
    return db.query(AuditLogModel).filter(
        AuditLogModel.equipment_id == equipment_id
    ).order_by(AuditLogModel.created_at.desc()).all()

@router.get("/users")
def get_audit_users(db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    """获取有操作记录的用户列表"""
    users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).distinct().all()
    return [{"id": user.id, "username": user.username} for user in users]

def create_audit_log(db: Session, user_id: int, equipment_id: int = None,
                    action: str = "", description: str = "",
                    old_value: str = None, new_value: str = None):
    """创建操作日志的辅助函数"""
    audit_log = AuditLogModel(
        user_id=user_id,
        equipment_id=equipment_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value
    )
    db.add(audit_log)
    db.commit()
    return audit_log
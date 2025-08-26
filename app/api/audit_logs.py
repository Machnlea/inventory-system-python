from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Any
from datetime import date, datetime, timedelta
from app.db.database import get_db
from app.schemas.schemas import AuditLog, PaginatedAuditLog
from app.api.auth import get_current_admin_user, get_current_user
from app.models.models import AuditLog as AuditLogModel, User, Equipment

router = APIRouter()

@router.get("/", response_model=PaginatedAuditLog)
def get_audit_logs(skip: int = 0, limit: int = 100,
                  user_id: Optional[int] = Query(None),
                  action: Optional[str] = Query(None),
                  start_date: Optional[date] = Query(None),
                  end_date: Optional[date] = Query(None),
                  db: Session = Depends(get_db),
                  current_user = Depends(get_current_user)):
    """获取操作日志（管理员可查看全部，普通用户只能查看授权设备的日志）"""
    query = db.query(AuditLogModel).join(User, AuditLogModel.user_id == User.id).outerjoin(Equipment, AuditLogModel.equipment_id == Equipment.id)
    
    # 权限控制：普通用户只能查看授权设备的日志
    if not current_user.is_admin:
        from sqlalchemy import select
        from app.models.models import UserCategory
        
        # 获取用户授权的设备类别
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        
        # 只显示授权类别下设备的日志，以及无关联设备的系统级日志
        query = query.filter(
            (Equipment.category_id.in_(authorized_categories)) | 
            (AuditLogModel.equipment_id == None)
        )
    
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
                           current_user = Depends(get_current_user)):
    """获取特定设备的操作日志（管理员可查看全部，普通用户只能查看授权设备）"""
    
    # 检查设备是否存在
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 权限检查：普通用户只能查看授权类别的设备日志
    if not current_user.is_admin:
        from sqlalchemy import select
        from app.models.models import UserCategory
        
        # 获取用户授权的设备类别
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        
        # 检查设备是否在用户授权类别中
        is_authorized = db.query(authorized_categories.filter(
            UserCategory.category_id == equipment.category_id
        ).exists()).scalar()
        
        if not is_authorized:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="无权限查看此设备的日志")
    
    return db.query(AuditLogModel).filter(
        AuditLogModel.equipment_id == equipment_id
    ).order_by(AuditLogModel.created_at.desc()).all()

@router.get("/users")
def get_audit_users(db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    """获取有操作记录的用户列表（管理员可查看全部，普通用户只能看到与授权设备相关的用户）"""
    
    if current_user.is_admin:
        # 管理员可以查看所有有操作记录的用户
        users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).distinct().all()
    else:
        # 普通用户只能看到与授权设备相关的用户
        from sqlalchemy import select
        from app.models.models import UserCategory
        
        # 获取用户授权的设备类别
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        
        # 查找与授权设备或系统级操作相关的用户
        users = db.query(User).join(AuditLogModel, User.id == AuditLogModel.user_id).outerjoin(
            Equipment, AuditLogModel.equipment_id == Equipment.id
        ).filter(
            (Equipment.category_id.in_(authorized_categories)) | 
            (AuditLogModel.equipment_id == None)
        ).distinct().all()
    
    return [{"id": user.id, "username": user.username} for user in users]

@router.post("/cleanup")
def cleanup_audit_logs(db: Session = Depends(get_db),
                      current_user = Depends(get_current_admin_user)):
    """手动清理超过一年的操作日志"""
    one_year_ago = datetime.now() - timedelta(days=365)
    
    # 查询超过一年的日志数量
    old_logs_count = db.query(AuditLogModel).filter(
        AuditLogModel.created_at < one_year_ago
    ).count()
    
    if old_logs_count > 0:
        # 删除超过一年的日志
        db.query(AuditLogModel).filter(
            AuditLogModel.created_at < one_year_ago
        ).delete(synchronize_session=False)
        db.commit()
        
        return {
            "message": f"已清理 {old_logs_count} 条超过一年的操作日志",
            "cleaned_count": old_logs_count
        }
    else:
        return {
            "message": "没有需要清理的操作日志",
            "cleaned_count": 0
        }

def cleanup_old_audit_logs(db: Session):
    """清理超过一年的操作日志"""
    one_year_ago = datetime.now() - timedelta(days=365)
    
    # 查询超过一年的日志
    old_logs = db.query(AuditLogModel).filter(
        AuditLogModel.created_at < one_year_ago
    ).all()
    
    if old_logs:
        # 删除超过一年的日志
        count = len(old_logs)
        db.query(AuditLogModel).filter(
            AuditLogModel.created_at < one_year_ago
        ).delete(synchronize_session=False)
        db.commit()
        print(f"已清理 {count} 条超过一年的操作日志")

def create_audit_log(db: Session, user_id: Any, equipment_id: Optional[Any] = None,
                    action: str = "", description: str = "",
                    old_value: Optional[str] = None, new_value: Optional[str] = None):
    """创建操作日志的辅助函数"""
    # 先清理超过一年的日志
    cleanup_old_audit_logs(db)
    
    # 确保user_id和equipment_id是int类型
    user_id_int = int(user_id) if user_id is not None else None
    equipment_id_int = int(equipment_id) if equipment_id is not None else None
    
    audit_log = AuditLogModel(
        user_id=user_id_int,
        equipment_id=equipment_id_int,
        action=action or "未知操作",
        description=description or "无描述",
        old_value=old_value,
        new_value=new_value
    )
    db.add(audit_log)
    db.commit()
    return audit_log
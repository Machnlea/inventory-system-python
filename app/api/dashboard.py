from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from datetime import date, timedelta
from calendar import monthrange
from app.db.database import get_db
from app.crud import equipment
from app.schemas.schemas import DashboardStats
from app.api.auth import get_current_user
from app.models.models import Equipment, EquipmentCategory

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db),
                       current_user = Depends(get_current_user)):
    """获取仪表盘统计数据"""
    
    # 计算本月的日期范围
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)
    
    # 本月待检设备数量和列表
    monthly_due_equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=current_month_start, end_date=current_month_end,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    monthly_due_count = len(monthly_due_equipments)
    
    # 已超期未检设备数量
    overdue_equipments = equipment.get_overdue_equipments(
        db, user_id=current_user.id, is_admin=current_user.is_admin
    )
    overdue_count = len(overdue_equipments)
    
    # 停用状态设备总数
    inactive_query = db.query(Equipment).filter(Equipment.status.in_(["停用", "报废"]))
    if not current_user.is_admin:
        from app.crud import users
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        inactive_query = inactive_query.filter(Equipment.category_id.in_(authorized_categories))
    
    inactive_count = inactive_query.count()
    
    # 设备类别分布
    category_query = db.query(
        EquipmentCategory.name,
        func.count(Equipment.id).label('count')
    ).join(Equipment).group_by(EquipmentCategory.id, EquipmentCategory.name)
    
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        category_query = category_query.filter(Equipment.category_id.in_(authorized_categories))
    
    category_distribution = [
        {"name": name, "count": count} 
        for name, count in category_query.all()
    ]
    
    return DashboardStats(
        monthly_due_count=monthly_due_count,
        overdue_count=overdue_count,
        inactive_count=inactive_count,
        category_distribution=category_distribution
    )

@router.get("/monthly-due-equipments")
def get_monthly_due_equipments(db: Session = Depends(get_db),
                              current_user = Depends(get_current_user)):
    """获取当月待检设备列表"""
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)
    
    equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=current_month_start, end_date=current_month_end,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    return equipments
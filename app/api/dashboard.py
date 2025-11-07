from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from datetime import date, timedelta
from calendar import monthrange
from app.db.database import get_db
from app.crud import equipment
from app.schemas.schemas import DashboardStats
from app.api.auth import get_current_user
from app.models.models import Equipment, EquipmentCategory, Department
from app.core.cache import cached, invalidate_cache_pattern
from app.core.cache_config import CacheConfig, CacheInvalidationRules

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
@cached(
    ttl=CacheConfig.get_cache_ttl_for_api("dashboard_stats"),
    key_prefix=CacheConfig.get_cache_prefix_for_api("dashboard_stats")
)
def get_dashboard_stats(db: Session = Depends(get_db),
                       current_user = Depends(get_current_user)):
    """获取仪表盘统计数据 - 支持缓存"""
    
    # 设备总数
    total_equipment_count = equipment.get_equipments_count(
        db, user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 在用设备数量
    active_query = db.query(Equipment).filter(Equipment.status == "在用")
    if not current_user.is_admin:
        from app.crud import users
        from app.models.models import UserEquipmentPermission
        from sqlalchemy import and_

        # 修复权限冲突：需要同时匹配category_id和equipment_name
        equipment_subquery = db.query(
            Equipment.id
        ).join(
            UserEquipmentPermission,
            and_(
                Equipment.category_id == UserEquipmentPermission.category_id,
                Equipment.name == UserEquipmentPermission.equipment_name,
                UserEquipmentPermission.user_id == current_user.id
            )
        ).subquery()

        authorized_equipment_ids = select(equipment_subquery.c.id)
        active_query = active_query.filter(Equipment.id.in_(authorized_equipment_ids))

    active_equipment_count = active_query.count()
    
    # 计算待检设备的日期范围：从当前日期到月底
    today = date.today()
    _, last_day = monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)
    
    # 本月待检设备数量和列表：从今天到月底
    monthly_due_equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=today, end_date=current_month_end,
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
        from app.models.models import UserEquipmentPermission
        # 修复权限冲突：需要同时匹配category_id和equipment_name
        equipment_subquery = db.query(
            Equipment.id
        ).join(
            UserEquipmentPermission,
            and_(
                Equipment.category_id == UserEquipmentPermission.category_id,
                Equipment.name == UserEquipmentPermission.equipment_name,
                UserEquipmentPermission.user_id == current_user.id
            )
        ).subquery()

        authorized_equipment_ids = select(equipment_subquery.c.id)
        inactive_query = inactive_query.filter(Equipment.id.in_(authorized_equipment_ids))
    
    inactive_count = inactive_query.count()
    
    # 设备具体器具分布（只统计在用设备）
    equipment_query = db.query(
        Equipment.name,
        func.count(Equipment.id).label('count')
    ).filter(Equipment.status == "在用").group_by(Equipment.name)
    
    if not current_user.is_admin:
        from app.models.models import UserEquipmentPermission
        # 修复权限冲突：需要同时匹配category_id和equipment_name
        equipment_subquery = db.query(
            Equipment.id
        ).join(
            UserEquipmentPermission,
            and_(
                Equipment.category_id == UserEquipmentPermission.category_id,
                Equipment.name == UserEquipmentPermission.equipment_name,
                UserEquipmentPermission.user_id == current_user.id
            )
        ).subquery()

        authorized_equipment_ids = select(equipment_subquery.c.id)
        equipment_query = equipment_query.filter(Equipment.id.in_(authorized_equipment_ids))
    
    category_distribution = [
        {"name": name, "count": count} 
        for name, count in equipment_query.all()
    ]
    
    # 部门分布（只统计在用设备）
    department_query = db.query(
        Department.name,
        func.count(Equipment.id).label('count')
    ).join(Equipment).filter(Equipment.status == "在用").group_by(Department.id, Department.name)
    
    if not current_user.is_admin:
        from app.models.models import UserEquipmentPermission
        # 修复权限冲突：需要同时匹配category_id和equipment_name
        equipment_subquery = db.query(
            Equipment.id
        ).join(
            UserEquipmentPermission,
            and_(
                Equipment.category_id == UserEquipmentPermission.category_id,
                Equipment.name == UserEquipmentPermission.equipment_name,
                UserEquipmentPermission.user_id == current_user.id
            )
        ).subquery()

        authorized_equipment_ids = select(equipment_subquery.c.id)
        department_query = department_query.filter(Equipment.id.in_(authorized_equipment_ids))
    
    department_distribution = [
        {"name": name, "count": count} 
        for name, count in department_query.all()
    ]
    
    return DashboardStats(
        total_equipment_count=total_equipment_count,
        active_equipment_count=active_equipment_count,
        monthly_due_count=monthly_due_count,
        overdue_count=overdue_count,
        inactive_count=inactive_count,
        category_distribution=category_distribution,
        department_distribution=department_distribution
    )

@router.get("/monthly-due-equipments")
def get_monthly_due_equipments(db: Session = Depends(get_db),
                              current_user = Depends(get_current_user)):
    """获取当月待检设备列表"""
    today = date.today()
    _, last_day = monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)
    
    equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=today, end_date=current_month_end,
        user_id=current_user.id, is_admin=current_user.is_admin
    )

    return equipments

@router.post("/clear-cache")
def clear_dashboard_cache(current_user = Depends(get_current_user)):
    """清空仪表盘相关缓存"""
    try:
        patterns = CacheInvalidationRules.EQUIPMENT_CHANGE_PATTERNS
        cleared_count = 0

        for pattern in patterns:
            cleared_count += invalidate_cache_pattern(pattern)

        return {
            "success": True,
            "message": f"已清空 {cleared_count} 个缓存项",
            "cleared_patterns": patterns
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"清空缓存失败: {str(e)}"
        }

@router.get("/cache-stats")
def get_cache_statistics(current_user = Depends(get_current_user)):
    """获取缓存统计信息"""
    try:
        from app.core.cache import get_cache_stats
        from app.core.cache_config import cache_metrics

        redis_stats = get_cache_stats()
        metrics_stats = cache_metrics.get_stats()

        return {
            "cache_metrics": metrics_stats,
            "redis_info": redis_stats,
            "cache_configurations": CacheConfig.all_cache_configs()
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "获取缓存统计失败"
        }
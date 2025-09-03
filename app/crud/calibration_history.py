"""
检定历史记录 CRUD 操作
处理设备检定历史记录的增删改查功能
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import date, datetime

from app.models.models import CalibrationHistory, Equipment, User
from app.schemas.calibration import CalibrationHistoryCreate, CalibrationHistoryUpdate


def get_calibration_history(db: Session, history_id: int) -> Optional[CalibrationHistory]:
    """获取单个检定历史记录"""
    return db.query(CalibrationHistory).filter(CalibrationHistory.id == history_id).first()


def get_calibration_histories_by_equipment(
    db: Session, 
    equipment_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[CalibrationHistory]:
    """获取设备的检定历史记录列表"""
    return db.query(CalibrationHistory).filter(
        CalibrationHistory.equipment_id == equipment_id
    ).order_by(
        desc(CalibrationHistory.calibration_date)
    ).offset(skip).limit(limit).all()


def get_calibration_histories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    equipment_id: Optional[int] = None,
    calibration_method: Optional[str] = None,
    calibration_result: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[CalibrationHistory]:
    """获取检定历史记录列表（支持多种过滤条件）"""
    query = db.query(CalibrationHistory)
    
    # 设备过滤
    if equipment_id:
        query = query.filter(CalibrationHistory.equipment_id == equipment_id)
    
    # 检定方式过滤
    if calibration_method:
        query = query.filter(CalibrationHistory.calibration_method == calibration_method)
    
    # 检定结果过滤
    if calibration_result:
        query = query.filter(CalibrationHistory.calibration_result == calibration_result)
    
    # 日期范围过滤
    if start_date:
        query = query.filter(CalibrationHistory.calibration_date >= start_date)
    if end_date:
        query = query.filter(CalibrationHistory.calibration_date <= end_date)
    
    return query.order_by(
        desc(CalibrationHistory.created_at)
    ).offset(skip).limit(limit).all()


def get_latest_calibration_history(db: Session, equipment_id: int) -> Optional[CalibrationHistory]:
    """获取设备最新的检定历史记录"""
    return db.query(CalibrationHistory).filter(
        CalibrationHistory.equipment_id == equipment_id
    ).order_by(
        desc(CalibrationHistory.calibration_date)
    ).first()


def create_calibration_history(
    db: Session, 
    calibration_history: CalibrationHistoryCreate, 
    created_by_user_id: int
) -> CalibrationHistory:
    """创建检定历史记录"""
    db_history = CalibrationHistory(
        equipment_id=calibration_history.equipment_id,
        calibration_date=calibration_history.calibration_date,
        valid_until=calibration_history.valid_until,
        calibration_method=calibration_history.calibration_method,
        calibration_result=calibration_history.calibration_result,
        certificate_number=calibration_history.certificate_number,
        certificate_form=calibration_history.certificate_form,
        verification_result=calibration_history.verification_result,
        verification_agency=calibration_history.verification_agency,
        notes=calibration_history.notes,
        created_by=created_by_user_id
    )
    
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def update_calibration_history(
    db: Session, 
    history_id: int, 
    calibration_history: CalibrationHistoryUpdate
) -> Optional[CalibrationHistory]:
    """更新检定历史记录"""
    db_history = db.query(CalibrationHistory).filter(CalibrationHistory.id == history_id).first()
    
    if not db_history:
        return None
    
    update_data = calibration_history.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_history, field, value)
    
    db.commit()
    db.refresh(db_history)
    return db_history


def delete_calibration_history(db: Session, history_id: int) -> bool:
    """删除检定历史记录"""
    db_history = db.query(CalibrationHistory).filter(CalibrationHistory.id == history_id).first()
    
    if not db_history:
        return False
    
    db.delete(db_history)
    db.commit()
    return True


def get_calibration_statistics(db: Session) -> dict:
    """获取检定统计信息"""
    from sqlalchemy import func
    
    # 总检定记录数
    total_count = db.query(CalibrationHistory).count()
    
    # 按检定方式统计
    method_stats = db.query(
        CalibrationHistory.calibration_method,
        func.count(CalibrationHistory.id)
    ).group_by(CalibrationHistory.calibration_method).all()
    
    # 按检定结果统计
    result_stats = db.query(
        CalibrationHistory.calibration_result,
        func.count(CalibrationHistory.id)
    ).group_by(CalibrationHistory.calibration_result).all()
    
    # 近期检定统计（最近30天）
    from datetime import timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_count = db.query(CalibrationHistory).filter(
        CalibrationHistory.calibration_date >= thirty_days_ago
    ).count()
    
    return {
        "total_count": total_count,
        "method_distribution": {method: count for method, count in method_stats},
        "result_distribution": {result: count for result, count in result_stats},
        "recent_count": recent_count
    }


def get_calibration_due_soon(db: Session, days: int = 30) -> List[CalibrationHistory]:
    """获取即将到期的检定记录"""
    from datetime import timedelta
    
    due_date = date.today() + timedelta(days=days)
    
    # 获取每个设备最新的检定记录，且即将到期
    latest_histories = db.query(CalibrationHistory).filter(
        and_(
            CalibrationHistory.valid_until <= due_date,
            CalibrationHistory.valid_until >= date.today()
        )
    ).order_by(CalibrationHistory.valid_until).all()
    
    # 过滤出每个设备最新的记录
    equipment_latest = {}
    for history in latest_histories:
        if (history.equipment_id not in equipment_latest or 
            history.calibration_date > equipment_latest[history.equipment_id].calibration_date):
            equipment_latest[history.equipment_id] = history
    
    return list(equipment_latest.values())


def batch_create_calibration_histories(
    db: Session, 
    calibration_histories: List[CalibrationHistoryCreate], 
    created_by_user_id: int
) -> List[CalibrationHistory]:
    """批量创建检定历史记录"""
    db_histories = []
    
    for calibration_history in calibration_histories:
        db_history = CalibrationHistory(
            equipment_id=calibration_history.equipment_id,
            calibration_date=calibration_history.calibration_date,
            valid_until=calibration_history.valid_until,
            calibration_method=calibration_history.calibration_method,
            calibration_result=calibration_history.calibration_result,
            certificate_number=calibration_history.certificate_number,
            certificate_form=calibration_history.certificate_form,
            verification_result=calibration_history.verification_result,
            verification_agency=calibration_history.verification_agency,
            notes=calibration_history.notes,
            created_by=created_by_user_id
        )
        db_histories.append(db_history)
    
    db.add_all(db_histories)
    db.commit()
    
    for db_history in db_histories:
        db.refresh(db_history)
    
    return db_histories
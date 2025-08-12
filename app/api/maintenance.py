from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.db.database import get_db
from app.models.models import MaintenanceRecord, MaintenanceAttachment, User, Equipment
from app.schemas.maintenance import MaintenanceRecordCreate, MaintenanceRecordResponse, MaintenanceRecordUpdate
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_records(
    equipment_id: Optional[int] = Query(None, description="设备ID"),
    equipment_name: Optional[str] = Query(None, description="设备名称"),
    maintenance_type: Optional[str] = Query(None, description="维护类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="限制记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取维护记录列表"""
    query = db.query(MaintenanceRecord)
    
    if equipment_id:
        query = query.filter(MaintenanceRecord.equipment_id == equipment_id)
    
    if equipment_name:
        query = query.join(Equipment).filter(Equipment.name.contains(equipment_name))
    
    if maintenance_type:
        query = query.filter(MaintenanceRecord.maintenance_type == maintenance_type)
    
    if start_date:
        query = query.filter(MaintenanceRecord.maintenance_date >= start_date)
    
    if end_date:
        query = query.filter(MaintenanceRecord.maintenance_date <= end_date)
    
    # 按维护日期倒序排列
    query = query.order_by(MaintenanceRecord.maintenance_date.desc())
    
    records = query.offset(skip).limit(limit).all()
    return records

@router.get("/{record_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个维护记录"""
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="维护记录不存在")
    
    return record

@router.post("/", response_model=MaintenanceRecordResponse)
async def create_maintenance_record(
    record: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建维护记录"""
    # 验证设备是否存在
    equipment = db.query(Equipment).filter(Equipment.id == record.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 创建维护记录
    db_record = MaintenanceRecord(
        equipment_id=record.equipment_id,
        maintenance_type=record.maintenance_type,
        maintenance_date=record.maintenance_date,
        maintenance_person=record.maintenance_person,
        maintenance_company=record.maintenance_company,
        description=record.description,
        result=record.result,
        cost=record.cost,
        next_maintenance_date=record.next_maintenance_date,
        notes=record.notes,
        created_by=current_user.id
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return db_record

@router.put("/{record_id}", response_model=MaintenanceRecordResponse)
async def update_maintenance_record(
    record_id: int,
    record: MaintenanceRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新维护记录"""
    db_record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="维护记录不存在")
    
    # 更新字段
    update_data = record.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_record, field, value)
    
    db_record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_record)
    
    return db_record

@router.delete("/{record_id}")
async def delete_maintenance_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除维护记录"""
    db_record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="维护记录不存在")
    
    # 删除相关附件
    db.query(MaintenanceAttachment).filter(MaintenanceAttachment.maintenance_id == record_id).delete()
    
    # 删除维护记录
    db.delete(db_record)
    db.commit()
    
    return {"message": "维护记录已删除"}

@router.get("/equipment/{equipment_id}", response_model=List[MaintenanceRecordResponse])
async def get_equipment_maintenance_records(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定设备的维护记录"""
    # 验证设备是否存在
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    records = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.equipment_id == equipment_id
    ).order_by(MaintenanceRecord.maintenance_date.desc()).all()
    
    return records

@router.get("/stats/overview")
async def get_maintenance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取维护记录统计信息"""
    total_records = db.query(MaintenanceRecord).count()
    
    # 按维护类型统计
    type_stats = db.query(
        MaintenanceRecord.maintenance_type,
        db.func.count(MaintenanceRecord.id).label('count')
    ).group_by(MaintenanceRecord.maintenance_type).all()
    
    # 按月份统计最近6个月的维护记录
    from datetime import timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_stats = db.query(
        db.func.strftime('%Y-%m', MaintenanceRecord.maintenance_date).label('month'),
        db.func.count(MaintenanceRecord.id).label('count')
    ).filter(MaintenanceRecord.maintenance_date >= six_months_ago).group_by('month').all()
    
    # 即将到期的维护记录
    upcoming_maintenance = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.next_maintenance_date >= date.today(),
        MaintenanceRecord.next_maintenance_date <= date.today() + timedelta(days=30)
    ).count()
    
    return {
        "total_records": total_records,
        "type_stats": [{"type": stat[0], "count": stat[1]} for stat in type_stats],
        "monthly_stats": [{"month": stat[0], "count": stat[1]} for stat in monthly_stats],
        "upcoming_maintenance": upcoming_maintenance
    }
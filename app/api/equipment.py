from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, timedelta
from calendar import monthrange
import io
import pandas as pd
from urllib.parse import quote
from app.db.database import get_db
from app.crud import equipment
from app.schemas.schemas import Equipment, EquipmentCreate, EquipmentUpdate, EquipmentFilter, EquipmentSearch, PaginatedEquipment
from app.api.audit_logs import create_audit_log
from app.api.auth import get_current_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=PaginatedEquipment)
def read_equipments(skip: int = 0, limit: int = 999999,
                   sort_field: str = "next_calibration_date", 
                   sort_order: str = "asc",
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    return equipment.get_equipments_paginated(
        db, skip=skip, limit=limit, 
        sort_field=sort_field, sort_order=sort_order,
        user_id=current_user.id, is_admin=current_user.is_admin
    )

@router.post("/", response_model=Equipment)
def create_equipment(equipment_data: EquipmentCreate,
                    db: Session = Depends(get_db),
                    current_user = Depends(get_current_user)):
    # 检查用户是否有该设备类别的权限
    if not current_user.is_admin:
        from app.crud import users
        user_categories = users.get_user_categories(db, current_user.id)
        authorized_category_ids = [uc.category_id for uc in user_categories]
        if equipment_data.category_id not in authorized_category_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage this equipment category"
            )
    
    new_equipment = equipment.create_equipment(db=db, equipment=equipment_data)
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=new_equipment.id,
        action="创建",
        description=f"创建设备: {new_equipment.name} ({new_equipment.serial_number})"
    )
    
    return new_equipment

@router.get("/{equipment_id}", response_model=Equipment)
def read_equipment(equipment_id: int,
                  db: Session = Depends(get_db),
                  current_user = Depends(get_current_user)):
    db_equipment = equipment.get_equipment(
        db, equipment_id=equipment_id,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return db_equipment

@router.put("/{equipment_id}", response_model=Equipment)
def update_equipment(equipment_id: int, equipment_update: EquipmentUpdate,
                    db: Session = Depends(get_db),
                    current_user = Depends(get_current_user)):
    # 检查设备是否存在且用户有权限
    db_equipment = equipment.get_equipment(
        db, equipment_id=equipment_id,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # 记录更新前的状态
    old_status = db_equipment.status
    
    updated_equipment = equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
    
    # 记录操作日志
    changes = []
    if equipment_update.status and equipment_update.status != old_status:
        changes.append(f"状态从'{old_status}'改为'{equipment_update.status}'")
    
    description = f"更新设备: {updated_equipment.name} ({updated_equipment.serial_number})"
    if changes:
        description += f" - {', '.join(changes)}"
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=equipment_id,
        action="更新",
        description=description
    )
    
    return updated_equipment

@router.delete("/{equipment_id}")
def delete_equipment(equipment_id: int,
                    db: Session = Depends(get_db),
                    current_user = Depends(get_current_user)):
    # 检查设备是否存在且用户有权限
    db_equipment = equipment.get_equipment(
        db, equipment_id=equipment_id,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=equipment_id,
        action="删除",
        description=f"删除设备: {db_equipment.name} ({db_equipment.serial_number})"
    )
    
    success = equipment.delete_equipment(db, equipment_id=equipment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}

@router.post("/filter", response_model=PaginatedEquipment)
def filter_equipments(filters: EquipmentFilter, skip: int = 0, limit: int = 999999,
                     sort_field: str = "next_calibration_date", 
                     sort_order: str = "asc",
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_user)):
    return equipment.filter_equipments_paginated(
        db, filters=filters, skip=skip, limit=limit,
        sort_field=sort_field, sort_order=sort_order,
        user_id=current_user.id, is_admin=current_user.is_admin
    )

@router.get("/export/monthly-plan")
def export_monthly_plan(year: int, month: int,
                       db: Session = Depends(get_db),
                       current_user = Depends(get_current_user)):
    """导出月度检定计划"""
    # 计算月份的开始和结束日期
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    
    equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=start_date, end_date=end_date,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 转换为DataFrame
    data = []
    for eq in equipments:
        data.append({
            '部门': eq.department.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '检定周期': eq.calibration_cycle,
            '检定日期': eq.calibration_date.strftime('%Y-%m-%d'),
            '下次检定日期': eq.next_calibration_date.strftime('%Y-%m-%d'),
            '计量编号': eq.serial_number,
            '安装地点': eq.installation_location,
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date else '',
            '分度值': eq.scale_value or '',
            '检定方式': eq.calibration_method,
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{year}年{month}月检定计划', index=False)
    output.seek(0)
    
    filename = f"{year}年{month}月检定计划.xlsx"
    encoded_filename = quote(filename, safe='')
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.get("/export/yearly-plan")
def export_yearly_plan(year: int,
                      db: Session = Depends(get_db),
                      current_user = Depends(get_current_user)):
    """导出年度检定计划"""
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=start_date, end_date=end_date,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 转换为DataFrame
    data = []
    for eq in equipments:
        data.append({
            '部门': eq.department.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '检定周期': eq.calibration_cycle,
            '检定日期': eq.calibration_date.strftime('%Y-%m-%d'),
            '下次检定日期': eq.next_calibration_date.strftime('%Y-%m-%d'),
            '计量编号': eq.serial_number,
            '安装地点': eq.installation_location,
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date else '',
            '分度值': eq.scale_value or '',
            '检定方式': eq.calibration_method,
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'{year}年检定计划', index=False)
    output.seek(0)
    
    filename = f"{year}年检定计划.xlsx"
    encoded_filename = quote(filename, safe='')
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/export/filtered")
def export_filtered_equipments(filters: EquipmentFilter,
                              db: Session = Depends(get_db),
                              current_user = Depends(get_current_user)):
    """根据筛选条件导出设备数据"""
    equipments = equipment.filter_equipments(
        db, filters=filters, skip=0, limit=10000,  # 导出时不限制数量
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 转换为DataFrame
    data = []
    for eq in equipments:
        data.append({
            '部门': eq.department.name,
            '设备类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '检定周期': eq.calibration_cycle,
            '检定日期': eq.calibration_date.strftime('%Y-%m-%d'),
            '下次检定日期': eq.next_calibration_date.strftime('%Y-%m-%d'),
            '计量编号': eq.serial_number,
            '安装地点': eq.installation_location,
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date else '',
            '分度值': eq.scale_value or '',
            '检定方式': eq.calibration_method,
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date else '',
            '备注': eq.notes,
            '创建时间': eq.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            '更新时间': eq.updated_at.strftime('%Y-%m-%d %H:%M:%S') if eq.updated_at else ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账', index=False)
    output.seek(0)
    
    filename = f"设备台账_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename, safe='')
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/batch/update-calibration")
def batch_update_calibration(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量更新设备检定日期"""
    equipment_ids = request_data.get('equipment_ids', [])
    calibration_date = request_data.get('calibration_date')
    
    if not equipment_ids:
        raise HTTPException(status_code=400, detail="未选择设备")
    
    if not calibration_date:
        raise HTTPException(status_code=400, detail="未提供检定日期")
    
    success_count = 0
    error_count = 0
    
    for equipment_id in equipment_ids:
        try:
            # 检查设备是否存在且用户有权限
            db_equipment = equipment.get_equipment(
                db, equipment_id=equipment_id,
                user_id=current_user.id, is_admin=current_user.is_admin
            )
            if db_equipment is None:
                error_count += 1
                continue
            
            # 更新检定日期
            from app.schemas.schemas import EquipmentUpdate
            equipment_update = EquipmentUpdate(calibration_date=calibration_date)
            equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
            
            # 记录操作日志
            create_audit_log(
                db=db,
                user_id=current_user.id,
                equipment_id=equipment_id,
                action="批量更新检定日期",
                description=f"批量更新设备 {db_equipment.name} 的检定日期为 {calibration_date}"
            )
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            continue
    
    # 记录总体操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="批量操作",
        description=f"批量更新检定日期，成功{success_count}台，失败{error_count}台"
    )
    
    return {
        "message": "批量更新完成",
        "success_count": success_count,
        "error_count": error_count
    }

@router.post("/batch/change-status")
def batch_change_status(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量变更设备状态"""
    equipment_ids = request_data.get('equipment_ids', [])
    new_status = request_data.get('status')
    status_change_date = request_data.get('status_change_date')
    
    if not equipment_ids:
        raise HTTPException(status_code=400, detail="未选择设备")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="未提供新状态")
    
    if new_status in ['停用', '报废'] and not status_change_date:
        raise HTTPException(status_code=400, detail="停用或报废状态时，状态变更时间为必填项")
    
    success_count = 0
    error_count = 0
    
    for equipment_id in equipment_ids:
        try:
            # 检查设备是否存在且用户有权限
            db_equipment = equipment.get_equipment(
                db, equipment_id=equipment_id,
                user_id=current_user.id, is_admin=current_user.is_admin
            )
            if db_equipment is None:
                error_count += 1
                continue
            
            # 更新设备状态
            from app.schemas.schemas import EquipmentUpdate
            update_data = {"status": new_status}
            if status_change_date:
                update_data["status_change_date"] = status_change_date
            
            equipment_update = EquipmentUpdate(**update_data)
            equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
            
            # 记录操作日志
            create_audit_log(
                db=db,
                user_id=current_user.id,
                equipment_id=equipment_id,
                action="批量变更状态",
                description=f"批量变更设备 {db_equipment.name} 状态为 {new_status}"
            )
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            continue
    
    # 记录总体操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="批量操作",
        description=f"批量变更设备状态，成功{success_count}台，失败{error_count}台"
    )
    
    return {
        "message": "批量状态变更完成",
        "success_count": success_count,
        "error_count": error_count
    }

@router.post("/search", response_model=PaginatedEquipment)
def search_equipments(search_params: EquipmentSearch, skip: int = 0, limit: int = 999999,
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_user)):
    """全文本搜索设备"""
    return equipment.search_equipments_paginated(
        db, search=search_params, skip=skip, limit=limit,
        user_id=current_user.id, is_admin=current_user.is_admin
    )

@router.post("/export/search")
def export_search_equipments(search_params: EquipmentSearch,
                            db: Session = Depends(get_db),
                            current_user = Depends(get_current_user)):
    """导出全文本搜索结果"""
    equipments = equipment.search_equipments(
        db, search=search_params, skip=0, limit=10000,  # 导出时不限制数量
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 转换为DataFrame
    data = []
    for eq in equipments:
        data.append({
            '部门': eq.department.name,
            '设备类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '检定周期': eq.calibration_cycle,
            '检定日期': eq.calibration_date.strftime('%Y-%m-%d'),
            '下次检定日期': eq.next_calibration_date.strftime('%Y-%m-%d'),
            '计量编号': eq.serial_number,
            '安装地点': eq.installation_location,
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date else '',
            '分度值': eq.scale_value or '',
            '检定方式': eq.calibration_method,
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date else '',
            '备注': eq.notes,
            '创建时间': eq.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            '更新时间': eq.updated_at.strftime('%Y-%m-%d %H:%M:%S') if eq.updated_at else ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='搜索结果', index=False)
    output.seek(0)
    
    filename = f"设备搜索结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename, safe='')
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
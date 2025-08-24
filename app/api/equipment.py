from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import date, datetime
from calendar import monthrange
import io
import pandas as pd
from urllib.parse import quote
from app.db.database import get_db
from app.crud import equipment
from app.schemas.schemas import Equipment, EquipmentCreate, EquipmentUpdate, EquipmentFilter, EquipmentSearch, PaginatedEquipment
from app.api.audit_logs import create_audit_log
from app.api.auth import get_current_user
from app.utils.auto_id import generate_internal_id

router = APIRouter()

@router.get("/", response_model=PaginatedEquipment)
def read_equipments(skip: int = 0, limit: int = 999999,
                   sort_field: str = "valid_until", 
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
    # 检查用户是否有该设备的权限
    if not current_user.is_admin:
        from app.crud import users
        from app.models.models import UserEquipmentPermission
        
        # 检查类别权限
        user_categories = users.get_user_categories(db, current_user.id)
        authorized_category_ids = [uc.category_id for uc in user_categories]
        
        # 检查器具权限
        user_equipment_permissions = db.query(UserEquipmentPermission).filter(
            UserEquipmentPermission.user_id == current_user.id
        ).all()
        authorized_equipment_names = [perm.equipment_name for perm in user_equipment_permissions]
        
        # 用户必须有该设备类别的权限，或者该设备名称的权限
        if (equipment_data.category_id not in authorized_category_ids and 
            equipment_data.name not in authorized_equipment_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage this equipment"
            )
    
    try:
        # 生成自动编号
        internal_id = generate_internal_id(db, equipment_data.category_id, equipment_data.name)
        
        # 创建equipment_data的副本并设置自动编号
        equipment_dict = equipment_data.model_dump()
        equipment_dict['internal_id'] = internal_id
        
        # 创建设备
        new_equipment = equipment.create_equipment(db=db, equipment=EquipmentCreate(**equipment_dict))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=new_equipment.id,
        action="创建",
        description=f"创建设备: {new_equipment.name} ({new_equipment.internal_id})"
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
    
    try:
        updated_equipment = equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 记录操作日志
    changes = []
    if equipment_update.status and equipment_update.status != old_status:
        changes.append(f"状态从'{old_status}'改为'{equipment_update.status}'")
    
    description = f"更新设备: {updated_equipment.name if updated_equipment else '未知设备'} ({updated_equipment.internal_id if updated_equipment else '未知编号'})"
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
        description=f"删除设备: {db_equipment.name} ({db_equipment.internal_id})"
    )
    
    success = equipment.delete_equipment(db, equipment_id=equipment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}

@router.post("/filter", response_model=PaginatedEquipment)
def filter_equipments(filters: EquipmentFilter, skip: int = 0, limit: int = 999999,
                     sort_field: str = "valid_until", 
                     sort_order: str = "asc",
                     db: Session = Depends(get_db),
                     current_user = Depends(get_current_user)):
    return equipment.filter_equipments_paginated(
        db, filters=filters, skip=skip, limit=limit,
        sort_field=sort_field, sort_order=sort_order,
        user_id=current_user.id, is_admin=current_user.is_admin
    )

@router.get("/export/monthly-plan")
def export_monthly_plan(db: Session = Depends(get_db),
                       current_user = Depends(get_current_user)):
    """导出本月待检设备计划"""
    from datetime import datetime
    
    # 获取当前日期
    today = datetime.now().date()
    
    # 计算本月的开始和结束日期
    start_date = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    end_date = date(today.year, today.month, last_day)
    
    equipments = equipment.get_equipments_due_for_calibration(
        db, start_date=start_date, end_date=end_date,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    # 转换为DataFrame
    data = []
    for i, eq in enumerate(equipments, 1):
        data.append({
            '序号': i,
            '使用部门': eq.department.name,
            '计量器具类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '内部编号': eq.internal_id,
            '出厂编号': eq.manufacturer_id or '',
            '检定周期': eq.calibration_cycle,
            '检定（校准）日期': eq.calibration_date.strftime('%Y-%m-%d') if eq.calibration_date is not None else '',
            '有效期至': eq.valid_until.strftime('%Y-%m-%d') if eq.valid_until is not None else '',
            '安装地点': eq.installation_location,
            '分度值': eq.scale_value or '',
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date is not None else '',
            '检定方式': eq.calibration_method,
            '证书编号': eq.certificate_number or '',
            '检定结果': eq.verification_result or '',
            '检定机构': eq.verification_agency or '',
            '证书形式': eq.certificate_form or '',
            '管理级别': eq.management_level or '',
            '原值/元': eq.original_value or '',
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date is not None else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 重新排列列顺序，确保序号在第一列
    if not df.empty:
        columns = ['序号'] + [col for col in df.columns if col != '序号']
        df = df[columns]
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='选中设备', index=False)
    output.seek(0)
    
    filename = f"选中设备_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename)
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="月度检定计划导出",
        description=f"月度检定计划导出，共{len(equipments)}台"
    )
    
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
    for i, eq in enumerate(equipments, 1):
        data.append({
            '序号': i,
            '使用部门': eq.department.name,
            '计量器具类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '内部编号': eq.internal_id,
            '出厂编号': eq.manufacturer_id or '',
            '检定周期': eq.calibration_cycle,
            '检定（校准）日期': eq.calibration_date.strftime('%Y-%m-%d') if eq.calibration_date is not None else '',
            '有效期至': eq.valid_until.strftime('%Y-%m-%d') if eq.valid_until is not None else '',
            '安装地点': eq.installation_location,
            '分度值': eq.scale_value or '',
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date is not None else '',
            '检定方式': eq.calibration_method,
            '证书编号': eq.certificate_number or '',
            '检定结果': eq.verification_result or '',
            '检定机构': eq.verification_agency or '',
            '证书形式': eq.certificate_form or '',
            '管理级别': eq.management_level or '',
            '原值/元': eq.original_value or '',
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date is not None else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 重新排列列顺序，确保序号在第一列
    columns = ['序号'] + [col for col in df.columns if col != '序号']
    df = df[columns]
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账', index=False)
    output.seek(0)
    
    filename = f"设备台账_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename)
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
            from datetime import datetime
            
            # 将字符串转换为date对象
            calibration_date_obj = datetime.strptime(calibration_date, '%Y-%m-%d').date()
            equipment_update = EquipmentUpdate(calibration_date=calibration_date_obj)
            equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
            
            # 记录操作日志
            create_audit_log(
                db=db,
                user_id=current_user.id,
                equipment_id=int(equipment_id),
                action="批量更新检定日期",
                description=f"批量更新设备 {db_equipment.name} 的检定日期为 {calibration_date}"
            )
            
            success_count += 1
            
        except Exception:
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
    
    # 状态变更时间：当状态为"停用"或"报废"时可选填
    if new_status in ['停用', '报废']:
        # 如果提供了状态变更时间，验证格式
        if status_change_date:
            try:
                from datetime import datetime
                datetime.strptime(status_change_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="状态变更时间格式错误，请使用YYYY-MM-DD格式")
        # 如果没有提供状态变更时间，使用当前日期
        else:
            from datetime import datetime
            status_change_date = datetime.now().strftime('%Y-%m-%d')
    
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
            from datetime import datetime
            
            update_data = {"status": new_status}
            if status_change_date:
                # 将字符串转换为date对象
                status_change_date_obj = datetime.strptime(status_change_date, '%Y-%m-%d').date()
                update_data["status_change_date"] = status_change_date_obj
            
            equipment_update = EquipmentUpdate(**update_data)
            equipment.update_equipment(db, equipment_id=equipment_id, equipment_update=equipment_update)
            
            # 记录操作日志
            create_audit_log(
                db=db,
                user_id=current_user.id,
                equipment_id=int(equipment_id),
                action="批量变更状态",
                description=f"批量变更设备 {db_equipment.name} 状态为 {new_status}"
            )
            
            success_count += 1
            
        except Exception:
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

@router.post("/batch/delete")
def batch_delete_equipments(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量删除设备"""
    equipment_ids = request_data.get('equipment_ids', [])
    
    if not equipment_ids:
        raise HTTPException(status_code=400, detail="未选择设备")
    
    success_count = 0
    error_count = 0
    deleted_equipment_names = []
    
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
            
            equipment_name = db_equipment.name
            equipment_serial = db_equipment.internal_id
            
            # 删除设备
            success = equipment.delete_equipment(db, equipment_id=equipment_id)
            if success:
                # 记录操作日志
                create_audit_log(
                    db=db,
                    user_id=current_user.id,
                    equipment_id=int(equipment_id),
                    action="批量删除",
                    description=f"批量删除设备: {equipment_name} ({equipment_serial})"
                )
                deleted_equipment_names.append(f"{equipment_name} ({equipment_serial})")
                success_count += 1
            else:
                error_count += 1
            
        except Exception:
            error_count += 1
            continue
    
    # 记录总体操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="批量操作",
        description=f"批量删除设备，成功{success_count}台，失败{error_count}台"
    )
    
    return {
        "message": f"批量删除完成，成功删除{success_count}台设备",
        "success_count": success_count,
        "error_count": error_count,
        "deleted_equipment": deleted_equipment_names
    }

@router.post("/batch/export-selected")
def batch_export_selected_equipments(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量导出选中的设备"""
    equipment_ids = request_data.get('equipment_ids', [])
    
    if not equipment_ids:
        raise HTTPException(status_code=400, detail="未选择设备")
    
    # 获取选中的设备
    selected_equipments = []
    for equipment_id in equipment_ids:
        try:
            db_equipment = equipment.get_equipment(
                db, equipment_id=equipment_id,
                user_id=current_user.id, is_admin=current_user.is_admin
            )
            if db_equipment:
                selected_equipments.append(db_equipment)
        except Exception:
            continue
    
    if not selected_equipments:
        raise HTTPException(status_code=404, detail="未找到可导出的设备")
    
    # 转换为DataFrame
    data = []
    for i, eq in enumerate(selected_equipments, 1):
        data.append({
            '序号': i,
            '使用部门': eq.department.name,
            '计量器具类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '内部编号': eq.internal_id,
            '出厂编号': eq.manufacturer_id or '',
            '检定周期': eq.calibration_cycle,
            '检定（校准）日期': eq.calibration_date.strftime('%Y-%m-%d') if eq.calibration_date is not None else '',
            '有效期至': eq.valid_until.strftime('%Y-%m-%d') if eq.valid_until is not None else '',
            '安装地点': eq.installation_location,
            '分度值': eq.scale_value or '',
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date is not None else '',
            '检定方式': eq.calibration_method,
            '证书编号': eq.certificate_number or '',
            '检定结果': eq.verification_result or '',
            '检定机构': eq.verification_agency or '',
            '证书形式': eq.certificate_form or '',
            '管理级别': eq.management_level or '',
            '原值/元': eq.original_value or '',
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date is not None else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 重新排列列顺序，确保序号在第一列
    columns = ['序号'] + [col for col in df.columns if col != '序号']
    df = df[columns]
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='选中设备', index=False)
    output.seek(0)
    
    filename = f"选中设备_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename)
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="批量导出选中设备",
        description=f"批量导出选中设备，共{len(selected_equipments)}台"
    )
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

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
    for i, eq in enumerate(equipments, 1):
        data.append({
            '序号': i,
            '使用部门': eq.department.name,
            '计量器具类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '内部编号': eq.internal_id,
            '出厂编号': eq.manufacturer_id or '',
            '检定周期': eq.calibration_cycle,
            '检定（校准）日期': eq.calibration_date.strftime('%Y-%m-%d') if eq.calibration_date is not None else '',
            '有效期至': eq.valid_until.strftime('%Y-%m-%d') if eq.valid_until is not None else '',
            '安装地点': eq.installation_location,
            '分度值': eq.scale_value or '',
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date is not None else '',
            '检定方式': eq.calibration_method,
            '证书编号': eq.certificate_number or '',
            '检定结果': eq.verification_result or '',
            '检定机构': eq.verification_agency or '',
            '证书形式': eq.certificate_form or '',
            '管理级别': eq.management_level or '',
            '原值/元': eq.original_value or '',
            '设备状态': eq.status,
            '状态变更时间': eq.status_change_date.strftime('%Y-%m-%d') if eq.status_change_date is not None else '',
            '备注': eq.notes
        })
    
    df = pd.DataFrame(data)
    
    # 重新排列列顺序，确保序号在第一列
    columns = ['序号'] + [col for col in df.columns if col != '序号']
    df = df[columns]
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='搜索结果', index=False)
    output.seek(0)
    
    filename = f"设备搜索结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename)
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.get("/utils/generate-internal-id")
def generate_internal_id_endpoint(category_id: int,
                                equipment_name: str | None = None,
                                db: Session = Depends(get_db)):
    """生成内部编号"""
    try:
        internal_id = generate_internal_id(db, category_id, equipment_name)
        return {"internal_id": internal_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="生成编号失败")
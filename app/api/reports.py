from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_, or_, case
from datetime import datetime, date, timedelta
from calendar import monthrange
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.crud import equipment
from app.api.auth import get_current_user
from app.models.models import Equipment, EquipmentCategory, Department

router = APIRouter()

@router.get("/overview")
async def get_reports_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取报表概览数据"""
    
    # 基础查询条件
    base_query = db.query(Equipment)
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        base_query = base_query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 设备状态统计
    total_count = base_query.count()
    active_count = base_query.filter(Equipment.status == "在用").count()
    inactive_count = base_query.filter(Equipment.status.in_(["停用", "报废"])).count()
    
    # 检定相关统计
    today = date.today()
    overdue_count = base_query.filter(
        and_(
            Equipment.status == "在用",
            Equipment.valid_until < today
        )
    ).count()
    
    # 本月待检
    current_month_start = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)
    
    monthly_due_count = base_query.filter(
        and_(
            Equipment.status == "在用",
            Equipment.valid_until.between(current_month_start, current_month_end)
        )
    ).count()
    
    # 设备类别分布
    category_stats = db.query(
        EquipmentCategory.name,
        func.count(Equipment.id).label('count'),
        func.sum(case((Equipment.status == "在用", 1), else_=0)).label('active_count'),
    ).join(Equipment).group_by(EquipmentCategory.id, EquipmentCategory.name)
    
    if not current_user.is_admin:
        category_stats = category_stats.filter(Equipment.category_id.in_(authorized_categories))
    
    category_distribution = [
        {
            "name": name,
            "total": count,
            "active": active_count or 0
        }
        for name, count, active_count in category_stats.all()
    ]
    
    # 部门分布
    department_stats = db.query(
        Department.name,
        func.count(Equipment.id).label('count'),
        func.sum(case((Equipment.status == "在用", 1), else_=0)).label('active_count'),
    ).join(Equipment).group_by(Department.id, Department.name)
    
    if not current_user.is_admin:
        department_stats = department_stats.filter(Equipment.category_id.in_(authorized_categories))
    
    department_distribution = [
        {
            "name": name,
            "total": count,
            "active": active_count or 0
        }
        for name, count, active_count in department_stats.all()
    ]
    
    return {
        "overview": {
            "total_equipment": total_count,
            "active_equipment": active_count,
            "inactive_equipment": inactive_count,
            "overdue_equipment": overdue_count,
            "monthly_due_equipment": monthly_due_count
        },
        "category_distribution": category_distribution,
        "department_distribution": department_distribution
    }

@router.get("/calibration-stats")
async def get_calibration_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取检定统计信息"""
    
    today = date.today()
    
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    # 基础查询
    base_query = db.query(Equipment).filter(Equipment.status == "在用")
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        base_query = base_query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 检定方式统计
    calibration_method_stats = db.query(
        Equipment.calibration_method,
        func.count(Equipment.id).label('count')
    ).filter(
        and_(
            Equipment.calibration_date.between(start_date, end_date),
            Equipment.category_id.in_(base_query.with_entities(Equipment.category_id))
        )
    ).group_by(Equipment.calibration_method).all()
    
    # 月度检定完成情况
    monthly_completion = []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        _, last_day = monthrange(current_date.year, current_date.month)
        month_end = current_date.replace(day=last_day)
        
        monthly_query = base_query.filter(
            Equipment.calibration_date.between(month_start, month_end)
        )
        
        completed_count = monthly_query.count()
        total_due = base_query.filter(
            Equipment.valid_until.between(month_start, month_end)
        ).count()
        
        monthly_completion.append({
            "month": current_date.strftime("%Y-%m"),
            "completed": completed_count,
            "due": total_due,
            "completion_rate": (completed_count / total_due * 100) if total_due > 0 else 0
        })
        
        # 移动到下个月
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # 超期分析
    overdue_analysis = []
    for i in range(1, 7):  # 分析未来6个月
        future_date = today + timedelta(days=30 * i)
        month_start = future_date.replace(day=1)
        _, last_day = monthrange(future_date.year, future_date.month)
        month_end = future_date.replace(day=last_day)
        
        overdue_count = base_query.filter(
            and_(
                Equipment.valid_until < month_start,
                Equipment.status == "在用"
            )
        ).count()
        
        due_count = base_query.filter(
            and_(
                Equipment.valid_until.between(month_start, month_end),
                Equipment.status == "在用"
            )
        ).count()
        
        overdue_analysis.append({
            "month": future_date.strftime("%Y-%m"),
            "overdue_count": overdue_count,
            "due_count": due_count
        })
    
    return {
        "calibration_methods": [
            {"method": method, "count": count}
            for method, count in calibration_method_stats
        ],
        "monthly_completion": monthly_completion,
        "overdue_analysis": overdue_analysis
    }

@router.get("/equipment-trends")
async def get_equipment_trends(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取设备趋势分析"""
    
    trends_data = []
    today = date.today()
    
    for i in range(months):
        target_date = today - timedelta(days=30 * i)
        month_start = target_date.replace(day=1)
        _, last_day = monthrange(target_date.year, target_date.month)
        month_end = target_date.replace(day=last_day)
        
        # 基础查询
        base_query = db.query(Equipment)
        if not current_user.is_admin:
            from app.models.models import UserCategory
            authorized_categories = select(UserCategory.category_id).filter(
                UserCategory.user_id == current_user.id
            )
            base_query = base_query.filter(Equipment.category_id.in_(authorized_categories))
        
        # 统计各状态设备数量
        total_count = base_query.filter(
            Equipment.created_at <= month_end
        ).count()
        
        active_count = base_query.filter(
            and_(
                Equipment.status == "在用",
                Equipment.created_at <= month_end
            )
        ).count()
        
        inactive_count = base_query.filter(
            and_(
                Equipment.status.in_(["停用", "报废"]),
                Equipment.created_at <= month_end
            )
        ).count()
        
        # 当月新增设备
        new_count = base_query.filter(
            Equipment.created_at.between(month_start, month_end)
        ).count()
        
        trends_data.append({
            "month": target_date.strftime("%Y-%m"),
            "total": total_count,
            "active": active_count,
            "inactive": inactive_count,
            "new": new_count
        })
    
    # 反转数组，按时间顺序排列
    trends_data.reverse()
    
    return {
        "trends": trends_data
    }

@router.get("/department-comparison")
async def get_department_comparison(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取部门对比分析"""
    
    # 基础查询
    base_query = db.query(Equipment)
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        base_query = base_query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 部门详细统计
    department_stats = db.query(
        Department.id,
        Department.name,
        func.count(Equipment.id).label('total_count'),
        func.sum(case((Equipment.status == "在用", 1), else_=0)).label('active_count'),
        func.sum(case((Equipment.status == "停用", 1), else_=0)).label('inactive_count'),
        func.sum(case((Equipment.status == "报废", 1), else_=0)).label('scrap_count'),
        func.sum(case((Equipment.valid_until < date.today(), 1), else_=0)).label('overdue_count')
    ).join(Equipment).group_by(Department.id, Department.name).all()
    
    comparison_data = []
    for dept_id, name, total, active, inactive, scrap, overdue in department_stats:
        # 部门设备类别分布
        category_distribution = db.query(
            EquipmentCategory.name,
            func.count(Equipment.id).label('count')
        ).join(Equipment).filter(
            and_(
                Equipment.department_id == dept_id,
                Equipment.category_id.in_(base_query.with_entities(Equipment.category_id))
            )
        ).group_by(EquipmentCategory.id, EquipmentCategory.name).all()
        
        comparison_data.append({
            "department": name,
            "statistics": {
                "total": total,
                "active": active or 0,
                "inactive": inactive or 0,
                "scrap": scrap or 0,
                "overdue": overdue or 0
            },
            "category_distribution": [
                {"category": cat_name, "count": count}
                for cat_name, count in category_distribution
            ]
        })
    
    return {
        "department_comparison": comparison_data
    }

@router.get("/export-data")
async def export_reports_data(
    report_type: str = Query(..., description="报表类型：overview, calibration, trends, department"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("excel", description="导出格式：excel, csv"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """导出报表数据"""
    
    if report_type == "overview":
        data = await get_reports_overview(db, current_user)
    elif report_type == "calibration":
        data = await get_calibration_stats(start_date, end_date, db, current_user)
    elif report_type == "trends":
        data = await get_equipment_trends(12, db, current_user)
    elif report_type == "department":
        data = await get_department_comparison(db, current_user)
    else:
        return {"error": "不支持的报表类型"}
    
    return {
        "data": data,
        "export_info": {
            "report_type": report_type,
            "format": format,
            "export_time": datetime.now().isoformat(),
            "exported_by": current_user.username
        }
    }


@router.get("/equipment-stats")
async def get_equipment_stats(
    sort_by: str = Query("original_value", description="主排序字段：original_value, name, status, department, category"),
    sort_order: str = Query("desc", description="主排序方向：asc, desc"),
    sort_by2: str = Query(None, description="次排序字段：original_value, name, status, department, category"),
    sort_order2: str = Query("desc", description="次排序方向：asc, desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取设备统计数据，支持按原值排序"""
    
    # 基础查询
    query = db.query(Equipment)
    
    # 权限控制
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 获取总数
    total = query.count()
    
    # 构建排序条件
    order_by_clauses = []
    
    # 主排序字段
    if sort_by == "original_value":
        primary_order = Equipment.original_value.desc() if sort_order == "desc" else Equipment.original_value.asc()
    elif sort_by == "name":
        primary_order = Equipment.name.desc() if sort_order == "desc" else Equipment.name.asc()
    elif sort_by == "status":
        primary_order = Equipment.status.desc() if sort_order == "desc" else Equipment.status.asc()
    elif sort_by == "department":
        primary_order = Department.name.desc() if sort_order == "desc" else Department.name.asc()
    elif sort_by == "category":
        primary_order = EquipmentCategory.name.desc() if sort_order == "desc" else EquipmentCategory.name.asc()
    else:
        primary_order = Equipment.original_value.desc()
    
    order_by_clauses.append(primary_order)
    
    # 次排序字段
    if sort_by2:
        if sort_by2 == "original_value":
            secondary_order = Equipment.original_value.desc() if sort_order2 == "desc" else Equipment.original_value.asc()
        elif sort_by2 == "name":
            secondary_order = Equipment.name.desc() if sort_order2 == "desc" else Equipment.name.asc()
        elif sort_by2 == "status":
            secondary_order = Equipment.status.desc() if sort_order2 == "desc" else Equipment.status.asc()
        elif sort_by2 == "department":
            secondary_order = Department.name.desc() if sort_order2 == "desc" else Department.name.asc()
        elif sort_by2 == "category":
            secondary_order = EquipmentCategory.name.desc() if sort_order2 == "desc" else EquipmentCategory.name.asc()
        else:
            secondary_order = Equipment.name.asc()  # 默认次排序为名称升序
        
        # 避免重复排序字段
        if str(secondary_order) != str(primary_order):
            order_by_clauses.append(secondary_order)
    
    # 分页查询
    offset = (page - 1) * page_size
    equipments = query.order_by(*order_by_clauses).offset(offset).limit(page_size).all()
    
    # 统计数据
    total_original_value = query.with_entities(func.sum(Equipment.original_value)).scalar() or 0
    avg_original_value = query.with_entities(func.avg(Equipment.original_value)).scalar() or 0
    
    # 按状态统计
    status_stats = query.with_entities(
        Equipment.status,
        func.count(Equipment.id).label('count'),
        func.sum(Equipment.original_value).label('total_value')
    ).group_by(Equipment.status).all()
    
    # 时效监控统计
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    # 已超期设备数量（红色预警）
    overdue_count = query.filter(
        and_(
            Equipment.status == "在用",
            Equipment.valid_until < today
        )
    ).count()
    
    # 30天内即将到期设备数量（黄色预警）
    expiring_soon_count = query.filter(
        and_(
            Equipment.status == "在用",
            Equipment.valid_until.between(today, thirty_days_later)
        )
    ).count()
    
    # 正常有效期设备数量
    valid_count = query.filter(
        and_(
            Equipment.status == "在用",
            Equipment.valid_until > thirty_days_later
        )
    ).count()
    
    # 合规性指标统计
    # 外检设备数量（假设检定方式包含"外检"的为外检设备）
    external_inspection_count = query.filter(
        Equipment.calibration_method.contains("外检")
    ).count()
    
    # 强检设备数量（管理级别为A级的设备）
    mandatory_inspection_count = query.filter(
        Equipment.management_level == "A级"
    ).count()
    
    # A级设备数量（管理级别为A级且状态为在用的设备）
    a_grade_count = query.filter(
        and_(
            Equipment.management_level == "A级",
            Equipment.status == "在用"
        )
    ).count()
    
    # 计算合规性指标
    external_inspection_rate = (external_inspection_count / total * 100) if total > 0 else 0
    a_grade_rate = (a_grade_count / mandatory_inspection_count * 100) if mandatory_inspection_count > 0 else 0
    
    # 按部门统计
    department_stats = query.with_entities(
        Department.name,
        func.count(Equipment.id).label('count'),
        func.sum(Equipment.original_value).label('total_value'),
        func.avg(Equipment.original_value).label('avg_value')
    ).join(Department).group_by(Department.id, Department.name).all()
    
    # 按类别统计
    category_stats = query.with_entities(
        EquipmentCategory.name,
        func.count(Equipment.id).label('count'),
        func.sum(Equipment.original_value).label('total_value'),
        func.avg(Equipment.original_value).label('avg_value')
    ).join(EquipmentCategory).group_by(EquipmentCategory.id, EquipmentCategory.name).all()
    
    # 构建设备列表
    equipment_list = []
    for equipment in equipments:
        equipment_list.append({
            "id": equipment.id,
            "name": equipment.name,
            "model": equipment.model,
            "serial_number": equipment.serial_number,
            "department_name": equipment.department.name if equipment.department else "未知部门",
            "category_name": equipment.category.name if equipment.category else "其他",
            "original_value": equipment.original_value or 0,
            "status": equipment.status,
            "calibration_date": equipment.calibration_date.strftime("%Y-%m-%d") if equipment.calibration_date else None,
            "valid_until": equipment.valid_until.strftime("%Y-%m-%d") if equipment.valid_until else None,
            "manufacture_date": equipment.manufacture_date.strftime("%Y-%m-%d") if equipment.manufacture_date else None,
            "manufacturer": equipment.manufacturer or "",
            "calibration_method": equipment.calibration_method or "",
            "verification_result": equipment.verification_result or "",
            "installation_location": equipment.installation_location or ""
        })
    
    return {
        "equipment_list": equipment_list,
        "statistics": {
            "total_count": total,
            "total_original_value": float(total_original_value),
            "avg_original_value": float(avg_original_value),
            "status_distribution": [
                {
                    "status": status,
                    "count": count,
                    "total_value": float(total_value) if total_value else 0
                }
                for status, count, total_value in status_stats
            ],
            "department_stats": [
                {
                    "department": dept_name,
                    "count": count,
                    "total_value": float(total_value) if total_value else 0,
                    "avg_value": float(avg_value) if avg_value else 0
                }
                for dept_name, count, total_value, avg_value in department_stats
            ],
            "category_stats": [
                {
                    "category": cat_name,
                    "count": count,
                    "total_value": float(total_value) if total_value else 0,
                    "avg_value": float(avg_value) if avg_value else 0
                }
                for cat_name, count, total_value, avg_value in category_stats
            ],
            # 新增时效监控统计
            "time_monitoring": {
                "overdue_count": overdue_count,
                "expiring_soon_count": expiring_soon_count,
                "valid_count": valid_count
            },
            # 新增合规性指标
            "compliance_metrics": {
                "external_inspection_rate": round(external_inspection_rate, 2),
                "a_grade_rate": round(a_grade_rate, 2),
                "external_inspection_count": external_inspection_count,
                "mandatory_inspection_count": mandatory_inspection_count,
                "a_grade_count": a_grade_count
            }
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }

@router.get("/calibration-records")
async def get_calibration_records(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取检定记录明细（带分页）"""
    
    # 构建查询
    query = db.query(Equipment).filter(Equipment.calibration_date.isnot(None))
    
    # 权限控制
    if not current_user.is_admin:
        from app.models.models import UserCategory
        authorized_categories = select(UserCategory.category_id).filter(
            UserCategory.user_id == current_user.id
        )
        query = query.filter(Equipment.category_id.in_(authorized_categories))
    
    # 日期范围过滤
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Equipment.calibration_date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Equipment.calibration_date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误")
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    equipments = query.order_by(Equipment.calibration_date.desc()).offset(offset).limit(page_size).all()
    
    # 构建返回数据
    records = []
    for equipment in equipments:
        records.append({
            "id": equipment.id,
            "equipment_name": equipment.name,
            "equipment_model": equipment.model,
            "serial_number": equipment.serial_number,
            "department_name": equipment.department.name if equipment.department else "未知部门",
            "category_name": equipment.category.name if equipment.category else "其他",
            "calibration_date": equipment.calibration_date.strftime("%Y-%m-%d") if equipment.calibration_date else None,
            "calibration_result": equipment.verification_result or "未知",
            "valid_until": equipment.valid_until.strftime("%Y-%m-%d") if equipment.valid_until else None,
            "status": equipment.status
        })
    
    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/export")
async def export_reports(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = Query("excel", regex="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """导出统计报表"""
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    
    try:
        # 获取检定记录数据
        query = db.query(Equipment).filter(Equipment.calibration_date.isnot(None))
        
        # 权限控制
        if not current_user.is_admin:
            from app.models.models import UserCategory
            authorized_categories = select(UserCategory.category_id).filter(
                UserCategory.user_id == current_user.id
            )
            query = query.filter(Equipment.category_id.in_(authorized_categories))
        
        # 日期范围过滤
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Equipment.calibration_date >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Equipment.calibration_date <= end_dt)
        
        equipments = query.order_by(Equipment.calibration_date.desc()).all()
        
        # 构建数据
        data = []
        for equipment in equipments:
            data.append({
                "计量编号": equipment.serial_number or "",
                "设备名称": equipment.name or "",
                "型号规格": equipment.model or "",
                "所属部门": equipment.department.name if equipment.department else "未知部门",
                "设备类别": equipment.category.name if equipment.category else "其他",
                "检定日期": equipment.calibration_date.strftime("%Y-%m-%d") if equipment.calibration_date else "",
                "检定结果": equipment.verification_result or "未知",
                "有效期至": equipment.valid_until.strftime("%Y-%m-%d") if equipment.valid_until else "",
                "设备状态": equipment.status or "",
                "检定机构": equipment.verification_agency or "",
                "证书编号": equipment.certificate_number or ""
            })
        
        df = pd.DataFrame(data)
        
        # 生成文件
        if format == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='检定记录', index=False)
            output.seek(0)
            
            filename = f"calibration_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            return StreamingResponse(
                io.BytesIO(output.getvalue()),
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers=headers
            )
        else:  # CSV导出
            import csv
            output = io.BytesIO()
            
            # 使用utf-8编码写入CSV
            with io.TextIOWrapper(output, encoding='utf-8', newline='') as text_output:
                writer = csv.writer(text_output)
                
                # 写入表头
                writer.writerow(data[0].keys() if data else [])
                
                # 写入数据
                for row in data:
                    writer.writerow(row.values())
            
            output.seek(0)
            
            filename = f"calibration_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            return StreamingResponse(
                io.BytesIO(output.getvalue()),
                media_type='text/csv',
                headers=headers
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
from urllib.parse import quote
from datetime import datetime
from app.db.database import get_db
from app.crud import equipment, departments, categories, users
from app.schemas.schemas import Equipment, ImportTemplate
from app.api.auth import get_current_admin_user, get_current_user
from app.api.audit_logs import create_audit_log

router = APIRouter()

def get_responsible_person(db: Session, category_id: int) -> str:
    """获取负责指定设备类别的用户名"""
    from app.models.models import UserCategory
    user_category = db.query(UserCategory).filter(
        UserCategory.category_id == category_id
    ).first()
    return user_category.user.username if user_category else ''

def generate_export_data(equipments, db: Session) -> tuple:
    """生成导出数据，返回(data_df, dynamic_columns)"""
    data = []
    has_status_change_date = False
    has_external_inspection = False
    has_responsible_person = False
    
    # 基础列
    base_columns = [
        '序号', '使用部门', '设备类别', '计量器具名称', '型号/规格', '准确度等级', 
        '测量范围', '计量编号', '检定周期', '检定(校准)日期', '有效期至', '安装地点', 
        '分度值', '制造厂家', '出厂日期', '检定方式', '管理级别', '原值/元', '设备状态', '备注'
    ]
    
    # 动态列
    dynamic_columns = []
    
    for i, eq in enumerate(equipments, 1):
        row_data = {
            '序号': i,
            '使用部门': eq.department.name,
            '设备类别': eq.category.name,
            '计量器具名称': eq.name,
            '型号/规格': eq.model,
            '准确度等级': eq.accuracy_level,
            '测量范围': eq.measurement_range,
            '计量编号': eq.serial_number,
            '检定周期': eq.calibration_cycle,
            '检定(校准)日期': eq.calibration_date.strftime('%Y-%m-%d'),
            '有效期至': eq.valid_until.strftime('%Y-%m-%d'),
            '安装地点': eq.installation_location,
            '分度值': eq.scale_value or '',
            '制造厂家': eq.manufacturer,
            '出厂日期': eq.manufacture_date.strftime('%Y-%m-%d') if eq.manufacture_date else '',
            '检定方式': eq.calibration_method,
            '管理级别': eq.management_level or '',
            '原值/元': eq.original_value or '',
            '设备状态': eq.status,
            '备注': eq.notes
        }
        
        # 检查是否需要状态变更时间列
        if eq.status in ['停用', '报废'] and eq.status_change_date:
            has_status_change_date = True
            row_data['状态变更时间'] = eq.status_change_date.strftime('%Y-%m-%d')
        
        # 检查是否需要外检信息列
        if eq.calibration_method == '外检':
            has_external_inspection = True
            row_data['证书编号'] = eq.certificate_number or ''
            row_data['检定结果'] = eq.verification_result or ''
            row_data['检定机构'] = eq.verification_agency or ''
            row_data['证书形式'] = eq.certificate_form or ''
        
        # 检查是否需要负责人列
        responsible_person = get_responsible_person(db, eq.category_id)
        if responsible_person:
            has_responsible_person = True
            row_data['负责人'] = responsible_person
        
        data.append(row_data)
    
    # 构建最终的列顺序
    final_columns = base_columns.copy()
    
    if has_responsible_person:
        final_columns.append('负责人')
        dynamic_columns.append('负责人')
    
    if has_status_change_date:
        final_columns.append('状态变更时间')
        dynamic_columns.append('状态变更时间')
    
    if has_external_inspection:
        external_columns = ['证书编号', '检定结果', '检定机构', '证书形式']
        final_columns.extend(external_columns)
        dynamic_columns.extend(external_columns)
    
    df = pd.DataFrame(data)
    if not df.empty:
        df = df[final_columns]
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    return df, dynamic_columns

@router.get("/template", response_model=ImportTemplate)
def get_import_template():
    """获取数据导入模板信息"""
    return ImportTemplate(
        filename="设备台账导入模板.xlsx",
        url="/api/import/template/download"
    )

@router.get("/template/download")
def download_import_template():
    """下载数据导入Excel模板"""
    # 创建模板数据
    template_data = {
        '使用部门': ['树脂车间', '工业漆车间', '质检部', '树脂车间', '仓库'],
        '设备类别': ['铂热电阻', '玻璃量器', '压力表', '热电偶', '扳手'],
        '计量器具名称': ['铂热电阻温度计', '玻璃量筒', '压力表', '热电偶温度计', '扭矩扳手'],
        '型号/规格': ['PT100', '500ml A级', 'Y-100', 'K型', 'DN-100'],
        '准确度等级': ['A级', 'A级', '1.6级', 'B级', '2级'],
        '测量范围': ['-200~850℃', '0~500ml', '0~1.6MPa', '0~1300℃', '10-100N·m'],
        '计量编号': ['PT001', 'GL001', 'YL001', 'TC001', 'BS001'],
        '检定周期': ['6个月', '12个月', '24个月', '36个月', '随坏随换'],
        '检定(校准)日期': ['2024-01-15', '2024-03-20', '2024-06-01', '2024-09-01', ''],
        '安装地点': ['1号反应釜', '质检室', '实验室', '2号反应釜', '工具间'],
        '分度值': ['0.1℃', '1ml', '0.01MPa', '1℃', '1N·m'],
        '制造厂家': ['上海仪表厂', '北京玻璃厂', '深圳仪表厂', '上海仪表厂', '日本工具'],
        '出厂日期': ['2023-12-01', '2023-11-15', '2023-10-20', '2024-08-01', '2023-05-01'],
        '检定方式': ['内检', '外检', '内检', '外检', '内检'],
        '管理级别': ['A级', 'B级', 'C级', 'A级', 'C级'],
        '原值/元': [1500.00, 800.00, 1200.00, 2000.00, 500.00],
        '设备状态': ['在用', '在用', '在用', '在用', '在用'],
        '证书编号': ['', 'CERT001', '', 'CERT002', ''],
        '检定结果': ['', '合格', '', '合格', ''],
        '检定机构': ['', '国家计量院', '', '省计量院', ''],
        '证书形式': ['', '校准证书', '', '检定证书', ''],
        '备注': ['正常使用', '新购设备', '半年检定周期示例', '三年检定周期', '随坏随换设备无需定期检定']
    }
    
    df = pd.DataFrame(template_data)
    
    # 替换NaN值为空字符串
    df = df.fillna('')
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账模板', index=False)
        
        # 添加说明工作表
        explanation_data = {
            '字段名': [
                '使用部门', '设备类别', '计量器具名称', '型号/规格', '准确度等级', '测量范围',
                '计量编号', '检定周期', '检定(校准)日期', '安装地点', '分度值', '制造厂家', 
                '出厂日期', '检定方式', '管理级别', '原值/元', '设备状态', '证书编号', 
                '检定结果', '检定机构', '证书形式', '备注'
            ],
            '是否必填': [
                '是', '是', '是', '是', '是', '否',
                '是', '是', '否', '否', '否', '否', 
                '否', '是', '否', '否', '否', '否', 
                '否', '否', '否', '否'
            ],
            '说明': [
                '必须是系统中已存在的部门名称',
                '必须是系统中已存在的设备类别名称',
                '设备的具体名称',
                '设备的型号或规格',
                '设备的准确度等级',
                '设备的测量范围',
                '设备的唯一编号',
                '只能填写"6个月"、"12个月"、"24个月"、"36个月"或"随坏随换"，随坏随换设备无需填写检定日期',
                '格式：YYYY-MM-DD，如2024-01-15（注：随坏随换设备无需填写）',
                '设备的安装位置',
                '设备的分度值，如0.01mm',
                '设备制造商名称',
                '格式：YYYY-MM-DD',
                '检定方式：内检/外检',
                '管理级别：A级/B级/C级（外检时自动设为"-"）',
                '设备原值，单位：元（支持小数）',
                '设备状态：在用/停用/报废',
                '证书编号（外检时必填）',
                '检定结果（外检时必填）',
                '检定机构（外检时必填）',
                '证书形式（外检时必填）：校准证书/检定证书',
                '备注信息'
            ]
        }
        
        explanation_df = pd.DataFrame(explanation_data)
        # 替换NaN值为空字符串
        explanation_df = explanation_df.fillna('')
        explanation_df.to_excel(writer, sheet_name='填写说明', index=False)
    
    output.seek(0)
    
    filename = "设备台账导入模板.xlsx"
    encoded_filename = quote(filename, safe='')
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/upload")
async def import_equipment_data(
    file: UploadFile = File(...),
    overwrite: bool = False,  # 新增参数：是否覆盖重复数据
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """导入设备数据"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 将所有NaN值替换为空字符串，避免空单元格显示为"nan"
        df = df.fillna('')
        
        # 验证必需的列
        required_columns = [
            '使用部门', '设备类别', '计量器具名称', '型号/规格', '准确度等级',
            '检定周期', '检定(校准)日期', '计量编号', '检定方式'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必需的列: {', '.join(missing_columns)}"
            )
        
        success_count = 0
        update_count = 0
        error_count = 0
        detailed_results = []
        
        for index, row in df.iterrows():
            row_number = index + 2  # Excel行号从2开始（第1行是标题）
            result = {
                "row": row_number,
                "serial_number": str(row['计量编号']),
                "name": str(row['计量器具名称']),
                "status": "",
                "message": ""
            }
            
            try:
                # 验证部门
                department = departments.get_department_by_name(db, str(row['使用部门']))
                if not department:
                    result["status"] = "失败"
                    result["message"] = f"部门'{row['使用部门']}'不存在"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证设备类别
                category = categories.get_category_by_name(db, str(row['设备类别']))
                if not category:
                    result["status"] = "失败"
                    result["message"] = f"设备类别'{row['设备类别']}'不存在"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证检定周期
                calibration_cycle = str(row['检定周期'])
                if calibration_cycle not in ['6个月', '12个月', '24个月', '36个月', '随坏随换']:
                    result["status"] = "失败"
                    result["message"] = "检定周期必须是'6个月'、'12个月'、'24个月'、'36个月'或'随坏随换'"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证检定方式
                calibration_method = str(row['检定方式'])
                if calibration_method not in ['内检', '外检']:
                    result["status"] = "失败"
                    result["message"] = "检定方式必须是'内检'或'外检'"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证外检必填字段
                if calibration_method == '外检':
                    external_fields = {
                        '证书编号': row.get('证书编号', ''),
                        '检定结果': row.get('检定结果', ''),
                        '检定机构': row.get('检定机构', ''),
                        '证书形式': row.get('证书形式', '')
                    }
                    
                    for field_name, field_value in external_fields.items():
                        if pd.isna(field_value) or str(field_value).strip() == '':
                            result["status"] = "失败"
                            result["message"] = f"外检时'{field_name}'为必填项"
                            detailed_results.append(result)
                            error_count += 1
                            continue
                    
                    # 验证证书形式字段值
                    certificate_form = str(row.get('证书形式', '')).strip()
                    if certificate_form not in ['校准证书', '检定证书']:
                        result["status"] = "失败"
                        result["message"] = "证书形式必须是'校准证书'或'检定证书'"
                        detailed_results.append(result)
                        error_count += 1
                        continue
                
                # 验证日期格式
                try:
                    calibration_date = pd.to_datetime(row['检定(校准)日期']).date()
                except:
                    result["status"] = "失败"
                    result["message"] = "检定日期格式错误，请使用YYYY-MM-DD格式"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                manufacture_date = None
                if pd.notna(row.get('出厂日期')):
                    try:
                        manufacture_date = pd.to_datetime(row['出厂日期']).date()
                    except:
                        result["status"] = "失败"
                        result["message"] = "出厂日期格式错误，请使用YYYY-MM-DD格式"
                        detailed_results.append(result)
                        error_count += 1
                        continue
                
                # 自动计算有效期至（随坏随换设备无有效期）
                from datetime import timedelta
                if calibration_cycle == "随坏随换":
                    valid_until = None
                else:
                    cycle_days = {
                        '6个月': 180,
                        '12个月': 365,
                        '24个月': 730,
                        '36个月': 1095
                    }
                    valid_until = calibration_date + timedelta(days=cycle_days[calibration_cycle] - 1)
                
                # 自动设置管理级别（外检时设为"-"）
                management_level = str(row.get('管理级别', '')) if calibration_method == '内检' else '-'
                
                # 验证状态变更时间
                status_change_date = None
                equipment_status = str(row.get('设备状态', '在用'))
                if equipment_status in ['停用', '报废']:
                    status_change_date_input = row.get('状态变更时间')
                    if pd.isna(status_change_date_input) or str(status_change_date_input).strip() == '':
                        result["status"] = "失败"
                        result["message"] = f"设备状态为'{equipment_status}'时，状态变更时间为必填项"
                        detailed_results.append(result)
                        error_count += 1
                        continue
                    try:
                        status_change_date = pd.to_datetime(status_change_date_input).date()
                    except:
                        result["status"] = "失败"
                        result["message"] = "状态变更时间格式错误，请使用YYYY-MM-DD格式"
                        detailed_results.append(result)
                        error_count += 1
                        continue
                
                # 创建设备数据
                from app.schemas.schemas import EquipmentCreate, EquipmentUpdate
                equipment_data = EquipmentCreate(
                    department_id=department.id,
                    category_id=category.id,
                    name=str(row['计量器具名称']),
                    model=str(row['型号/规格']),
                    accuracy_level=str(row['准确度等级']),
                    measurement_range=str(row.get('测量范围', '')) if pd.notna(row.get('测量范围')) else '',
                    calibration_cycle=calibration_cycle,
                    calibration_date=calibration_date,
                    calibration_method=calibration_method,
                    serial_number=str(row['计量编号']),
                    installation_location=str(row.get('安装地点', '')) if pd.notna(row.get('安装地点')) else '',
                    manufacturer=str(row.get('制造厂家', '')) if pd.notna(row.get('制造厂家')) else '',
                    manufacture_date=manufacture_date,
                    scale_value=str(row.get('分度值', '')) if pd.notna(row.get('分度值')) else '',
                    management_level=management_level,
                    original_value=float(row['原值/元']) if pd.notna(row.get('原值/元')) and str(row['原值/元']).strip() != '' else None,
                    status=equipment_status,
                    status_change_date=status_change_date,
                    certificate_number=str(row.get('证书编号', '')) if calibration_method == '外检' and pd.notna(row.get('证书编号')) else '',
                    verification_result=str(row.get('检定结果', '')) if calibration_method == '外检' and pd.notna(row.get('检定结果')) else '',
                    verification_agency=str(row.get('检定机构', '')) if calibration_method == '外检' and pd.notna(row.get('检定机构')) else '',
                    certificate_form=str(row.get('证书形式', '')) if calibration_method == '外检' and pd.notna(row.get('证书形式')) else '',
                    notes=str(row.get('备注', '')) if pd.notna(row.get('备注')) else ''
                )
                
                # 检查计量编号是否已存在
                from app.models.models import Equipment
                existing_equipment = db.query(Equipment).filter(
                    Equipment.serial_number == equipment_data.serial_number
                ).first()
                
                if existing_equipment:
                    if overwrite:
                        # 覆盖现有设备
                        update_data = EquipmentUpdate(
                            department_id=equipment_data.department_id,
                            category_id=equipment_data.category_id,
                            name=equipment_data.name,
                            model=equipment_data.model,
                            accuracy_level=equipment_data.accuracy_level,
                            measurement_range=equipment_data.measurement_range,
                            calibration_cycle=equipment_data.calibration_cycle,
                            calibration_date=equipment_data.calibration_date,
                            calibration_method=equipment_data.calibration_method,
                            installation_location=equipment_data.installation_location,
                            manufacturer=equipment_data.manufacturer,
                            manufacture_date=equipment_data.manufacture_date,
                            scale_value=equipment_data.scale_value,
                            management_level=equipment_data.management_level,
                            original_value=equipment_data.original_value,
                            status=equipment_data.status,
                            status_change_date=equipment_data.status_change_date,
                            certificate_number=equipment_data.certificate_number,
                            verification_result=equipment_data.verification_result,
                            verification_agency=equipment_data.verification_agency,
                            certificate_form=equipment_data.certificate_form,
                            notes=equipment_data.notes
                        )
                        
                        updated_equipment = equipment.update_equipment(
                            db, equipment_id=existing_equipment.id, equipment_update=update_data
                        )
                        
                        # 记录操作日志
                        create_audit_log(
                            db=db,
                            user_id=current_user.id,
                            equipment_id=existing_equipment.id,
                            action="导入更新",
                            description=f"通过Excel导入更新设备: {updated_equipment.name}"
                        )
                        
                        result["status"] = "更新"
                        result["message"] = "成功覆盖更新现有设备"
                        detailed_results.append(result)
                        update_count += 1
                    else:
                        result["status"] = "跳过"
                        result["message"] = f"计量编号'{equipment_data.serial_number}'已存在，如需覆盖请勾选覆盖选项"
                        detailed_results.append(result)
                        error_count += 1
                    continue
                
                # 创建新设备
                new_equipment = equipment.create_equipment(db, equipment_data)
                
                # 记录操作日志
                create_audit_log(
                    db=db,
                    user_id=current_user.id,
                    equipment_id=new_equipment.id,
                    action="导入",
                    description=f"通过Excel导入设备: {new_equipment.name}"
                )
                
                result["status"] = "成功"
                result["message"] = "成功导入新设备"
                detailed_results.append(result)
                success_count += 1
                
            except Exception as e:
                result["status"] = "失败"
                result["message"] = f"处理数据时发生错误: {str(e)}"
                detailed_results.append(result)
                error_count += 1
                continue
        
        # 记录总体操作日志
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="批量导入",
            description=f"批量导入设备数据，新增{success_count}条，更新{update_count}条，失败{error_count}条"
        )
        
        return {
            "message": "导入完成",
            "success_count": success_count,
            "update_count": update_count,
            "error_count": error_count,
            "detailed_results": detailed_results,
            "summary": {
                "total_rows": len(df),
                "processed": success_count + update_count + error_count,
                "success_rate": round((success_count + update_count) / len(df) * 100, 2) if len(df) > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.get("/export/all")
def export_all_equipments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """导出所有设备数据"""
    equipments = equipment.get_equipments(
        db, skip=0, limit=10000,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    df, dynamic_columns = generate_export_data(equipments, db)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账', index=False)
        
        # 添加动态列说明工作表
        if dynamic_columns:
            explanation_data = {
                '动态列': dynamic_columns,
                '说明': [
                    '负责人: 负责此设备类别的器具负责人账号名',
                    '状态变更时间: 设备状态为停用或报废时显示',
                    '证书编号: 检定方式为外检时显示',
                    '检定结果: 检定方式为外检时显示',
                    '检定机构: 检定方式为外检时显示',
                    '证书形式: 检定方式为外检时显示'
                ][:len(dynamic_columns)]
            }
            explanation_df = pd.DataFrame(explanation_data)
            # 替换NaN值为空字符串
            explanation_df = explanation_df.fillna('')
            explanation_df.to_excel(writer, sheet_name='动态列说明', index=False)
    
    output.seek(0)
    
    filename = f"设备台账_全部_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename, safe='')
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="导出全部",
        description=f"导出全部设备数据，共{len(equipments)}台"
    )
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/export/filtered")
def export_filtered_equipments(
    filters: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """根据筛选条件导出设备数据"""
    from app.schemas.schemas import EquipmentFilter
    
    equipment_filter = EquipmentFilter(**filters)
    equipments = equipment.filter_equipments(
        db, filters=equipment_filter, skip=0, limit=10000,
        user_id=current_user.id, is_admin=current_user.is_admin
    )
    
    df, dynamic_columns = generate_export_data(equipments, db)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='筛选设备', index=False)
        
        # 添加动态列说明工作表
        if dynamic_columns:
            explanation_data = {
                '动态列': dynamic_columns,
                '说明': [
                    '负责人: 负责此设备类别的器具负责人账号名',
                    '状态变更时间: 设备状态为停用或报废时显示',
                    '证书编号: 检定方式为外检时显示',
                    '检定结果: 检定方式为外检时显示',
                    '检定机构: 检定方式为外检时显示',
                    '证书形式: 检定方式为外检时显示'
                ][:len(dynamic_columns)]
            }
            explanation_df = pd.DataFrame(explanation_data)
            # 替换NaN值为空字符串
            explanation_df = explanation_df.fillna('')
            explanation_df.to_excel(writer, sheet_name='动态列说明', index=False)
    
    output.seek(0)
    
    filename = f"设备台账_筛选_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    encoded_filename = quote(filename, safe='')
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="导出筛选",
        description=f"导出筛选设备数据，共{len(equipments)}台"
    )
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
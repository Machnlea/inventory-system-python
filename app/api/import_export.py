from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
from urllib.parse import quote
from datetime import datetime
from app.db.database import get_db
from app.crud import equipment, departments, categories
from app.schemas.schemas import Equipment, ImportTemplate
from app.api.auth import get_current_admin_user
from app.api.audit_logs import create_audit_log

router = APIRouter()

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
        '使用部门': ['树脂车间', '工业漆车间', '质检部'],
        '计量器具类别': ['铂热电阻', '玻璃量器', '压力表'],
        '计量器具名称': ['铂热电阻温度计', '玻璃量筒', '压力表'],
        '型号/规格': ['PT100', '500ml A级', 'Y-100'],
        '准确度等级': ['A级', 'A级', '1.6级'],
        '测量范围': ['-200~850℃', '0~500ml', '0~1.6MPa'],
        '计量编号': ['PT001', 'GL001', 'YL001'],
        '检定周期': ['半年', '1年', '2年'],
        '检定（校准）日期': ['2024-01-15', '2024-03-20', '2024-06-01'],
        '有效期至': ['2024-07-14', '2025-03-19', '2026-05-31'],
        '安装地点': ['1号反应釜', '质检室', '实验室'],
        '分度值': ['0.1℃', '1ml', '0.01MPa'],
        '制造厂家': ['上海仪表厂', '北京玻璃厂', '深圳仪表厂'],
        '出厂日期': ['2023-12-01', '2023-11-15', '2023-10-20'],
        '检定方式': ['送检', '现场检定', '送检'],
        '管理级别': ['B级', '校准证书', 'C级'],
        '原值/元': [1500, 800, 1200],
        '设备状态': ['在用', '在用', '在用'],
        '状态变更时间': ['', '', ''],
        '备注': ['正常使用', '新购设备', '半年检定周期示例']
    }
    
    df = pd.DataFrame(template_data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账模板', index=False)
        
        # 添加说明工作表
        explanation_data = {
            '字段名': [
                '使用部门', '计量器具类别', '计量器具名称', '型号/规格', '准确度等级', '测量范围',
                '计量编号', '检定周期', '检定（校准）日期', '有效期至', 
                '安装地点', '分度值', '制造厂家', '出厂日期', '检定方式', '管理级别', '原值/元', '设备状态', '状态变更时间', '备注'
            ],
            '是否必填': [
                '是', '是', '是', '是', '是', '否',
                '是', '是', '是', '否', 
                '否', '否', '否', '否', '否', '否', '否', '否', '否', '否'
            ],
            '说明': [
                '必须是系统中已存在的部门名称',
                '必须是系统中已存在的计量器具类别名称',
                '设备的具体名称',
                '设备的型号或规格',
                '设备的准确度等级',
                '设备的测量范围',
                '设备的唯一编号',
                '只能填写"半年"、"1年"或"2年"',
                '格式：YYYY-MM-DD，如2024-01-15',
                '自动计算，可不填',
                '设备的安装位置',
                '设备的分度值，如0.01mm',
                '设备制造商名称',
                '格式：YYYY-MM-DD',
                '检定方式说明',
                '管理级别：B级/C级/校准证书/检定证书',
                '设备原值，单位：元',
                '设备状态：在用/停用/报废',
                '状态变更时间，格式：YYYY-MM-DD',
                '备注信息'
            ]
        }
        
        explanation_df = pd.DataFrame(explanation_data)
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
        
        # 验证必需的列
        required_columns = [
            '使用部门', '计量器具类别', '计量器具名称', '型号/规格', '准确度等级',
            '检定周期', '检定（校准）日期', '计量编号'
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
                category = categories.get_category_by_name(db, str(row['计量器具类别']))
                if not category:
                    result["status"] = "失败"
                    result["message"] = f"计量器具类别'{row['计量器具类别']}'不存在"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证检定周期
                if str(row['检定周期']) not in ['半年', '1年', '2年']:
                    result["status"] = "失败"
                    result["message"] = "检定周期必须是'半年'、'1年'或'2年'"
                    detailed_results.append(result)
                    error_count += 1
                    continue
                
                # 验证日期格式
                try:
                    calibration_date = pd.to_datetime(row['检定（校准）日期']).date()
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
                
                # 创建设备数据
                from app.schemas.schemas import EquipmentCreate, EquipmentUpdate
                equipment_data = EquipmentCreate(
                    department_id=department.id,
                    category_id=category.id,
                    name=str(row['计量器具名称']),
                    model=str(row['型号/规格']),
                    accuracy_level=str(row['准确度等级']),
                    measurement_range=str(row.get('测量范围', '')),
                    calibration_cycle=str(row['检定周期']),
                    calibration_date=calibration_date,
                    calibration_method=str(row.get('检定方式', '')),
                    serial_number=str(row['计量编号']),
                    installation_location=str(row.get('安装地点', '')),
                    manufacturer=str(row.get('制造厂家', '')),
                    manufacture_date=manufacture_date,
                    scale_value=str(row.get('分度值', '')),
                    management_level=str(row.get('管理级别', '')),
                    original_value=int(row.get('原值/元', 0)) if pd.notna(row.get('原值/元')) else None,
                    status=str(row.get('设备状态', '在用')),
                    notes=str(row.get('备注', ''))
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
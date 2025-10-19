from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import io
import csv
import threading
import time
from datetime import datetime

import pandas as pd

from app.db.database import get_db, SessionLocal
from app.core.config import settings
from app.crud import import_jobs as jobs_crud, departments, categories, equipment
from app.schemas.import_job import ImportJobStatus
from app.api.auth import get_current_admin_user, get_current_user
from app.api.audit_logs import log_equipment_operation
from app.utils.auto_id import generate_internal_id

router = APIRouter()


def _ensure_import_dirs():
    os.makedirs(settings.IMPORT_TEMP_DIR, exist_ok=True)


def _import_file_path(job_id: str) -> str:
    return os.path.join(settings.IMPORT_TEMP_DIR, f"{job_id}.xlsx")


def _error_file_path(job_id: str) -> str:
    return os.path.join(settings.IMPORT_TEMP_DIR, f"{job_id}_errors.csv")


@router.post("/excel/start")
async def start_excel_import(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    overwrite: str = Form("false"),
    dry_run: str = Form("false"),
    defer_seconds: Optional[int] = Form(0),  # 可选：为了测试/演示延迟启动
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """启动Excel导入任务（异步）"""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")

    _ensure_import_dirs()

    job_id = str(uuid.uuid4())
    # 保存上传文件到临时目录（以job_id命名，便于定位）
    file_bytes = await file.read()
    fpath = _import_file_path(job_id)
    with open(fpath, "wb") as f:
        f.write(file_bytes)

    # 创建任务记录
    job = jobs_crud.create_job(db, job_id=job_id, uploader_id=current_user.id, filename=file.filename)

    # 启动后台线程处理任务
    def _launch():
        th = threading.Thread(
            target=_process_import_job,
            args=(job_id, bool(overwrite.lower() in ["true", "1", "yes", "on"]), bool(dry_run.lower() in ["true", "1", "yes", "on"]), int(defer_seconds or 0)),
            daemon=True,
        )
        th.start()

    background_tasks.add_task(_launch)

    return {"job_id": job_id}


@router.get("/excel/{job_id}/status", response_model=ImportJobStatus)
async def get_import_status(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = jobs_crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not current_user.is_admin and int(job.uploader_id) != int(current_user.id):
        raise HTTPException(status_code=403, detail="没有权限查看该任务")

    # 构建状态响应
    status_data = ImportJobStatus.model_validate(job)

    # 错误文件下载链接
    err_path = _error_file_path(job_id)
    if os.path.exists(err_path):
        status_data.error_report_url = f"/api/imports/excel/{job_id}/errors"

    # 是否可取消
    status_data.can_cancel = job.status in ["queued", "running"] and (current_user.is_admin or int(job.uploader_id) == int(current_user.id))

    return status_data


@router.get("/excel/{job_id}/errors")
async def download_error_report(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = jobs_crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not current_user.is_admin and int(job.uploader_id) != int(current_user.id):
        raise HTTPException(status_code=403, detail="没有权限")
    err_path = _error_file_path(job_id)
    if not os.path.exists(err_path):
        raise HTTPException(status_code=404, detail="错误明细文件不存在")
    return FileResponse(path=err_path, filename=f"import_errors_{job_id}.csv", media_type="text/csv")


@router.post("/excel/{job_id}/cancel")
async def cancel_import(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_admin_user)):
    job = jobs_crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if job.status not in ["queued", "running"]:
        return {"message": "任务已结束，无法取消", "status": job.status}

    jobs_crud.set_status(db, job_id, status="canceled")
    return {"message": "已请求取消"}


# ---------------- 内部实现：导入处理逻辑 ----------------

def _process_import_job(job_id: str, overwrite: bool, dry_run: bool, defer_seconds: int = 0):
    session: Session = SessionLocal()
    try:
        job = jobs_crud.get_job(session, job_id)
        if not job:
            return
        # 可能由cancel先行设置为canceled
        if job.status == "canceled":
            jobs_crud.set_status(session, job_id, status="canceled", set_finished=True)
            return

        jobs_crud.set_status(session, job_id, status="running", set_started=True)

        if defer_seconds and defer_seconds > 0:
            time.sleep(defer_seconds)
            # 再次检查取消
            job = jobs_crud.get_job(session, job_id)
            if job and job.status == "canceled":
                jobs_crud.set_status(session, job_id, status="canceled", set_finished=True)
                return

        path = _import_file_path(job_id)
        if not os.path.exists(path):
            jobs_crud.set_status(session, job_id, status="failed", error_summary="找不到上传文件", set_finished=True)
            return

        # 读取Excel到DataFrame（为简单起见）
        with open(path, "rb") as f:
            contents = f.read()
        df = pd.read_excel(io.BytesIO(contents))
        df = df.fillna("")

        total_rows = len(df)
        jobs_crud.update_progress(session, job_id, processed_rows=0, total_rows=total_rows, status="running")

        # 必需列
        required_columns = [
            '使用部门', '设备类别', '计量器具名称', '型号/规格', '准确度等级',
            '检定周期', '检定(校准)日期', '检定方式', '检定结果'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            jobs_crud.set_status(
                session,
                job_id,
                status="failed",
                error_summary=f"缺少必需的列: {', '.join(missing_columns)}",
                set_finished=True,
            )
            return

        processed = 0
        error_rows = []
        success_count = 0
        update_count = 0
        error_count = 0
        batch_commit = 0
        BATCH_SIZE = max(1, int(getattr(settings, 'IMPORT_BATCH_SIZE', 1000)))

        for index, row in df.iterrows():
            processed += 1
            # 取消检查（每行）
            cur_job = jobs_crud.get_job(session, job_id)
            if cur_job and cur_job.status == "canceled":
                jobs_crud.set_status(session, job_id, status="canceled", set_finished=True)
                return

            row_number = int(float(index)) + 2  # Excel行号从2开始
            try:
                # 验证部门
                department = departments.get_department_by_name(session, str(row['使用部门']))
                if not department:
                    raise ValueError(f"部门'{row['使用部门']}'不存在")

                # 验证设备类别
                category = categories.get_category_by_name(session, str(row['设备类别']))
                if not category:
                    raise ValueError(f"设备类别'{row['设备类别']}'不存在")

                # 验证计量器具名称
                equipment_name = str(row['计量器具名称'])
                if category.predefined_names:
                    if equipment_name not in category.predefined_names:
                        # 提供更友好的错误信息，包含前几个可用名称
                        available_names = ', '.join(category.predefined_names[:5])
                        if len(category.predefined_names) > 5:
                            available_names += f" 等(共{len(category.predefined_names)}种)"
                        raise ValueError(f"计量器具名称'{equipment_name}'不在设备类别'{category.name}'的预定义器具名称列表中。可用名称包括：{available_names}")

                # 验证检定周期
                calibration_cycle = str(row['检定周期'])
                if calibration_cycle not in ['6个月', '12个月', '24个月', '36个月', '随坏随换']:
                    raise ValueError("检定周期必须是'6个月'、'12个月'、'24个月'、'36个月'或'随坏随换'")

                # 验证检定方式
                calibration_method = str(row['检定方式'])
                if calibration_method not in ['内检', '外检']:
                    raise ValueError("检定方式必须是'内检'或'外检'")

                # 验证检定结果
                calibration_result = str(row['检定结果'])
                if calibration_result not in ['合格', '不合格']:
                    raise ValueError("检定结果必须是'合格'或'不合格'")

                # 外检必填字段
                if calibration_method == '外检':
                    external_fields = {
                        '证书编号': row.get('证书编号', ''),
                        '检定机构': row.get('检定机构', ''),
                        '证书形式': row.get('证书形式', '')
                    }
                    for field_name, field_value in external_fields.items():
                        if pd.isna(field_value) or str(field_value).strip() == '':
                            raise ValueError(f"外检时'{field_name}'为必填项")
                    certificate_form = str(row.get('证书形式', '')).strip()
                    if certificate_form not in ['校准证书', '检定证书']:
                        raise ValueError("证书形式必须是'校准证书'或'检定证书'")

                # 日期
                calibration_date = None
                calibration_date_str = str(row['检定(校准)日期']).strip()
                if calibration_cycle == "随坏随换":
                    if calibration_date_str and calibration_date_str != '':
                        try:
                            calibration_date_parsed = pd.to_datetime(calibration_date_str).date()
                            if pd.notna(calibration_date_parsed):
                                calibration_date = calibration_date_parsed
                        except Exception:
                            calibration_date = None
                else:
                    if not calibration_date_str or calibration_date_str == '':
                        raise ValueError("检定(校准)日期为必填项")
                    try:
                        calibration_date_parsed = pd.to_datetime(calibration_date_str).date()
                        if pd.notna(calibration_date_parsed):
                            calibration_date = calibration_date_parsed
                        else:
                            raise ValueError("检定日期格式错误，请使用YYYY-MM-DD格式")
                    except Exception:
                        raise ValueError("检定日期格式错误，请使用YYYY-MM-DD格式")

                manufacture_date = None
                if pd.notna(row.get('出厂日期')) and str(row.get('出厂日期')).strip() != '':
                    try:
                        manufacture_date_parsed = pd.to_datetime(row['出厂日期']).date()
                        if pd.notna(manufacture_date_parsed):
                            manufacture_date = manufacture_date_parsed
                    except Exception:
                        raise ValueError("出厂日期格式错误，请使用YYYY-MM-DD格式")

                # 有效期
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
                    valid_until = calibration_date + timedelta(days=cycle_days[calibration_cycle] - 1) if calibration_date else None

                # 管理级别
                management_level = str(row.get('管理级别', '')) if calibration_method == '内检' else '-'

                # 状态
                status_change_date = None
                equipment_status = str(row.get('设备状态', '在用')).strip()
                if equipment_status not in ['在用', '停用', '报废']:
                    raise ValueError(f"设备状态'{equipment_status}'不合法，只能是'在用'、'停用'或'报废'")
                if equipment_status in ['停用', '报废']:
                    status_change_date_input = row.get('状态变更时间')
                    if pd.notna(status_change_date_input) and str(status_change_date_input).strip() != '':
                        try:
                            status_change_date_parsed = pd.to_datetime(status_change_date_input).date()
                            if pd.notna(status_change_date_parsed):
                                status_change_date = status_change_date_parsed
                        except Exception:
                            raise ValueError("状态变更时间格式错误，请使用YYYY-MM-DD格式")

                # 自动生成内部编号
                generated_internal_id = generate_internal_id(session, int(float(category.id)), str(row['计量器具名称']))

                # 原值字段
                original_value = None
                if pd.notna(row.get('原值/元')) and str(row['原值/元']).strip() != '':
                    try:
                        original_value = float(str(row['原值/元']).strip())
                    except (ValueError, TypeError):
                        original_value = None

                from app.schemas.schemas import EquipmentCreate, EquipmentUpdate
                equipment_data = EquipmentCreate(
                    department_id=int(float(department.id)),
                    category_id=int(float(category.id)),
                    name=str(row['计量器具名称']),
                    model=str(row['型号/规格']),
                    accuracy_level=str(row['准确度等级']),
                    measurement_range=str(row.get('测量范围', '')) if pd.notna(row.get('测量范围')) else '',
                    calibration_cycle=calibration_cycle,
                    calibration_date=calibration_date,
                    calibration_method=calibration_method,
                    current_calibration_result=calibration_result,
                    internal_id=generated_internal_id,
                    manufacturer_id=str(row.get('出厂编号', '')) if pd.notna(row.get('出厂编号')) else None,
                    installation_location=str(row.get('安装地点', '')) if pd.notna(row.get('安装地点')) else '',
                    manufacturer=str(row.get('制造厂家', '')) if pd.notna(row.get('制造厂家')) else '',
                    manufacture_date=manufacture_date,
                    scale_value=str(row.get('分度值', '')) if pd.notna(row.get('分度值')) else '',
                    management_level=management_level,
                    original_value=original_value,
                    status=equipment_status,
                    status_change_date=status_change_date,
                    certificate_number=str(row.get('证书编号', '')) if calibration_method == '外检' and pd.notna(row.get('证书编号')) else '',
                    verification_agency=str(row.get('检定机构', '')) if calibration_method == '外检' and pd.notna(row.get('检定机构')) else '',
                    certificate_form=str(row.get('证书形式', '')) if calibration_method == '外检' and pd.notna(row.get('证书形式')) else '',
                    notes=str(row.get('备注', '')) if pd.notna(row.get('备注')) else ''
                )

                # 出厂编号为必填且唯一（作为业务唯一键）
                manufacturer_id = str(row.get('出厂编号', '')).strip()
                if not manufacturer_id:
                    raise ValueError("出厂编号为必填项，不能为空")

                from app.models.models import Equipment as EquipmentModel
                existing_equipment = session.query(EquipmentModel).filter(EquipmentModel.manufacturer_id == manufacturer_id).first()

                if existing_equipment:
                    if overwrite and not dry_run:
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
                            verification_agency=equipment_data.verification_agency,
                            certificate_form=equipment_data.certificate_form,
                            notes=equipment_data.notes
                        )
                        updated_equipment = equipment.update_equipment(
                            session, equipment_id=int(float(existing_equipment.id)), equipment_update=update_data
                        )
                        # 审计日志
                        log_equipment_operation(
                            db=session,
                            user_id=job.uploader_id,
                            equipment_id=int(float(existing_equipment.id)),
                            action="导入更新",
                            description=f"通过Excel导入更新设备: {updated_equipment.name if updated_equipment else '未知设备'}"
                        )
                        update_count += 1
                    else:
                        raise ValueError(f"出厂编号'{manufacturer_id}'的设备已存在，无法重复导入")
                else:
                    if not dry_run:
                        new_equipment = equipment.create_equipment(session, equipment_data)
                        log_equipment_operation(
                            db=session,
                            user_id=job.uploader_id,
                            equipment_id=int(float(new_equipment.id)),
                            action="导入",
                            description=f"通过Excel导入设备: {new_equipment.name}"
                        )
                        success_count += 1

                batch_commit += 1
                if batch_commit >= max(1, min(2000, BATCH_SIZE)) and not dry_run:
                    session.commit()
                    batch_commit = 0

            except Exception as e:
                error_count += 1
                error_rows.append({
                    "row": row_number,
                    "name": str(row.get('计量器具名称', '')),
                    "manufacturer_id": str(row.get('出厂编号', '')),
                    "message": str(e),
                })
                # 不抛出，继续处理

            # 更新进度（每行）
            jobs_crud.update_progress(session, job_id, processed_rows=processed)

        # 最后一批提交
        if batch_commit and not dry_run:
            session.commit()

        # 生成错误报告
        error_summary = None
        if error_rows:
            err_path = _error_file_path(job_id)
            with open(err_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["row", "manufacturer_id", "name", "message"])
                writer.writeheader()
                for r in error_rows:
                    writer.writerow(r)
            # 错误摘要（前N条）
            N = int(getattr(settings, 'IMPORT_ERROR_MAX_LINES', 50))
            preview = error_rows[:N]
            error_summary = "\n".join([f"第{r['row']}行: {r['message']}" for r in preview])

        # 完成
        jobs_crud.set_status(
            session,
            job_id,
            status="succeeded",
            progress=100,
            processed_rows=processed,
            total_rows=total_rows,
            error_summary=error_summary,
            set_finished=True,
        )

        # 清理上传文件
        try:
            os.remove(path)
        except Exception:
            pass

    except Exception as e:
        try:
            jobs_crud.set_status(session, job_id, status="failed", error_summary=str(e), set_finished=True)
        except Exception:
            pass
    finally:
        session.close()

"""
检定历史记录 API 接口
处理设备检定信息更新和历史记录查询
"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
import json

from app.db.database import get_db
from app.models.models import User, Equipment, CalibrationHistory, EquipmentAttachment
from app.crud import calibration_history as crud_calibration
from app.crud import equipment as crud_equipment
from app.crud import attachments as crud_attachments
from app.schemas.calibration import (
    CalibrationHistoryCreate, CalibrationHistoryUpdate, CalibrationHistoryResponse,
    CalibrationHistoryWithDetails, CalibrationStatistics, CalibrationUpdateRequest,
    BatchCalibrationUpdateRequest, CalibrationDueReminder, CalibrationHistoryFilter
)
from app.schemas.schemas import EquipmentAttachmentCreate
from app.api.auth import get_current_user, get_current_admin_user
from app.utils.files import save_uploaded_file, get_file_path
from app.utils.audit import log_audit


router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("/equipment/{equipment_id}/last-external-info")
async def get_equipment_last_external_calibration_info(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备上次外检信息，用于更新时预填充
    
    - **equipment_id**: 设备ID
    - **returns**: 上次外检信息（检定机构、证书形式）
    """
    
    # 验证设备存在
    equipment = crud_equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限检查（管理员或设备管理者）
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看设备外检信息"
        )
    
    # 获取上次外检信息
    last_external_info = get_last_external_calibration_info(db, equipment_id)
    
    if last_external_info:
        source_text = "检定历史记录" if last_external_info.get("source") == "history" else "设备基本信息"
        return {
            "success": True,
            "verification_agency": last_external_info["verification_agency"],
            "certificate_form": last_external_info["certificate_form"],
            "source": last_external_info.get("source"),
            "message": f"成功获取上次外检信息（来源：{source_text}）"
        }
    else:
        return {
            "success": False,
            "verification_agency": None,
            "certificate_form": None,
            "source": None,
            "message": "暂无外检信息记录"
        }


@router.post("/equipment/{equipment_id}/update", response_model=CalibrationHistoryResponse)
async def update_equipment_calibration(
    equipment_id: int,
    calibration_data: CalibrationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新设备检定信息
    
    - **equipment_id**: 设备ID
    - **calibration_data**: 检定更新数据
    
    业务逻辑：
    1. 验证设备存在性和用户权限
    2. 根据检定方式验证必填字段
    3. 更新设备基础信息
    4. 创建检定历史记录
    5. 处理检定不合格的状态变更
    6. 记录审计日志
    """
    
    # 获取设备信息
    equipment = crud_equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限检查（管理员或设备管理者）
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新设备检定信息"
        )
    
    # 检查设备状态（已报废设备不允许更新）
    if equipment.status == "报废":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已报废设备不允许更新检定信息"
        )
    
    # 外检字段验证和自动填充
    if equipment.calibration_method == "外检":
        if not calibration_data.certificate_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的证书编号为必填项"
            )
        
        # 如果检定机构或证书形式未提供，尝试从上次外检记录中获取
        if not calibration_data.verification_agency or not calibration_data.certificate_form:
            last_external_info = get_last_external_calibration_info(db, equipment_id)
            
            if last_external_info:
                # 自动填充上次的外检信息
                if not calibration_data.verification_agency:
                    calibration_data.verification_agency = last_external_info["verification_agency"]
                if not calibration_data.certificate_form:
                    calibration_data.certificate_form = last_external_info["certificate_form"]
        
        # 验证必填字段（经过自动填充后）
        if not calibration_data.verification_agency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的检定机构为必填项，且无历史记录可自动填充"
            )
        if not calibration_data.certificate_form:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的证书形式为必填项，且无历史记录可自动填充"
            )
    
    try:
        # 计算有效期
        valid_until_date = calculate_valid_until(
            calibration_data.calibration_date, 
            equipment.calibration_cycle
        )
        
        # 更新设备基础信息
        equipment.calibration_date = calibration_data.calibration_date
        equipment.valid_until = valid_until_date
        equipment.current_calibration_result = calibration_data.calibration_result
        equipment.certificate_number = calibration_data.certificate_number
        equipment.certificate_form = calibration_data.certificate_form
        equipment.verification_agency = calibration_data.verification_agency
        equipment.calibration_notes = calibration_data.notes
        
        # 处理设备状态变更
        if calibration_data.calibration_result == "不合格":
            # 检定不合格，设备状态设为报废
            equipment.status = "报废"
            equipment.status_change_date = calibration_data.status_change_date or date.today()
            equipment.disposal_reason = calibration_data.disposal_reason
        elif calibration_data.calibration_result == "合格":
            # 检定合格，根据用户选择设置设备状态
            if calibration_data.equipment_status == "停用":
                equipment.status = "停用"
                equipment.status_change_date = calibration_data.status_change_date or date.today()
                equipment.disposal_reason = calibration_data.disposal_reason  # 停用原因
            else:
                # 默认为在用状态
                equipment.status = "在用"
                equipment.status_change_date = None
                equipment.disposal_reason = None
            
        # 创建检定历史记录
        history_data = CalibrationHistoryCreate(
            equipment_id=equipment_id,
            calibration_date=calibration_data.calibration_date,
            valid_until=valid_until_date,
            calibration_method=equipment.calibration_method,
            calibration_result=calibration_data.calibration_result,
            certificate_number=calibration_data.certificate_number,
            certificate_form=calibration_data.certificate_form,
            verification_agency=calibration_data.verification_agency,
            notes=calibration_data.notes
        )
        
        db_history = crud_calibration.create_calibration_history(
            db, history_data, current_user.id
        )
        
        # 提交设备更新
        db.commit()
        db.refresh(equipment)
        
        # 记录审计日志
        log_audit(
            db=db,
            user_id=current_user.id,
            equipment_id=equipment_id,
            action="更新检定信息",
            description=f"更新检定信息，结果：{calibration_data.calibration_result}，有效期至：{valid_until_date}",
            old_value=None,
            new_value=f"检定结果: {calibration_data.calibration_result}, 有效期: {valid_until_date}"
        )
        
        return db_history
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新检定信息失败: {str(e)}"
        )


@router.post("/equipment/{equipment_id}/update-with-files", response_model=CalibrationHistoryResponse)
async def update_equipment_calibration_with_files(
    equipment_id: int,
    # Form fields
    calibration_date: str = Form(..., description="检定日期"),
    calibration_result: str = Form(..., description="检定结果"),
    certificate_number: Optional[str] = Form(None, description="证书编号"),
    certificate_form: Optional[str] = Form(None, description="证书形式"),
    verification_agency: Optional[str] = Form(None, description="检定机构"),
    notes: Optional[str] = Form(None, description="备注"),
    status_change_date: Optional[str] = Form(None, description="状态变更日期"),
    disposal_reason: Optional[str] = Form(None, description="报废原因"),
    # File uploads
    certificate_files: Optional[List[UploadFile]] = File(None, description="证书附件"),
    disposal_files: Optional[List[UploadFile]] = File(None, description="报废附件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新设备检定信息（支持文件上传）
    
    - **equipment_id**: 设备ID
    - **calibration_date**: 检定日期
    - **calibration_result**: 检定结果
    - **certificate_files**: 证书附件文件列表
    - **disposal_files**: 报废附件文件列表
    - 其他字段与普通更新接口相同
    """
    
    # 获取设备信息
    equipment = crud_equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 权限检查（管理员或设备管理者）
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限更新设备检定信息"
        )
    
    # 检查设备状态（已报废设备不允许更新）
    if equipment.status == "报废":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已报废设备不允许更新检定信息"
        )
    
    # 转换日期格式
    try:
        cal_date = datetime.strptime(calibration_date, "%Y-%m-%d").date()
        status_change_date_obj = None
        if status_change_date:
            status_change_date_obj = datetime.strptime(status_change_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，请使用YYYY-MM-DD格式"
        )
    
    # 外检字段验证和自动填充
    if equipment.calibration_method == "外检":
        if not certificate_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的证书编号为必填项"
            )
        
        # 如果检定机构或证书形式未提供，尝试从上次外检记录中获取
        if not verification_agency or not certificate_form:
            last_external_info = get_last_external_calibration_info(db, equipment_id)
            
            if last_external_info:
                # 自动填充上次的外检信息
                if not verification_agency:
                    verification_agency = last_external_info["verification_agency"]
                if not certificate_form:
                    certificate_form = last_external_info["certificate_form"]
        
        # 验证必填字段（经过自动填充后）
        if not verification_agency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的检定机构为必填项，且无历史记录可自动填充"
            )
        if not certificate_form:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="外检设备的证书形式为必填项，且无历史记录可自动填充"
            )
    
    try:
        # 计算有效期
        valid_until_date = calculate_valid_until(cal_date, equipment.calibration_cycle)
        
        # 更新设备基础信息
        equipment.calibration_date = cal_date
        equipment.valid_until = valid_until_date
        equipment.current_calibration_result = calibration_result
        equipment.certificate_number = certificate_number
        equipment.certificate_form = certificate_form
        equipment.verification_agency = verification_agency
        equipment.calibration_notes = notes
        
        # 处理检定不合格的情况
        if calibration_result == "不合格":
            equipment.status = "报废"
            equipment.status_change_date = status_change_date_obj or date.today()
            equipment.disposal_reason = disposal_reason
        
        # 创建检定历史记录
        history_data = CalibrationHistoryCreate(
            equipment_id=equipment_id,
            calibration_date=cal_date,
            valid_until=valid_until_date,
            calibration_method=equipment.calibration_method,
            calibration_result=calibration_result,
            certificate_number=certificate_number,
            certificate_form=certificate_form,
            verification_agency=verification_agency,
            notes=notes
        )
        
        db_history = crud_calibration.create_calibration_history(
            db, history_data, current_user.id
        )
        
        # 处理文件上传
        uploaded_files = []
        
        # 上传证书文件
        if certificate_files:
            for cert_file in certificate_files:
                if cert_file.filename:
                    # 保存文件
                    file_info = await save_uploaded_file(cert_file, "certificates")
                    
                    # 创建附件记录
                    attachment_data = EquipmentAttachmentCreate(
                        equipment_id=equipment_id,
                        calibration_history_id=db_history.id,
                        filename=file_info["filename"],
                        original_filename=file_info["original_filename"],
                        file_path=file_info["file_path"],
                        file_size=file_info["file_size"],
                        file_type=file_info["file_type"],
                        mime_type=file_info["mime_type"],
                        description=f"检定证书 - {cal_date}",
                        is_certificate=True,
                        certificate_type="检定证书"
                    )
                    
                    attachment = crud_attachments.create_equipment_attachment(
                        db=db, attachment=attachment_data, uploaded_by=current_user.id
                    )
                    uploaded_files.append(attachment)
        
        # 上传报废文件
        if disposal_files and calibration_result == "不合格":
            for disposal_file in disposal_files:
                if disposal_file.filename:
                    # 保存文件
                    file_info = await save_uploaded_file(disposal_file, "disposal")
                    
                    # 创建附件记录
                    attachment_data = EquipmentAttachmentCreate(
                        equipment_id=equipment_id,
                        calibration_history_id=db_history.id,
                        filename=file_info["filename"],
                        original_filename=file_info["original_filename"],
                        file_path=file_info["file_path"],
                        file_size=file_info["file_size"],
                        file_type=file_info["file_type"],
                        mime_type=file_info["mime_type"],
                        description=f"报废文件 - {cal_date}",
                        is_certificate=False,
                        certificate_type=None
                    )
                    
                    attachment = crud_attachments.create_equipment_attachment(
                        db=db, attachment=attachment_data, uploaded_by=current_user.id
                    )
                    uploaded_files.append(attachment)
        
        # 提交所有更改
        db.commit()
        db.refresh(equipment)
        db.refresh(db_history)
        
        # 记录审计日志
        file_names = [att.original_filename for att in uploaded_files if att.original_filename]
        file_desc = f", 上传文件: {', '.join(file_names)}" if file_names else ""
        
        log_audit(
            db=db,
            user_id=current_user.id,
            equipment_id=equipment_id,
            action="更新检定信息（含文件）",
            description=f"更新检定信息，结果：{calibration_result}，有效期至：{valid_until_date}{file_desc}",
            old_value=None,
            new_value=f"检定结果: {calibration_result}, 有效期: {valid_until_date}, 文件数: {len(uploaded_files)}"
        )
        
        return db_history
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新检定信息失败: {str(e)}"
        )


@router.post("/equipment/batch-update")
async def batch_update_equipment_calibration(
    batch_data: BatchCalibrationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量更新设备检定信息
    
    - **batch_data**: 批量更新数据（设备ID列表和对应的检定信息）
    
    返回每个设备的处理结果
    """
    
    # 权限检查
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限批量更新设备检定信息"
        )
    
    results = []
    
    for i, (equipment_id, calibration_data) in enumerate(
        zip(batch_data.equipment_ids, batch_data.calibration_updates)
    ):
        try:
            # 调用单个设备更新接口
            result = await update_equipment_calibration(
                equipment_id, calibration_data, db, current_user
            )
            results.append({
                "equipment_id": equipment_id,
                "success": True,
                "history_id": result.id,
                "message": "更新成功"
            })
        except HTTPException as e:
            results.append({
                "equipment_id": equipment_id,
                "success": False,
                "error": e.detail,
                "message": "更新失败"
            })
        except Exception as e:
            results.append({
                "equipment_id": equipment_id,
                "success": False,
                "error": str(e),
                "message": "更新失败"
            })
    
    return {
        "total": len(batch_data.equipment_ids),
        "success_count": sum(1 for r in results if r["success"]),
        "failed_count": sum(1 for r in results if not r["success"]),
        "results": results
    }


@router.get("/equipment/{equipment_id}/history", response_model=List[CalibrationHistoryWithDetails])
async def get_equipment_calibration_history(
    equipment_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备检定历史记录
    
    - **equipment_id**: 设备ID
    - **skip**: 跳过记录数
    - **limit**: 限制记录数
    """
    
    # 验证设备存在
    equipment = crud_equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 获取检定历史
    histories = crud_calibration.get_calibration_histories_by_equipment(
        db, equipment_id, skip, limit
    )
    
    # 组装详细信息
    result = []
    for history in histories:
        history_dict = CalibrationHistoryResponse.from_orm(history).__dict__
        
        # 添加设备信息
        history_dict["equipment_name"] = equipment.name
        history_dict["equipment_internal_id"] = equipment.internal_id
        history_dict["equipment_model"] = equipment.model
        history_dict["department_name"] = equipment.department.name if equipment.department else None
        history_dict["category_name"] = equipment.category.name if equipment.category else None
        
        # 添加创建者信息
        if history.creator:
            history_dict["creator_username"] = history.creator.username
        
        result.append(CalibrationHistoryWithDetails(**history_dict))
    
    return result


@router.get("/history", response_model=List[CalibrationHistoryWithDetails])
async def get_calibration_histories(
    filter_params: CalibrationHistoryFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取检定历史记录列表（支持过滤）
    
    支持按设备、检定方式、检定结果、日期范围等条件过滤
    """
    
    histories = crud_calibration.get_calibration_histories(
        db=db,
        skip=filter_params.skip,
        limit=filter_params.limit,
        equipment_id=filter_params.equipment_id,
        calibration_method=filter_params.calibration_method,
        calibration_result=filter_params.calibration_result,
        start_date=filter_params.start_date,
        end_date=filter_params.end_date
    )
    
    # 预加载关联数据
    histories_with_details = db.query(CalibrationHistory).options(
        joinedload(CalibrationHistory.equipment).joinedload(Equipment.department),
        joinedload(CalibrationHistory.equipment).joinedload(Equipment.category),
        joinedload(CalibrationHistory.creator)
    ).filter(
        CalibrationHistory.id.in_([h.id for h in histories])
    ).all()
    
    result = []
    for history in histories_with_details:
        history_dict = CalibrationHistoryResponse.from_orm(history).__dict__
        
        # 添加设备信息
        if history.equipment:
            history_dict["equipment_name"] = history.equipment.name
            history_dict["equipment_internal_id"] = history.equipment.internal_id
            history_dict["equipment_model"] = history.equipment.model
            history_dict["department_name"] = history.equipment.department.name if history.equipment.department else None
            history_dict["category_name"] = history.equipment.category.name if history.equipment.category else None
        
        # 添加创建者信息
        if history.creator:
            history_dict["creator_username"] = history.creator.username
        
        result.append(CalibrationHistoryWithDetails(**history_dict))
    
    return result


@router.get("/statistics", response_model=CalibrationStatistics)
async def get_calibration_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取检定统计信息
    
    包括总数、按方式分布、按结果分布、近期检定数量等
    """
    
    # 权限检查（管理员或经理）
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看检定统计信息"
        )
    
    stats = crud_calibration.get_calibration_statistics(db)
    return CalibrationStatistics(**stats)


@router.get("/due-reminders", response_model=List[CalibrationDueReminder])
async def get_calibration_due_reminders(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取即将到期的检定提醒
    
    - **days**: 提前多少天提醒（默认30天）
    """
    
    due_histories = crud_calibration.get_calibration_due_soon(db, days)
    
    result = []
    for history in due_histories:
        equipment = history.equipment
        days_until_due = (history.valid_until - date.today()).days
        
        reminder = CalibrationDueReminder(
            equipment_id=equipment.id,
            equipment_name=equipment.name,
            internal_id=equipment.internal_id,
            department_name=equipment.department.name if equipment.department else "",
            calibration_date=history.calibration_date,
            valid_until=history.valid_until,
            days_until_due=days_until_due
        )
        result.append(reminder)
    
    return sorted(result, key=lambda x: x.days_until_due)


@router.post("/upload-certificate/{history_id}")
async def upload_calibration_certificate(
    history_id: int,
    file: UploadFile = File(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传检定证书附件
    
    - **history_id**: 检定历史记录ID
    - **file**: 上传的文件
    - **description**: 文件描述
    """
    
    # 验证检定历史记录存在
    history = crud_calibration.get_calibration_history(db, history_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检定历史记录不存在"
        )
    
    # 权限检查
    if not current_user.is_admin and current_user.user_type != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限上传检定证书"
        )
    
    try:
        # 保存文件
        file_info = await save_uploaded_file(file, "calibration_certificates")
        
        # 创建附件记录
        attachment = EquipmentAttachment(
            equipment_id=history.equipment_id,
            calibration_history_id=history_id,
            filename=file_info["filename"],
            original_filename=file.filename,
            file_path=file_info["file_path"],
            file_size=file_info["file_size"],
            file_type=file_info["file_type"],
            mime_type=file.content_type,
            description=description,
            is_certificate=True,
            certificate_type="检定证书",
            attachment_category="calibration",
            uploaded_by=current_user.id
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        # 记录审计日志
        log_audit(
            db=db,
            user_id=current_user.id,
            equipment_id=history.equipment_id,
            action="上传检定证书",
            description=f"为检定历史记录 {history_id} 上传证书: {file.filename}",
            old_value=None,
            new_value=f"文件: {file.filename}, 大小: {file_info['file_size']} bytes"
        )
        
        return {
            "attachment_id": attachment.id,
            "filename": attachment.filename,
            "message": "检定证书上传成功"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传检定证书失败: {str(e)}"
        )


def get_last_external_calibration_info(db: Session, equipment_id: int) -> Optional[dict]:
    """
    获取设备上次外检信息
    
    优先从检定历史记录中获取最新的外检记录，如果没有则从设备基本信息中获取首次录入的信息
    
    - **equipment_id**: 设备ID
    - **returns**: 上次外检信息字典，如果没有则返回None
    """
    try:
        # 首先查询检定历史记录，获取最新的外检记录
        # 如果检定日期相同，则按创建时间降序排列，确保获取到最新的记录
        last_calibration = db.query(CalibrationHistory).filter(
            CalibrationHistory.equipment_id == equipment_id,
            CalibrationHistory.calibration_method == "外检"
        ).order_by(desc(CalibrationHistory.calibration_date), desc(CalibrationHistory.created_at)).first()
        
        if last_calibration:
            print(f"DEBUG: 找到检定历史记录 - 设备ID: {equipment_id}")
            print(f"  检定日期: {last_calibration.calibration_date}")
            print(f"  创建时间: {last_calibration.created_at}")
            print(f"  检定机构: {last_calibration.verification_agency}")
            print(f"  证书形式: {last_calibration.certificate_form}")
            print(f"  证书编号: {last_calibration.certificate_number}")
            print(f"  检定结果: {last_calibration.calibration_result}")
            return {
                "verification_agency": last_calibration.verification_agency,
                "certificate_form": last_calibration.certificate_form,
                "source": "history"  # 标记来源为历史记录
            }
        
        # 如果没有历史记录，尝试从设备基本信息中获取首次录入的信息
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if equipment and equipment.calibration_method == "外检":
            # 检查设备基本信息中是否有外检信息
            if equipment.verification_agency or equipment.certificate_form:
                print(f"DEBUG: 从设备基本信息获取 - 设备ID: {equipment_id}, 检定机构: {equipment.verification_agency}, 证书形式: {equipment.certificate_form}")
                return {
                    "verification_agency": equipment.verification_agency,
                    "certificate_form": equipment.certificate_form,
                    "source": "equipment"  # 标记来源为设备基本信息
                }
            else:
                print(f"DEBUG: 设备基本信息中无外检信息 - 设备ID: {equipment_id}")
        
        print(f"DEBUG: 无任何外检信息 - 设备ID: {equipment_id}")
        return None
    except Exception as e:
        print(f"DEBUG: 获取外检信息异常 - 设备ID: {equipment_id}, 错误: {str(e)}")
        return None


def calculate_valid_until(calibration_date: date, calibration_cycle: str) -> date:
    """
    根据检定日期和检定周期计算有效期
    
    计算方式：检定日期 + 检定周期月数 - 1天 (因为到期当天不算有效)
    
    - **calibration_date**: 检定日期
    - **calibration_cycle**: 检定周期（6个月/12个月/24个月/随坏随换）
    """
    if calibration_cycle == "随坏随换":
        # 随坏随换设为很远的未来日期
        return date(2099, 12, 31)
    
    try:
        # 提取月份数
        months = 0
        if calibration_cycle == "6个月":
            months = 6
        elif calibration_cycle == "12个月":
            months = 12
        elif calibration_cycle == "24个月":
            months = 24
        elif calibration_cycle == "36个月":
            months = 36
        else:
            # 默认12个月
            months = 12
        
        # 计算有效期：加上月份数后减去一天
        # 使用 datetime 来处理月份加减
        dt = datetime(calibration_date.year, calibration_date.month, calibration_date.day)
        
        # 加上月份数
        if dt.month + months <= 12:
            dt = dt.replace(month=dt.month + months)
        else:
            # 跨年处理
            new_year = dt.year + (dt.month + months - 1) // 12
            new_month = (dt.month + months - 1) % 12 + 1
            dt = dt.replace(year=new_year, month=new_month)
        
        # 减去一天
        valid_until = dt.date() - timedelta(days=1)
        return valid_until
        
    except Exception:
        # 出错时使用简单计算，默认12个月减1天
        return calibration_date + timedelta(days=365) - timedelta(days=1)
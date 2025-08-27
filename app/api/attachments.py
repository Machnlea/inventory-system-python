from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from app.db.database import get_db
from app.crud import attachments as crud_attachments
from app.schemas.schemas import EquipmentAttachment, EquipmentAttachmentCreate, EquipmentAttachmentUpdate
from app.api.auth import get_current_user
from app.api.audit_logs import create_audit_log

router = APIRouter()

# 创建上传目录
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
CERTIFICATE_DIR = UPLOAD_DIR / "certificates"
CERTIFICATE_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR = UPLOAD_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)


@router.post("/equipment/{equipment_id}/attachments", response_model=EquipmentAttachment)
async def upload_equipment_attachment(
    equipment_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    is_certificate: Optional[bool] = Form(False),
    certificate_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """上传设备附件"""
    
    # 验证文件类型
    if file.filename and not crud_attachments.is_allowed_file_type(file.filename):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件类型。支持的格式：PDF, JPG, PNG, DOC, DOCX, XLS, XLSX, TXT"
        )
    
    # 验证证书类型
    if is_certificate and certificate_type not in ["检定证书", "校准证书"]:
        raise HTTPException(
            status_code=400,
            detail="证书类型必须是'检定证书'或'校准证书'"
        )
    
    # 生成唯一文件名
    unique_filename = crud_attachments.generate_unique_filename(file.filename or "upload")
    
    # 确定保存路径
    if is_certificate:
        save_dir = CERTIFICATE_DIR
    else:
        save_dir = DOCUMENTS_DIR
    
    file_path = save_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 获取文件信息
    file_size = crud_attachments.get_file_size(str(file_path))
    file_type = crud_attachments.get_file_type(file.filename or "unknown")
    mime_type = crud_attachments.get_mime_type(file.filename or "unknown")
    
    # 创建附件记录
    attachment_data = EquipmentAttachmentCreate(
        equipment_id=equipment_id,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_type,
        mime_type=mime_type,
        description=description,
        is_certificate=is_certificate or False,
        certificate_type=certificate_type
    )
    
    attachment = crud_attachments.create_equipment_attachment(
        db=db, attachment=attachment_data, uploaded_by=current_user.id
    )
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=equipment_id,
        action="上传附件",
        description=f"上传附件: {file.filename}"
    )
    
    return attachment


@router.get("/equipment/{equipment_id}/attachments", response_model=List[EquipmentAttachment])
def get_equipment_attachments(
    equipment_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取设备附件列表"""
    return crud_attachments.get_equipment_attachments(
        db=db, equipment_id=equipment_id, skip=skip, limit=limit
    )


@router.get("/equipment/{equipment_id}/attachments/certificates", response_model=List[EquipmentAttachment])
def get_equipment_certificates(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取设备证书附件"""
    return crud_attachments.get_attachments_by_type(
        db=db, equipment_id=equipment_id, is_certificate=True
    )


@router.get("/{attachment_id}", response_model=EquipmentAttachment)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个附件信息"""
    attachment = crud_attachments.get_equipment_attachment(db=db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    return attachment


@router.put("/{attachment_id}", response_model=EquipmentAttachment)
def update_attachment(
    attachment_id: int,
    attachment_update: EquipmentAttachmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新附件信息"""
    attachment = crud_attachments.update_equipment_attachment(
        db=db, attachment_id=attachment_id, attachment_update=attachment_update
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=int(attachment.equipment_id),
        action="更新附件",
        description=f"更新附件信息: {attachment.original_filename or 'unknown'}"
    )
    
    return attachment


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除附件"""
    # 先获取附件信息用于日志记录
    attachment = crud_attachments.get_equipment_attachment(db=db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    equipment_id = int(attachment.equipment_id)
    filename = attachment.original_filename or 'unknown'
    
    success = crud_attachments.delete_equipment_attachment(db=db, attachment_id=attachment_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    # 记录操作日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=equipment_id,
        action="删除附件",
        description=f"删除附件: {filename}"
    )
    
    return {"message": "附件删除成功"}


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """下载附件"""
    attachment = crud_attachments.get_equipment_attachment(db=db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 检查文件是否存在
    if not os.path.exists(str(attachment.file_path)):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    from fastapi.responses import FileResponse
    from urllib.parse import quote
    
    # 记录下载日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=int(attachment.equipment_id),
        action="下载附件",
        description=f"下载附件: {attachment.original_filename or 'unknown'}"
    )
    
    # 返回文件
    original_filename = attachment.original_filename or "attachment"
    encoded_filename = quote(str(original_filename), safe='')
    return FileResponse(
        path=str(attachment.file_path),
        filename=original_filename,
        media_type=str(attachment.mime_type or "application/octet-stream")
    )


@router.get("/{attachment_id}/preview")
def preview_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """预览附件（仅支持图片和PDF）"""
    attachment = crud_attachments.get_equipment_attachment(db=db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 检查文件是否存在
    if not os.path.exists(str(attachment.file_path)):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查文件类型是否支持预览
    if attachment.file_type not in ['PDF', 'JPG', 'PNG', 'GIF', 'JPEG']:
        raise HTTPException(status_code=400, detail="该文件类型不支持在线预览")
    
    from fastapi.responses import FileResponse
    
    # 记录预览日志
    create_audit_log(
        db=db,
        user_id=current_user.id,
        equipment_id=int(attachment.equipment_id),
        action="预览附件",
        description=f"预览附件: {attachment.original_filename or 'unknown'}"
    )
    
    # 返回文件用于预览
    return FileResponse(
        path=str(attachment.file_path),
        media_type=str(attachment.mime_type or "application/octet-stream")
    )
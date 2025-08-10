from sqlalchemy.orm import Session
from app.models.models import EquipmentAttachment
from app.schemas.schemas import EquipmentAttachmentCreate, EquipmentAttachmentUpdate
from typing import List, Optional
import os
import uuid
from datetime import datetime


def create_equipment_attachment(db: Session, attachment: EquipmentAttachmentCreate, uploaded_by: int) -> EquipmentAttachment:
    """创建设备附件记录"""
    db_attachment = EquipmentAttachment(
        equipment_id=attachment.equipment_id,
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        file_path=attachment.file_path,
        file_size=attachment.file_size,
        file_type=attachment.file_type,
        mime_type=attachment.mime_type,
        description=attachment.description,
        is_certificate=attachment.is_certificate,
        certificate_type=attachment.certificate_type,
        uploaded_by=uploaded_by
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def get_equipment_attachments(db: Session, equipment_id: int, skip: int = 0, limit: int = 100) -> List[EquipmentAttachment]:
    """获取设备的附件列表"""
    return db.query(EquipmentAttachment).filter(
        EquipmentAttachment.equipment_id == equipment_id
    ).order_by(EquipmentAttachment.created_at.desc()).offset(skip).limit(limit).all()


def get_equipment_attachment(db: Session, attachment_id: int) -> Optional[EquipmentAttachment]:
    """获取单个附件"""
    return db.query(EquipmentAttachment).filter(EquipmentAttachment.id == attachment_id).first()


def update_equipment_attachment(db: Session, attachment_id: int, attachment_update: EquipmentAttachmentUpdate) -> Optional[EquipmentAttachment]:
    """更新附件信息"""
    db_attachment = db.query(EquipmentAttachment).filter(EquipmentAttachment.id == attachment_id).first()
    if not db_attachment:
        return None
    
    update_data = attachment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_attachment, field, value)
    
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def delete_equipment_attachment(db: Session, attachment_id: int) -> bool:
    """删除附件记录和文件"""
    db_attachment = db.query(EquipmentAttachment).filter(EquipmentAttachment.id == attachment_id).first()
    if not db_attachment:
        return False
    
    # 删除物理文件
    try:
        if os.path.exists(db_attachment.file_path):
            os.remove(db_attachment.file_path)
    except Exception as e:
        print(f"Error deleting file {db_attachment.file_path}: {e}")
    
    # 删除数据库记录
    db.delete(db_attachment)
    db.commit()
    return True


def get_attachments_by_type(db: Session, equipment_id: int, is_certificate: bool = None) -> List[EquipmentAttachment]:
    """根据类型获取附件"""
    query = db.query(EquipmentAttachment).filter(EquipmentAttachment.equipment_id == equipment_id)
    
    if is_certificate is not None:
        query = query.filter(EquipmentAttachment.is_certificate == is_certificate)
    
    return query.order_by(EquipmentAttachment.created_at.desc()).all()


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    
    # 生成唯一文件名
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{timestamp}_{unique_id}{ext}"


def get_file_size(file_path: str) -> int:
    """获取文件大小"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def get_file_type(filename: str) -> str:
    """根据文件扩展名获取文件类型"""
    _, ext = os.path.splitext(filename.lower())
    
    type_mapping = {
        '.pdf': 'PDF',
        '.jpg': 'JPG',
        '.jpeg': 'JPG',
        '.png': 'PNG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.doc': 'DOC',
        '.docx': 'DOCX',
        '.xls': 'XLS',
        '.xlsx': 'XLSX',
        '.txt': 'TXT'
    }
    
    return type_mapping.get(ext, 'OTHER')


def get_mime_type(filename: str) -> str:
    """根据文件扩展名获取MIME类型"""
    _, ext = os.path.splitext(filename.lower())
    
    mime_mapping = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.txt': 'text/plain'
    }
    
    return mime_mapping.get(ext, 'application/octet-stream')


def is_allowed_file_type(filename: str) -> bool:
    """检查文件类型是否允许"""
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.doc', '.docx', '.xls', '.xlsx', '.txt'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
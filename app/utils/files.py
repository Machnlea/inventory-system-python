"""
文件处理工具函数
处理文件上传、保存、路径管理等功能
"""

import os
import uuid
import shutil
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException


async def save_uploaded_file(file: UploadFile, subdirectory: str = "uploads") -> Dict[str, Any]:
    """
    保存上传的文件
    
    Args:
        file: FastAPI UploadFile对象
        subdirectory: 子目录名称
    
    Returns:
        包含文件信息的字典
    """
    
    # 创建上传目录
    upload_base = Path("data/uploads")
    upload_dir = upload_base / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_extension = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 确定文件类型
        file_type = get_file_type(file.filename or "")
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": file_type,
            "mime_type": file.content_type,
            "upload_date": datetime.now()
        }
        
    except Exception as e:
        # 如果保存失败，删除已创建的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


def get_file_path(filename: str, subdirectory: str = "uploads") -> Optional[Path]:
    """
    获取文件的完整路径
    
    Args:
        filename: 文件名
        subdirectory: 子目录
    
    Returns:
        文件路径或None
    """
    file_path = Path("data/uploads") / subdirectory / filename
    return file_path if file_path.exists() else None


def get_file_type(filename: str) -> str:
    """
    根据文件扩展名确定文件类型
    
    Args:
        filename: 文件名
    
    Returns:
        文件类型字符串
    """
    if not filename:
        return "unknown"
    
    extension = Path(filename).suffix.lower()
    
    # 文档类型
    if extension in ['.pdf']:
        return 'PDF'
    elif extension in ['.doc', '.docx']:
        return 'DOCX'
    elif extension in ['.xls', '.xlsx']:
        return 'XLSX'
    elif extension in ['.ppt', '.pptx']:
        return 'PPTX'
    elif extension in ['.txt']:
        return 'TXT'
    
    # 图片类型
    elif extension in ['.jpg', '.jpeg']:
        return 'JPG'
    elif extension in ['.png']:
        return 'PNG'
    elif extension in ['.gif']:
        return 'GIF'
    elif extension in ['.bmp']:
        return 'BMP'
    elif extension in ['.svg']:
        return 'SVG'
    
    # 压缩文件
    elif extension in ['.zip']:
        return 'ZIP'
    elif extension in ['.rar']:
        return 'RAR'
    elif extension in ['.7z']:
        return '7Z'
    
    # 其他
    else:
        return extension.upper().replace('.', '') or 'UNKNOWN'


def delete_file(file_path: str) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        删除是否成功
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_size_display(size_bytes: int) -> str:
    """
    将字节大小转换为人类可读的格式
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def is_allowed_file_type(filename: str, allowed_extensions: list = None) -> bool:
    """
    检查文件类型是否被允许
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的文件扩展名列表
    
    Returns:
        是否允许该文件类型
    """
    if not filename:
        return False
    
    if allowed_extensions is None:
        # 默认允许的文件类型
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.zip', '.rar', '.7z'
        ]
    
    extension = Path(filename).suffix.lower()
    return extension in allowed_extensions


def create_backup_filename(original_filename: str) -> str:
    """
    创建备份文件名
    
    Args:
        original_filename: 原始文件名
    
    Returns:
        备份文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    return f"{name}_backup_{timestamp}{ext}"


def ensure_directory_exists(directory_path: str):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)
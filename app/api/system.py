#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理API
提供系统状态、监控和管理功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import psutil
import os
import platform
from datetime import datetime, timedelta
from pathlib import Path

from app.db.database import get_db, test_database_connection
from app.api.auth import get_current_admin_user
from app.schemas.schemas import User
from app.utils.log_viewer import LogViewer

router = APIRouter()

@router.get("/status")
async def get_system_status(current_user: User = Depends(get_current_admin_user)):
    """获取系统状态信息（仅管理员）"""
    
    try:
        # 系统基本信息
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }
        
        # CPU信息
        cpu_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100,
        }
        
        # 网络信息
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
        }
        
        # 进程信息
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "create_time": process.create_time(),
            "num_threads": process.num_threads(),
        }
        
        # 数据库连接测试
        db_status, db_message = test_database_connection()
        
        # 日志文件信息
        log_dir = Path("data/logs")
        log_files = []
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                stat = log_file.stat()
                log_files.append({
                    "name": log_file.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        
        # 上传文件信息
        upload_dir = Path("data/uploads")
        upload_info = {"total_files": 0, "total_size": 0}
        if upload_dir.exists():
            for file_path in upload_dir.rglob("*"):
                if file_path.is_file():
                    upload_info["total_files"] += 1
                    upload_info["total_size"] += file_path.stat().st_size
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": datetime.now() - datetime.fromtimestamp(process.create_time()),
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
            "process": process_info,
            "database": {
                "status": "connected" if db_status else "disconnected",
                "message": db_message,
            },
            "logs": {
                "files": log_files,
                "total_files": len(log_files),
            },
            "uploads": upload_info,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查端点（无需认证）"""
    
    try:
        # 基本健康检查
        db_status, db_message = test_database_connection()
        
        # 检查关键目录
        data_dir = Path("data")
        logs_dir = Path("data/logs")
        uploads_dir = Path("data/uploads")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": {
                    "status": "ok" if db_status else "error",
                    "message": db_message,
                },
                "directories": {
                    "data": data_dir.exists(),
                    "logs": logs_dir.exists(),
                    "uploads": uploads_dir.exists(),
                },
                "disk_space": {
                    "available": psutil.disk_usage('/').free > 100 * 1024 * 1024,  # 100MB
                    "free_bytes": psutil.disk_usage('/').free,
                },
                "memory": {
                    "available": psutil.virtual_memory().percent < 90,
                    "usage_percent": psutil.virtual_memory().percent,
                },
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }

@router.post("/cleanup")
async def cleanup_system(current_user: User = Depends(get_current_admin_user)):
    """系统清理（仅管理员）"""
    
    try:
        cleanup_results = {
            "logs_cleaned": 0,
            "temp_files_cleaned": 0,
            "space_freed": 0,
        }
        
        # 清理过期日志文件（保留最近7天）
        log_dir = Path("data/logs")
        if log_dir.exists():
            cutoff_time = datetime.now() - timedelta(days=7)
            
            for log_file in log_dir.glob("*.log.*"):  # 轮转的日志文件
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        cleanup_results["logs_cleaned"] += 1
                        cleanup_results["space_freed"] += file_size
        
        # 清理临时文件
        temp_patterns = ["*.tmp", "*.temp", "*~", ".DS_Store"]
        for pattern in temp_patterns:
            for temp_file in Path(".").rglob(pattern):
                if temp_file.is_file():
                    file_size = temp_file.stat().st_size
                    temp_file.unlink()
                    cleanup_results["temp_files_cleaned"] += 1
                    cleanup_results["space_freed"] += file_size
        
        return {
            "success": True,
            "message": "系统清理完成",
            "results": cleanup_results,
            "space_freed_mb": cleanup_results["space_freed"] / (1024 * 1024),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统清理失败: {str(e)}")

@router.get("/logs/summary")
async def get_logs_summary(
    hours: int = 24,
    current_user: User = Depends(get_current_admin_user)
):
    """获取日志摘要信息（仅管理员）"""
    
    try:
        viewer = LogViewer()
        stats = viewer.analyze_logs(hours)
        
        # 获取最近的错误日志
        recent_errors = viewer.get_error_logs(hours)[:10]  # 最近10条错误
        
        # 获取最近的安全事件
        recent_security = viewer.get_security_logs(hours)[:10]  # 最近10条安全事件
        
        return {
            "period_hours": hours,
            "statistics": stats,
            "recent_errors": recent_errors,
            "recent_security_events": recent_security,
            "summary": {
                "total_logs": stats["total_logs"],
                "error_rate": (stats["errors"] / max(stats["total_logs"], 1)) * 100,
                "warning_rate": (stats["warnings"] / max(stats["total_logs"], 1)) * 100,
                "top_loggers": sorted(stats["by_logger"].items(), key=lambda x: x[1], reverse=True)[:5],
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志摘要失败: {str(e)}")

def format_bytes(bytes_value: int) -> str:
    """格式化字节数为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"
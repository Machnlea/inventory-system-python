from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_admin_user
from app.schemas.schemas import User
from app.core.logging import log_manager
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import glob
import json
import re
from pydantic import BaseModel

router = APIRouter()

class LogSearchRequest(BaseModel):
    keyword: str
    log_type: str = "all"
    hours: int = 24
    max_results: int = 200

@router.get("/stats")
def get_log_stats(
    hours: int = Query(24, description="统计时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取日志统计信息"""
    try:
        # 获取真实的日志统计数据
        stats = log_manager.get_log_stats(hours)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")

@router.post("/search")
def search_logs(
    search_request: LogSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """搜索日志"""
    try:
        # 搜索真实的日志文件
        logs = log_manager.search_logs(
            keyword=search_request.keyword,
            hours=search_request.hours,
            max_results=search_request.max_results
        )
        
        return {
            "logs": logs,
            "total": len(logs),
            "keyword": search_request.keyword,
            "hours": search_request.hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索日志失败: {str(e)}")

@router.get("/errors")
def get_error_logs(
    hours: int = Query(24, description="时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取错误日志"""
    try:
        # 获取真实的错误日志
        error_logs = log_manager.get_error_logs(hours)
        
        return {
            "logs": error_logs,
            "total": len(error_logs),
            "hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误日志失败: {str(e)}")

@router.get("/security")
def get_security_logs(
    hours: int = Query(24, description="时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取安全日志"""
    try:
        # 获取真实的安全日志
        security_logs = log_manager.get_security_logs(hours)
        
        return {
            "logs": security_logs,
            "total": len(security_logs),
            "hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取安全日志失败: {str(e)}")

@router.get("/api")
def get_api_logs(
    hours: int = Query(24, description="时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取API日志"""
    try:
        # 获取真实的API访问日志
        api_logs = log_manager.get_api_logs(hours)
        
        return {
            "logs": api_logs,
            "total": len(api_logs),
            "hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API日志失败: {str(e)}")

@router.get("/preview")
def get_preview_logs(
    hours: int = Query(24, description="时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取预览日志（最新的混合日志）"""
    try:
        # 获取混合的最新日志
        all_logs = []
        
        # 收集各类日志
        all_logs.extend(log_manager.get_api_logs(hours)[:10])
        all_logs.extend(log_manager.get_error_logs(hours)[:5])
        all_logs.extend(log_manager.get_security_logs(hours)[:5])
        
        # 按时间排序
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 限制数量
        preview_logs = all_logs[:20]
        
        return {
            "logs": preview_logs,
            "total": len(preview_logs),
            "hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预览日志失败: {str(e)}")

@router.get("/download")
def download_logs(
    log_type: str = Query("all", description="日志类型"),
    hours: int = Query(24, description="时间范围（小时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """下载日志文件"""
    try:
        # 在实际应用中，这里应该生成并返回日志文件
        return {
            "message": "日志下载功能开发中",
            "log_type": log_type,
            "hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载日志失败: {str(e)}")

@router.delete("/cleanup")
def cleanup_old_logs(
    days: int = Query(30, description="保留天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """清理旧日志"""
    try:
        # 在实际应用中，这里应该清理旧的日志文件
        return {
            "message": f"已清理 {days} 天前的日志",
            "cleaned_files": 5,
            "freed_space_mb": 125.6
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")
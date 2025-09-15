#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理API
提供日志查看、搜索和分析的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.db.database import get_db
from app.api.auth import get_current_user, get_current_admin_user
from app.utils.log_viewer import LogViewer
from app.schemas.schemas import User

router = APIRouter()

class LogSearchRequest(BaseModel):
    keyword: str
    log_type: str = "all"
    hours: int = 24
    max_results: int = 100

class LogSearchResponse(BaseModel):
    total: int
    logs: List[Dict[str, Any]]

class LogStatsResponse(BaseModel):
    total_logs: int
    errors: int
    warnings: int
    api_requests: int
    security_events: int
    by_level: Dict[str, int]
    by_logger: Dict[str, int]
    by_hour: Dict[str, int]

@router.get("/files", response_model=List[str])
async def get_log_files(current_user: User = Depends(get_current_admin_user)):
    """获取所有日志文件列表（仅管理员）"""
    viewer = LogViewer()
    return viewer.get_log_files()

@router.get("/tail")
async def tail_log(
    file_name: str = Query(..., description="日志文件名"),
    lines: int = Query(50, description="显示行数"),
    current_user: User = Depends(get_current_admin_user)
):
    """查看日志文件末尾（仅管理员）"""
    viewer = LogViewer()
    
    # 安全检查：只允许访问logs目录下的文件
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    log_files = viewer.get_log_files()
    target_file = None
    
    for file_path in log_files:
        if file_name in file_path:
            target_file = file_path
            break
    
    if not target_file:
        raise HTTPException(status_code=404, detail="日志文件不存在")
    
    lines_content = viewer.tail_log(target_file, lines)
    
    return {
        "file": target_file,
        "lines": len(lines_content),
        "content": lines_content
    }

@router.post("/search", response_model=LogSearchResponse)
async def search_logs(
    request: LogSearchRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """搜索日志（仅管理员）"""
    viewer = LogViewer()
    
    start_time = datetime.now() - timedelta(hours=request.hours)
    logs = viewer.search_logs(
        keyword=request.keyword,
        log_type=request.log_type,
        start_time=start_time,
        max_results=request.max_results
    )
    
    return LogSearchResponse(
        total=len(logs),
        logs=logs
    )

@router.get("/errors")
async def get_error_logs(
    hours: int = Query(24, description="查看最近N小时"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取错误日志（仅管理员）"""
    viewer = LogViewer()
    logs = viewer.get_error_logs(hours)
    
    return {
        "total": len(logs),
        "hours": hours,
        "logs": logs
    }

@router.get("/security")
async def get_security_logs(
    hours: int = Query(24, description="查看最近N小时"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取安全日志（仅管理员）"""
    viewer = LogViewer()
    logs = viewer.get_security_logs(hours)
    
    return {
        "total": len(logs),
        "hours": hours,
        "logs": logs
    }

@router.get("/api")
async def get_api_logs(
    hours: int = Query(24, description="查看最近N小时"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取API日志（仅管理员）"""
    viewer = LogViewer()
    logs = viewer.get_api_logs(hours)
    
    return {
        "total": len(logs),
        "hours": hours,
        "logs": logs
    }

@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    hours: int = Query(24, description="统计最近N小时"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取日志统计信息（仅管理员）"""
    viewer = LogViewer()
    stats = viewer.analyze_logs(hours)
    
    return LogStatsResponse(**stats)

@router.get("/preview")
async def preview_attachment_logs(
    attachment_id: Optional[int] = Query(None, description="附件ID"),
    hours: int = Query(1, description="查看最近N小时"),
    current_user: User = Depends(get_current_admin_user)
):
    """获取附件预览相关的日志（用于调试预览问题）"""
    viewer = LogViewer()
    
    start_time = datetime.now() - timedelta(hours=hours)
    
    # 搜索预览相关的日志
    keywords = ["preview", "预览", "attachment"]
    all_logs = []
    
    for keyword in keywords:
        logs = viewer.search_logs(
            keyword=keyword,
            log_type="all",
            start_time=start_time,
            max_results=200
        )
        all_logs.extend(logs)
    
    # 如果指定了附件ID，进一步过滤
    if attachment_id:
        filtered_logs = []
        for log in all_logs:
            content = str(log.get('content', '')) + str(log.get('message', ''))
            if str(attachment_id) in content:
                filtered_logs.append(log)
        all_logs = filtered_logs
    
    # 按时间排序
    all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        "total": len(all_logs),
        "attachment_id": attachment_id,
        "hours": hours,
        "logs": all_logs[:100]  # 限制返回数量
    }
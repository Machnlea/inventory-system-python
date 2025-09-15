#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录系统配置
提供统一的日志记录功能，支持文件日志、控制台日志和结构化日志
"""

import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

# 创建日志目录
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'equipment_id'):
            log_entry["equipment_id"] = record.equipment_id
        if hasattr(record, 'action'):
            log_entry["action"] = record.action
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 格式化消息
        formatted = super().format(record)
        return f"{color}{formatted}{reset}"

def setup_logging(
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: 是否启用控制台日志
        enable_file: 是否启用文件日志
        enable_json: 是否启用JSON格式日志
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件数量
    """
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别
        root_logger.addHandler(console_handler)
    
    # 文件处理器 - 普通格式
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # JSON格式日志处理器
    if enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.json",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)
    
    # 错误日志处理器
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s\n%(exc_info)s'
    )
    error_handler.setFormatter(error_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    logging.info("日志系统初始化完成")

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)

class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，用于添加上下文信息"""
    
    def process(self, msg, kwargs):
        # 添加额外的上下文信息到日志记录中
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # 合并适配器的额外信息
        kwargs['extra'].update(self.extra)
        
        return msg, kwargs

def get_context_logger(
    name: str,
    user_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None
) -> LoggerAdapter:
    """
    获取带上下文信息的日志记录器
    
    Args:
        name: 日志记录器名称
        user_id: 用户ID
        equipment_id: 设备ID
        request_id: 请求ID
        ip_address: IP地址
    
    Returns:
        带上下文信息的日志适配器
    """
    logger = logging.getLogger(name)
    extra = {}
    
    if user_id is not None:
        extra['user_id'] = user_id
    if equipment_id is not None:
        extra['equipment_id'] = equipment_id
    if request_id is not None:
        extra['request_id'] = request_id
    if ip_address is not None:
        extra['ip_address'] = ip_address
    
    return LoggerAdapter(logger, extra)

@contextmanager
def log_execution_time(logger: logging.Logger, operation: str):
    """
    记录操作执行时间的上下文管理器
    
    Args:
        logger: 日志记录器
        operation: 操作描述
    """
    start_time = datetime.now()
    logger.info(f"开始执行: {operation}")
    
    try:
        yield
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"执行完成: {operation}, 耗时: {duration:.3f}秒")
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"执行失败: {operation}, 耗时: {duration:.3f}秒, 错误: {str(e)}")
        raise

def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
):
    """
    记录API请求日志
    
    Args:
        logger: 日志记录器
        method: HTTP方法
        path: 请求路径
        user_id: 用户ID
        ip_address: IP地址
        user_agent: 用户代理
        request_id: 请求ID
    """
    extra = {
        'action': 'api_request',
        'method': method,
        'path': path
    }
    
    if user_id is not None:
        extra['user_id'] = user_id
    if ip_address is not None:
        extra['ip_address'] = ip_address
    if user_agent is not None:
        extra['user_agent'] = user_agent
    if request_id is not None:
        extra['request_id'] = request_id
    
    logger.info(f"API请求: {method} {path}", extra=extra)

def log_api_response(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    user_id: Optional[int] = None,
    request_id: Optional[str] = None
):
    """
    记录API响应日志
    
    Args:
        logger: 日志记录器
        method: HTTP方法
        path: 请求路径
        status_code: 响应状态码
        response_time: 响应时间（秒）
        user_id: 用户ID
        request_id: 请求ID
    """
    extra = {
        'action': 'api_response',
        'method': method,
        'path': path,
        'status_code': status_code,
        'response_time': response_time
    }
    
    if user_id is not None:
        extra['user_id'] = user_id
    if request_id is not None:
        extra['request_id'] = request_id
    
    level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
    logger.log(level, f"API响应: {method} {path} - {status_code} ({response_time:.3f}s)", extra=extra)

def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    record_id: Optional[int] = None,
    user_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    记录数据库操作日志
    
    Args:
        logger: 日志记录器
        operation: 操作类型 (CREATE, READ, UPDATE, DELETE)
        table: 表名
        record_id: 记录ID
        user_id: 操作用户ID
        details: 操作详情
    """
    extra = {
        'action': 'database_operation',
        'operation': operation,
        'table': table
    }
    
    if record_id is not None:
        extra['record_id'] = record_id
    if user_id is not None:
        extra['user_id'] = user_id
    if details is not None:
        extra['details'] = details
    
    logger.info(f"数据库操作: {operation} {table}", extra=extra)

def log_security_event(
    logger: logging.Logger,
    event_type: str,
    description: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    severity: str = "INFO"
):
    """
    记录安全事件日志
    
    Args:
        logger: 日志记录器
        event_type: 事件类型 (LOGIN, LOGOUT, FAILED_LOGIN, PERMISSION_DENIED, etc.)
        description: 事件描述
        user_id: 用户ID
        ip_address: IP地址
        severity: 严重程度 (INFO, WARNING, ERROR, CRITICAL)
    """
    extra = {
        'action': 'security_event',
        'event_type': event_type,
        'severity': severity
    }
    
    if user_id is not None:
        extra['user_id'] = user_id
    if ip_address is not None:
        extra['ip_address'] = ip_address
    
    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(level, f"安全事件: {event_type} - {description}", extra=extra)

def log_file_operation(
    logger: logging.Logger,
    operation: str,
    file_path: str,
    user_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    file_size: Optional[int] = None
):
    """
    记录文件操作日志
    
    Args:
        logger: 日志记录器
        operation: 操作类型 (UPLOAD, DOWNLOAD, DELETE, PREVIEW)
        file_path: 文件路径
        user_id: 用户ID
        equipment_id: 设备ID
        file_size: 文件大小
    """
    extra = {
        'action': 'file_operation',
        'operation': operation,
        'file_path': file_path
    }
    
    if user_id is not None:
        extra['user_id'] = user_id
    if equipment_id is not None:
        extra['equipment_id'] = equipment_id
    if file_size is not None:
        extra['file_size'] = file_size
    
    logger.info(f"文件操作: {operation} {file_path}", extra=extra)

# 预定义的日志记录器
app_logger = get_logger("app")
api_logger = get_logger("api")
db_logger = get_logger("database")
security_logger = get_logger("security")
file_logger = get_logger("file")
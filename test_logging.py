#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.logging import setup_logging, get_logger, get_context_logger, log_security_event, log_file_operation
import logging

def test_logging():
    """测试日志系统"""
    
    # 初始化日志系统
    setup_logging(log_level="DEBUG")
    
    # 获取不同的日志记录器
    app_logger = get_logger("app")
    api_logger = get_logger("api")
    security_logger = get_logger("security")
    
    print("=== 测试基本日志记录 ===")
    
    # 测试不同级别的日志
    app_logger.debug("这是一个调试信息")
    app_logger.info("这是一个信息日志")
    app_logger.warning("这是一个警告日志")
    app_logger.error("这是一个错误日志")
    
    print("\n=== 测试带上下文的日志记录 ===")
    
    # 测试带上下文的日志记录器
    context_logger = get_context_logger(
        "test.context",
        user_id=123,
        equipment_id=456,
        ip_address="192.168.1.100",
        request_id="req-12345"
    )
    
    context_logger.info("这是一个带上下文的日志")
    context_logger.error("这是一个带上下文的错误日志")
    
    print("\n=== 测试安全事件日志 ===")
    
    # 测试安全事件日志
    log_security_event(
        security_logger,
        event_type="LOGIN_SUCCESS",
        description="用户admin登录成功",
        user_id=1,
        ip_address="192.168.1.100",
        severity="INFO"
    )
    
    log_security_event(
        security_logger,
        event_type="FAILED_LOGIN",
        description="用户test登录失败：密码错误",
        ip_address="192.168.1.101",
        severity="WARNING"
    )
    
    print("\n=== 测试文件操作日志 ===")
    
    # 测试文件操作日志
    log_file_operation(
        api_logger,
        operation="UPLOAD",
        file_path="/uploads/test.pdf",
        user_id=123,
        equipment_id=456,
        file_size=1024000
    )
    
    log_file_operation(
        api_logger,
        operation="PREVIEW",
        file_path="/uploads/test.pdf",
        user_id=123,
        equipment_id=456,
        file_size=1024000
    )
    
    print("\n=== 测试异常日志 ===")
    
    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        app_logger.error("捕获到异常", exc_info=True)
    
    print("\n=== 日志测试完成 ===")
    print("请检查 data/logs/ 目录下的日志文件：")
    print("- app.log: 普通格式的应用日志")
    print("- app.json: JSON格式的结构化日志")
    print("- error.log: 错误日志")

if __name__ == "__main__":
    test_logging()
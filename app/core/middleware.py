#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中间件模块
包含日志记录、安全头、请求追踪等中间件
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.core.logging import log_api_request, log_api_response, log_security_event

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("api")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 获取客户端信息
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 记录请求开始
        start_time = time.time()
        
        # 获取用户ID（如果已认证）
        user_id = getattr(request.state, 'user_id', None)
        
        # 记录API请求
        log_api_request(
            self.logger,
            method=request.method,
            path=str(request.url.path),
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 记录API响应
            log_api_response(
                self.logger,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time=process_time,
                user_id=user_id,
                request_id=request_id
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            self.logger.error(
                f"请求处理异常: {request.method} {request.url.path} - {str(e)}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'ip_address': client_ip,
                    'process_time': process_time,
                    'exception': str(e)
                },
                exc_info=True
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={"detail": "内部服务器错误", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        if request.client:
            return request.client.host
        
        return "unknown"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("security")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # 在HTTPS环境下添加HSTS头
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {ip: [(timestamp, count), ...]}
        self.logger = logging.getLogger("security")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # 清理过期记录
        self.cleanup_old_requests(current_time)
        
        # 检查速率限制
        if self.is_rate_limited(client_ip, current_time):
            # 记录速率限制事件
            log_security_event(
                self.logger,
                event_type="RATE_LIMIT_EXCEEDED",
                description=f"IP {client_ip} 超过速率限制",
                ip_address=client_ip,
                severity="WARNING"
            )
            
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": "60"}
            )
        
        # 记录请求
        self.record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def cleanup_old_requests(self, current_time: float):
        """清理超过1分钟的请求记录"""
        cutoff_time = current_time - 60  # 1分钟前
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (timestamp, count) for timestamp, count in self.requests[ip]
                if timestamp > cutoff_time
            ]
            
            # 如果没有记录了，删除这个IP
            if not self.requests[ip]:
                del self.requests[ip]
    
    def is_rate_limited(self, ip: str, current_time: float) -> bool:
        """检查是否超过速率限制"""
        if ip not in self.requests:
            return False
        
        # 计算最近1分钟的请求总数
        total_requests = sum(count for timestamp, count in self.requests[ip])
        
        return total_requests >= self.requests_per_minute
    
    def record_request(self, ip: str, current_time: float):
        """记录请求"""
        if ip not in self.requests:
            self.requests[ip] = []
        
        self.requests[ip].append((current_time, 1))

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("app")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # 记录未捕获的异常
            request_id = getattr(request.state, 'request_id', 'unknown')
            client_ip = self.get_client_ip(request)
            
            self.logger.error(
                f"未捕获的异常: {str(e)}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': str(request.url.path),
                    'ip_address': client_ip,
                    'exception_type': type(e).__name__
                },
                exc_info=True
            )
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "服务器内部错误",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
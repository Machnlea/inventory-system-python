from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from app.core.logging import log_manager
import time
import json
from typing import Callable

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 获取用户信息（如果有的话）
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录API访问日志
        log_manager.log_api_access(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            user_id=user_id,
            ip_address=client_ip
        )
        
        # 记录安全相关事件
        if response.status_code == 401:
            log_manager.log_security_event(
                event_type="UNAUTHORIZED_ACCESS",
                message=f"未授权访问: {request.method} {request.url.path}",
                user_id=user_id,
                ip_address=client_ip
            )
        elif response.status_code == 403:
            log_manager.log_security_event(
                event_type="FORBIDDEN_ACCESS",
                message=f"禁止访问: {request.method} {request.url.path}",
                user_id=user_id,
                ip_address=client_ip
            )
        elif response.status_code >= 500:
            log_manager.log_error(
                error_message=f"服务器错误: {request.method} {request.url.path} - {response.status_code}",
                user_id=user_id
            )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_counts = {}  # 简单的内存存储，生产环境应使用Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 简单的速率限制
        current_time = time.time()
        minute_key = f"{client_ip}:{int(current_time // 60)}"
        
        if minute_key in self.request_counts:
            self.request_counts[minute_key] += 1
        else:
            self.request_counts[minute_key] = 1
            # 清理旧的计数
            old_keys = [k for k in self.request_counts.keys() if int(k.split(':')[1]) < int(current_time // 60) - 5]
            for old_key in old_keys:
                del self.request_counts[old_key]
        
        if self.request_counts[minute_key] > self.max_requests_per_minute:
            log_manager.log_security_event(
                event_type="RATE_LIMIT_EXCEEDED",
                message=f"速率限制超出: {self.request_counts[minute_key]} 请求/分钟",
                ip_address=client_ip
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"}
            )
        
        response = await call_next(request)
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录错误
            client_ip = request.client.host if request.client else "127.0.0.1"
            user_id = None
            if hasattr(request.state, 'user'):
                user_id = getattr(request.state.user, 'id', None)
            
            log_manager.log_error(
                error_message=f"未处理的异常: {request.method} {request.url.path}",
                exception=e,
                user_id=user_id
            )
            
            # 返回通用错误响应
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"}
            )
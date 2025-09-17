import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
from pathlib import Path

class LogManager:
    """日志管理器 - 处理真实的日志文件"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 日志文件路径
        self.app_log_file = self.logs_dir / "app.log"
        self.access_log_file = self.logs_dir / "access.log"
        self.error_log_file = self.logs_dir / "error.log"
        self.security_log_file = self.logs_dir / "security.log"
        
        # 设置日志记录器
        self.setup_loggers()
    
    def setup_loggers(self):
        """设置各种日志记录器"""
        
        # 应用日志记录器
        self.app_logger = logging.getLogger("app")
        self.app_logger.setLevel(logging.INFO)
        
        # 访问日志记录器
        self.access_logger = logging.getLogger("access")
        self.access_logger.setLevel(logging.INFO)
        
        # 错误日志记录器
        self.error_logger = logging.getLogger("error")
        self.error_logger.setLevel(logging.ERROR)
        
        # 安全日志记录器
        self.security_logger = logging.getLogger("security")
        self.security_logger.setLevel(logging.WARNING)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
        
        # 为每个记录器添加文件处理器
        self._add_file_handler(self.app_logger, self.app_log_file, formatter)
        self._add_file_handler(self.access_logger, self.access_log_file, formatter)
        self._add_file_handler(self.error_logger, self.error_log_file, formatter)
        self._add_file_handler(self.security_logger, self.security_log_file, formatter)
    
    def _add_file_handler(self, logger, file_path, formatter):
        """为记录器添加文件处理器"""
        handler = logging.FileHandler(file_path, encoding='utf-8')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 防止重复日志
        logger.propagate = False
    
    def log_api_access(self, method: str, path: str, status_code: int, 
                      user_id: Optional[int] = None, ip_address: str = "127.0.0.1"):
        """记录API访问日志"""
        message = f"{method} {path} - {status_code}"
        if user_id:
            message += f" - User: {user_id}"
        message += f" - IP: {ip_address}"
        
        self.access_logger.info(message)
    
    def log_security_event(self, event_type: str, message: str, 
                          user_id: Optional[int] = None, ip_address: str = "127.0.0.1"):
        """记录安全事件"""
        security_message = f"[{event_type}] {message}"
        if user_id:
            security_message += f" - User: {user_id}"
        security_message += f" - IP: {ip_address}"
        
        self.security_logger.warning(security_message)
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None,
                  user_id: Optional[int] = None):
        """记录错误日志"""
        message = error_message
        if user_id:
            message += f" - User: {user_id}"
        if exception:
            message += f" - Exception: {str(exception)}"
        
        self.error_logger.error(message)
    
    def parse_log_file(self, file_path: Path, hours: int = 24) -> List[Dict[str, Any]]:
        """解析日志文件"""
        if not file_path.exists():
            return []
        
        logs = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析日志行
                    log_entry = self._parse_log_line(line)
                    if log_entry and log_entry.get('timestamp'):
                        try:
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            if log_time >= cutoff_time:
                                logs.append(log_entry)
                        except:
                            # 如果时间解析失败，仍然包含这条日志
                            logs.append(log_entry)
        except Exception as e:
            print(f"Error reading log file {file_path}: {e}")
        
        return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行日志"""
        # 尝试解析JSON格式
        if line.startswith('{'):
            try:
                return json.loads(line)
            except:
                pass
        
        # 解析标准格式: 2024-01-15 10:30:25,123 - app - INFO - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),?\d* - ([^-]+) - ([^-]+) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, logger, level, message = match.groups()
            return {
                'timestamp': timestamp.strip(),
                'logger': logger.strip(),
                'level': level.strip(),
                'message': message.strip()
            }
        
        # 如果无法解析，返回原始行
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'logger': 'unknown',
            'level': 'INFO',
            'message': line
        }
    
    def get_log_stats(self, hours: int = 24) -> Dict[str, int]:
        """获取日志统计信息"""
        stats = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'info_logs': 0,
            'security_events': 0,
            'api_requests': 0
        }
        
        # 统计各类日志
        for log_file, log_type in [
            (self.app_log_file, 'app'),
            (self.access_log_file, 'access'),
            (self.error_log_file, 'error'),
            (self.security_log_file, 'security')
        ]:
            logs = self.parse_log_file(log_file, hours)
            
            for log in logs:
                stats['total_logs'] += 1
                level = log.get('level', '').upper()
                
                if level == 'ERROR':
                    stats['errors'] += 1
                elif level == 'WARNING':
                    stats['warnings'] += 1
                elif level == 'INFO':
                    stats['info_logs'] += 1
                
                if log_type == 'security':
                    stats['security_events'] += 1
                elif log_type == 'access':
                    stats['api_requests'] += 1
        
        return stats
    
    def get_error_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取错误日志"""
        error_logs = self.parse_log_file(self.error_log_file, hours)
        app_logs = self.parse_log_file(self.app_log_file, hours)
        
        # 合并错误级别的日志
        all_errors = error_logs + [log for log in app_logs if log.get('level') == 'ERROR']
        
        return sorted(all_errors, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_security_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取安全日志"""
        return self.parse_log_file(self.security_log_file, hours)
    
    def get_api_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取API访问日志"""
        return self.parse_log_file(self.access_log_file, hours)
    
    def search_logs(self, keyword: str, hours: int = 24, max_results: int = 200) -> List[Dict[str, Any]]:
        """搜索日志"""
        all_logs = []
        
        # 搜索所有日志文件
        for log_file in [self.app_log_file, self.access_log_file, self.error_log_file, self.security_log_file]:
            logs = self.parse_log_file(log_file, hours)
            all_logs.extend(logs)
        
        # 过滤包含关键词的日志
        keyword_lower = keyword.lower()
        filtered_logs = [
            log for log in all_logs 
            if keyword_lower in log.get('message', '').lower()
        ]
        
        # 按时间排序并限制结果数量
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return filtered_logs[:max_results]

# 全局日志管理器实例
log_manager = LogManager()

def get_context_logger(name: str, **kwargs):
    """获取上下文日志记录器（兼容性函数）"""
    logger = logging.getLogger(name)
    # 为了兼容性，我们忽略额外的参数
    return logger

def log_security_event(logger, event_type: str, description: str, ip_address: str = "127.0.0.1", 
                      severity: str = "INFO", user_id: Optional[int] = None, **kwargs):
    """记录安全事件（兼容性函数）"""
    # 兼容旧的调用方式
    log_manager.log_security_event(event_type, description, user_id, ip_address)

def log_database_operation(logger, operation: str, table: str, record_id: Optional[int] = None, 
                          user_id: Optional[int] = None, **kwargs):
    """记录数据库操作（兼容性函数）"""
    message = f"数据库操作: {operation} on {table}"
    if record_id:
        message += f" (ID: {record_id})"
    log_manager.app_logger.info(message)

def log_file_operation(logger, operation: str, file_path: str, user_id: Optional[int] = None, 
                      equipment_id: Optional[int] = None, **kwargs):
    """记录文件操作（兼容性函数）"""
    message = f"文件操作: {operation} - {file_path}"
    if user_id:
        message += f" - User: {user_id}"
    if equipment_id:
        message += f" - Equipment: {equipment_id}"
    log_manager.app_logger.info(message)

def setup_logging():
    """设置应用日志"""
    # 简化版本，只返回日志管理器
    return log_manager
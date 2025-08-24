"""
服务器端会话管理器
用于跟踪用户会话，实现单点登录和会话冲突检测
"""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from threading import Lock
import uuid

@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    user_id: int
    username: str
    created_at: float
    last_activity: float
    user_agent: str = ""
    ip_address: str = ""

class SessionManager:
    """服务器端会话管理器"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionInfo] = {}  # session_id -> SessionInfo
        self._user_sessions: Dict[int, Set[str]] = {}  # user_id -> set of session_ids
        self._lock = Lock()
        self._session_timeout = 2 * 60 * 60  # 2小时超时
    
    def create_session(self, user_id: int, username: str, user_agent: str = "", ip_address: str = "") -> str:
        """创建新会话"""
        with self._lock:
            session_id = str(uuid.uuid4())
            current_time = time.time()
            
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                username=username,
                created_at=current_time,
                last_activity=current_time,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            self._sessions[session_id] = session_info
            
            # 更新用户会话映射
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)
            
            return session_id
    
    def get_user_active_sessions(self, user_id: int) -> List[SessionInfo]:
        """获取用户的所有活跃会话"""
        with self._lock:
            if user_id not in self._user_sessions:
                return []
            
            active_sessions = []
            current_time = time.time()
            expired_sessions = []
            
            for session_id in self._user_sessions[user_id]:
                if session_id in self._sessions:
                    session = self._sessions[session_id]
                    if current_time - session.last_activity <= self._session_timeout:
                        active_sessions.append(session)
                    else:
                        expired_sessions.append(session_id)
                else:
                    expired_sessions.append(session_id)
            
            # 清理过期会话
            for expired_id in expired_sessions:
                self._cleanup_session(expired_id)
            
            return active_sessions
    
    def update_session_activity(self, session_id: str) -> bool:
        """更新会话活动时间"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].last_activity = time.time()
                return True
            return False
    
    def invalidate_session(self, session_id: str) -> bool:
        """使会话失效"""
        with self._lock:
            return self._cleanup_session(session_id)
    
    def invalidate_user_sessions(self, user_id: int, exclude_session: Optional[str] = None) -> int:
        """使用户的所有会话失效（可排除指定会话）"""
        with self._lock:
            if user_id not in self._user_sessions:
                return 0
            
            sessions_to_remove = []
            for session_id in self._user_sessions[user_id]:
                if exclude_session and session_id == exclude_session:
                    continue
                sessions_to_remove.append(session_id)
            
            count = 0
            for session_id in sessions_to_remove:
                if self._cleanup_session(session_id):
                    count += 1
            
            return count
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        with self._lock:
            return self._sessions.get(session_id)
    
    def is_session_valid(self, session_id: str) -> bool:
        """检查会话是否有效"""
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            session = self._sessions[session_id]
            current_time = time.time()
            
            if current_time - session.last_activity > self._session_timeout:
                self._cleanup_session(session_id)
                return False
            
            return True
    
    def _cleanup_session(self, session_id: str) -> bool:
        """清理会话（内部方法，需要已持有锁）"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            user_id = session.user_id
            
            # 从会话字典中移除
            del self._sessions[session_id]
            
            # 从用户会话映射中移除
            if user_id in self._user_sessions:
                self._user_sessions[user_id].discard(session_id)
                if not self._user_sessions[user_id]:
                    del self._user_sessions[user_id]
            
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """清理所有过期会话"""
        with self._lock:
            current_time = time.time()
            expired_sessions = []
            
            for session_id, session in self._sessions.items():
                if current_time - session.last_activity > self._session_timeout:
                    expired_sessions.append(session_id)
            
            count = 0
            for session_id in expired_sessions:
                if self._cleanup_session(session_id):
                    count += 1
            
            return count
    
    def get_session_stats(self) -> Dict:
        """获取会话统计信息"""
        with self._lock:
            total_sessions = len(self._sessions)
            active_users = len(self._user_sessions)
            
            # 计算过期会话数量
            current_time = time.time()
            expired_count = 0
            for session in self._sessions.values():
                if current_time - session.last_activity > self._session_timeout:
                    expired_count += 1
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": total_sessions - expired_count,
                "expired_sessions": expired_count,
                "active_users": active_users
            }

# 全局会话管理器实例
session_manager = SessionManager()
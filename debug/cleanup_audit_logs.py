#!/usr/bin/env python3
"""
定时任务脚本：清理超过一年的操作日志
可以设置为每天运行一次
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.models import AuditLog as AuditLogModel
from app.api.audit_logs import cleanup_old_audit_logs

def cleanup_audit_logs_task():
    """执行操作日志清理任务"""
    print(f"[{datetime.now()}] 开始清理操作日志...")
    
    db = SessionLocal()
    try:
        # 清理超过一年的操作日志
        cleanup_old_audit_logs(db)
        print(f"[{datetime.now()}] 操作日志清理完成")
    except Exception as e:
        print(f"[{datetime.now()}] 清理操作日志时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_audit_logs_task()
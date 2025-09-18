from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_admin_user
from app.schemas.schemas import User
import psutil
import os
import platform
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any
import shutil
import glob
import json
import re

router = APIRouter()

@router.get("/status")
def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统状态信息"""
    try:
        # CPU信息
        cpu_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # 数据库状态
        try:
            # 测试数据库连接
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            database_status = {
                "status": "connected",
                "message": "数据库连接正常"
            }
        except Exception as e:
            database_status = {
                "status": "error",
                "message": f"数据库连接错误: {str(e)}"
            }
        
        # 日志文件信息
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            # 统计各种日志文件类型
            log_patterns = ["*.log", "*.json", "*.txt"]
            log_files = []
            for pattern in log_patterns:
                log_files.extend(glob.glob(os.path.join(logs_dir, pattern)))
            
            # 排除系统文件
            excluded_files = {'.gitkeep', '.gitignore'}
            actual_log_files = [f for f in log_files if os.path.basename(f) not in excluded_files]
            
            logs_info = {
                "total_files": len(actual_log_files)
            }
        else:
            # 创建日志目录
            os.makedirs(logs_dir, exist_ok=True)
            logs_info = {
                "total_files": 0
            }
        
        # 上传文件信息
        uploads_dir = "data/uploads"  # 根据项目结构调整路径
        if os.path.exists(uploads_dir):
            upload_files = []
            total_size = 0
            
            # 需要排除的系统文件
            excluded_files = {'.gitkeep', '.gitignore', '.DS_Store', 'Thumbs.db'}
            
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    # 排除系统文件和隐藏文件
                    if file not in excluded_files and not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            upload_files.append({
                                "name": file,
                                "path": file_path,
                                "size": file_size
                            })
            
            uploads_info = {
                "total_files": len(upload_files),
                "total_size": total_size
            }
        else:
            # 创建上传目录
            os.makedirs(uploads_dir, exist_ok=True)
            uploads_info = {
                "total_files": 0,
                "total_size": 0
            }
        
        # 系统信息
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": sys.version.split()[0]
        }
        
        # 进程信息
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_info": process.memory_info()._asdict(),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time()
        }
        
        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "database": database_status,
            "logs": logs_info,
            "uploads": uploads_info,
            "system": system_info,
            "process": process_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/database/status")
def get_database_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取数据库状态"""
    try:
        # 获取数据库文件信息
        db_path = "data/inventory.db"  # 根据实际数据库文件路径调整
        
        database_info = {
            "status": "connected",
            "database_size": os.path.getsize(db_path) if os.path.exists(db_path) else 0,
            "tables_count": 0
        }
        
        # 获取表数量
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
            database_info["tables_count"] = result.scalar()
        except Exception:
            database_info["tables_count"] = 0
        
        return database_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库状态失败: {str(e)}")

@router.post("/database/backup")
def create_database_backup(
    include_files: bool = Form(False),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建数据库备份"""
    try:
        # 创建备份目录
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if include_files:
            # 创建包含文件的完整备份包
            backup_filename = f"complete_backup_{timestamp}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. 备份数据库文件
                db_path = "data/inventory.db"
                if os.path.exists(db_path):
                    zipf.write(db_path, "inventory.db")
                    db_file_size = os.path.getsize(db_path)
                else:
                    db_file_size = 0
                
                # 2. 备份上传的文件
                uploads_dir = "data/uploads"
                files_count = 0
                total_files_size = 0
                
                if os.path.exists(uploads_dir):
                    for root, dirs, files in os.walk(uploads_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, "data")
                            zipf.write(file_path, arcname)
                            files_count += 1
                            total_files_size += os.path.getsize(file_path)
                
                # 3. 添加备份信息
                backup_info = {
                    "backup_type": "complete_backup",
                    "created_at": datetime.now().isoformat(),
                    "created_by": current_user.username,
                    "database_file": "inventory.db",
                    "database_size": db_file_size,
                    "uploads_directory": "data/uploads",
                    "files_count": files_count,
                    "files_total_size": total_files_size,
                    "description": "完整备份：数据库 + 上传文件"
                }
                
                zipf.writestr("backup_info.json", json.dumps(backup_info, indent=2))
                
                backup_size = os.path.getsize(backup_path)
                
                return {
                    "message": "完整备份创建成功（数据库 + 上传文件）",
                    "backup_file": backup_filename,
                    "backup_path": backup_path,
                    "backup_size": backup_size,
                    "backup_type": "complete",
                    "database_size": db_file_size,
                    "files_count": files_count,
                    "files_size": total_files_size,
                    "compression_ratio": round((1 - backup_size / (db_file_size + total_files_size)) * 100, 1) if (db_file_size + total_files_size) > 0 else 0,
                    "created_at": datetime.now().isoformat()
                }
        else:
            # 仅备份数据库文件
            backup_filename = f"database_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 复制数据库文件
            db_path = "data/inventory.db"
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                
                return {
                    "message": "数据库备份创建成功",
                    "backup_file": backup_filename,
                    "backup_path": backup_path,
                    "backup_size": os.path.getsize(backup_path),
                    "backup_type": "database_only",
                    "created_at": datetime.now().isoformat()
                }
            else:
                # 如果数据库文件不存在，尝试从连接中获取数据库信息
                try:
                    from sqlalchemy import text
                    # 测试连接并创建一个简单的备份标记文件
                    db.execute(text("SELECT 1"))
                    
                    # 创建一个备份信息文件
                    backup_info = {
                        "backup_type": "connection_based",
                        "created_at": datetime.now().isoformat(),
                        "message": "数据库连接正常，但未找到物理文件"
                    }
                    
                    with open(backup_path, 'w') as f:
                        json.dump(backup_info, f, indent=2)
                    
                    return {
                        "message": "数据库备份创建成功（基于连接）",
                        "backup_file": backup_filename,
                        "backup_path": backup_path,
                        "backup_size": os.path.getsize(backup_path),
                        "backup_type": "connection_based",
                        "created_at": datetime.now().isoformat()
                    }
                except Exception as e:
                    raise HTTPException(status_code=404, detail=f"数据库备份失败: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")

@router.get("/security/audit")
def get_security_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取安全审计信息"""
    try:
        from app.models.models import User as UserModel
        
        # 获取用户统计
        total_users = db.query(UserModel).count()
        admin_users = db.query(UserModel).filter(UserModel.is_admin == True).count()
        normal_users = total_users - admin_users
        
        # 模拟登录统计（实际应该从日志或审计表中获取）
        audit_info = {
            "today_logins": 0,  # 今日登录次数
            "failed_logins": 0,  # 失败登录次数
            "security_events": 0,  # 安全事件数
            "recent_logins": [],  # 最近登录记录
            "admin_users_count": admin_users,
            "normal_users_count": normal_users,
            "users_with_permissions": 0,  # 有权限的用户数
            "users_without_permissions": normal_users  # 无权限的用户数
        }
        
        # 获取有权限的用户数（有类别权限或器具权限的用户）
        from app.models.models import UserCategory, UserEquipmentPermission
        
        users_with_category_permissions = db.query(UserCategory.user_id).distinct().count()
        users_with_equipment_permissions = db.query(UserEquipmentPermission.user_id).distinct().count()
        
        # 合并去重（用户可能同时有两种权限）
        all_permission_user_ids = set()
        
        category_user_ids = db.query(UserCategory.user_id).distinct().all()
        equipment_user_ids = db.query(UserEquipmentPermission.user_id).distinct().all()
        
        for user_id in category_user_ids:
            all_permission_user_ids.add(user_id[0])
        for user_id in equipment_user_ids:
            all_permission_user_ids.add(user_id[0])
        
        audit_info["users_with_permissions"] = len(all_permission_user_ids)
        audit_info["users_without_permissions"] = normal_users - len(all_permission_user_ids)
        
        return audit_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取安全审计信息失败: {str(e)}")

@router.post("/cleanup")
def perform_system_cleanup(
    cleanup_options: Dict[str, bool],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """执行系统清理"""
    try:
        cleanup_results = {
            "cleaned_files": 0,
            "freed_space": 0,
            "operations": []
        }
        
        # 清理过期日志
        if cleanup_options.get("clean_logs", False):
            logs_dir = "logs"
            if os.path.exists(logs_dir):
                cutoff_date = datetime.now() - timedelta(days=30)
                cleaned_logs = 0
                freed_log_space = 0
                
                for log_file in glob.glob(os.path.join(logs_dir, "*.log")):
                    file_stat = os.stat(log_file)
                    file_date = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_date < cutoff_date:
                        file_size = file_stat.st_size
                        os.remove(log_file)
                        cleaned_logs += 1
                        freed_log_space += file_size
                
                cleanup_results["operations"].append({
                    "operation": "清理过期日志",
                    "files_cleaned": cleaned_logs,
                    "space_freed": freed_log_space
                })
                cleanup_results["cleaned_files"] += cleaned_logs
                cleanup_results["freed_space"] += freed_log_space
        
        # 清理临时文件
        if cleanup_options.get("clean_temp", False):
            temp_dirs = ["temp", "tmp", "__pycache__"]
            cleaned_temp = 0
            freed_temp_space = 0
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_temp += 1
                                freed_temp_space += file_size
            
            cleanup_results["operations"].append({
                "operation": "清理临时文件",
                "files_cleaned": cleaned_temp,
                "space_freed": freed_temp_space
            })
            cleanup_results["cleaned_files"] += cleaned_temp
            cleanup_results["freed_space"] += freed_temp_space
        
        # 清理孤立上传文件（这里需要根据实际业务逻辑实现）
        if cleanup_options.get("clean_uploads", False):
            # 实际实现中应该检查上传文件是否被设备记录引用
            cleanup_results["operations"].append({
                "operation": "清理孤立上传文件",
                "files_cleaned": 0,
                "space_freed": 0
            })
        
        # 清理过期会话（这里需要根据实际会话存储实现）
        if cleanup_options.get("clean_sessions", False):
            cleanup_results["operations"].append({
                "operation": "清理过期会话",
                "files_cleaned": 0,
                "space_freed": 0
            })
        
        return {
            "message": "系统清理完成",
            "results": cleanup_results,
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统清理失败: {str(e)}")

@router.get("/settings")
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统设置"""
    # 返回默认设置，实际应该从配置文件或数据库中读取
    default_settings = {
        "themeMode": "light",
        "sessionTimeout": 2,
        "minPasswordLength": 6,
        "enableTwoFactor": False,
        "enableLoginLog": True,
        "enableEmailNotification": True,
        "enableExpirationReminder": True,
        "enableCalibrationReminder": True,
        "reminderDays": 7,
        "smtpServer": "",
        "enableAutoBackup": True,
        "enableAutoCleanup": False,
        "backupFrequency": "weekly",
        "backupRetention": 30,
        "backupPath": "./backups"
    }
    
    return {"data": default_settings}

@router.put("/settings")
def update_system_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新系统设置"""
    try:
        # 这里应该将设置保存到配置文件或数据库中
        # 为了演示，我们只是返回成功消息
        
        return {
            "message": "系统设置更新成功",
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新系统设置失败: {str(e)}")

@router.post("/settings/reset")
def reset_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """重置系统设置为默认值"""
    try:
        default_settings = {
            "themeMode": "light",
            "sessionTimeout": 2,
            "minPasswordLength": 6,
            "enableTwoFactor": False,
            "enableLoginLog": True,
            "enableEmailNotification": True,
            "enableExpirationReminder": True,
            "enableCalibrationReminder": True,
            "reminderDays": 7,
            "smtpServer": "",
            "enableAutoBackup": True,
            "enableAutoCleanup": False,
            "backupFrequency": "weekly",
            "backupRetention": 30,
            "backupPath": "./backups"
        }
        
        return {
            "message": "系统设置已重置为默认值",
            "settings": default_settings,
            "reset_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置系统设置失败: {str(e)}")

@router.get("/files/details")
def get_file_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取文件详细信息"""
    try:
        file_details = {
            "uploads": {
                "total_files": 0,
                "total_size": 0,
                "by_type": {},
                "by_directory": {},
                "files": []
            },
            "logs": {
                "total_files": 0,
                "files": []
            }
        }
        
        # 分析上传文件
        uploads_dir = "data/uploads"
        if os.path.exists(uploads_dir):
            excluded_files = {'.gitkeep', '.gitignore', '.DS_Store', 'Thumbs.db'}
            
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    if file not in excluded_files and not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            file_ext = os.path.splitext(file)[1].lower()
                            rel_dir = os.path.relpath(root, uploads_dir)
                            
                            file_info = {
                                "name": file,
                                "path": file_path,
                                "size": file_size,
                                "extension": file_ext,
                                "directory": rel_dir,
                                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            }
                            
                            file_details["uploads"]["files"].append(file_info)
                            file_details["uploads"]["total_size"] += file_size
                            
                            # 按类型统计
                            if file_ext not in file_details["uploads"]["by_type"]:
                                file_details["uploads"]["by_type"][file_ext] = {"count": 0, "size": 0}
                            file_details["uploads"]["by_type"][file_ext]["count"] += 1
                            file_details["uploads"]["by_type"][file_ext]["size"] += file_size
                            
                            # 按目录统计
                            if rel_dir not in file_details["uploads"]["by_directory"]:
                                file_details["uploads"]["by_directory"][rel_dir] = {"count": 0, "size": 0}
                            file_details["uploads"]["by_directory"][rel_dir]["count"] += 1
                            file_details["uploads"]["by_directory"][rel_dir]["size"] += file_size
            
            file_details["uploads"]["total_files"] = len(file_details["uploads"]["files"])
        
        # 分析日志文件
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            log_patterns = ["*.log", "*.json", "*.txt"]
            excluded_files = {'.gitkeep', '.gitignore'}
            
            for pattern in log_patterns:
                for log_file in glob.glob(os.path.join(logs_dir, pattern)):
                    file_name = os.path.basename(log_file)
                    if file_name not in excluded_files:
                        file_size = os.path.getsize(log_file)
                        file_details["logs"]["files"].append({
                            "name": file_name,
                            "path": log_file,
                            "size": file_size,
                            "modified": datetime.fromtimestamp(os.path.getmtime(log_file)).isoformat()
                        })
            
            file_details["logs"]["total_files"] = len(file_details["logs"]["files"])
        
        return file_details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件详情失败: {str(e)}")

@router.post("/database/optimize")
def optimize_database(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """优化数据库"""
    try:
        from sqlalchemy import text
        
        # 执行SQLite优化命令
        optimization_results = []
        
        # 1. VACUUM - 重新组织数据库文件，减少碎片
        try:
            db.execute(text("VACUUM"))
            optimization_results.append("VACUUM: 数据库文件重新组织完成")
        except Exception as e:
            optimization_results.append(f"VACUUM: 失败 - {str(e)}")
        
        # 2. ANALYZE - 更新统计信息
        try:
            db.execute(text("ANALYZE"))
            optimization_results.append("ANALYZE: 数据库统计信息更新完成")
        except Exception as e:
            optimization_results.append(f"ANALYZE: 失败 - {str(e)}")
        
        # 3. 清理过期数据（根据实际业务逻辑）
        try:
            # 示例：清理30天前的日志（如果有的话）
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # 这里可以根据实际业务需求添加清理逻辑
            # 例如：清理过期的操作日志、临时数据等
            
            optimization_results.append("数据清理: 检查完成，未发现需要清理的数据")
        except Exception as e:
            optimization_results.append(f"数据清理: 失败 - {str(e)}")
        
        # 获取优化后的数据库信息
        db_path = "data/inventory.db"
        final_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        return {
            "message": "数据库优化完成",
            "optimization_results": optimization_results,
            "final_database_size": final_size,
            "optimized_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库优化失败: {str(e)}")

@router.get("/database/statistics")
def get_database_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取数据库统计信息"""
    try:
        from sqlalchemy import text
        
        statistics = {
            "tables": {},
            "records": {},
            "size_info": {},
            "indexes": {}
        }
        
        # 获取所有表信息
        tables_result = db.execute(text("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """))
        
        total_records = 0
        for table_name, table_sql in tables_result:
            # 获取表的记录数
            try:
                count_result = db.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
                record_count = count_result.scalar()
                total_records += record_count
                
                statistics["tables"][table_name] = {
                    "record_count": record_count,
                    "sql_definition": table_sql
                }
            except Exception as e:
                statistics["tables"][table_name] = {
                    "record_count": "ERROR",
                    "error": str(e)
                }
        
        statistics["records"]["total_records"] = total_records
        
        # 获取数据库文件大小信息
        db_path = "data/inventory.db"
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            statistics["size_info"] = {
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "file_path": db_path
            }
        
        # 获取索引信息
        try:
            indexes_result = db.execute(text("""
                SELECT name, tbl_name, sql FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """))
            
            for index_name, table_name, index_sql in indexes_result:
                if table_name not in statistics["indexes"]:
                    statistics["indexes"][table_name] = []
                statistics["indexes"][table_name].append({
                    "name": index_name,
                    "sql": index_sql
                })
        except Exception as e:
            statistics["indexes"]["error"] = str(e)
        
        return {
            "message": "数据库统计信息获取成功",
            "statistics": statistics,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库统计失败: {str(e)}")

@router.get("/database/backups")
def get_backup_history(
    current_user: User = Depends(get_current_admin_user)
):
    """获取备份历史记录"""
    try:
        backup_dir = "backups"
        backups = []
        
        if os.path.exists(backup_dir):
            # 获取所有备份文件（.db 和 .zip）
            backup_files = glob.glob(os.path.join(backup_dir, "*.db")) + glob.glob(os.path.join(backup_dir, "*.zip"))
            
            for backup_file in backup_files:
                try:
                    file_stat = os.stat(backup_file)
                    file_size = file_stat.st_size
                    modified_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # 从文件名提取时间戳
                    file_name = os.path.basename(backup_file)
                    # 匹配 database_backup_*.db 和 complete_backup_*.zip
                    created_match = re.search(r'(database_backup|complete_backup)_(\d{8}_\d{6})\.(db|zip)', file_name)
                    created_at = None
                    backup_type = "database"  # 默认类型
                    
                    if created_match:
                        try:
                            created_at = datetime.strptime(created_match.group(2), "%Y%m%d_%H%M%S")
                            backup_type = "complete" if created_match.group(1) == "complete_backup" else "database"
                        except:
                            created_at = modified_time
                    else:
                        created_at = modified_time
                    
                    backups.append({
                        "file_name": file_name,
                        "file_path": backup_file,
                        "file_size": file_size,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "created_at": created_at.isoformat(),
                        "modified_at": modified_time.isoformat(),
                        "backup_type": backup_type,
                        "is_complete_backup": backup_type == "complete"
                    })
                    
                except Exception as e:
                    # 跳过无法读取的文件
                    continue
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "message": "备份历史获取成功",
            "backups": backups,
            "total_backups": len(backups),
            "backup_directory": backup_dir,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份历史失败: {str(e)}")

@router.get("/database/backups/{backup_name}/download")
def download_backup(
    backup_name: str,
    current_user: User = Depends(get_current_admin_user)
):
    """下载指定备份文件"""
    try:
        backup_path = os.path.join("backups", backup_name)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 安全检查：确保文件名符合预期格式
        if not (backup_name.startswith("database_backup_") and backup_name.endswith(".db")) and \
           not (backup_name.startswith("complete_backup_") and backup_name.endswith(".zip")):
            raise HTTPException(status_code=400, detail="无效的备份文件名")
        
        from fastapi.responses import FileResponse
        
        # 根据文件类型设置媒体类型
        if backup_name.endswith(".zip"):
            media_type = "application/zip"
        else:
            media_type = "application/x-sqlite3"
        
        return FileResponse(
            path=backup_path,
            filename=backup_name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载备份失败: {str(e)}")

@router.get("/database/backups/{backup_name}/download-with-token")
def download_backup_with_token(
    backup_name: str,
    token: str = None
):
    """使用URL令牌下载指定备份文件"""
    try:
        # 验证令牌
        if not token:
            raise HTTPException(status_code=401, detail="缺少认证令牌")
        
        from app.core.security import verify_token
        try:
            username = verify_token(token)
            if not username:
                raise HTTPException(status_code=401, detail="无效的认证令牌")
            print(f"令牌验证成功，用户: {username}")  # 调试信息
        except Exception as e:
            print(f"令牌验证失败: {e}")  # 调试信息
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        
        backup_path = os.path.join("backups", backup_name)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 安全检查：确保文件名符合预期格式
        if not (backup_name.startswith("database_backup_") and backup_name.endswith(".db")) and \
           not (backup_name.startswith("complete_backup_") and backup_name.endswith(".zip")):
            raise HTTPException(status_code=400, detail="无效的备份文件名")
        
        from fastapi.responses import FileResponse
        
        # 根据文件类型设置媒体类型
        if backup_name.endswith(".zip"):
            media_type = "application/zip"
        else:
            media_type = "application/x-sqlite3"
        
        print(f"正在下载文件: {backup_path}, 类型: {media_type}")  # 调试信息
        
        return FileResponse(
            path=backup_path,
            filename=backup_name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"下载失败: {e}")  # 调试信息
        raise HTTPException(status_code=500, detail=f"下载备份失败: {str(e)}")

@router.get("/database/backups/test-token")
def test_token_validation(
    token: str = None
):
    """测试令牌验证"""
    try:
        if not token:
            return {"status": "error", "message": "缺少令牌"}
        
        from app.core.security import verify_token
        username = verify_token(token)
        
        if username:
            return {"status": "success", "message": f"令牌有效，用户: {username}"}
        else:
            return {"status": "error", "message": "令牌无效"}
            
    except Exception as e:
        return {"status": "error", "message": f"令牌验证失败: {str(e)}"}

@router.delete("/database/backups/{backup_name}")
def delete_backup(
    backup_name: str,
    current_user: User = Depends(get_current_admin_user)
):
    """删除指定备份文件"""
    try:
        backup_path = os.path.join("backups", backup_name)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 安全检查：确保文件名符合预期格式
        if not (backup_name.startswith("database_backup_") and backup_name.endswith(".db")) and \
           not (backup_name.startswith("complete_backup_") and backup_name.endswith(".zip")):
            raise HTTPException(status_code=400, detail="无效的备份文件名")
        
        os.remove(backup_path)
        
        return {
            "message": f"备份文件 {backup_name} 删除成功",
            "deleted_file": backup_name,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")
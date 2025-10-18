#!/usr/bin/env python3
"""
执行数据库迁移脚本
"""

import sys
import os
import importlib.util
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.db.database import SessionLocal, engine

def load_migration_module(migration_file):
    """动态加载迁移模块"""
    spec = importlib.util.spec_from_file_location("migration", migration_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def get_applied_migrations():
    """获取已应用的迁移列表"""
    db = SessionLocal()
    try:
        # 检查迁移表是否存在
        inspector = inspect(engine)
        if 'alembic_version' not in inspector.get_table_names():
            # 创建迁移版本表
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL PRIMARY KEY
                )
            """))
            db.commit()
            return set()
        
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        return {row[0] for row in result.fetchall()}
    except Exception as e:
        print(f"获取已应用迁移时出错: {e}")
        return set()
    finally:
        db.close()

def mark_migration_applied(version):
    """标记迁移为已应用"""
    db = SessionLocal()
    try:
        # 删除旧版本记录
        db.execute(text("DELETE FROM alembic_version"))
        # 插入新版本记录
        db.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version)"), 
                  {"version": version})
        db.commit()
        print(f"标记迁移 {version} 为已应用")
    except Exception as e:
        print(f"标记迁移时出错: {e}")
        db.rollback()
    finally:
        db.close()

def run_migrations():
    """运行所有待执行的迁移"""
    migrations_dir = project_root / "migrations"
    
    # 获取所有迁移文件
    migration_files = sorted([
        f for f in migrations_dir.glob("*.py") 
        if f.name != "__init__.py" and not f.name.startswith(".")
    ])
    
    if not migration_files:
        print("没有找到迁移文件")
        return
    
    print(f"找到 {len(migration_files)} 个迁移文件")
    
    # 获取已应用的迁移
    applied_migrations = get_applied_migrations()
    print(f"已应用的迁移: {applied_migrations}")
    
    # 执行迁移
    db = SessionLocal()
    latest_version = None
    
    try:
        for migration_file in migration_files:
            try:
                # 加载迁移模块
                module = load_migration_module(migration_file)
                
                if not hasattr(module, 'revision') or not hasattr(module, 'upgrade'):
                    print(f"跳过无效的迁移文件: {migration_file.name}")
                    continue
                
                version = module.revision
                latest_version = version
                
                if version in applied_migrations:
                    print(f"跳过已应用的迁移: {migration_file.name} (版本 {version})")
                    continue
                
                print(f"执行迁移: {migration_file.name} (版本 {version})")
                
                # 执行迁移的upgrade函数
                # 注意：这里我们直接执行SQL，因为我们没有完整的Alembic环境
                if hasattr(module, 'upgrade'):
                    # 手动执行迁移逻辑
                    execute_migration_manually(db, migration_file.name, version)
                
            except Exception as e:
                print(f"执行迁移 {migration_file.name} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 标记最新版本为已应用
        if latest_version:
            mark_migration_applied(latest_version)
            
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        db.rollback()
    finally:
        db.close()

def execute_migration_manually(db, migration_name, version):
    """手动执行特定迁移的SQL语句"""
    
    if "016_finalize_rollback_fields" in migration_name:
        execute_016_migration(db)
    elif "017_enhance_audit_and_rollback_system" in migration_name:
        execute_017_migration(db)
    else:
        print(f"未知的迁移: {migration_name}")

def execute_016_migration(db):
    """执行016迁移：完善回滚字段"""
    try:
        # 检查字段是否存在
        result = db.execute(text("PRAGMA table_info(calibration_history)"))
        columns = [row[1] for row in result.fetchall()]
        
        # 添加缺失的字段
        if 'is_rolled_back' not in columns:
            db.execute(text("ALTER TABLE calibration_history ADD COLUMN is_rolled_back BOOLEAN DEFAULT 0"))
            print("添加 is_rolled_back 字段")
        
        if 'rolled_back_at' not in columns:
            db.execute(text("ALTER TABLE calibration_history ADD COLUMN rolled_back_at DATETIME"))
            print("添加 rolled_back_at 字段")
        
        if 'rolled_back_by' not in columns:
            db.execute(text("ALTER TABLE calibration_history ADD COLUMN rolled_back_by INTEGER"))
            print("添加 rolled_back_by 字段")
        
        if 'rollback_reason' not in columns:
            db.execute(text("ALTER TABLE calibration_history ADD COLUMN rollback_reason TEXT"))
            print("添加 rollback_reason 字段")
        
        # 更新默认值
        db.execute(text("UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL"))
        
        # 创建索引
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_calibration_history_is_rolled_back ON calibration_history(is_rolled_back)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_calibration_history_rolled_back_at ON calibration_history(rolled_back_at)"))
        except Exception as e:
            print(f"创建索引时出错: {e}")
        
        db.commit()
        print("016迁移执行完成")
        
    except Exception as e:
        print(f"执行016迁移时出错: {e}")
        db.rollback()
        raise

def execute_017_migration(db):
    """执行017迁移：增强审计和回滚系统"""
    try:
        # 检查audit_logs表字段
        result = db.execute(text("PRAGMA table_info(audit_logs)"))
        audit_columns = [row[1] for row in result.fetchall()]
        
        # 添加审计日志的回滚字段
        if 'rollback_target_id' not in audit_columns:
            db.execute(text("ALTER TABLE audit_logs ADD COLUMN rollback_target_id INTEGER"))
            print("添加 rollback_target_id 字段到 audit_logs")
        
        if 'rollback_target_type' not in audit_columns:
            db.execute(text("ALTER TABLE audit_logs ADD COLUMN rollback_target_type VARCHAR(50)"))
            print("添加 rollback_target_type 字段到 audit_logs")
        
        if 'is_rollback_operation' not in audit_columns:
            db.execute(text("ALTER TABLE audit_logs ADD COLUMN is_rollback_operation BOOLEAN DEFAULT 0"))
            print("添加 is_rollback_operation 字段到 audit_logs")
        
        # 检查calibration_history表字段
        result = db.execute(text("PRAGMA table_info(calibration_history)"))
        cal_columns = [row[1] for row in result.fetchall()]
        
        if 'rollback_audit_log_id' not in cal_columns:
            db.execute(text("ALTER TABLE calibration_history ADD COLUMN rollback_audit_log_id INTEGER"))
            print("添加 rollback_audit_log_id 字段到 calibration_history")
        
        # 更新默认值
        db.execute(text("UPDATE audit_logs SET is_rollback_operation = 0 WHERE is_rollback_operation IS NULL"))
        
        # 创建索引
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_rollback_operation ON audit_logs(is_rollback_operation)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_rollback_target ON audit_logs(rollback_target_type, rollback_target_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_calibration_history_rollback_status ON calibration_history(is_rolled_back, rolled_back_at)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_calibration_history_equipment_rollback ON calibration_history(equipment_id, is_rolled_back)"))
        except Exception as e:
            print(f"创建索引时出错: {e}")
        
        # 创建视图
        try:
            db.execute(text("""
                CREATE VIEW IF NOT EXISTS v_rollback_summary AS
                SELECT 
                    ch.id as calibration_history_id,
                    ch.equipment_id,
                    ch.calibration_date,
                    ch.is_rolled_back,
                    ch.rolled_back_at,
                    ch.rollback_reason,
                    u.username as rolled_back_by_user,
                    al.action as rollback_action,
                    al.timestamp as rollback_timestamp
                FROM calibration_history ch
                LEFT JOIN users u ON ch.rolled_back_by = u.id
                LEFT JOIN audit_logs al ON ch.rollback_audit_log_id = al.id
                WHERE ch.is_rolled_back = 1
            """))
            print("创建回滚摘要视图")
        except Exception as e:
            print(f"创建视图时出错: {e}")
        
        db.commit()
        print("017迁移执行完成")
        
    except Exception as e:
        print(f"执行017迁移时出错: {e}")
        db.rollback()
        raise

def main():
    """主函数"""
    print("=== 数据库迁移工具 ===")
    print(f"项目根目录: {project_root}")
    
    try:
        run_migrations()
        print("所有迁移执行完成！")
    except Exception as e:
        print(f"迁移执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
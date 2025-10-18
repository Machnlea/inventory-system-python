#!/usr/bin/env python3
"""
快速应用回滚功能相关的数据库迁移
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.db.database import SessionLocal, engine

def apply_rollback_migrations():
    """应用回滚功能相关的数据库迁移"""
    db = SessionLocal()
    
    try:
        print("=== 应用回滚功能数据库迁移 ===")
        
        # 1. 检查当前数据库结构
        print("\n1. 检查当前数据库结构...")
        inspector = inspect(engine)
        
        # 检查calibration_history表
        if 'calibration_history' not in inspector.get_table_names():
            print("错误: calibration_history 表不存在")
            return False
        
        cal_columns = [col['name'] for col in inspector.get_columns('calibration_history')]
        print(f"   calibration_history 现有字段: {len(cal_columns)} 个")
        
        # 检查audit_logs表
        if 'audit_logs' not in inspector.get_table_names():
            print("错误: audit_logs 表不存在")
            return False
        
        audit_columns = [col['name'] for col in inspector.get_columns('audit_logs')]
        print(f"   audit_logs 现有字段: {len(audit_columns)} 个")
        
        # 2. 应用calibration_history表的回滚字段
        print("\n2. 添加calibration_history表的回滚字段...")
        
        rollback_fields = [
            ('is_rolled_back', 'BOOLEAN DEFAULT 0', '回滚状态标记'),
            ('rolled_back_at', 'DATETIME', '回滚时间'),
            ('rolled_back_by', 'INTEGER', '回滚操作者ID'),
            ('rollback_reason', 'TEXT', '回滚原因'),
            ('rollback_audit_log_id', 'INTEGER', '关联的审计日志ID')
        ]
        
        for field_name, field_type, description in rollback_fields:
            if field_name not in cal_columns:
                try:
                    db.execute(text(f"ALTER TABLE calibration_history ADD COLUMN {field_name} {field_type}"))
                    print(f"   ✓ 添加字段: {field_name} ({description})")
                except Exception as e:
                    print(f"   ✗ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"   - 字段 {field_name} 已存在")
        
        # 3. 应用audit_logs表的回滚字段
        print("\n3. 添加audit_logs表的回滚字段...")
        
        audit_rollback_fields = [
            ('rollback_target_id', 'INTEGER', '被回滚的目标记录ID'),
            ('rollback_target_type', 'VARCHAR(50)', '被回滚的目标记录类型'),
            ('is_rollback_operation', 'BOOLEAN DEFAULT 0', '是否为回滚操作')
        ]
        
        for field_name, field_type, description in audit_rollback_fields:
            if field_name not in audit_columns:
                try:
                    db.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {field_name} {field_type}"))
                    print(f"   ✓ 添加字段: {field_name} ({description})")
                except Exception as e:
                    print(f"   ✗ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"   - 字段 {field_name} 已存在")
        
        # 4. 更新默认值
        print("\n4. 更新默认值...")
        try:
            result = db.execute(text("UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL"))
            print(f"   ✓ 更新calibration_history表默认值 (影响 {result.rowcount} 行)")
            
            result = db.execute(text("UPDATE audit_logs SET is_rollback_operation = 0 WHERE is_rollback_operation IS NULL"))
            print(f"   ✓ 更新audit_logs表默认值 (影响 {result.rowcount} 行)")
        except Exception as e:
            print(f"   ✗ 更新默认值失败: {e}")
        
        # 5. 创建索引
        print("\n5. 创建性能优化索引...")
        
        indexes = [
            ('idx_calibration_history_is_rolled_back', 'calibration_history', 'is_rolled_back'),
            ('idx_calibration_history_rolled_back_at', 'calibration_history', 'rolled_back_at'),
            ('idx_audit_logs_rollback_operation', 'audit_logs', 'is_rollback_operation'),
            ('idx_calibration_history_equipment_rollback', 'calibration_history', 'equipment_id, is_rolled_back')
        ]
        
        for index_name, table_name, columns in indexes:
            try:
                db.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"))
                print(f"   ✓ 创建索引: {index_name}")
            except Exception as e:
                print(f"   ✗ 创建索引 {index_name} 失败: {e}")
        
        # 6. 创建回滚摘要视图
        print("\n6. 创建回滚摘要视图...")
        try:
            db.execute(text("DROP VIEW IF EXISTS v_rollback_summary"))
            db.execute(text("""
                CREATE VIEW v_rollback_summary AS
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
            print("   ✓ 创建回滚摘要视图: v_rollback_summary")
        except Exception as e:
            print(f"   ✗ 创建视图失败: {e}")
        
        # 7. 提交更改
        db.commit()
        print("\n✓ 所有迁移应用成功！")
        
        # 8. 验证结果
        print("\n7. 验证迁移结果...")
        verify_migration_result(db)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 迁移过程中出错: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def verify_migration_result(db):
    """验证迁移结果"""
    try:
        # 检查字段是否都存在
        result = db.execute(text("PRAGMA table_info(calibration_history)"))
        cal_columns = [row[1] for row in result.fetchall()]
        
        result = db.execute(text("PRAGMA table_info(audit_logs)"))
        audit_columns = [row[1] for row in result.fetchall()]
        
        required_cal_fields = ['is_rolled_back', 'rolled_back_at', 'rolled_back_by', 'rollback_reason', 'rollback_audit_log_id']
        required_audit_fields = ['rollback_target_id', 'rollback_target_type', 'is_rollback_operation']
        
        cal_missing = [f for f in required_cal_fields if f not in cal_columns]
        audit_missing = [f for f in required_audit_fields if f not in audit_columns]
        
        if not cal_missing and not audit_missing:
            print("   ✓ 所有必需字段都已添加")
        else:
            if cal_missing:
                print(f"   ✗ calibration_history 缺失字段: {cal_missing}")
            if audit_missing:
                print(f"   ✗ audit_logs 缺失字段: {audit_missing}")
        
        # 检查数据完整性
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_rolled_back IS NULL THEN 1 END) as null_count
            FROM calibration_history
        """))
        
        row = result.fetchone()
        if row:
            total, null_count = row
            if null_count == 0:
                print(f"   ✓ 数据完整性检查通过 (总记录数: {total})")
            else:
                print(f"   ✗ 发现 {null_count} 条记录的回滚状态为NULL")
        
        # 检查视图是否存在
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='view' AND name='v_rollback_summary'"))
        if result.fetchone():
            print("   ✓ 回滚摘要视图创建成功")
        else:
            print("   ✗ 回滚摘要视图创建失败")
            
    except Exception as e:
        print(f"   验证过程中出错: {e}")

def main():
    """主函数"""
    print("回滚功能数据库迁移工具")
    print("=" * 50)
    
    # 确认执行
    response = input("是否要应用回滚功能的数据库迁移? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("迁移已取消")
        return
    
    # 执行迁移
    success = apply_rollback_migrations()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ 迁移完成！现在可以使用回滚功能了。")
        print("\n建议:")
        print("1. 重启应用服务器")
        print("2. 测试回滚功能是否正常工作")
        print("3. 检查操作日志页面的回滚按钮")
    else:
        print("\n" + "=" * 50)
        print("✗ 迁移失败！请检查错误信息并手动修复。")

if __name__ == "__main__":
    main()
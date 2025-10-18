#!/usr/bin/env python3
"""
验证数据库结构是否包含所有必要的回滚字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.db.database import SessionLocal, engine

def verify_table_structure():
    """验证数据库表结构"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        print("=== 数据库结构验证 ===")
        
        # 1. 验证calibration_history表
        print("\n1. 检查 calibration_history 表结构:")
        if 'calibration_history' in inspector.get_table_names():
            columns = inspector.get_columns('calibration_history')
            column_names = [col['name'] for col in columns]
            
            required_rollback_fields = [
                'is_rolled_back',
                'rolled_back_at', 
                'rolled_back_by',
                'rollback_reason',
                'rollback_audit_log_id'
            ]
            
            print(f"   现有字段: {column_names}")
            
            missing_fields = []
            for field in required_rollback_fields:
                if field in column_names:
                    print(f"   ✓ {field} - 存在")
                else:
                    print(f"   ✗ {field} - 缺失")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   警告: 缺失字段 {missing_fields}")
            else:
                print("   ✓ 所有回滚字段都存在")
        else:
            print("   ✗ calibration_history 表不存在")
        
        # 2. 验证audit_logs表
        print("\n2. 检查 audit_logs 表结构:")
        if 'audit_logs' in inspector.get_table_names():
            columns = inspector.get_columns('audit_logs')
            column_names = [col['name'] for col in columns]
            
            required_audit_fields = [
                'rollback_target_id',
                'rollback_target_type',
                'is_rollback_operation'
            ]
            
            print(f"   现有字段: {column_names}")
            
            missing_fields = []
            for field in required_audit_fields:
                if field in column_names:
                    print(f"   ✓ {field} - 存在")
                else:
                    print(f"   ✗ {field} - 缺失")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   警告: 缺失字段 {missing_fields}")
            else:
                print("   ✓ 所有审计回滚字段都存在")
        else:
            print("   ✗ audit_logs 表不存在")
        
        # 3. 验证索引
        print("\n3. 检查索引:")
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%rollback%'"))
            indexes = [row[0] for row in result.fetchall()]
            
            expected_indexes = [
                'idx_calibration_history_is_rolled_back',
                'idx_calibration_history_rolled_back_at',
                'idx_audit_logs_rollback_operation',
                'idx_calibration_history_rollback_status'
            ]
            
            for index in expected_indexes:
                if index in indexes:
                    print(f"   ✓ {index} - 存在")
                else:
                    print(f"   ✗ {index} - 缺失")
            
            if indexes:
                print(f"   现有回滚相关索引: {indexes}")
            
        except Exception as e:
            print(f"   检查索引时出错: {e}")
        
        # 4. 验证视图
        print("\n4. 检查视图:")
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%rollback%'"))
            views = [row[0] for row in result.fetchall()]
            
            if 'v_rollback_summary' in views:
                print("   ✓ v_rollback_summary - 存在")
            else:
                print("   ✗ v_rollback_summary - 缺失")
            
        except Exception as e:
            print(f"   检查视图时出错: {e}")
        
        # 5. 验证数据完整性
        print("\n5. 检查数据完整性:")
        try:
            # 检查calibration_history表中的回滚字段数据
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN is_rolled_back = 1 THEN 1 END) as rolled_back_records,
                    COUNT(CASE WHEN is_rolled_back IS NULL THEN 1 END) as null_rollback_status
                FROM calibration_history
            """))
            
            row = result.fetchone()
            if row:
                total, rolled_back, null_status = row
                print(f"   总检定记录数: {total}")
                print(f"   已回滚记录数: {rolled_back}")
                print(f"   回滚状态为NULL的记录数: {null_status}")
                
                if null_status > 0:
                    print(f"   警告: 有 {null_status} 条记录的回滚状态为NULL")
                else:
                    print("   ✓ 所有记录的回滚状态都已设置")
            
        except Exception as e:
            print(f"   检查数据完整性时出错: {e}")
        
        print("\n=== 验证完成 ===")
        
    except Exception as e:
        print(f"验证过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def fix_missing_fields():
    """修复缺失的字段"""
    db = SessionLocal()
    try:
        print("\n=== 修复缺失字段 ===")
        
        # 检查并添加calibration_history表的字段
        result = db.execute(text("PRAGMA table_info(calibration_history)"))
        cal_columns = [row[1] for row in result.fetchall()]
        
        fields_to_add = [
            ('is_rolled_back', 'BOOLEAN DEFAULT 0'),
            ('rolled_back_at', 'DATETIME'),
            ('rolled_back_by', 'INTEGER'),
            ('rollback_reason', 'TEXT'),
            ('rollback_audit_log_id', 'INTEGER')
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in cal_columns:
                try:
                    db.execute(text(f"ALTER TABLE calibration_history ADD COLUMN {field_name} {field_type}"))
                    print(f"   ✓ 添加字段: {field_name}")
                except Exception as e:
                    print(f"   ✗ 添加字段 {field_name} 失败: {e}")
        
        # 检查并添加audit_logs表的字段
        result = db.execute(text("PRAGMA table_info(audit_logs)"))
        audit_columns = [row[1] for row in result.fetchall()]
        
        audit_fields_to_add = [
            ('rollback_target_id', 'INTEGER'),
            ('rollback_target_type', 'VARCHAR(50)'),
            ('is_rollback_operation', 'BOOLEAN DEFAULT 0')
        ]
        
        for field_name, field_type in audit_fields_to_add:
            if field_name not in audit_columns:
                try:
                    db.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {field_name} {field_type}"))
                    print(f"   ✓ 添加字段: {field_name}")
                except Exception as e:
                    print(f"   ✗ 添加字段 {field_name} 失败: {e}")
        
        # 更新默认值
        db.execute(text("UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL"))
        db.execute(text("UPDATE audit_logs SET is_rollback_operation = 0 WHERE is_rollback_operation IS NULL"))
        
        db.commit()
        print("   ✓ 字段修复完成")
        
    except Exception as e:
        print(f"修复字段时出错: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主函数"""
    print("数据库结构验证工具")
    
    # 首先验证结构
    verify_table_structure()
    
    # 询问是否需要修复
    response = input("\n是否需要修复缺失的字段? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        fix_missing_fields()
        print("\n重新验证结构:")
        verify_table_structure()

if __name__ == "__main__":
    main()
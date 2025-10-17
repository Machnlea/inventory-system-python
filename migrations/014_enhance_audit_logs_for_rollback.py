#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本: 增强操作日志功能支持回滚操作
- 为 audit_logs 表添加回滚相关字段
- 添加操作类型、目标表、IP地址等追踪字段
- 支持操作历史回溯和撤销功能
"""

import sqlite3
import os
from datetime import datetime

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')

def migrate_up():
    """执行向上迁移"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("开始增强操作日志功能...")

        # 1. 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if not cursor.fetchone():
            print("✗ audit_logs 表不存在，请先创建基础表")
            return False

        # 2. 检查新字段是否已存在
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [column[1] for column in cursor.fetchall()]

        # 需要添加的新字段
        new_fields = {
            'operation_type': 'VARCHAR(20) DEFAULT "equipment"',
            'target_table': 'VARCHAR(50)',
            'target_id': 'INTEGER',
            'parent_log_id': 'INTEGER',
            'rollback_log_id': 'INTEGER',
            'is_rollback': 'BOOLEAN DEFAULT 0',
            'rollback_reason': 'TEXT',
            'ip_address': 'VARCHAR(45)',
            'user_agent': 'TEXT'
        }

        fields_to_add = []
        for field in new_fields:
            if field not in columns:
                fields_to_add.append((field, new_fields[field]))

        if not fields_to_add:
            print("✓ 所有新字段已存在，跳过迁移")
            return True

        # 3. 添加新字段
        for field_name, field_def in fields_to_add:
            try:
                alter_sql = f"ALTER TABLE audit_logs ADD COLUMN {field_name} {field_def}"
                cursor.execute(alter_sql)
                print(f"✓ 添加字段: {field_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ 字段 {field_name} 已存在")
                else:
                    print(f"✗ 添加字段 {field_name} 失败: {e}")
                    return False

        # 4. 创建索引以提高查询性能
        indexes = [
            ("idx_audit_logs_operation_type", "audit_logs", "operation_type"),
            ("idx_audit_logs_target", "audit_logs", "target_table, target_id"),
            ("idx_audit_logs_parent", "audit_logs", "parent_log_id"),
            ("idx_audit_logs_rollback", "audit_logs", "rollback_log_id"),
            ("idx_audit_logs_is_rollback", "audit_logs", "is_rollback"),
            ("idx_audit_logs_created_at", "audit_logs", "created_at"),
            ("idx_audit_logs_user_equipment", "audit_logs", "user_id, equipment_id")
        ]

        for index_name, table_name, columns in indexes:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                if not cursor.fetchone():
                    create_index_sql = f"CREATE INDEX {index_name} ON {table_name} ({columns})"
                    cursor.execute(create_index_sql)
                    print(f"✓ 创建索引: {index_name}")
                else:
                    print(f"✓ 索引 {index_name} 已存在")
            except sqlite3.OperationalError as e:
                print(f"✗ 创建索引 {index_name} 失败: {e}")

        # 5. 迁移现有数据，为新字段设置默认值
        print("✓ 开始迁移现有数据...")

        # 为现有记录设置操作类型
        cursor.execute("""
            UPDATE audit_logs
            SET operation_type = CASE
                WHEN equipment_id IS NOT NULL THEN 'equipment'
                ELSE 'system'
            END
            WHERE operation_type IS NULL OR operation_type = ''
        """)

        # 为现有记录设置目标表和ID
        cursor.execute("""
            UPDATE audit_logs
            SET target_table = 'equipments',
                target_id = equipment_id
            WHERE equipment_id IS NOT NULL
            AND (target_table IS NULL OR target_id IS NULL)
        """)

        # 统计迁移的记录数
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_records = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE operation_type IS NOT NULL")
        migrated_records = cursor.fetchone()[0]

        print(f"✓ 数据迁移完成: {migrated_records}/{total_records} 条记录")

        # 6. 提交事务
        conn.commit()
        print("✓ 操作日志功能增强完成")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ 迁移失败: {e}")
        return False

    finally:
        conn.close()

def migrate_down():
    """执行向下迁移（可选）"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("开始回滚操作日志功能增强...")

        # SQLite不支持直接删除列，我们需要重建表
        # 1. 创建临时表
        cursor.execute("""
            CREATE TABLE audit_logs_temp (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                equipment_id INTEGER,
                action VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (equipment_id) REFERENCES equipments (id)
            )
        """)

        # 2. 复制数据（只复制原始字段）
        cursor.execute("""
            INSERT INTO audit_logs_temp (
                id, user_id, equipment_id, action, description,
                old_value, new_value, created_at
            )
            SELECT
                id, user_id, equipment_id, action, description,
                old_value, new_value, created_at
            FROM audit_logs
        """)

        # 3. 删除原表
        cursor.execute("DROP TABLE audit_logs")

        # 4. 重命名临时表
        cursor.execute("ALTER TABLE audit_logs_temp RENAME TO audit_logs")

        # 5. 重建基本索引
        cursor.execute("CREATE INDEX idx_audit_logs_user_id ON audit_logs (user_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_equipment_id ON audit_logs (equipment_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at)")

        conn.commit()
        print("✓ 回滚操作日志功能增强完成")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ 回滚失败: {e}")
        return False

    finally:
        conn.close()

def check_migration_status():
    """检查迁移状态"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("✗ 数据库文件不存在")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if not cursor.fetchone():
            print("✗ audit_logs 表不存在")
            return False

        # 检查新字段是否存在
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [column[1] for column in cursor.fetchall()]

        required_fields = [
            'operation_type', 'target_table', 'target_id',
            'parent_log_id', 'rollback_log_id', 'is_rollback',
            'rollback_reason', 'ip_address', 'user_agent'
        ]

        missing_fields = [field for field in required_fields if field not in columns]

        if missing_fields:
            print(f"✗ 缺少字段: {', '.join(missing_fields)}")
            return False

        print("✓ 操作日志功能增强已完成")

        # 显示统计信息
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_logs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE is_rollback = 1")
        rollback_logs = cursor.fetchone()[0]

        print(f"✓ 总日志数: {total_logs}")
        print(f"✓ 回滚日志数: {rollback_logs}")

        return True

    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "up":
            migrate_up()
        elif command == "down":
            migrate_down()
        elif command == "status":
            check_migration_status()
        else:
            print("用法: python 014_enhance_audit_logs_for_rollback.py [up|down|status]")
    else:
        print("用法: python 014_enhance_audit_logs_for_rollback.py [up|down|status]")
        print("默认执行向上迁移...")
        migrate_up()
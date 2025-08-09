#!/usr/bin/env python3
"""
数据库迁移脚本：更新设备信息字段
添加外检相关字段并修改现有字段
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始数据库迁移...")
        
        # 1. 重命名 next_calibration_date 为 valid_until
        print("1. 重命名 next_calibration_date 为 valid_until...")
        cursor.execute("PRAGMA table_info(equipments)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'next_calibration_date' in column_names and 'valid_until' not in column_names:
            # SQLite不支持直接重命名列，需要重新创建表
            cursor.execute("""
                CREATE TABLE equipments_new (
                    id INTEGER PRIMARY KEY,
                    department_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    accuracy_level VARCHAR(50) NOT NULL,
                    measurement_range VARCHAR(100),
                    calibration_cycle VARCHAR(10) NOT NULL,
                    calibration_date DATE NOT NULL,
                    valid_until DATE NOT NULL,
                    calibration_method VARCHAR(50) NOT NULL,
                    serial_number VARCHAR(100) UNIQUE NOT NULL,
                    installation_location VARCHAR(100),
                    manufacturer VARCHAR(100),
                    manufacture_date DATE,
                    scale_value VARCHAR(50),
                    management_level VARCHAR(20),
                    original_value REAL,
                    status VARCHAR(20) DEFAULT '在用',
                    status_change_date DATE,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    FOREIGN KEY (category_id) REFERENCES equipment_categories (id)
                )
            """)
            
            # 复制数据
            cursor.execute("""
                INSERT INTO equipments_new (
                    id, department_id, category_id, name, model, accuracy_level,
                    measurement_range, calibration_cycle, calibration_date,
                    valid_until, calibration_method, serial_number, installation_location,
                    manufacturer, manufacture_date, scale_value, management_level,
                    original_value, status, status_change_date, notes, created_at, updated_at
                )
                SELECT 
                    id, department_id, category_id, name, model, accuracy_level,
                    measurement_range, calibration_cycle, calibration_date,
                    next_calibration_date, 
                    COALESCE(calibration_method, '内检'), 
                    serial_number, installation_location,
                    manufacturer, manufacture_date, scale_value, management_level,
                    original_value, status, 
                    CASE 
                        WHEN status_change_date IS NOT NULL THEN date(status_change_date)
                        ELSE NULL
                    END,
                    notes, created_at, updated_at
                FROM equipments
            """)
            
            # 删除旧表并重命名新表
            cursor.execute("DROP TABLE equipments")
            cursor.execute("ALTER TABLE equipments_new RENAME TO equipments")
            
            print("✓ 表结构更新完成")
        else:
            print("✓ 字段已存在，跳过重命名")
        
        # 2. 添加外检相关字段
        print("2. 添加外检相关字段...")
        new_columns = [
            ('certificate_number', 'VARCHAR(100)'),
            ('verification_result', 'VARCHAR(100)'),
            ('verification_agency', 'VARCHAR(100)'),
            ('certificate_form', 'VARCHAR(50)')
        ]
        
        cursor.execute("PRAGMA table_info(equipments)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE equipments ADD COLUMN {col_name} {col_type}")
                print(f"  ✓ 添加字段 {col_name}")
            else:
                print(f"  ✓ 字段 {col_name} 已存在")
        
        # 3. 更新现有数据：将检定方式为NULL的设为'内检'
        print("3. 更新现有数据...")
        cursor.execute("UPDATE equipments SET calibration_method = '内检' WHERE calibration_method IS NULL")
        print("  ✓ 更新检定方式默认值")
        
        # 4. 更新现有数据：如果检定方式为外检，管理级别设为'-'
        print("4. 更新外检设备管理级别...")
        cursor.execute("UPDATE equipments SET management_level = '-' WHERE calibration_method = '外检'")
        print("  ✓ 更新外检设备管理级别")
        
        # 5. 更新状态变更时间字段类型
        print("5. 更新状态变更时间格式...")
        cursor.execute("""
            UPDATE equipments 
            SET status_change_date = CASE 
                WHEN status_change_date IS NOT NULL THEN date(status_change_date)
                ELSE NULL 
            END
        """)
        print("  ✓ 更新状态变更时间格式")
        
        # 提交事务
        conn.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
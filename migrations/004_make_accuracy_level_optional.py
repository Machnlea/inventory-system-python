#!/usr/bin/env python3
"""
数据库迁移脚本：将准确度等级字段设为非必填
修改 accuracy_level 字段的 NOT NULL 约束
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'inventory.db')
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始数据库迁移：将准确度等级字段设为非必填...")
        
        # 检查当前表结构
        cursor.execute("PRAGMA table_info(equipments)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 查找 accuracy_level 字段的定义
        accuracy_level_def = None
        for col in columns:
            if col[1] == 'accuracy_level':
                accuracy_level_def = col
                break
        
        if accuracy_level_def and accuracy_level_def[3] == 1:  # NOT NULL 约束
            print("发现 accuracy_level 字段有 NOT NULL 约束，开始迁移...")
            
            # SQLite不支持直接修改列约束，需要重新创建表
            cursor.execute("""
                CREATE TABLE equipments_new (
                    id INTEGER PRIMARY KEY,
                    department_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    accuracy_level VARCHAR(50),
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
                    certificate_number VARCHAR(100),
                    verification_result VARCHAR(100),
                    verification_agency VARCHAR(100),
                    certificate_form VARCHAR(50),
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
                    original_value, status, status_change_date, notes,
                    certificate_number, verification_result, verification_agency, 
                    certificate_form, created_at, updated_at
                )
                SELECT 
                    id, department_id, category_id, name, model, accuracy_level,
                    measurement_range, calibration_cycle, calibration_date,
                    valid_until, calibration_method, serial_number, installation_location,
                    manufacturer, manufacture_date, scale_value, management_level,
                    original_value, status, status_change_date, notes,
                    certificate_number, verification_result, verification_agency, 
                    certificate_form, created_at, updated_at
                FROM equipments
            """)
            
            # 删除旧表并重命名新表
            cursor.execute("DROP TABLE equipments")
            cursor.execute("ALTER TABLE equipments_new RENAME TO equipments")
            
            print("✓ accuracy_level 字段已设为非必填")
            
        else:
            print("✓ accuracy_level 字段已经是非必填，跳过迁移")
        
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
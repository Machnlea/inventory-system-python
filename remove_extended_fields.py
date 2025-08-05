#!/usr/bin/env python3
"""
移除扩展字段系统，只保留分度值字段
"""
import sqlite3
import os

def remove_extended_fields():
    """移除扩展字段"""
    db_path = "app.db"
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，无需迁移")
        return
    
    print("开始移除扩展字段...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查extended_fields字段是否存在
        cursor.execute("PRAGMA table_info(equipments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'extended_fields' in columns:
            print("发现extended_fields字段，正在移除...")
            
            # SQLite不支持直接删除列，需要重新创建表
            # 1. 创建新表结构
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
                    next_calibration_date DATE NOT NULL,
                    calibration_method VARCHAR(50),
                    serial_number VARCHAR(100) UNIQUE NOT NULL,
                    installation_location VARCHAR(100),
                    manufacturer VARCHAR(100),
                    manufacture_date DATE,
                    scale_value VARCHAR(50),
                    status VARCHAR(20) DEFAULT '在用',
                    status_change_date DATETIME,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    FOREIGN KEY (category_id) REFERENCES equipment_categories (id)
                )
            """)
            
            # 2. 复制数据（排除extended_fields）
            cursor.execute("""
                INSERT INTO equipments_new (
                    id, department_id, category_id, name, model, accuracy_level,
                    measurement_range, calibration_cycle, calibration_date,
                    next_calibration_date, calibration_method, serial_number,
                    installation_location, manufacturer, manufacture_date,
                    scale_value, status, status_change_date, notes,
                    created_at, updated_at
                )
                SELECT 
                    id, department_id, category_id, name, model, accuracy_level,
                    measurement_range, calibration_cycle, calibration_date,
                    next_calibration_date, calibration_method, serial_number,
                    installation_location, manufacturer, manufacture_date,
                    scale_value, status, status_change_date, notes,
                    created_at, updated_at
                FROM equipments
            """)
            
            # 3. 删除旧表
            cursor.execute("DROP TABLE equipments")
            
            # 4. 重命名新表
            cursor.execute("ALTER TABLE equipments_new RENAME TO equipments")
            
            print("✓ extended_fields字段已成功移除")
        else:
            print("✓ extended_fields字段不存在，无需处理")
        
        # 验证scale_value字段是否存在
        if 'scale_value' not in columns:
            print("添加scale_value字段...")
            cursor.execute("ALTER TABLE equipments ADD COLUMN scale_value VARCHAR(50)")
            print("✓ scale_value字段已添加")
        else:
            print("✓ scale_value字段已存在")
        
        conn.commit()
        conn.close()
        
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    remove_extended_fields()
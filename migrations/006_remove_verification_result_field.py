#!/usr/bin/env python3
"""
数据库迁移脚本: 删除verification_result字段
- 从equipments表中删除verification_result字段
- 从calibration_history表中删除verification_result字段
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """获取数据库路径"""
    # 脚本所在目录的上级目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "inventory.db")
    return db_path

def backup_database(db_path):
    """备份数据库"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    return backup_path

def check_table_structure(cursor, table_name):
    """检查表结构"""
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print(f"\n{table_name}表当前结构:")
    for col in columns:
        print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
    
    return columns

def column_exists(cursor, table_name, column_name):
    """检查字段是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def remove_verification_result_from_equipments(cursor):
    """从equipments表中删除verification_result字段"""
    if not column_exists(cursor, 'equipments', 'verification_result'):
        print("equipments表中不存在verification_result字段，跳过删除")
        return True
    
    print("开始从equipments表删除verification_result字段...")
    
    try:
        # SQLite不支持直接删除列，需要重建表
        
        # 1. 创建临时表（不包含verification_result字段）
        cursor.execute('''
        CREATE TABLE equipments_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            accuracy_level TEXT NOT NULL,
            measurement_range TEXT,
            calibration_cycle TEXT NOT NULL,
            calibration_date DATE,
            valid_until DATE,
            calibration_method TEXT NOT NULL,
            certificate_number TEXT,
            verification_agency TEXT,
            certificate_form TEXT,
            internal_id TEXT UNIQUE NOT NULL,
            manufacturer_id TEXT,
            installation_location TEXT,
            manufacturer TEXT,
            manufacture_date DATE,
            scale_value TEXT,
            management_level TEXT,
            original_value REAL,
            status TEXT DEFAULT '在用',
            status_change_date DATE,
            notes TEXT,
            calibration_notes TEXT,
            disposal_reason TEXT,
            current_calibration_result TEXT DEFAULT '合格',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (category_id) REFERENCES equipment_categories(id)
        )
        ''')
        
        # 2. 复制数据（排除verification_result字段）
        cursor.execute('''
        INSERT INTO equipments_new (
            id, department_id, category_id, name, model, accuracy_level, measurement_range,
            calibration_cycle, calibration_date, valid_until, calibration_method, certificate_number,
            verification_agency, certificate_form, internal_id, manufacturer_id, installation_location,
            manufacturer, manufacture_date, scale_value, management_level, original_value, status,
            status_change_date, notes, calibration_notes, disposal_reason, current_calibration_result,
            created_at, updated_at
        )
        SELECT 
            id, department_id, category_id, name, model, accuracy_level, measurement_range,
            calibration_cycle, calibration_date, valid_until, calibration_method, certificate_number,
            verification_agency, certificate_form, internal_id, manufacturer_id, installation_location,
            manufacturer, manufacture_date, scale_value, management_level, original_value, status,
            status_change_date, notes, calibration_notes, disposal_reason, current_calibration_result,
            created_at, updated_at
        FROM equipments
        ''')
        
        # 3. 删除原表
        cursor.execute('DROP TABLE equipments')
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE equipments_new RENAME TO equipments')
        
        print("✓ 成功从equipments表删除verification_result字段")
        return True
        
    except Exception as e:
        print(f"✗ 删除equipments表verification_result字段失败: {e}")
        return False

def remove_verification_result_from_calibration_history(cursor):
    """从calibration_history表中删除verification_result字段"""
    if not column_exists(cursor, 'calibration_history', 'verification_result'):
        print("calibration_history表中不存在verification_result字段，跳过删除")
        return True
    
    print("开始从calibration_history表删除verification_result字段...")
    
    try:
        # 1. 创建临时表（不包含verification_result字段）
        cursor.execute('''
        CREATE TABLE calibration_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            calibration_date DATE NOT NULL,
            valid_until DATE NOT NULL,
            calibration_method TEXT NOT NULL,
            calibration_result TEXT NOT NULL,
            certificate_number TEXT,
            certificate_form TEXT,
            verification_agency TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (equipment_id) REFERENCES equipments(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
        ''')
        
        # 2. 复制数据（排除verification_result字段）
        cursor.execute('''
        INSERT INTO calibration_history_new (
            id, equipment_id, calibration_date, valid_until, calibration_method, calibration_result,
            certificate_number, certificate_form, verification_agency, notes, created_at, created_by
        )
        SELECT 
            id, equipment_id, calibration_date, valid_until, calibration_method, calibration_result,
            certificate_number, certificate_form, verification_agency, notes, created_at, created_by
        FROM calibration_history
        ''')
        
        # 3. 删除原表
        cursor.execute('DROP TABLE calibration_history')
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE calibration_history_new RENAME TO calibration_history')
        
        print("✓ 成功从calibration_history表删除verification_result字段")
        return True
        
    except Exception as e:
        print(f"✗ 删除calibration_history表verification_result字段失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("数据库迁移：删除verification_result字段")
    print("=" * 60)
    
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 {db_path}")
        sys.exit(1)
    
    print(f"数据库路径: {db_path}")
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查迁移前的表结构
        print("\n" + "=" * 40)
        print("迁移前表结构:")
        print("=" * 40)
        check_table_structure(cursor, 'equipments')
        check_table_structure(cursor, 'calibration_history')
        
        # 执行迁移
        print("\n" + "=" * 40)
        print("开始执行迁移:")
        print("=" * 40)
        
        success = True
        
        # 删除equipments表的verification_result字段
        if not remove_verification_result_from_equipments(cursor):
            success = False
        
        # 删除calibration_history表的verification_result字段
        if not remove_verification_result_from_calibration_history(cursor):
            success = False
        
        if success:
            # 提交事务
            conn.commit()
            print("\n✓ 数据库迁移成功完成")
            
            # 检查迁移后的表结构
            print("\n" + "=" * 40)
            print("迁移后表结构:")
            print("=" * 40)
            check_table_structure(cursor, 'equipments')
            check_table_structure(cursor, 'calibration_history')
            
        else:
            # 回滚事务
            conn.rollback()
            print("\n✗ 数据库迁移失败，已回滚")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ 数据库连接或操作失败: {e}")
        sys.exit(1)
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
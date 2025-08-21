#!/usr/bin/env python3
"""
数据库迁移脚本：添加设备自动编号功能
1. 在部门表中添加代码字段
2. 在类别表中添加代码字段  
3. 在设备表中添加厂内编号字段
4. 将serial_number重命名为manufacturer_id（出厂编号）
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
        print("开始数据库迁移：添加设备自动编号功能...")
        
        # 1. 检查并添加部门代码字段
        cursor.execute("PRAGMA table_info(departments)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'code' not in column_names:
            print("添加部门代码字段...")
            cursor.execute("ALTER TABLE departments ADD COLUMN code VARCHAR(10)")
            
            # 为现有部门生成代码
            departments = cursor.execute("SELECT id, name FROM departments").fetchall()
            for dept_id, dept_name in departments:
                # 生成部门代码：取部门名称前两个字符的大写拼音首字母
                dept_code = generate_department_code(dept_name)
                cursor.execute("UPDATE departments SET code = ? WHERE id = ?", (dept_code, dept_id))
                print(f"  部门 '{dept_name}' 代码: {dept_code}")
        
        # 2. 检查并添加类别代码字段
        cursor.execute("PRAGMA table_info(equipment_categories)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'code' not in column_names:
            print("添加类别代码字段...")
            cursor.execute("ALTER TABLE equipment_categories ADD COLUMN code VARCHAR(10)")
            
            # 为现有类别生成代码
            categories = cursor.execute("SELECT id, name FROM equipment_categories").fetchall()
            for cat_id, cat_name in categories:
                # 生成类别代码：取类别名称关键词的拼音首字母
                cat_code = generate_category_code(cat_name)
                cursor.execute("UPDATE equipment_categories SET code = ? WHERE id = ?", (cat_code, cat_id))
                print(f"  类别 '{cat_name}' 代码: {cat_code}")
        
        # 3. 检查设备表结构
        cursor.execute("PRAGMA table_info(equipments)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 4. 添加厂内编号字段
        if 'internal_id' not in column_names:
            print("添加厂内编号字段...")
            cursor.execute("ALTER TABLE equipments ADD COLUMN internal_id VARCHAR(20)")
        
        # 5. 重命名serial_number为manufacturer_id（出厂编号）
        if 'serial_number' in column_names and 'manufacturer_id' not in column_names:
            print("重命名计量编号为出厂编号...")
            # SQLite不支持直接重命名列，需要创建新表
            create_new_equipment_table(cursor)
        
        # 6. 为现有设备生成厂内编号
        print("为现有设备生成厂内编号...")
        equipments = cursor.execute("""
            SELECT e.id, e.name, d.code as dept_code, c.code as cat_code 
            FROM equipments e
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN equipment_categories c ON e.category_id = c.id
            WHERE e.internal_id IS NULL OR e.internal_id = ''
        """).fetchall()
        
        for eq_id, eq_name, dept_code, cat_code in equipments:
            if dept_code and cat_code:
                # 生成厂内编号
                internal_id = generate_internal_id(cursor, dept_code, cat_code)
                cursor.execute("UPDATE equipments SET internal_id = ? WHERE id = ?", (internal_id, eq_id))
                print(f"  设备 '{eq_name}' 厂内编号: {internal_id}")
        
        # 7. 设置厂内编号为唯一约束
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_equipments_internal_id ON equipments(internal_id)")
        
        conn.commit()
        print("✅ 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 数据库迁移失败: {e}")
        raise
    finally:
        conn.close()

def create_new_equipment_table(cursor):
    """创建新的设备表结构"""
    print("创建新的设备表结构...")
    
    # 创建新表
    cursor.execute("""
        CREATE TABLE equipments_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            model VARCHAR(100) NOT NULL,
            accuracy_level VARCHAR(50),
            measurement_range VARCHAR(100),
            calibration_cycle VARCHAR(10) NOT NULL,
            calibration_date DATE,
            valid_until DATE,
            calibration_method VARCHAR(50) NOT NULL,
            certificate_number VARCHAR(100),
            verification_result VARCHAR(100),
            verification_agency VARCHAR(100),
            certificate_form VARCHAR(50),
            manufacturer_id VARCHAR(100),  -- 原serial_number
            installation_location VARCHAR(100),
            manufacturer VARCHAR(100),
            manufacture_date DATE,
            scale_value VARCHAR(50),
            management_level VARCHAR(20),
            original_value REAL,
            status VARCHAR(20) DEFAULT '在用',
            status_change_date DATE,
            notes TEXT,
            internal_id VARCHAR(20),  -- 厂内编号
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
            valid_until, calibration_method, certificate_number, verification_result, 
            verification_agency, certificate_form, serial_number, installation_location,
            manufacturer, manufacture_date, scale_value, management_level,
            original_value, status, status_change_date, notes, created_at, updated_at
        )
        SELECT 
            id, department_id, category_id, name, model, accuracy_level,
            measurement_range, calibration_cycle, calibration_date,
            valid_until, calibration_method, certificate_number, verification_result, 
            verification_agency, certificate_form, serial_number, installation_location,
            manufacturer, manufacture_date, scale_value, management_level,
            original_value, status, status_change_date, notes, created_at, updated_at
        FROM equipments
    """)
    
    # 删除旧表并重命名新表
    cursor.execute("DROP TABLE equipments")
    cursor.execute("ALTER TABLE equipments_new RENAME TO equipments")

def generate_department_code(dept_name):
    """生成部门代码"""
    # 简单的部门代码生成规则
    code_mapping = {
        '生产': 'SC',
        '质量': 'QL', 
        '技术': 'TC',
        '研发': 'RD',
        '设备': 'EQ',
        '采购': 'PU',
        '销售': 'SL',
        '人事': 'HR',
        '财务': 'FI',
        '行政': 'AD'
    }
    
    # 查找匹配的关键词
    for keyword, code in code_mapping.items():
        if keyword in dept_name:
            return code
    
    # 如果没有匹配，取前两个字符的大写
    return dept_name[:2].upper() if len(dept_name) >= 2 else dept_name.upper()

def generate_category_code(cat_name):
    """生成类别代码"""
    # 简单的类别代码生成规则
    code_mapping = {
        '温度': 'TP',
        '压力': 'PR',
        '流量': 'FL',
        '长度': 'LG',
        '质量': 'MA',
        '时间': 'TM',
        '电学': 'EL',
        '光学': 'OP',
        '声学': 'AC',
        '化学': 'CH',
        '力学': 'MC',
        '热学': 'TH'
    }
    
    # 查找匹配的关键词
    for keyword, code in code_mapping.items():
        if keyword in cat_name:
            return code
    
    # 如果没有匹配，取前两个字符的大写
    return cat_name[:2].upper() if len(cat_name) >= 2 else cat_name.upper()

def generate_internal_id(cursor, dept_code, cat_code):
    """生成厂内编号：DD-CC-NNN"""
    # 查询该部门+类别的最大序号
    cursor.execute("""
        SELECT MAX(CAST(SUBSTR(internal_id, 7, 3) AS INTEGER)) as max_seq
        FROM equipments 
        WHERE internal_id LIKE ? AND internal_id IS NOT NULL
    """, (f"{dept_code}-{cat_code}-%",))
    
    result = cursor.fetchone()
    max_seq = result[0] if result[0] is not None else 0
    
    # 生成新序号（3位数字，前面补零）
    new_seq = max_seq + 1
    seq_str = f"{new_seq:03d}"
    
    return f"{dept_code}-{cat_code}-{seq_str}"

if __name__ == "__main__":
    migrate_database()
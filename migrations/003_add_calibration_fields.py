#!/usr/bin/env python3
"""
数据库迁移脚本：为设备表添加检定历史记录相关字段
添加检定备注、报废原因、当前检定结果字段
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
        print("开始数据库迁移：为设备表添加检定相关字段...")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(equipments)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        # 1. 添加检定备注字段
        print("1. 检查并添加检定备注字段...")
        if 'calibration_notes' not in existing_columns:
            cursor.execute("ALTER TABLE equipments ADD COLUMN calibration_notes TEXT")
            print("  ✓ 添加字段 calibration_notes")
        else:
            print("  ✓ 字段 calibration_notes 已存在")
        
        # 2. 添加报废原因字段
        print("2. 检查并添加报废原因字段...")
        if 'disposal_reason' not in existing_columns:
            cursor.execute("ALTER TABLE equipments ADD COLUMN disposal_reason TEXT")
            print("  ✓ 添加字段 disposal_reason")
        else:
            print("  ✓ 字段 disposal_reason 已存在")
        
        # 3. 添加当前检定结果字段
        print("3. 检查并添加当前检定结果字段...")
        if 'current_calibration_result' not in existing_columns:
            cursor.execute("ALTER TABLE equipments ADD COLUMN current_calibration_result VARCHAR(20) DEFAULT '合格'")
            print("  ✓ 添加字段 current_calibration_result")
            
            # 为现有数据设置默认值
            cursor.execute("UPDATE equipments SET current_calibration_result = '合格' WHERE current_calibration_result IS NULL")
            print("  ✓ 为现有数据设置默认检定结果为'合格'")
        else:
            print("  ✓ 字段 current_calibration_result 已存在")
        
        # 4. 扩展附件表字段
        print("4. 检查并扩展附件表字段...")
        cursor.execute("PRAGMA table_info(equipment_attachments)")
        attachment_columns = cursor.fetchall()
        attachment_existing_columns = [col[1] for col in attachment_columns]
        
        # 添加检定历史记录ID字段
        if 'calibration_history_id' not in attachment_existing_columns:
            cursor.execute("ALTER TABLE equipment_attachments ADD COLUMN calibration_history_id INTEGER")
            print("  ✓ 添加字段 calibration_history_id 到附件表")
        else:
            print("  ✓ 字段 calibration_history_id 已存在于附件表")
        
        # 添加附件类别字段
        if 'attachment_category' not in attachment_existing_columns:
            cursor.execute("ALTER TABLE equipment_attachments ADD COLUMN attachment_category VARCHAR(50) DEFAULT 'equipment'")
            print("  ✓ 添加字段 attachment_category 到附件表")
            
            # 为现有附件设置默认类别
            cursor.execute("UPDATE equipment_attachments SET attachment_category = 'equipment' WHERE attachment_category IS NULL")
            print("  ✓ 为现有附件设置默认类别为'equipment'")
        else:
            print("  ✓ 字段 attachment_category 已存在于附件表")
        
        # 提交事务
        conn.commit()
        print("数据库字段扩展迁移完成！")
        
        # 显示迁移后的表结构
        print("\n=== 迁移后设备表结构 ===")
        cursor.execute("PRAGMA table_info(equipments)")
        equipment_columns = cursor.fetchall()
        for col in equipment_columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        print("\n=== 迁移后附件表结构 ===")
        cursor.execute("PRAGMA table_info(equipment_attachments)")
        attachment_columns = cursor.fetchall()
        for col in attachment_columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
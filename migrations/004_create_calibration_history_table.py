#!/usr/bin/env python3
"""
数据库迁移脚本：创建检定历史记录表
支持设备检定历史的完整追踪
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
        print("开始数据库迁移：创建检定历史记录表...")
        
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calibration_history'")
        if cursor.fetchone():
            print("检定历史记录表已存在，跳过创建")
            return
        
        # 创建检定历史记录表
        print("1. 创建检定历史记录表...")
        cursor.execute("""
            CREATE TABLE calibration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                calibration_date DATE NOT NULL,
                valid_until DATE NOT NULL,
                calibration_method VARCHAR(20) NOT NULL,
                calibration_result VARCHAR(20) NOT NULL,
                certificate_number VARCHAR(100),
                certificate_form VARCHAR(50),
                verification_result VARCHAR(100),
                verification_agency VARCHAR(100),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                
                FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        print("  ✓ 检定历史记录表创建完成")
        
        # 创建索引
        print("2. 创建检定历史记录表索引...")
        
        # 按设备查询优化
        cursor.execute("CREATE INDEX idx_calibration_history_equipment_id ON calibration_history(equipment_id)")
        print("  ✓ 创建设备ID索引")
        
        # 按创建时间查询优化
        cursor.execute("CREATE INDEX idx_calibration_history_created_at ON calibration_history(created_at)")
        print("  ✓ 创建创建时间索引")
        
        # 按检定日期查询优化
        cursor.execute("CREATE INDEX idx_calibration_history_calibration_date ON calibration_history(calibration_date)")
        print("  ✓ 创建检定日期索引")
        
        # 复合索引：按设备和检定日期查询优化
        cursor.execute("CREATE INDEX idx_calibration_history_equipment_date ON calibration_history(equipment_id, calibration_date DESC)")
        print("  ✓ 创建设备-检定日期复合索引")
        
        # 3. 扩展附件表的外键约束（如果需要）
        print("3. 检查附件表外键约束...")
        
        # 由于SQLite的限制，我们不能直接添加外键约束到现有表
        # 但可以创建一个触发器来维护数据完整性
        cursor.execute("""
            CREATE TRIGGER fk_calibration_history_attachment
            BEFORE INSERT ON equipment_attachments
            FOR EACH ROW
            WHEN NEW.calibration_history_id IS NOT NULL
            BEGIN
                SELECT CASE
                    WHEN (SELECT id FROM calibration_history WHERE id = NEW.calibration_history_id) IS NULL
                    THEN RAISE(ABORT, 'Foreign key violation: calibration_history_id does not exist')
                END;
            END
        """)
        print("  ✓ 创建附件表外键检查触发器")
        
        # 4. 为现有设备创建初始检定历史记录
        print("4. 为现有设备创建初始检定历史记录...")
        
        cursor.execute("""
            INSERT INTO calibration_history (
                equipment_id, calibration_date, valid_until, 
                calibration_method, calibration_result,
                certificate_number, certificate_form, 
                verification_result, verification_agency,
                notes, created_at, created_by
            )
            SELECT 
                id, 
                COALESCE(calibration_date, date('now', '-1 year')),
                COALESCE(valid_until, date('now')),
                COALESCE(calibration_method, '内检'),
                COALESCE(current_calibration_result, '合格'),
                certificate_number, 
                certificate_form,
                verification_result, 
                verification_agency,
                CASE 
                    WHEN notes IS NOT NULL AND calibration_notes IS NOT NULL 
                    THEN notes || ' | ' || calibration_notes
                    WHEN notes IS NOT NULL 
                    THEN notes
                    WHEN calibration_notes IS NOT NULL 
                    THEN calibration_notes
                    ELSE NULL
                END,
                created_at, 
                1  -- 默认创建者为管理员
            FROM equipments 
            WHERE calibration_date IS NOT NULL OR valid_until IS NOT NULL
        """)
        
        rows_inserted = cursor.rowcount
        print(f"  ✓ 为 {rows_inserted} 个设备创建了初始检定历史记录")
        
        # 提交事务
        conn.commit()
        print("检定历史记录表创建和数据迁移完成！")
        
        # 显示表结构
        print("\n=== 检定历史记录表结构 ===")
        cursor.execute("PRAGMA table_info(calibration_history)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        # 显示索引信息
        print("\n=== 检定历史记录表索引 ===")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='calibration_history' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  {idx[0]}")
        
        # 显示记录统计
        cursor.execute("SELECT COUNT(*) FROM calibration_history")
        count = cursor.fetchone()[0]
        print(f"\n=== 数据统计 ===")
        print(f"  检定历史记录总数: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT calibration_method, COUNT(*) 
                FROM calibration_history 
                GROUP BY calibration_method
            """)
            method_stats = cursor.fetchall()
            print("  按检定方式分布:")
            for method, count in method_stats:
                print(f"    {method}: {count}")
                
            cursor.execute("""
                SELECT calibration_result, COUNT(*) 
                FROM calibration_history 
                GROUP BY calibration_result
            """)
            result_stats = cursor.fetchall()
            print("  按检定结果分布:")
            for result, count in result_stats:
                print(f"    {result}: {count}")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
#!/usr/bin/env python3
"""
调试脚本：检查附件表和数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import SQLALCHEMY_DATABASE_URL

# 创建数据库连接
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 检查表是否存在（SQLite）
    print("检查数据库表:")
    tables_result = db.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '%attachment%'
    """))
    
    tables = tables_result.fetchall()
    print(f"找到的附件相关表: {[table[0] for table in tables]}")
    
    if tables:
        # 检查表结构
        for table in tables:
            table_name = table[0]
            print(f"\n表 {table_name} 的结构:")
            columns_result = db.execute(text(f"PRAGMA table_info({table_name})"))
            
            for column in columns_result:
                print(f"  {column[1]}: {column[2]} (nullable: {not column[3]}, primary_key: {column[5]})")
            
            # 检查表中的数据
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.fetchone()[0]
            print(f"  记录数: {count}")
            
            if count > 0:
                print(f"  前5条记录:")
                records_result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                for record in records_result:
                    print(f"    {record}")
    
    # 检查equipments表中的数据
    print(f"\nequipments表记录数:")
    equip_count_result = db.execute(text("SELECT COUNT(*) FROM equipments"))
    equip_count = equip_count_result.fetchone()[0]
    print(f"  设备总数: {equip_count}")
    
    if equip_count > 0:
        print(f"  前5台设备:")
        equip_result = db.execute(text("SELECT id, name, department_id FROM equipments LIMIT 5"))
        for equip in equip_result:
            print(f"    ID: {equip[0]}, 名称: {equip[1]}, 部门ID: {equip[2]}")
    
    # 检查所有表
    print(f"\n所有数据库表:")
    all_tables_result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    all_tables = all_tables_result.fetchall()
    print(f"所有表: {[table[0] for table in all_tables]}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
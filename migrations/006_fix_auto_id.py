"""
简化的数据库迁移脚本：添加自动编号功能
"""

import sqlite3
import os

def migrate_database():
    """执行数据库迁移"""
    db_path = "./inventory.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始数据库迁移：添加设备自动编号功能...")
        
        # 检查是否已经添加了code字段
        cursor.execute("PRAGMA table_info(departments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'code' not in columns:
            print("添加部门代码字段...")
            cursor.execute("ALTER TABLE departments ADD COLUMN code VARCHAR(10)")
        
        # 更新现有部门的代码（无论字段是否存在都更新）
        department_codes = {
            "制听车间": "ZT",
            "安环部": "AH", 
            "工业漆车间": "GY",
            "技术中心": "TC",
            "服务中心": "FW",
            "机修车间": "JX",
            "树脂车间": "SZ",
            "水性漆车间": "SX",
            "汽摩漆车间": "QM",
            "物管部": "WG",
            "电控部": "DK",
            "质管部": "ZG",
            "通用漆车间": "TY",
            "防腐漆车间": "FF"
        }
        
        print("更新部门代码...")
        for name, code in department_codes.items():
            cursor.execute("UPDATE departments SET code = ? WHERE name = ?", (code, name))
            print(f"  部门 '{name}' 代码: {code}")
        
        # 检查类别表
        cursor.execute("PRAGMA table_info(equipment_categories)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'code' not in columns:
            print("添加类别代码字段...")
            cursor.execute("ALTER TABLE equipment_categories ADD COLUMN code VARCHAR(10)")
            
            # 更新现有类别的代码
            category_codes = {
                "压力表": "YL",
                "外委": "WW",
                "流量计": "LL",
                "液位计": "YW",
                "玻璃温度计": "WD",
                "玻璃量器": "BL",
                "理化": "LH",
                "电子天平": "TP",
                "铂热电阻": "PR"
            }
            
            for name, code in category_codes.items():
                cursor.execute("UPDATE equipment_categories SET code = ? WHERE name = ?", (code, name))
                print(f"  类别 '{name}' 代码: {code}")
        
        # 检查设备表
        cursor.execute("PRAGMA table_info(equipments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'internal_id' not in columns:
            print("添加内部编号字段...")
            cursor.execute("ALTER TABLE equipments ADD COLUMN internal_id VARCHAR(20)")
        
        if 'manufacturer_id' not in columns:
            print("添加厂家编号字段...")
            cursor.execute("ALTER TABLE equipments ADD COLUMN manufacturer_id VARCHAR(100)")
            
            # 将原有的serial_number数据迁移到manufacturer_id
            cursor.execute("UPDATE equipments SET manufacturer_id = serial_number WHERE serial_number IS NOT NULL")
        
        # 设置唯一约束
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_departments_code ON departments(code)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_equipment_categories_code ON equipment_categories(code)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_equipments_internal_id ON equipments(internal_id)")
        
        conn.commit()
        print("✅ 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
#!/usr/bin/env python3
"""
数据迁移脚本：为现有设备创建初始检定历史记录
处理现有设备数据的兼容性问题
"""

import sqlite3
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def calculate_valid_until(calibration_date: date, calibration_cycle: str) -> date:
    """
    根据检定日期和检定周期计算有效期
    与后端API保持一致的计算逻辑
    """
    if calibration_cycle == "随坏随换":
        return date(2099, 12, 31)
    
    try:
        # Extract months from cycle string
        months = 12  # default
        if calibration_cycle == "6个月":
            months = 6
        elif calibration_cycle == "12个月":
            months = 12
        elif calibration_cycle == "24个月":
            months = 24
        elif calibration_cycle == "36个月":
            months = 36
        
        # Calculate: add months then subtract 1 day
        dt = datetime(calibration_date.year, calibration_date.month, calibration_date.day)
        
        # Add months with proper year/month handling
        if dt.month + months <= 12:
            dt = dt.replace(month=dt.month + months)
        else:
            new_year = dt.year + (dt.month + months - 1) // 12
            new_month = (dt.month + months - 1) % 12 + 1
            dt = dt.replace(year=new_year, month=new_month)
        
        # Subtract 1 day because expiry date is not valid
        valid_until = dt.date() - timedelta(days=1)
        return valid_until
        
    except Exception:
        return calibration_date + timedelta(days=365) - timedelta(days=1)


def migrate_existing_equipment_data():
    """
    为现有设备创建初始检定历史记录
    """
    
    db_path = 'data/inventory.db'
    if not os.path.exists(db_path):
        print("错误：数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始数据迁移...")
        
        # 1. 查找所有已有检定日期但没有检定历史记录的设备
        cursor.execute("""
            SELECT e.id, e.name, e.calibration_date, e.valid_until, e.calibration_method, 
                   e.current_calibration_result, e.certificate_number, e.certificate_form,
                   e.verification_result, e.verification_agency, e.calibration_notes,
                   e.calibration_cycle
            FROM equipments e 
            LEFT JOIN calibration_history ch ON e.id = ch.equipment_id 
            WHERE e.calibration_date IS NOT NULL 
            AND ch.id IS NULL
        """)
        
        equipment_records = cursor.fetchall()
        total_count = len(equipment_records)
        
        if total_count == 0:
            print("所有设备的检定历史记录都已存在，无需迁移。")
            conn.close()
            return True
        
        print(f"找到 {total_count} 台设备需要创建初始检定历史记录")
        
        # 2. 为每台设备创建初始检定历史记录
        migrated_count = 0
        updated_count = 0
        
        for record in equipment_records:
            equipment_id = record[0]
            equipment_name = record[1]
            calibration_date = record[2]
            valid_until_current = record[3]
            calibration_method = record[4]
            calibration_result = record[5] or '合格'  # 默认为合格
            certificate_number = record[6]
            certificate_form = record[7]
            verification_result = record[8]
            verification_agency = record[9]
            calibration_notes = record[10]
            calibration_cycle = record[11]
            
            # 转换日期格式
            if isinstance(calibration_date, str):
                cal_date = datetime.strptime(calibration_date, '%Y-%m-%d').date()
            else:
                cal_date = calibration_date
            
            # 重新计算有效期以确保一致性
            calculated_valid_until = calculate_valid_until(cal_date, calibration_cycle)
            
            try:
                # 创建检定历史记录
                cursor.execute("""
                    INSERT INTO calibration_history 
                    (equipment_id, calibration_date, valid_until, calibration_method, 
                     calibration_result, certificate_number, certificate_form, 
                     verification_result, verification_agency, notes, 
                     performed_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    equipment_id,
                    cal_date.isoformat(),
                    calculated_valid_until.isoformat(),
                    calibration_method,
                    calibration_result,
                    certificate_number,
                    certificate_form,
                    verification_result,
                    verification_agency,
                    calibration_notes,
                    1,  # 系统用户ID
                    datetime.now().isoformat()
                ))
                
                migrated_count += 1
                
                # 如果计算的有效期与当前存储的不一致，更新设备记录
                if valid_until_current != calculated_valid_until.isoformat():
                    cursor.execute("""
                        UPDATE equipments 
                        SET valid_until = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        calculated_valid_until.isoformat(),
                        datetime.now().isoformat(),
                        equipment_id
                    ))
                    updated_count += 1
                    print(f"  设备 {equipment_name} (ID: {equipment_id}): 创建历史记录 + 更新有效期")
                else:
                    print(f"  设备 {equipment_name} (ID: {equipment_id}): 创建历史记录")
                
            except Exception as e:
                print(f"  错误：为设备 {equipment_name} (ID: {equipment_id}) 创建记录失败: {str(e)}")
                continue
        
        # 3. 处理没有检定日期的设备，设置默认值
        cursor.execute("""
            SELECT id, name, calibration_cycle 
            FROM equipments 
            WHERE calibration_date IS NULL
        """)
        
        no_date_records = cursor.fetchall()
        default_date_count = 0
        
        if no_date_records:
            print(f"\n找到 {len(no_date_records)} 台设备没有检定日期，将设置默认值:")
            
            # 使用当前日期作为默认检定日期
            default_calibration_date = date.today()
            
            for record in no_date_records:
                equipment_id = record[0]
                equipment_name = record[1]
                calibration_cycle = record[2]
                
                # 计算有效期
                calculated_valid_until = calculate_valid_until(default_calibration_date, calibration_cycle)
                
                try:
                    # 更新设备的检定信息
                    cursor.execute("""
                        UPDATE equipments 
                        SET calibration_date = ?, 
                            valid_until = ?, 
                            current_calibration_result = '合格',
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        default_calibration_date.isoformat(),
                        calculated_valid_until.isoformat(),
                        datetime.now().isoformat(),
                        equipment_id
                    ))
                    
                    # 创建检定历史记录
                    cursor.execute("""
                        INSERT INTO calibration_history 
                        (equipment_id, calibration_date, valid_until, calibration_method, 
                         calibration_result, notes, performed_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        equipment_id,
                        default_calibration_date.isoformat(),
                        calculated_valid_until.isoformat(),
                        '内检',  # 默认为内检
                        '合格',
                        '系统初始化默认记录',
                        1,  # 系统用户ID
                        datetime.now().isoformat()
                    ))
                    
                    default_date_count += 1
                    print(f"  设备 {equipment_name} (ID: {equipment_id}): 设置默认检定信息")
                    
                except Exception as e:
                    print(f"  错误：为设备 {equipment_name} (ID: {equipment_id}) 设置默认值失败: {str(e)}")
                    continue
        
        # 提交事务
        conn.commit()
        conn.close()
        
        print(f"\n数据迁移完成!")
        print(f"  创建检定历史记录: {migrated_count} 条")
        print(f"  更新设备有效期: {updated_count} 条")
        print(f"  设置默认检定信息: {default_date_count} 条")
        print(f"  总计处理设备: {migrated_count + default_date_count} 台")
        
        return True
        
    except Exception as e:
        print(f"数据迁移失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("设备数据兼容性处理脚本")
    print("=" * 60)
    
    # 执行数据迁移
    success = migrate_existing_equipment_data()
    
    if success:
        print("\n✅ 数据迁移成功完成!")
    else:
        print("\n❌ 数据迁移失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
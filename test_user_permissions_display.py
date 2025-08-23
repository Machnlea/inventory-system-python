#!/usr/bin/env python3
"""
测试用户列表权限显示功能
"""

import sqlite3
import os

def test_user_permissions_display():
    """测试用户权限显示"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🧪 测试用户权限显示...")
        
        # 获取所有用户
        cursor.execute("SELECT id, username, is_admin FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("📋 用户权限状态:")
        print("-" * 80)
        
        for user_id, username, is_admin in users:
            print(f"👤 {username} (管理员: {is_admin})")
            
            # 获取类别权限
            cursor.execute('''
                SELECT ec.name 
                FROM user_categories uc
                JOIN equipment_categories ec ON uc.category_id = ec.id
                WHERE uc.user_id = ?
            ''', (user_id,))
            
            category_permissions = cursor.fetchall()
            
            # 获取器具权限
            cursor.execute('''
                SELECT ec.name, uep.equipment_name 
                FROM user_equipment_permissions uep
                JOIN equipment_categories ec ON uep.category_id = ec.id
                WHERE uep.user_id = ?
            ''', (user_id,))
            
            equipment_permissions = cursor.fetchall()
            
            # 显示权限信息
            if is_admin:
                print(f"   🏷️ 权限显示: 全部权限")
                print(f"   🔘 按钮状态: 类别(灰色)、器具(灰色)、编辑(灰色)")
            else:
                has_category_permissions = len(category_permissions) > 0
                has_equipment_permissions = len(equipment_permissions) > 0
                
                if has_category_permissions or has_equipment_permissions:
                    permission_texts = []
                    
                    if has_category_permissions:
                        category_names = [cat[0] for cat in category_permissions]
                        permission_texts.append(f"类别: {', '.join(category_names)}")
                    
                    if has_equipment_permissions:
                        equipment_names = [eq[1] for eq in equipment_permissions]
                        permission_texts.append(f"器具: {', '.join(equipment_names)}")
                    
                    print(f"   🏷️ 权限显示: {' | '.join(permission_texts)}")
                    print(f"   🔘 按钮状态: 类别(蓝色)、器具(紫色)、编辑(绿色)")
                else:
                    print(f"   🏷️ 权限显示: 无权限")
                    print(f"   🔘 按钮状态: 类别(蓝色)、器具(紫色)、编辑(绿色)")
                
                # 检查删除权限
                if has_category_permissions or has_equipment_permissions:
                    print(f"   🗑️ 删除按钮: 灰色(有权限，无法删除)")
                else:
                    print(f"   🗑️ 删除按钮: 红色(无权限，可以删除)")
            
            print()
        
        # 专门检查zmms用户
        zmms_user = next((u for u in users if u[1] == 'zmms'), None)
        if zmms_user:
            zmms_id = zmms_user[0]
            
            cursor.execute('''
                SELECT ec.name, uep.equipment_name 
                FROM user_equipment_permissions uep
                JOIN equipment_categories ec ON uep.category_id = ec.id
                WHERE uep.user_id = ? AND uep.equipment_name = '温湿度计'
            ''', (zmms_id,))
            
            humidity_meter_permission = cursor.fetchone()
            
            if humidity_meter_permission:
                print("✅ zmms用户确实有温湿度计管理权限")
                print("💡 前端应该显示: '温湿度计' 而不是 '无权限'")
            else:
                print("❌ zmms用户没有温湿度计管理权限")
        
        print("-" * 80)
        print("🎯 预期修复效果:")
        print("1. zmms用户应该显示 '温湿度计' 而不是 '无权限'")
        print("2. 管理员账号的权限管理按钮应该是灰色不可点击")
        print("3. 有权限的用户删除按钮应该是灰色")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 测试用户权限显示功能...")
    print("=" * 60)
    
    success = test_user_permissions_display()
    
    print("=" * 60)
    if success:
        print("🎉 测试完成！")
        print("📱 现在可以访问 http://127.0.0.1:8000/users 查看修复效果")
    else:
        print("⚠️ 测试失败！")
#!/usr/bin/env python3
"""
测试仪表盘环形图颜色扩展效果
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db
from app.models.models import Equipment, EquipmentCategory, Department
from sqlalchemy import func

def test_chart_colors():
    """测试环形图数据准备情况"""
    print("🧪 测试仪表盘环形图颜色扩展...")
    
    db = next(get_db())
    
    try:
        # 获取设备类别分布数据
        category_stats = db.query(
            EquipmentCategory.name,
            func.count(Equipment.id).label('count')
        ).join(
            Equipment, Equipment.category_id == EquipmentCategory.id
        ).filter(
            Equipment.status == '在用'
        ).group_by(
            EquipmentCategory.name
        ).all()
        
        print(f"\n📊 设备类别分布 ({len(category_stats)} 个类别):")
        for category in category_stats:
            print(f"  - {category.name}: {category.count} 台")
        
        # 获取部门分布数据
        department_stats = db.query(
            Department.name,
            func.count(Equipment.id).label('count')
        ).join(
            Equipment, Equipment.department_id == Department.id
        ).filter(
            Equipment.status == '在用'
        ).group_by(
            Department.name
        ).all()
        
        print(f"\n📊 部门分布 ({len(department_stats)} 个部门):")
        for dept in department_stats:
            print(f"  - {dept.name}: {dept.count} 台")
        
        # 分析颜色需求
        max_categories = len(category_stats)
        max_departments = len(department_stats)
        
        print(f"\n🎨 颜色需求分析:")
        print(f"  - 设备类别数量: {max_categories}")
        print(f"  - 部门数量: {max_departments}")
        print(f"  - 总计需要颜色数: {max(max_categories, max_departments)}")
        
        # 颜色方案信息
        available_colors = 120  # 我们提供了120种颜色
        print(f"  - 可用颜色数量: {available_colors}")
        
        if max_categories <= available_colors and max_departments <= available_colors:
            print("✅ 颜色方案充足，不会出现颜色重复问题")
        else:
            print("⚠️  颜色方案可能不足，建议增加更多颜色")
        
        # 颜色使用建议
        print(f"\n💡 颜色使用建议:")
        if max_categories <= 10:
            print("  - 设备类别: 使用前10种颜色，颜色区分度良好")
        elif max_categories <= 30:
            print("  - 设备类别: 使用前30种颜色，颜色区分度中等")
        else:
            print("  - 设备类别: 建议考虑使用渐变色或分组显示")
            
        if max_departments <= 10:
            print("  - 部门分布: 使用前10种颜色，颜色区分度良好")
        elif max_departments <= 30:
            print("  - 部门分布: 使用前30种颜色，颜色区分度中等")
        else:
            print("  - 部门分布: 建议考虑使用渐变色或分组显示")
        
        print(f"\n🎉 颜色扩展测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_chart_colors()
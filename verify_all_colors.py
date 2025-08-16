#!/usr/bin/env python3
"""
验证所有页面饼图颜色扩展方案
"""

def count_colors_in_template(file_path, page_name):
    """统计模板文件中的颜色数量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找backgroundColor数组和colors数组定义
        import re
        
        # 方法1：直接查找backgroundColor数组
        pattern1 = r'backgroundColor:\s*\[(.*?)\]'
        matches1 = re.findall(pattern1, content, re.DOTALL)
        
        # 方法2：查找colors数组定义
        pattern2 = r'const\s+colors\s*=\s*\[(.*?)\];'
        matches2 = re.findall(pattern2, content, re.DOTALL)
        
        total_colors = 0
        all_colors = []
        
        # 处理直接backgroundColor数组
        for i, match in enumerate(matches1):
            color_pattern = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
            colors = re.findall(color_pattern, match)
            total_colors += len(colors)
            all_colors.extend(colors)
            print(f"  图表 {i+1} (直接): {len(colors)} 种颜色")
        
        # 处理colors数组定义
        for i, match in enumerate(matches2):
            color_pattern = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
            colors = re.findall(color_pattern, match)
            total_colors += len(colors)
            all_colors.extend(colors)
            print(f"  颜色数组 {i+1}: {len(colors)} 种颜色")
        
        print(f"  📊 {page_name} 颜色统计:")
        print(f"    - 总颜色数量: {total_colors}")
        print(f"    - 图表/数组数量: {len(matches1) + len(matches2)}")
        
        # 分析颜色多样性
        unique_colors = set(all_colors)
        print(f"    - 去重后颜色数: {len(unique_colors)}")
        
        # 评估结果
        if total_colors >= 120:
            print("    ✅ 颜色方案充足，支持大量数据分类")
        elif total_colors >= 60:
            print("    ✅ 颜色方案适中，适合一般数据分类")
        else:
            print("    ⚠️  颜色方案较少，建议增加更多颜色")
            
        return total_colors, len(unique_colors)
        
    except FileNotFoundError:
        print(f"❌ {page_name} 模板文件未找到")
        return 0, 0
    except Exception as e:
        print(f"❌ {page_name} 验证失败: {e}")
        return 0, 0

def main():
    """验证所有页面的颜色扩展"""
    print("🧪 验证所有页面饼图颜色扩展方案...")
    print("=" * 50)
    
    # 验证仪表盘
    print("\n📈 仪表盘页面:")
    dashboard_total, dashboard_unique = count_colors_in_template(
        '/home/ming/my_project/inventory-system-python/app/templates/dashboard.html',
        '仪表盘'
    )
    
    # 验证设备类别页面
    print("\n🏷️  设备类别页面:")
    categories_total, categories_unique = count_colors_in_template(
        '/home/ming/my_project/inventory-system-python/app/templates/categories.html',
        '设备类别'
    )
    
    # 验证部门管理页面
    print("\n🏢 部门管理页面:")
    departments_total, departments_unique = count_colors_in_template(
        '/home/ming/my_project/inventory-system-python/app/templates/departments.html',
        '部门管理'
    )
    
    # 汇总统计
    print("\n" + "=" * 50)
    print("📊 汇总统计:")
    print(f"  - 仪表盘总颜色: {dashboard_total}")
    print(f"  - 设备类别总颜色: {categories_total}")
    print(f"  - 部门管理总颜色: {departments_total}")
    print(f"  - 三个页面总计: {dashboard_total + categories_total + departments_total}")
    
    # 验证结果
    print("\n🎉 验证结果:")
    all_sufficient = all([
        dashboard_total >= 120,
        categories_total >= 120,
        departments_total >= 120
    ])
    
    if all_sufficient:
        print("  ✅ 所有页面颜色方案充足，完全避免颜色重复问题")
    else:
        insufficient = []
        if dashboard_total < 120:
            insufficient.append("仪表盘")
        if categories_total < 120:
            insufficient.append("设备类别")
        if departments_total < 120:
            insufficient.append("部门管理")
        print(f"  ⚠️  以下页面颜色方案不足: {', '.join(insufficient)}")
    
    print(f"\n🎉 验证完成！")

if __name__ == "__main__":
    main()
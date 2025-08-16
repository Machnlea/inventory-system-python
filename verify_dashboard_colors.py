#!/usr/bin/env python3
"""
验证仪表盘环形图颜色扩展方案
"""

def count_colors_in_dashboard():
    """统计仪表盘模板中的颜色数量"""
    try:
        with open('/home/ming/my_project/inventory-system-python/app/templates/dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找backgroundColor数组
        import re
        pattern = r'backgroundColor:\s*\[(.*?)\]'
        matches = re.findall(pattern, content, re.DOTALL)
        
        total_colors = 0
        for i, match in enumerate(matches):
            # 提取颜色代码
            color_pattern = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
            colors = re.findall(color_pattern, match)
            total_colors += len(colors)
            print(f"图表 {i+1}: {len(colors)} 种颜色")
        
        print(f"\n📊 颜色统计结果:")
        print(f"  - 总颜色数量: {total_colors}")
        print(f"  - 图表数量: {len(matches)}")
        print(f"  - 平均每图颜色数: {total_colors // len(matches) if matches else 0}")
        
        # 分析颜色多样性
        unique_colors = set()
        for match in matches:
            color_pattern = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
            colors = re.findall(color_pattern, match)
            unique_colors.update(colors)
        
        print(f"  - 去重后颜色数: {len(unique_colors)}")
        
        # 评估结果
        if total_colors >= 120:
            print("✅ 颜色方案充足，支持大量数据分类")
        elif total_colors >= 60:
            print("✅ 颜色方案适中，适合一般数据分类")
        else:
            print("⚠️  颜色方案较少，建议增加更多颜色")
            
        return total_colors, len(unique_colors)
        
    except FileNotFoundError:
        print("❌ 仪表盘模板文件未找到")
        return 0, 0
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🧪 验证仪表盘环形图颜色扩展方案...")
    total_colors, unique_colors = count_colors_in_dashboard()
    print(f"\n🎉 验证完成！")
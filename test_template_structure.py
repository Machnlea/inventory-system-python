#!/usr/bin/env python3
"""
测试导入模板数据结构
"""
import pandas as pd

def test_template_structure():
    """测试模板数据结构"""
    print("正在检查导入模板数据结构...")
    
    # 模板数据（从import_export.py复制）
    template_data = {
        '使用部门': ['树脂车间', '工业漆车间', '质检部', '树脂车间', '仓库'],
        '设备类别': ['铂热电阻', '玻璃量器', '压力表', '热电偶', '扳手'],
        '计量器具名称': ['铂热电阻温度计', '玻璃量筒', '压力表', '热电偶温度计', '扭矩扳手'],
        '型号/规格': ['PT100', '500ml A级', 'Y-100', 'K型', 'DN-100'],
        '准确度等级': ['A级', 'A级', '1.6级', 'B级', '2级'],
        '测量范围': ['-200~850℃', '0~500ml', '0~1.6MPa', '0~1300℃', '10-100N·m'],
        '计量编号': ['PT001', 'GL001', 'YL001', 'TC001', 'BS001'],
        '检定周期': ['6个月', '12个月', '24个月', '36个月', '随坏随换'],
        '检定(校准)日期': ['2024-01-15', '2024-03-20', '2024-06-01', '2024-09-01', ''],
        '安装地点': ['1号反应釜', '质检室', '实验室', '2号反应釜', '工具间'],
        '分度值': ['0.1℃', '1ml', '0.01MPa', '1℃', '1N·m'],
        '制造厂家': ['上海仪表厂', '北京玻璃厂', '深圳仪表厂', '上海仪表厂', '日本工具'],
        '出厂日期': ['2023-12-01', '2023-11-15', '2023-10-20', '2024-08-01', '2023-05-01'],
        '检定方式': ['内检', '外检', '内检', '外检', '内检'],
        '管理级别': ['A级', '-', 'C级', '-', 'C级'],
        '原值/元': [1500.00, 800.00, 1200.00, 2000.00, 500.00],
        '设备状态': ['在用', '在用', '在用', '在用', '在用'],
        '状态变更时间': ['', '', '', '', ''],
        '证书编号': ['', 'CERT001', '', 'CERT002', ''],
        '检定结果': ['', '合格', '', '合格', ''],
        '检定机构': ['', '国家计量院', '', '省计量院', ''],
        '证书形式': ['', '校准证书', '', '检定证书', ''],
        '备注': ['正常使用', '新购设备', '半年检定周期示例', '三年检定周期', '随坏随换设备无需定期检定']
    }
    
    df = pd.DataFrame(template_data)
    
    print("=" * 80)
    print("导入模板列顺序检查:")
    print("=" * 80)
    
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
        
    print("=" * 80)
    print("\n检查状态变更时间字段位置...")
    
    columns = list(df.columns)
    status_index = columns.index('设备状态') if '设备状态' in columns else -1
    status_change_index = columns.index('状态变更时间') if '状态变更时间' in columns else -1
    
    print(f"设备状态字段位置: {status_index + 1}")
    print(f"状态变更时间字段位置: {status_change_index + 1}")
    
    if status_change_index == status_index + 1:
        print("✅ 状态变更时间字段正确位于设备状态字段后面")
    else:
        print("❌ 状态变更时间字段位置不正确")
        
    print("=" * 80)
    print("\n模板数据预览（设备状态相关字段）:")
    print("=" * 80)
    print(df[['设备状态', '状态变更时间']].to_string())
    
    # 保存测试文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='设备台账模板', index=False)
    
    with open('test_import_template.xlsx', 'wb') as f:
        f.write(output.getvalue())
        
    print(f"\n✅ 测试文件已保存为: test_import_template.xlsx")
    print("请打开此Excel文件查看实际的列顺序")

if __name__ == "__main__":
    test_template_structure()
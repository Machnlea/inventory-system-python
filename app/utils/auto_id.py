"""
自动编号功能模块
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import re
from app.models.models import Equipment, Department, EquipmentCategory
from app.utils.equipment_mapping import get_equipment_type_code, get_equipment_sequence_number

def generate_department_code(department_name: str) -> str:
    """
    根据部门名称生成部门代码
    """
    code_mapping = {
        "生产部": "SC",
        "质量部": "ZL", 
        "技术部": "JS",
        "设备部": "SB",
        "采购部": "CG",
        "销售部": "XS",
        "人事部": "RS",
        "财务部": "CW",
        "行政部": "XZ",
        "研发部": "YF"
    }
    
    # 如果有预定义的代码，直接返回
    if department_name in code_mapping:
        return code_mapping[department_name]
    
    # 否则取部门名称的前两个字的首字母
    if len(department_name) >= 2:
        first_char = department_name[0].upper()
        second_char = department_name[1].upper()
        # 只取字母和数字
        if first_char.isalnum() and second_char.isalnum():
            return f"{first_char}{second_char}"
    
    # 如果无法生成，返回默认代码
    return "OT"  # Other

def generate_category_code(category_name: str) -> str:
    """
    根据类别名称生成类别代码
    """
    code_mapping = {
        "压力表": "YL",
        "温度计": "WD",
        "流量计": "LL",
        "电子秤": "DZ",
        "卡尺": "KC",
        "千分尺": "QF",
        "万用表": "WY",
        "示波器": "SB",
        "频谱仪": "PP",
        "硬度计": "YD",
        "显微镜": "XW",
        "天平": "TP",
        "pH计": "PH",
        "电导仪": "DD",
        "分光光度计": "FG"
    }
    
    # 如果有预定义的代码，直接返回
    if category_name in code_mapping:
        return code_mapping[category_name]
    
    # 否则取类别名称的前两个字的首字母
    if len(category_name) >= 2:
        first_char = category_name[0].upper()
        second_char = category_name[1].upper()
        # 只取字母和数字
        if first_char.isalnum() and second_char.isalnum():
            return f"{first_char}{second_char}"
    
    # 如果无法生成，返回默认代码
    return "OT"  # Other

def generate_internal_id(db: Session, category_id: int, equipment_name: str = None) -> str:
    """
    生成内部编号 (CC-TT-NNN格式)
    CC: 类别代码 (3位)
    TT: 设备类型编号 (格式: 类别代码-序列号)
    NNN: 该类型设备的序列号 (001-999)
    """
    # 获取类别信息
    category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    
    if not category:
        raise ValueError("找不到指定的类别")
    
    # 生成类别代码
    cat_code = category.code if category.code else generate_category_code(category.name)
    
    # 获取设备类型编号
    if equipment_name:
        type_code = get_equipment_type_code(cat_code, equipment_name)
        # 如果返回的是格式如"TEM-99"，则提取数字部分
        if '-' in type_code:
            simplified_type_code = type_code.split('-')[1]
        else:
            simplified_type_code = type_code
    else:
        # 如果没有提供设备名称，使用默认类型编号
        simplified_type_code = "99"
    
    # 查询该类别-设备类型组合下的最大序列号
    pattern = f"{cat_code}-{simplified_type_code}-(\\d{{3}})"
    result = db.query(Equipment).filter(
        Equipment.internal_id.like(f"{cat_code}-{simplified_type_code}-%")
    ).all()
    
    # 提取现有的序列号
    existing_numbers = []
    for equipment in result:
        match = re.match(pattern, equipment.internal_id)
        if match:
            try:
                num = int(match.group(1))
                existing_numbers.append(num)
            except ValueError:
                continue
    
    # 生成下一个序列号
    next_number = 1
    if existing_numbers:
        next_number = max(existing_numbers) + 1
    
    # 确保序列号不超过999
    if next_number > 999:
        raise ValueError(f"类别 {cat_code}-{simplified_type_code} 下的设备数量已达到上限(999)")
    
    # 格式化序列号为3位数字
    sequence = f"{next_number:03d}"
    
    # 返回完整的内部编号
    return f"{cat_code}-{simplified_type_code}-{sequence}"

def validate_internal_id(internal_id: str) -> bool:
    """
    验证内部编号格式是否正确
    新格式: CC-TT-NNN (如: TIM-1-001)
    """
    pattern = r'^[A-Z0-9]{3}-[A-Z0-9]+-\d{3}$'
    return bool(re.match(pattern, internal_id))

def parse_internal_id(internal_id: str) -> dict:
    """
    解析内部编号，返回类别代码、设备类型编号和序列号
    """
    if not validate_internal_id(internal_id):
        raise ValueError("内部编号格式不正确")
    
    parts = internal_id.split('-')
    if len(parts) != 3:
        raise ValueError("内部编号格式不正确")
    
    return {
        'category_code': parts[0],
        'equipment_type_code': parts[1],
        'sequence_number': int(parts[2])
    }

def get_next_sequence_number(db: Session, department_code: str, category_code: str) -> int:
    """
    获取指定部门-类别组合下的下一个序列号
    """
    pattern = f"{department_code}-{category_code}-(\\d{{3}})"
    result = db.query(Equipment).filter(
        Equipment.internal_id.like(f"{department_code}-{category_code}-%")
    ).all()
    
    # 提取现有的序列号
    existing_numbers = []
    for equipment in result:
        match = re.match(pattern, equipment.internal_id)
        if match:
            try:
                num = int(match.group(1))
                existing_numbers.append(num)
            except ValueError:
                continue
    
    # 生成下一个序列号
    if existing_numbers:
        return max(existing_numbers) + 1
    else:
        return 1
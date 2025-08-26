"""
智能预定义名称编号管理模块
"""

from typing import List, Dict, Tuple
from app.utils.equipment_mapping import EQUIPMENT_TYPE_MAPPING

def get_smart_name_mapping(category_code: str, predefined_names: List[str]) -> Dict[str, str]:
    """
    智能生成预定义名称的编号映射
    
    规则：
    1. 优先使用EQUIPMENT_TYPE_MAPPING中定义的编号
    2. 对于映射表中没有的名称，按顺序分配可用编号
    3. 保持已有名称的编号稳定性
    """
    name_mapping = {}
    used_numbers = set()
    
    # 第一步：收集映射表中已定义的编号
    predefined_mapping = EQUIPMENT_TYPE_MAPPING.get(category_code, {})
    
    # 第二步：为映射表中的名称分配编号
    for name, number in predefined_mapping.items():
        if name in predefined_names:
            name_mapping[name] = number
            used_numbers.add(int(number))
    
    # 第三步：为不在映射表中的名称分配编号
    remaining_names = [name for name in predefined_names if name not in name_mapping]
    
    # 找出最小的可用编号（从1开始）
    next_number = 1
    for name in remaining_names:
        # 找到下一个可用编号
        while next_number in used_numbers:
            next_number += 1
        
        name_mapping[name] = str(next_number)
        used_numbers.add(next_number)
        next_number += 1
    
    return name_mapping

def update_predefined_name_smart(category_code: str, predefined_names: List[str], 
                               old_name: str, new_name: str) -> Tuple[List[str], Dict[str, str]]:
    """
    智能更新预定义名称
    
    参数：
        category_code: 类别代码
        predefined_names: 当前的预定义名称列表
        old_name: 要修改的旧名称
        new_name: 新名称
    
    返回：
        (更新后的名称列表, 新的编号映射)
    """
    # 创建新的名称列表
    new_names_list = []
    name_changed = False
    
    for name in predefined_names:
        if name == old_name:
            new_names_list.append(new_name)
            name_changed = True
        else:
            new_names_list.append(name)
    
    # 如果旧名称不在列表中，则添加新名称
    if not name_changed:
        new_names_list.append(new_name)
    
    # 去重
    new_names_list = list(dict.fromkeys(new_names_list))
    
    # 生成新的编号映射
    new_mapping = get_smart_name_mapping(category_code, new_names_list)
    
    return new_names_list, new_mapping

def add_predefined_name_smart(category_code: str, predefined_names: List[str], 
                             new_name: str) -> Tuple[List[str], Dict[str, str]]:
    """
    智能添加预定义名称
    
    参数：
        category_code: 类别代码
        predefined_names: 当前的预定义名称列表
        new_name: 要添加的新名称
    
    返回：
        (更新后的名称列表, 新的编号映射)
    """
    # 添加新名称
    new_names_list = predefined_names.copy()
    if new_name not in new_names_list:
        new_names_list.append(new_name)
    
    # 去重
    new_names_list = list(dict.fromkeys(new_names_list))
    
    # 生成新的编号映射
    new_mapping = get_smart_name_mapping(category_code, new_names_list)
    
    return new_names_list, new_mapping

def remove_predefined_name_smart(category_code: str, predefined_names: List[str], 
                                remove_name: str) -> Tuple[List[str], Dict[str, str]]:
    """
    智能删除预定义名称
    
    参数：
        category_code: 类别代码
        predefined_names: 当前的预定义名称列表
        remove_name: 要删除的名称
    
    返回：
        (更新后的名称列表, 新的编号映射)
    """
    # 删除名称
    new_names_list = [name for name in predefined_names if name != remove_name]
    
    # 生成新的编号映射
    new_mapping = get_smart_name_mapping(category_code, new_names_list)
    
    return new_names_list, new_mapping

def get_smart_name_mapping_for_name(category_code: str, equipment_name: str) -> str:
    """
    为单个设备名称获取智能编号
    
    参数：
        category_code: 类别代码
        equipment_name: 设备名称
    
    返回：
        该名称的智能编号
    """
    # 从数据库获取该类别的所有预定义名称
    try:
        import json
        import sqlite3
        
        conn = sqlite3.connect('data/inventory.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
        result = cursor.fetchone()
        
        if result:
            predefined_names_json = result[0]
            predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
            
            # 如果设备名称在预定义名称中，使用智能编号映射
            if equipment_name in predefined_names:
                mapping = get_smart_name_mapping(category_code, predefined_names)
                if equipment_name in mapping:
                    conn.close()
                    return mapping[equipment_name]
        
        conn.close()
    except Exception as e:
        pass  # 静默处理数据库错误
    
    # 如果无法从数据库获取，尝试生成一个合理的编号
    try:
        # 生成一个基于名称哈希的编号（1-98之间）
        import hashlib
        hash_value = int(hashlib.md5(equipment_name.encode()).hexdigest(), 16)
        number = (hash_value % 98) + 1  # 1-98
        return str(number)
    except Exception as e:
        # 最后的备用方案
        return "99"
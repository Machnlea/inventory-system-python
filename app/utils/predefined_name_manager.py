"""
智能预定义名称编号管理模块
"""

from typing import List, Dict, Tuple
from app.utils.equipment_mapping import EQUIPMENT_TYPE_MAPPING

def get_smart_name_mapping(category_code: str, predefined_names: List[str], existing_equipment_names: List[str] = None, equipment_internal_ids: Dict[str, str] = None) -> Dict[str, str]:
    """
    智能生成预定义名称的编号映射
    
    规则：
    1. 有设备的器具保持原编号（基于设备internal_id中的编号）
    2. 无设备的器具重新排序，填补空缺
    3. 编号始终保持1.2.3.4.5这样顺序排序
    4. 映射表中的编号只作为参考，不强制使用
    """
    if existing_equipment_names is None:
        existing_equipment_names = []
    if equipment_internal_ids is None:
        equipment_internal_ids = {}
    
    name_mapping = {}
    used_numbers = set()
    
    # 第一步：为有设备的器具分配固定编号（基于设备internal_id中的编号）
    for name in existing_equipment_names:
        if name in predefined_names:
            # 从设备的internal_id中提取编号
            internal_id = equipment_internal_ids.get(name, "")
            number = extract_number_from_internal_id(internal_id, category_code)
            
            if not number:
                # 如果无法从internal_id提取编号，尝试从映射表中获取
                predefined_mapping = EQUIPMENT_TYPE_MAPPING.get(category_code, {})
                if name in predefined_mapping:
                    number = predefined_mapping[name]
                else:
                    # 最后的备用方案
                    number = "1"
            
            if number:
                name_mapping[name] = number
                used_numbers.add(int(number))
    
    # 第二步：为剩余的名称分配连续编号（填补空缺）
    remaining_names = [name for name in predefined_names if name not in name_mapping]
    
    # 找出最小的可用编号（从1开始），优先填补空缺
    next_number = 1
    for name in remaining_names:
        # 找到下一个可用编号
        while next_number in used_numbers:
            next_number += 1
        
        name_mapping[name] = str(next_number)
        used_numbers.add(next_number)
        next_number += 1
    
    return name_mapping

def extract_number_from_internal_id(internal_id: str, category_code: str) -> str:
    """
    从设备internal_id中提取编号
    
    参数：
        internal_id: 设备内部编号 (格式: CC-TT-NNN, 如 TEM-1-001)
        category_code: 类别代码
    
    返回：
        提取的编号字符串 (TT部分)
    """
    if not internal_id or not category_code:
        return ""
    
    try:
        # 新格式: CC-TT-NNN (如 TEM-1-001)
        if '-' in internal_id:
            parts = internal_id.split('-')
            if len(parts) >= 2:
                # 第二部分是设备类型编号
                equipment_type_code = parts[1]
                # 检查是否是数字格式
                if equipment_type_code.isdigit():
                    return equipment_type_code
                else:
                    # 如果不是纯数字，尝试从混合格式中提取数字
                    import re
                    match = re.search(r'(\d+)', equipment_type_code)
                    if match:
                        return match.group(1)
        else:
            # 旧格式尝试：移除类别代码前缀
            if internal_id.startswith(category_code):
                number_part = internal_id[len(category_code):]
                # 提取开头的数字部分
                import re
                match = re.match(r'^(\d+)', number_part)
                if match:
                    return match.group(1)
    except:
        pass
    
    return ""

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

def remove_predefined_name_with_equipment_check(category_code: str, predefined_names: List[str], 
                                              remove_name: str, existing_equipment_names: List[str], equipment_internal_ids: Dict[str, str] = None) -> Tuple[List[str], Dict[str, str]]:
    """
    智能删除预定义名称，考虑设备存在时的编号保持
    
    参数：
        category_code: 类别代码
        predefined_names: 当前的预定义名称列表
        remove_name: 要删除的名称
        existing_equipment_names: 该类别下已有设备的名称列表
        equipment_internal_ids: 设备名称到internal_id的映射
    
    返回：
        (更新后的名称列表, 新的编号映射)
    """
    if equipment_internal_ids is None:
        equipment_internal_ids = {}
    
    # 检查要删除的名称是否有设备在使用
    has_equipment = remove_name in existing_equipment_names
    
    if has_equipment:
        # 如果有设备，不能删除
        raise ValueError(f"无法删除预定义名称\"{remove_name}\"，该类别下还有设备使用此名称")
    
    # 删除名称
    new_names_list = [name for name in predefined_names if name != remove_name]
    
    # 使用统一的智能编号映射函数，传递设备internal_id信息以保持有设备器具的原始编号
    name_mapping = get_smart_name_mapping(category_code, new_names_list, existing_equipment_names, equipment_internal_ids)
    
    # 按照编号顺序重新排列名称列表
    sorted_names = sorted(new_names_list, key=lambda x: int(name_mapping[x]))
    
    return sorted_names, name_mapping

def get_smart_name_mapping_for_name(category_code: str, equipment_name: str) -> str:
    """
    为单个设备名称获取智能编号
    
    参数：
        category_code: 类别代码
        equipment_name: 设备名称
    
    返回：
        该名称的智能编号
    """
    # 从数据库获取该类别的所有预定义名称和设备信息
    try:
        import json
        import sqlite3
        
        conn = sqlite3.connect('data/inventory.db')
        cursor = conn.cursor()
        
        # 获取预定义名称
        cursor.execute('SELECT predefined_names FROM equipment_categories WHERE code = ?', (category_code,))
        result = cursor.fetchone()
        
        if result:
            predefined_names_json = result[0]
            predefined_names = json.loads(predefined_names_json) if predefined_names_json else []
            
            # 如果设备名称在预定义名称中，使用智能编号映射
            if equipment_name in predefined_names:
                # 获取该类别下的所有设备信息
                cursor.execute('''
                    SELECT e.name, e.internal_id, c.id 
                    FROM equipments e 
                    JOIN equipment_categories c ON e.category_id = c.id 
                    WHERE c.code = ?
                ''', (category_code,))
                
                equipment_data = cursor.fetchall()
                existing_equipment_names = [item[0] for item in equipment_data]
                equipment_internal_ids = {item[0]: item[1] for item in equipment_data}
                
                # 使用智能编号映射
                mapping = get_smart_name_mapping(category_code, predefined_names, existing_equipment_names, equipment_internal_ids)
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
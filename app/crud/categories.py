from sqlalchemy.orm import Session
from app.models.models import EquipmentCategory
from app.schemas.schemas import EquipmentCategoryCreate
from typing import List

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(EquipmentCategory).offset(skip).limit(limit).all()

def get_category(db: Session, category_id: int):
    return db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()

def get_category_by_name(db: Session, name: str):
    return db.query(EquipmentCategory).filter(EquipmentCategory.name == name).first()

def create_category(db: Session, category: EquipmentCategoryCreate):
    # 将category_code映射到code字段
    category_data = category.dict()
    if 'category_code' in category_data:
        category_data['code'] = category_data.pop('category_code')
    
    db_category = EquipmentCategory(**category_data)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

def update_category(db: Session, category_id: int, category: EquipmentCategoryCreate):
    db_category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if db_category:
        # 将category_code映射到code字段
        category_data = category.dict()
        if 'category_code' in category_data:
            category_data['code'] = category_data.pop('category_code')
        
        for field, value in category_data.items():
            setattr(db_category, field, value)
        db.commit()
        db.refresh(db_category)
        
        return db_category
    return None

def delete_category(db: Session, category_id: int):
    from app.models.models import Equipment
    
    try:
        # 检查该类别下是否有设备
        equipment_exists = db.query(Equipment).filter(Equipment.category_id == category_id).first()
        
        if equipment_exists:
            return False, "无法删除该类别，该类别下还有设备"
        
        db_category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
        if db_category:
            db.delete(db_category)
            db.commit()
            return True, "类别删除成功"
        return False, "类别不存在"
    except Exception as e:
        db.rollback()
        return False, f"删除类别时发生错误: {str(e)}"

def get_category_with_equipment_count(db: Session, skip: int = 0, limit: int = 100):
    """获取设备类别及其设备数量"""
    from app.models.models import Equipment
    from sqlalchemy import func
    
    result = db.query(
        EquipmentCategory,
        func.count(Equipment.id).label('equipment_count')
    ).outerjoin(Equipment).group_by(EquipmentCategory.id).offset(skip).limit(limit).all()
    
    categories_with_count = []
    for category, count in result:
        category_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "category_code": category.code,  # 使用category_code字段名返回
            "predefined_names": category.predefined_names,  # 添加预定义器具名称
            "created_at": category.created_at,
            "equipment_count": count
        }
        categories_with_count.append(category_dict)
    
    return categories_with_count

def add_predefined_name(db: Session, category_id: int, name: str):
    """为指定类别添加预定义器具名称"""
    category = get_category(db, category_id)
    if not category:
        return None
    
    # 确保predefined_names是列表
    if category.predefined_names is None:
        category.predefined_names = []
    
    # 添加新名称（如果不存在）
    if name not in category.predefined_names:
        category.predefined_names.append(name)
        # 直接使用SQL更新确保数据持久化
        import json
        from sqlalchemy import text
        updated_json = json.dumps(category.predefined_names, ensure_ascii=False)
        db.execute(
            text("UPDATE equipment_categories SET predefined_names = :names WHERE id = :id"),
            {"names": updated_json, "id": category_id}
        )
        db.commit()
        db.refresh(category)
    
    return category

def remove_predefined_name(db: Session, category_id: int, name: str):
    """从指定类别移除预定义器具名称"""
    from app.models.models import Equipment
    
    category = get_category(db, category_id)
    if not category or not category.predefined_names:
        return None
    
    # 检查是否有设备在使用这个预定义名称
    equipment_using_name = db.query(Equipment).filter(
        Equipment.category_id == category_id,
        Equipment.name == name
    ).first()
    
    if equipment_using_name:
        raise ValueError(f"无法删除预定义名称\"{name}\"，该类别下还有设备使用此名称")
    
    if name in category.predefined_names:
        category.predefined_names.remove(name)
        # 直接使用SQL更新确保数据持久化
        import json
        from sqlalchemy import text
        updated_json = json.dumps(category.predefined_names, ensure_ascii=False)
        db.execute(
            text("UPDATE equipment_categories SET predefined_names = :names WHERE id = :id"),
            {"names": updated_json, "id": category_id}
        )
        db.commit()
        db.refresh(category)
    
    return category

def update_predefined_names(db: Session, category_id: int, names: list):
    """更新指定类别的预定义器具名称列表"""
    from app.models.models import Equipment
    
    category = get_category(db, category_id)
    if not category:
        return None
    
    # 获取现有的预定义名称
    existing_names = set(category.predefined_names or [])
    new_names = set(names)
    
    # 找出被删除的名称
    removed_names = existing_names - new_names
    
    # 检查被删除的名称是否有设备在使用
    for removed_name in removed_names:
        equipment_using_name = db.query(Equipment).filter(
            Equipment.category_id == category_id,
            Equipment.name == removed_name
        ).first()
        
        if equipment_using_name:
            raise ValueError(f"无法更新预定义名称列表，名称\"{removed_name}\"已被设备使用，不能删除")
    
    category.predefined_names = names
    db.commit()
    db.refresh(category)
    
    return category
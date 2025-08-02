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
    db_category = EquipmentCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category: EquipmentCategoryCreate):
    db_category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if db_category:
        for field, value in category.dict().items():
            setattr(db_category, field, value)
        db.commit()
        db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
        return True
    return False

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
            "created_at": category.created_at,
            "equipment_count": count
        }
        categories_with_count.append(category_dict)
    
    return categories_with_count
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.crud import categories
from app.schemas.schemas import EquipmentCategory, EquipmentCategoryCreate
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

# 预定义器具名称请求模型
class PredefinedNameRequest(BaseModel):
    name: str

class PredefinedNamesRequest(BaseModel):
    names: List[str]

@router.get("/", response_model=List[EquipmentCategory])
def read_categories(skip: int = 0, limit: int = 100,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    return categories.get_categories(db, skip=skip, limit=limit)

@router.post("/", response_model=EquipmentCategory)
def create_category(category: EquipmentCategoryCreate,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    db_category = categories.get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    return categories.create_category(db=db, category=category)

@router.get("/with-counts")
def get_categories_with_counts(skip: int = 0, limit: int = 100,
                              db: Session = Depends(get_db),
                              current_user = Depends(get_current_user)):
    return categories.get_category_with_equipment_count(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=EquipmentCategory)
def read_category(category_id: int,
                 db: Session = Depends(get_db),
                 current_user = Depends(get_current_user)):
    db_category = categories.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/{category_id}", response_model=EquipmentCategory)
def update_category(category_id: int, category: EquipmentCategoryCreate,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    db_category = categories.update_category(db, category_id=category_id, category=category)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.delete("/{category_id}")
def delete_category(category_id: int,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_admin_user)):
    success, message = categories.delete_category(db, category_id=category_id)
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

# 预定义器具名称管理API
@router.post("/{category_id}/predefined-names")
def add_predefined_name(category_id: int,
                        request: PredefinedNameRequest,
                        db: Session = Depends(get_db),
                        current_user = Depends(get_current_admin_user)):
    """为指定类别添加预定义器具名称"""
    from app.utils.predefined_name_manager import add_predefined_name_smart
    
    # 检查类别是否存在
    existing_category = categories.get_category(db, category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 检查重复
    if existing_category.predefined_names and request.name in existing_category.predefined_names:
        raise HTTPException(status_code=400, detail="Predefined name already exists")
    
    # 使用智能添加逻辑
    current_names = existing_category.predefined_names or []
    category_code = existing_category.code
    
    new_names_list, new_mapping = add_predefined_name_smart(
        category_code, current_names, request.name
    )
    
    # 更新数据库
    import json
    from sqlalchemy import text
    updated_json = json.dumps(new_names_list, ensure_ascii=False)
    
    db.execute(
        text("UPDATE equipment_categories SET predefined_names = :names WHERE id = :id"),
        {"names": updated_json, "id": category_id}
    )
    db.commit()
    
    # 返回更新后的信息
    return {
        "message": "Predefined name added successfully", 
        "predefined_names": new_names_list,
        "name_mapping": new_mapping
    }

@router.delete("/{category_id}/predefined-names/{name}")
def remove_predefined_name(category_id: int,
                         name: str,
                         db: Session = Depends(get_db),
                         current_user = Depends(get_current_admin_user)):
    """从指定类别移除预定义器具名称"""
    try:
        category = categories.remove_predefined_name(db, category_id, name)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Predefined name removed successfully", "category": category}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{category_id}/predefined-names")
def edit_predefined_name(category_id: int,
                        request: dict = None,
                        db: Session = Depends(get_db),
                        current_user = Depends(get_current_admin_user)):
    """编辑指定类别的预定义器具名称"""
    from app.utils.predefined_name_manager import update_predefined_name_smart
    
    if not request:
        raise HTTPException(status_code=400, detail="Request body is required")
    
    old_name = request.get('old_name')
    new_name = request.get('new_name')
    
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Old name and new name are required")
    
    if old_name == new_name:
        raise HTTPException(status_code=400, detail="New name must be different from old name")
    
    # 检查类别是否存在
    existing_category = categories.get_category(db, category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 检查旧名称是否存在
    current_names = existing_category.predefined_names or []
    if old_name not in current_names:
        raise HTTPException(status_code=404, detail="Old name not found in predefined names")
    
    # 检查新名称是否已存在（排除旧名称）
    if new_name in current_names and new_name != old_name:
        raise HTTPException(status_code=400, detail="New name already exists")
    
    # 使用智能更新逻辑
    category_code = existing_category.code
    
    new_names_list, new_mapping = update_predefined_name_smart(
        category_code, current_names, old_name, new_name
    )
    
    # 更新数据库
    import json
    from sqlalchemy import text
    updated_json = json.dumps(new_names_list, ensure_ascii=False)
    
    db.execute(
        text("UPDATE equipment_categories SET predefined_names = :names WHERE id = :id"),
        {"names": updated_json, "id": category_id}
    )
    db.commit()
    
    # 返回更新后的信息
    return {
        "message": "Predefined name updated successfully", 
        "predefined_names": new_names_list,
        "name_mapping": new_mapping
    }

@router.put("/{category_id}/predefined-names")
def update_predefined_names(category_id: int,
                           request: PredefinedNamesRequest,
                           db: Session = Depends(get_db),
                           current_user = Depends(get_current_admin_user)):
    """更新指定类别的预定义器具名称列表"""
    try:
        category = categories.update_predefined_names(db, category_id, request.names)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Predefined names updated successfully", "category": category}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{category_id}/predefined-names")
def get_predefined_names(category_id: int,
                        db: Session = Depends(get_db),
                        current_user = Depends(get_current_user)):
    """获取指定类别的预定义器具名称列表"""
    category = categories.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"predefined_names": category.predefined_names or []}

@router.get("/{category_id}/equipment-usage")
def get_category_equipment_usage(category_id: int,
                                db: Session = Depends(get_db),
                                current_user = Depends(get_current_user)):
    """获取指定类别下预定义名称的设备使用情况和编号映射"""
    from app.models.models import Equipment, EquipmentCategory
    from sqlalchemy import func
    from app.utils.predefined_name_manager import get_smart_name_mapping
    
    # 获取类别信息
    category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 获取该类别下所有设备，按名称分组统计
    equipment_stats = db.query(
        Equipment.name,
        func.count(Equipment.id).label('count')
    ).filter(
        Equipment.category_id == category_id
    ).group_by(Equipment.name).all()
    
    # 获取预定义名称的编号映射 - 使用智能编号管理
    category_code = category.code
    predefined_names = category.predefined_names or []
    name_mapping = get_smart_name_mapping(category_code, predefined_names)
    
    # 转换为字典格式，并清理名称（去除可能的引号）
    usage_stats = {}
    fuzzy_mapping = {}  # 用于模糊匹配的映射
    
    for stat in equipment_stats:
        # 清理设备名称，去除可能的引号和空格
        clean_name = stat.name.strip().strip('"').strip("'")
        
        # 添加原始名称
        usage_stats[stat.name] = stat.count
        
        # 添加清理后的名称
        if clean_name != stat.name:
            usage_stats[clean_name] = usage_stats.get(clean_name, 0) + stat.count
        
        # 为模糊匹配创建映射
        fuzzy_mapping[clean_name.lower()] = stat.name
        
        # 如果清理后的名称不同，也添加到模糊映射
        if clean_name.lower() != stat.name.lower():
            fuzzy_mapping[stat.name.lower()] = stat.name
    
    # 模糊匹配：检查预定义名称是否与设备名称相似
    enhanced_usage_stats = usage_stats.copy()
    
    for predefined_name in predefined_names:
        predefined_lower = predefined_name.lower().strip()
        
        # 如果预定义名称还没有在使用统计中，尝试模糊匹配
        if predefined_name not in enhanced_usage_stats:
            # 直接匹配
            if predefined_lower in fuzzy_mapping:
                matched_device_name = fuzzy_mapping[predefined_lower]
                enhanced_usage_stats[predefined_name] = usage_stats.get(matched_device_name, 0)
            
            # 尝试部分匹配（去除特殊字符）
            else:
                # 去除预定义名称中的特殊字符再匹配
                simplified_predefined = ''.join(c for c in predefined_lower if c.isalnum())
                for device_key in fuzzy_mapping:
                    simplified_device = ''.join(c for c in device_key if c.isalnum())
                    if simplified_predefined == simplified_device and len(simplified_predefined) > 2:
                        matched_device_name = fuzzy_mapping[device_key]
                        enhanced_usage_stats[predefined_name] = usage_stats.get(matched_device_name, 0)
                        break
    
    # 添加调试信息
    debug_info = {
        "category_id": category_id,
        "category_code": category_code,
        "category_name": category.name,
        "predefined_names": predefined_names,
        "raw_equipment_stats": [(stat.name, stat.count) for stat in equipment_stats],
        "basic_usage_stats": usage_stats,
        "enhanced_usage_stats": enhanced_usage_stats,
        "fuzzy_mapping": fuzzy_mapping,
        "name_mapping": name_mapping
    }
    
    print(f"=== 调试信息 - 类别 {category.name} ===")
    print(f"预定义名称: {predefined_names}")
    print(f"设备统计: {[(stat.name, stat.count) for stat in equipment_stats]}")
    print(f"基本使用情况: {usage_stats}")
    print(f"增强使用情况: {enhanced_usage_stats}")
    print(f"模糊映射: {fuzzy_mapping}")
    print(f"名称映射: {name_mapping}")
    
    return {
        "category_id": category_id,
        "category_code": category_code,
        "usage_stats": enhanced_usage_stats,  # 使用增强的使用统计
        "name_mapping": name_mapping,
        "_debug": debug_info  # 包含调试信息
    }
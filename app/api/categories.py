from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union, Any
from pydantic import BaseModel
from app.db.database import get_db
from app.crud import categories
from app.schemas.schemas import EquipmentCategory, EquipmentCategoryCreate
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

def safe_get_list(column_value) -> List[str]:
    """安全地从SQLAlchemy Column对象获取列表"""
    if column_value is None:
        return []
    try:
        return list(column_value)
    except:
        return []

# 预定义器具名称请求模型
class PredefinedNameRequest(BaseModel):
    name: str

class PredefinedNamesRequest(BaseModel):
    names: List[str]

@router.get("/", response_model=List[EquipmentCategory])
def read_categories(skip: int = 0, limit: int = 100,
                   db: Session = Depends(get_db),
                   current_user = Depends(get_current_user)):
    
    # 管理员可以看到所有类别
    if current_user.is_admin:
        return categories.get_categories(db, skip=skip, limit=limit)
    
    # 普通用户只能看到有权限的设备所属的类别
    from app.models.models import UserEquipmentPermission, EquipmentCategory
    from sqlalchemy import distinct
    
    # 获取用户有权限的设备名称
    authorized_equipment_names = db.query(UserEquipmentPermission.equipment_name).filter(
        UserEquipmentPermission.user_id == current_user.id
    ).all()
    
    if not authorized_equipment_names:
        return []  # 用户没有任何设备权限
    
    # 提取设备名称列表
    equipment_names = [item[0] for item in authorized_equipment_names]
    
    # 通过用户权限记录直接找到对应的类别（不依赖现有设备）
    authorized_categories = db.query(EquipmentCategory).join(
        UserEquipmentPermission, UserEquipmentPermission.category_id == EquipmentCategory.id
    ).filter(
        UserEquipmentPermission.user_id == current_user.id
    ).distinct().offset(skip).limit(limit).all()
    
    return authorized_categories

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
    
    # 管理员可以看到所有类别
    if current_user.is_admin:
        return categories.get_category_with_equipment_count(db, skip=skip, limit=limit)
    
    # 普通用户只能看到有权限设备所属的类别及其设备数量
    from app.models.models import UserEquipmentPermission, EquipmentCategory, Equipment
    from sqlalchemy import func, distinct
    
    # 获取用户有权限的类别ID
    authorized_category_ids = db.query(UserEquipmentPermission.category_id).filter(
        UserEquipmentPermission.user_id == current_user.id
    ).distinct().all()
    
    if not authorized_category_ids:
        return []  # 用户没有任何设备权限
    
    # 提取类别ID列表
    category_ids = [item[0] for item in authorized_category_ids]
    
    # 查询用户有权限的类别及其设备数量
    result = db.query(
        EquipmentCategory.id,
        EquipmentCategory.name,
        EquipmentCategory.code,
        EquipmentCategory.description,
        EquipmentCategory.predefined_names,
        func.count(Equipment.id).label('equipment_count')
    ).outerjoin(
        Equipment, EquipmentCategory.id == Equipment.category_id
    ).filter(
        EquipmentCategory.id.in_(category_ids)
    ).group_by(
        EquipmentCategory.id,
        EquipmentCategory.name,
        EquipmentCategory.code,
        EquipmentCategory.description,
        EquipmentCategory.predefined_names
    ).offset(skip).limit(limit).all()
    
    # 转换为字典格式
    categories_with_counts = []
    for row in result:
        categories_with_counts.append({
            "id": row.id,
            "name": row.name,
            "code": row.code,
            "description": row.description,
            "predefined_names": row.predefined_names,
            "equipment_count": row.equipment_count
        })
    
    return categories_with_counts

@router.get("/{category_id}", response_model=EquipmentCategory)
def read_category(category_id: int,
                 db: Session = Depends(get_db),
                 current_user = Depends(get_current_user)):
    db_category = categories.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 普通用户权限检查：只能查看授权的类别
    if not current_user.is_admin:
        from app.models.models import UserCategory
        
        user_category = db.query(UserCategory).filter(
            UserCategory.user_id == current_user.id,
            UserCategory.category_id == category_id
        ).first()
        
        if not user_category:
            raise HTTPException(status_code=403, detail="No permission to access this category")
    
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
    predefined_names = safe_get_list(existing_category.predefined_names)
    
    if predefined_names and request.name in predefined_names:
        raise HTTPException(status_code=400, detail="Predefined name already exists")
    
    # 使用智能添加逻辑
    current_names = predefined_names or []
    category_code = str(existing_category.code or "")
    
    new_names_list, new_mapping = add_predefined_name_smart(
        category_code, list(current_names), request.name
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
        from app.utils.predefined_name_manager import remove_predefined_name_with_equipment_check
        from app.models.models import Equipment
        
        # 获取类别信息
        category = categories.get_category(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # 获取该类别下所有设备的名称和internal_id
        equipment_data = db.query(Equipment.name, Equipment.internal_id).filter(
            Equipment.category_id == category_id
        ).all()
        existing_equipment_names = [item[0] for item in equipment_data]
        equipment_internal_ids = {item[0]: item[1] for item in equipment_data}
        
        # 获取当前预定义名称列表
        current_names = safe_get_list(category.predefined_names)
        category_code = str(category.code or "")
        
        # 使用智能删除逻辑
        new_names_list, new_mapping = remove_predefined_name_with_equipment_check(
            category_code, current_names, name, existing_equipment_names, equipment_internal_ids
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
        
        # 重新获取更新后的类别信息
        updated_category = categories.get_category(db, category_id)
        
        return {
            "message": "Predefined name removed successfully", 
            "category": updated_category,
            "name_mapping": new_mapping
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{category_id}/predefined-names")
def edit_predefined_name(category_id: int,
                        request: dict = {},
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
    current_names = safe_get_list(existing_category.predefined_names)
    if old_name not in current_names:
        raise HTTPException(status_code=404, detail="Old name not found in predefined names")
    
    # 检查新名称是否已存在（排除旧名称）
    if new_name in current_names and new_name != old_name:
        raise HTTPException(status_code=400, detail="New name already exists")
    
    # 使用智能更新逻辑
    category_code = str(existing_category.code or "")
    current_names_list = current_names or []
    
    new_names_list, new_mapping = update_predefined_name_smart(
        category_code, list(current_names_list), old_name, new_name
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
    
    # 普通用户权限检查：只能查看授权的类别或有设备权限的类别
    if not current_user.is_admin:
        from app.models.models import UserCategory, UserEquipmentPermission, Equipment
        
        # 检查类别权限
        user_category = db.query(UserCategory).filter(
            UserCategory.user_id == current_user.id,
            UserCategory.category_id == category_id
        ).first()
        
        # 如果有类别权限，返回所有预定义名称
        if user_category:
            return {"predefined_names": category.predefined_names or []}
        
        # 如果没有类别权限，检查是否有该类别下特定设备的权限
        user_equipment_permissions = db.query(UserEquipmentPermission.equipment_name).filter(
            UserEquipmentPermission.user_id == current_user.id
        ).all()
        
        if user_equipment_permissions:
            # 获取用户有权限的设备名称
            user_equipment_names = [perm[0] for perm in user_equipment_permissions]
            
            # 检查这些设备名称是否在当前类别的预定义名称中
            category_predefined_names = set(category.predefined_names or [])
            authorized_equipment_names = [
                name for name in user_equipment_names 
                if name in category_predefined_names
            ]
            
            if authorized_equipment_names:
                # 返回用户有权限的所有设备名称（不管是否已有设备记录）
                return {"predefined_names": authorized_equipment_names}
        
        # 如果既没有类别权限，也没有该类别下的设备权限
        raise HTTPException(status_code=403, detail="No permission to access this category")
    
    # 管理员可以看到所有预定义名称
    return {"predefined_names": category.predefined_names or []}

@router.get("/{category_id}/equipment-usage")
def get_category_equipment_usage(category_id: int,
                                db: Session = Depends(get_db),
                                current_user = Depends(get_current_user)):
    """获取指定类别下预定义名称的设备使用情况和编号映射"""
    from app.models.models import Equipment, EquipmentCategory, UserCategory, UserEquipmentPermission
    from sqlalchemy import func
    from app.utils.predefined_name_manager import get_smart_name_mapping
    
    # 获取类别信息
    category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 普通用户权限检查：只能查看授权的类别或有设备权限的类别
    authorized_equipment_names = []  # 用户有权限的设备名称列表
    
    if not current_user.is_admin:
        # 检查类别权限
        user_category = db.query(UserCategory).filter(
            UserCategory.user_id == current_user.id,
            UserCategory.category_id == category_id
        ).first()
        
        if user_category:
            # 如果有类别权限，可以看到所有预定义名称
            predefined_names = safe_get_list(category.predefined_names)
        else:
            # 如果没有类别权限，检查是否有该类别下特定设备的权限
            user_equipment_permissions = db.query(UserEquipmentPermission.equipment_name).filter(
                UserEquipmentPermission.user_id == current_user.id
            ).all()
            
            if user_equipment_permissions:
                # 获取用户有权限的设备名称
                user_equipment_names = [perm[0] for perm in user_equipment_permissions]
                
                # 检查这些设备名称是否在当前类别的预定义名称中
                category_predefined_names = set(safe_get_list(category.predefined_names))
                authorized_equipment_names = [
                    name for name in user_equipment_names 
                    if name in category_predefined_names
                ]
                
                if authorized_equipment_names:
                    # 只处理用户有权限的设备名称（不管是否已有设备记录）
                    predefined_names = authorized_equipment_names
                else:
                    raise HTTPException(status_code=403, detail="No permission to access this category")
            else:
                raise HTTPException(status_code=403, detail="No permission to access this category")
    else:
        # 管理员可以看到所有预定义名称
        predefined_names = safe_get_list(category.predefined_names)
    
    # 获取该类别下设备，按名称分组统计，根据用户权限进行过滤
    equipment_query = db.query(
        Equipment.name,
        func.count(Equipment.id).label('count')
    ).filter(
        Equipment.category_id == category_id
    )
    
    # 如果用户只有特定设备权限，则只查询这些设备
    if authorized_equipment_names:
        equipment_query = equipment_query.filter(Equipment.name.in_(authorized_equipment_names))
    
    equipment_stats = equipment_query.group_by(Equipment.name).all()
    
    # 获取预定义名称的编号映射 - 使用智能编号管理
    category_code = str(category.code or "")
    
    # 获取该类别下所有设备的名称和internal_id，用于智能编号
    all_equipment_data = db.query(Equipment.name, Equipment.internal_id).filter(
        Equipment.category_id == category_id
    ).all()
    existing_equipment_names = [item[0] for item in all_equipment_data]
    equipment_internal_ids = {item[0]: item[1] for item in all_equipment_data}
    
    name_mapping = get_smart_name_mapping(category_code, predefined_names, existing_equipment_names, equipment_internal_ids)
    
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
    
    return {
        "category_id": category_id,
        "category_code": category_code,
        "usage_stats": enhanced_usage_stats,
        "name_mapping": name_mapping
    }
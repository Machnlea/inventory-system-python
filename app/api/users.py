from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.crud import users
from app.schemas.schemas import User, UserCreate, UserUpdate, UserCategory, UserEquipmentPermission, UserEquipmentPermissionCreate
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, 
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_admin_user)):
    return users.get_users(db, skip=skip, limit=limit)

@router.post("/", response_model=User)
def create_user(user: UserCreate, 
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    db_user = users.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return users.create_user(db=db, user=user)

@router.get("/equipment-counts-all")
def get_all_equipment_counts(db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_admin_user)):
    """获取所有类别中包含设备的器具信息"""
    from app.models.models import Equipment, EquipmentCategory
    from sqlalchemy import func
    
    # 获取所有类别
    categories = db.query(EquipmentCategory).all()
    
    result = []
    
    for category in categories:
        # 获取该类别下每个器具名称的设备数量（只统计在用设备）
        equipment_counts = db.query(
            Equipment.name,
            func.count(Equipment.id).label('count')
        ).filter(
            Equipment.category_id == category.id,
            Equipment.status == "在用"
        ).group_by(Equipment.name).all()
        
        # 创建器具名称到设备数量的映射
        count_map = {name: count for name, count in equipment_counts}
        
        # 只包含有设备的器具
        predefined_names = category.predefined_names or []
        for equipment_name in predefined_names:
            device_count = count_map.get(equipment_name, 0)
            if device_count > 0:  # 只包含有设备的器具
                result.append({
                    "category_id": category.id,
                    "category_name": category.name,
                    "equipment_name": equipment_name,
                    "device_count": device_count
                })
    
    return result

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, 
              db: Session = Depends(get_db),
              current_user: User = Depends(get_current_admin_user)):
    db_user = users.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user_update: UserUpdate,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    db_user = users.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_admin_user)):
    # 检查用户是否存在
    db_user = users.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查用户是否有关联的设备类别权限
    user_categories = users.get_user_categories(db, user_id)
    if user_categories:
        raise HTTPException(
            status_code=400, 
            detail="无法删除该用户，因为该用户还管理着设备类别。请先移除该用户的设备类别权限后再删除。"
        )
    
    # 检查用户是否有关联的器具权限
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel
    user_equipment_permissions = db.query(UserEquipmentPermissionModel).filter(
        UserEquipmentPermissionModel.user_id == user_id
    ).all()
    
    if user_equipment_permissions:
        raise HTTPException(
            status_code=400, 
            detail="无法删除该用户，因为该用户还管理着具体器具。请先移除该用户的器具权限后再删除。"
        )
    
    # 删除用户
    success = users.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete user")
    
    return {"message": "User deleted successfully"}

@router.get("/{user_id}/categories", response_model=List[UserCategory])
def get_user_categories(user_id: int,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_admin_user)):
    return users.get_user_categories(db, user_id=user_id)

@router.get("/categories/managed-status")
def get_categories_managed_status(db: Session = Depends(get_db),
                                 current_user: User = Depends(get_current_admin_user)):
    """获取所有设备类别的管理状态"""
    from app.models.models import EquipmentCategory, UserCategory as UserCategoryModel
    
    categories = db.query(EquipmentCategory).all()
    managed_status = []
    
    for category in categories:
        # 检查该类别是否被管理
        user_category = db.query(UserCategoryModel).filter(UserCategoryModel.category_id == category.id).first()
        if user_category:
            managed_status.append({
                "category_id": category.id,
                "category_name": category.name,
                "is_managed": True,
                "managed_by_user_id": user_category.user_id,
                "managed_by_username": user_category.user.username
            })
        else:
            managed_status.append({
                "category_id": category.id,
                "category_name": category.name,
                "is_managed": False,
                "managed_by_user_id": None,
                "managed_by_username": None
            })
    
    return managed_status

@router.post("/{user_id}/categories/{category_id}")
def assign_category_to_user(user_id: int, category_id: int,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_admin_user)):
    try:
        user_category = users.assign_category_to_user(db, user_id=user_id, category_id=category_id)
        return {"message": "Category assigned successfully", "user_category": user_category}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/categories")
def update_user_categories(user_id: int, category_data: dict,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_admin_user)):
    try:
        category_ids = category_data.get("category_ids", [])
        success = users.update_user_categories(db, user_id=user_id, category_ids=category_ids)
        if success:
            return {"message": "User categories updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update user categories")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 器具权限管理端点
@router.get("/{user_id}/equipment-permissions", response_model=List[UserEquipmentPermission])
def get_user_equipment_permissions(user_id: int,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_admin_user)):
    """获取用户的器具权限"""
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel
    permissions = db.query(UserEquipmentPermissionModel).filter(
        UserEquipmentPermissionModel.user_id == user_id
    ).all()
    
    result = []
    for perm in permissions:
        result.append(UserEquipmentPermission(
            id=perm.id,
            user_id=perm.user_id,
            category_id=perm.category_id,
            equipment_name=perm.equipment_name
        ))
    
    return result

@router.get("/equipment-permissions/managed-status")
def get_equipment_permissions_managed_status(db: Session = Depends(get_db),
                                          current_user: User = Depends(get_current_admin_user)):
    """获取所有器具的管理状态"""
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel, EquipmentCategory
    
    # 获取所有类别及其预定义器具
    categories = db.query(EquipmentCategory).all()
    managed_status = []
    
    for category in categories:
        predefined_names = category.predefined_names or []
        
        for equipment_name in predefined_names:
            # 检查该器具是否被管理
            permission = db.query(UserEquipmentPermissionModel).filter(
                UserEquipmentPermissionModel.category_id == category.id,
                UserEquipmentPermissionModel.equipment_name == equipment_name
            ).first()
            
            if permission:
                managed_status.append({
                    "category_id": category.id,
                    "category_name": category.name,
                    "equipment_name": equipment_name,
                    "is_managed": True,
                    "managed_by_user_id": permission.user_id,
                    "managed_by_username": permission.user.username
                })
            else:
                managed_status.append({
                    "category_id": category.id,
                    "category_name": category.name,
                    "equipment_name": equipment_name,
                    "is_managed": False,
                    "managed_by_user_id": None,
                    "managed_by_username": None
                })
    
    return managed_status

@router.post("/{user_id}/equipment-permissions")
def assign_equipment_permission(user_id: int, permission_data: UserEquipmentPermissionCreate,
                                db: Session = Depends(get_db),
                                current_user: User = Depends(get_current_admin_user)):
    """分配器具权限给用户"""
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel
    
    try:
        # 检查该器具是否已被其他用户管理（包括器具权限和类别权限）
        
        # 1. 检查其他用户的器具权限
        existing_equipment = db.query(UserEquipmentPermissionModel).filter(
            UserEquipmentPermissionModel.category_id == permission_data.category_id,
            UserEquipmentPermissionModel.equipment_name == permission_data.equipment_name
        ).first()
        
        if existing_equipment and existing_equipment.user_id != user_id:
            raise ValueError(f"器具 '{permission_data.equipment_name}' 已被用户 '{existing_equipment.user.username}' 通过器具权限管理")
        
        # 2. 检查其他用户的类别权限（该类别下的所有器具）
        from app.models.models import UserCategory, EquipmentCategory
        existing_category = db.query(UserCategory).filter(
            UserCategory.category_id == permission_data.category_id,
            UserCategory.user_id != user_id
        ).first()
        
        if existing_category:
            category_info = db.query(EquipmentCategory).filter(
                EquipmentCategory.id == permission_data.category_id
            ).first()
            if category_info:
                raise ValueError(f"器具 '{permission_data.equipment_name}' 所属的类别 '{category_info.name}' 已被用户 '{existing_category.user.username}' 通过类别权限管理")
        
        # 删除用户对该器具的现有权限
        db.query(UserEquipmentPermissionModel).filter(
            UserEquipmentPermissionModel.user_id == user_id,
            UserEquipmentPermissionModel.category_id == permission_data.category_id,
            UserEquipmentPermissionModel.equipment_name == permission_data.equipment_name
        ).delete()
        
        # 添加新权限
        permission = UserEquipmentPermissionModel(
            user_id=user_id,
            category_id=permission_data.category_id,
            equipment_name=permission_data.equipment_name
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        return {"message": "Equipment permission assigned successfully", "permission": permission}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/equipment-permissions")
def update_user_equipment_permissions(user_id: int, permissions_data: dict,
                                     db: Session = Depends(get_db),
                                     current_user: User = Depends(get_current_admin_user)):
    """更新用户的器具权限"""
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel
    
    try:
        equipment_names = permissions_data.get("equipment_names", [])
        category_id = permissions_data.get("category_id")
        
        if not category_id:
            raise HTTPException(status_code=400, detail="category_id is required")
        
        # 删除用户在该类别下的所有器具权限
        db.query(UserEquipmentPermissionModel).filter(
            UserEquipmentPermissionModel.user_id == user_id,
            UserEquipmentPermissionModel.category_id == category_id
        ).delete()
        
        # 添加新的权限
        for equipment_name in equipment_names:
            # 检查该器具是否已被其他用户管理（包括器具权限和类别权限）
            
            # 1. 检查其他用户的器具权限
            existing_equipment = db.query(UserEquipmentPermissionModel).filter(
                UserEquipmentPermissionModel.category_id == category_id,
                UserEquipmentPermissionModel.equipment_name == equipment_name
            ).first()
            
            if existing_equipment and existing_equipment.user_id != user_id:
                raise ValueError(f"器具 '{equipment_name}' 已被用户 '{existing_equipment.user.username}' 通过器具权限管理")
            
            # 2. 检查其他用户的类别权限（该类别下的所有器具）
            from app.models.models import UserCategory, EquipmentCategory
            existing_category = db.query(UserCategory).filter(
                UserCategory.category_id == category_id,
                UserCategory.user_id != user_id
            ).first()
            
            if existing_category:
                category_info = db.query(EquipmentCategory).filter(
                    EquipmentCategory.id == category_id
                ).first()
                if category_info:
                    raise ValueError(f"器具 '{equipment_name}' 所属的类别 '{category_info.name}' 已被用户 '{existing_category.user.username}' 通过类别权限管理")
            
            permission = UserEquipmentPermissionModel(
                user_id=user_id,
                category_id=category_id,
                equipment_name=equipment_name
            )
            db.add(permission)
        
        db.commit()
        return {"message": "User equipment permissions updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/equipment-permissions/{permission_id}")
def delete_equipment_permission(user_id: int, permission_id: int,
                                db: Session = Depends(get_db),
                                current_user: User = Depends(get_current_admin_user)):
    """删除用户的器具权限"""
    from app.models.models import UserEquipmentPermission as UserEquipmentPermissionModel
    
    permission = db.query(UserEquipmentPermissionModel).filter(
        UserEquipmentPermissionModel.id == permission_id,
        UserEquipmentPermissionModel.user_id == user_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()
    
    return {"message": "Equipment permission deleted successfully"}

@router.get("/equipment-counts/{category_id}")
def get_equipment_counts_by_category(category_id: int,
                                   db: Session = Depends(get_db),
                                   current_user: User = Depends(get_current_admin_user)):
    """获取指定类别下每个器具名称对应的实际设备数量"""
    from app.models.models import Equipment, EquipmentCategory
    from sqlalchemy import func
    
    # 获取类别信息及预定义器具名称
    category = db.query(EquipmentCategory).filter(EquipmentCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 获取该类别下每个器具名称的设备数量（只统计在用设备）
    equipment_counts = db.query(
        Equipment.name,
        func.count(Equipment.id).label('count')
    ).filter(
        Equipment.category_id == category_id,
        Equipment.status == "在用"
    ).group_by(Equipment.name).all()
    
    # 创建器具名称到设备数量的映射
    count_map = {name: count for name, count in equipment_counts}
    
    # 为所有预定义器具名称提供数量信息，没有设备的器具数量为0
    predefined_names = category.predefined_names or []
    result = {}
    for equipment_name in predefined_names:
        result[equipment_name] = count_map.get(equipment_name, 0)
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "equipment_counts": result
    }
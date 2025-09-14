#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部系统API接口
提供给外部系统调用的只读接口，支持API Key认证
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.crud import equipment, departments, categories
from app.schemas.schemas import Equipment, Department, EquipmentCategory
import hashlib
import hmac

router = APIRouter()

# API Key验证依赖
async def verify_api_key(x_api_key: str = Header(..., description="API密钥")):
    """验证API Key"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要API密钥"
        )
    
    # 这里可以实现更复杂的API Key验证逻辑
    # 简单示例：检查固定的API Key
    # 生产环境中应该从数据库查询并验证
    valid_api_keys = [
        "api_key_12345",  # 示例API Key
        "external_system_key_2024"  # 另一个示例
    ]
    
    if x_api_key not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥"
        )
    
    return x_api_key

@router.get("/equipment", 
           summary="获取所有设备信息", 
           description="获取系统中所有设备的基本信息，支持分页和筛选",
           response_model=List[Equipment])
async def get_all_equipment(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(1000, description="返回的最大记录数，最大1000"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    category_id: Optional[int] = Query(None, description="类别ID筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    获取所有设备信息
    
    支持的筛选参数：
    - department_id: 按部门筛选
    - category_id: 按类别筛选  
    - status: 按状态筛选（在用、报废、维修中等）
    """
    
    # 限制每次请求的最大数量
    limit = min(limit, 1000)
    
    try:
        # 获取设备列表（不需要用户权限检查）
        equipments = equipment.get_equipments_for_external_api(
            db, 
            skip=skip, 
            limit=limit,
            department_id=department_id,
            category_id=category_id,
            status=status
        )
        
        return equipments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch equipment data: {str(e)}"
        )

@router.get("/equipment/{equipment_id}", 
           summary="获取单个设备详情",
           description="根据设备ID获取设备的详细信息",
           response_model=Equipment)
async def get_equipment_by_id(
    equipment_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """获取单个设备的详细信息"""
    
    try:
        equipment_data = equipment.get_equipment(db, equipment_id)
        if not equipment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipment not found"
            )
        
        return equipment_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch equipment: {str(e)}"
        )

@router.get("/departments",
           summary="获取所有部门信息", 
           description="获取系统中所有部门的信息",
           response_model=List[Department])
async def get_all_departments(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """获取所有部门信息"""
    
    try:
        department_list = departments.get_departments(db)
        return department_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch departments: {str(e)}"
        )

@router.get("/categories",
           summary="获取所有设备类别", 
           description="获取系统中所有设备类别信息",
           response_model=List[EquipmentCategory])
async def get_all_categories(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """获取所有设备类别"""
    
    try:
        category_list = categories.get_categories(db)
        return category_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch categories: {str(e)}"
        )

@router.get("/equipment/by-department/{department_id}",
           summary="获取指定部门的所有设备",
           description="根据部门ID获取该部门下的所有设备",
           response_model=List[Equipment])
async def get_equipment_by_department(
    department_id: int,
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(1000, description="返回的最大记录数"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """获取指定部门的所有设备"""
    
    limit = min(limit, 1000)
    
    try:
        # 先验证部门是否存在
        dept = departments.get_department(db, department_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        # 获取部门设备
        equipments = equipment.get_equipments_for_external_api(
            db,
            skip=skip,
            limit=limit,
            department_id=department_id
        )
        
        return equipments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department equipment: {str(e)}"
        )

@router.get("/stats",
           summary="获取系统统计信息",
           description="获取设备台账的基本统计信息")
async def get_system_stats(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """获取系统统计信息"""
    
    try:
        from app.models.models import Equipment as EquipmentModel
        from sqlalchemy import func
        
        # 统计各种数据
        total_equipment = db.query(func.count(EquipmentModel.id)).scalar()
        active_equipment = db.query(func.count(EquipmentModel.id)).filter(
            EquipmentModel.status == "在用"
        ).scalar()
        total_departments = db.query(func.count()).select_from(
            db.query(EquipmentModel.department_id).distinct()
        ).scalar()
        
        return {
            "total_equipment": total_equipment or 0,
            "active_equipment": active_equipment or 0,
            "total_departments": total_departments or 0,
            "last_updated": datetime.utcnow().isoformat(),
            "api_version": "1.0"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )

@router.get("/health",
           summary="API健康检查",
           description="检查外部API服务的健康状态")
async def health_check():
    """API健康检查，不需要API Key"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Equipment Management External API",
        "version": "1.0"
    }
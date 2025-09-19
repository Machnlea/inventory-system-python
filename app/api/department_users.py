#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门用户API路由
包含部门用户认证、设备查看等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.database import get_db
from app.crud import department_users
from app.schemas.schemas import (
    DepartmentUserLogin, 
    DepartmentUserPasswordChange, 
    DepartmentUserPasswordReset,
    DepartmentUser,
    DepartmentEquipmentSimple,
    DepartmentEquipmentStats,
    DepartmentEquipmentFilter,
    PaginatedDepartmentEquipment,
    DepartmentUserLog,
    Token
)
from app.core.security import create_access_token
from app.api.auth import get_current_user
from app.models.models import User
from typing import List, Optional

router = APIRouter()

# ========== 部门用户认证相关 ==========

@router.post("/login", response_model=Token, summary="部门用户登录")
async def department_user_login(
    user_data: DepartmentUserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    部门用户登录
    - 使用部门名称作为用户名
    - 返回访问令牌
    """
    user = department_users.authenticate_department_user(
        db, user_data.username, user_data.password
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not bool(user.is_active):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用",
        )
    
    access_token_expires = timedelta(minutes=30)  # 部门用户会话时间较短
    access_token = create_access_token(
        data={"sub": user.username, "user_type": "department_user"},
        expires_delta=access_token_expires
    )
    
    # 记录登录日志
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        department_users.create_department_user_log(
            db=db,
            user_id=int(user.id),
            action="login",
            description=f"部门用户 {user.username} 成功登录",
            ip_address=str(ip_address) if ip_address else "",
            user_agent=user_agent
        )
    except Exception as e:
        # 日志记录失败不影响登录流程
        print(f"记录登录日志失败: {e}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/change-password", response_model=dict, summary="部门用户修改密码")
async def change_department_user_password(
    password_data: DepartmentUserPasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    部门用户修改密码
    - 首次登录必须修改密码
    - 验证当前密码
    """
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        department_users.change_department_user_password(
            db,
            int(current_user.id),
            password_data.current_password,
            password_data.new_password
        )
        
        # 记录密码修改日志
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            department_users.create_department_user_log(
                db=db,
                user_id=int(current_user.id),
                action="password_change",
                description=f"部门用户 {current_user.username} 修改了密码",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录密码修改日志失败: {e}")
        
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/profile", response_model=DepartmentUser, summary="获取当前部门用户信息")
async def get_department_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前登录的部门用户信息"""
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    user = department_users.get_department_user_by_id(db, int(current_user.id))
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user

# ========== 部门设备查看相关 ==========

@router.get("/equipment/stats", response_model=DepartmentEquipmentStats, summary="获取部门设备统计信息")
async def get_department_equipment_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门设备统计信息"""
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    stats = department_users.get_department_equipment_stats(db, int(current_user.department_id))
    return stats

@router.get("/equipment/list", response_model=PaginatedDepartmentEquipment, summary="获取部门设备列表")
async def get_department_equipment_list(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    equipment_name: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取部门设备列表
    - 支持分页
    - 支持按设备名称、状态筛选
    - 支持按名称搜索
    """
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 构建筛选条件
    filters = DepartmentEquipmentFilter(
        equipment_name=equipment_name,
        status=status,
        search=search
    )
    
    result = department_users.get_department_equipment_list(
        db,
        int(current_user.department_id),
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    # 记录查看设备列表日志（仅当不是分页请求时记录，避免过多日志）
    if skip == 0:  # 只在第一页时记录
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            filter_info = ""
            if equipment_name:
                filter_info += f" 设备名称:{equipment_name}"
            if status:
                filter_info += f" 状态:{status}"
            if search:
                filter_info += f" 搜索:{search}"
            
            department_users.create_department_user_log(
                db=db,
                user_id=int(current_user.id),
                action="view_equipment_list",
                description=f"部门用户 {current_user.username} 查看了设备列表{filter_info}",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录查看设备列表日志失败: {e}")
    
    return result

@router.get("/equipment-names", summary="获取部门设备名称列表")
async def get_department_equipment_names(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门拥有的设备名称列表（用于筛选）"""
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    equipment_names = department_users.get_department_equipment_names(db, int(current_user.department_id))
    return equipment_names

@router.get("/categories", summary="获取部门设备类别列表")
async def get_department_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门拥有的设备类别列表（用于筛选）"""
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    categories = department_users.get_department_categories(db, int(current_user.department_id))
    return categories

@router.get("/equipment/export", summary="导出部门设备清单")
async def export_department_equipment(
    request: Request,
    status: Optional[str] = None,
    equipment_name: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出部门设备清单为Excel文件
    """
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    import pandas as pd
    from datetime import datetime
    
    print(f"Export API called with: status={status}, equipment_name={equipment_name}, search={search}")
    print(f"Current user: {current_user.username}, type: {current_user.user_type}")
    
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        # 构建筛选条件 - 导出时不筛选状态，获取所有设备
        filters = DepartmentEquipmentFilter(
            equipment_name=equipment_name,
            status=None,  # 强制为None，确保导出所有状态的设备
            search=search
        )
        print(f"Filters created successfully: {filters}")
        
        # 获取所有符合条件的设备（不分页，不筛选状态）
        result = department_users.get_department_equipment_list(
            db,
            int(current_user.department_id),
            skip=0,
            limit=10000,  # 大数值获取全部
            filters=filters
        )
        
        print(f"Found {result['total']} equipment items (including all statuses)")
        
        
        # 准备Excel数据
        data = []
        for equipment in result['items']:
            data.append({
                '设备名称': equipment.name,
                '型号规格': equipment.model,
                '内部编号': equipment.internal_id,
                '设备类别': equipment.category.name,
                '部门': equipment.department.name,
                '准确度等级': equipment.accuracy_level or '',
                '测量范围': equipment.measurement_range or '',
                '检定周期': equipment.calibration_cycle or '',
                '检定日期': equipment.calibration_date or '',
                '有效期至': equipment.valid_until or '',
                '检定方式': equipment.calibration_method or '',
                '制造厂家': equipment.manufacturer or '',
                '出厂日期': equipment.manufacture_date or '',
                '出厂编号': equipment.manufacturer_id or '',
                '安装地点': equipment.installation_location or '',
                '原值(元)': equipment.original_value or '',
                '分度值': equipment.scale_value or '',
                '设备状态': equipment.status or '',
            })
        
        # 创建Excel文件
        df = pd.DataFrame(data)
        
        # 创建BytesIO对象
        output = BytesIO()
        
        # 使用pandas的ExcelWriter
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='设备清单', index=False)
            
            # 获取工作表进行样式设置
            worksheet = writer.sheets['设备清单']
            
            # 设置列宽
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # 生成文件名
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        department_name = current_user.department.name if hasattr(current_user, 'department') else current_user.username
        filename = f"{department_name}_设备清单_{current_time}.xlsx"
        
        # 对文件名进行URL编码以支持中文
        from urllib.parse import quote
        encoded_filename = quote(filename.encode('utf-8'))
        
        print(f"Generated Excel file: {filename} with {len(data)} rows")
        
        # 记录导出日志
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            filter_info = ""
            if equipment_name:
                filter_info += f" 设备名称:{equipment_name}"
            if search:
                filter_info += f" 搜索:{search}"
            
            department_users.create_department_user_log(
                db=db,
                user_id=int(current_user.id),
                action="export_equipment",
                description=f"部门用户 {current_user.username} 导出了设备清单({len(data)}条记录){filter_info}",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录导出日志失败: {e}")
        
        # 返回文件流
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except Exception as e:
        print(f"Error in export: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )

@router.get("/equipment/{equipment_id}", response_model=DepartmentEquipmentSimple, summary="获取部门设备详情")
async def get_department_equipment_detail(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门设备详情"""
    if str(current_user.user_type) != "department_user":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    equipment = department_users.get_department_equipment_by_id(
        db, equipment_id, int(current_user.department_id)
    )
    if not equipment:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="设备不存在或不属于您的部门"
        )
    
    return equipment


# ========== 管理员管理部门用户相关 ==========

@router.post("/admin/create", response_model=DepartmentUser, summary="管理员创建部门用户")
async def admin_create_department_user(
    department_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员为部门创建用户账户"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        user = department_users.create_department_user(db, department_id)
        
        # 记录创建部门用户日志
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            department_users.create_department_user_log(
                db=db,
                user_id=int(user.id),
                action="user_created",
                description=f"管理员 {current_user.username} 创建了部门用户 {user.username}",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录创建用户日志失败: {e}")
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/admin/reset-password", response_model=dict, summary="管理员重置部门用户密码")
async def admin_reset_department_user_password(
    reset_data: DepartmentUserPasswordReset,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员重置部门用户密码"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        # 获取要重置密码的用户信息
        target_user = db.query(User).filter(User.id == reset_data.user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        department_users.admin_reset_department_user_password(
            db, reset_data.user_id, reset_data.new_password
        )
        
        # 记录重置密码日志
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            department_users.create_department_user_log(
                db=db,
                user_id=reset_data.user_id,
                action="password_reset",
                description=f"管理员 {current_user.username} 重置了部门用户 {target_user.username} 的密码",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录密码重置日志失败: {e}")
        
        return {"message": "密码重置成功，用户下次登录需修改密码"}
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/admin/status/{user_id}", response_model=dict, summary="管理员更新部门用户状态")
async def admin_update_department_user_status(
    user_id: int,
    is_active: bool,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员启用或禁用部门用户"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        user = department_users.update_department_user_status(db, user_id, is_active)
        action = "启用" if is_active else "禁用"
        
        # 记录状态变更日志
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            department_users.create_department_user_log(
                db=db,
                user_id=int(user.id),
                action="status_change",
                description=f"管理员 {current_user.username} {action}了部门用户 {user.username}",
                ip_address=str(ip_address) if ip_address else "",
                user_agent=user_agent
            )
        except Exception as e:
            print(f"记录状态变更日志失败: {e}")
        
        return {
            "success": True,
            "message": f"用户{action}成功",
            "user": {
                "id": int(user.id),
                "username": user.username,
                "is_active": bool(user.is_active),
                "user_type": str(user.user_type),
                "department_id": int(user.department_id),
                "last_login": user.last_login,
                "created_at": user.created_at
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/admin/list", response_model=List[DepartmentUser], summary="管理员获取所有部门用户")
async def admin_get_all_department_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员获取所有部门用户列表"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    users = department_users.get_all_department_users(db, skip=skip, limit=limit)
    return users

@router.delete("/admin/{user_id}", response_model=dict, summary="管理员删除部门用户")
async def admin_delete_department_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员删除部门用户"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        department_users.delete_department_user(db, user_id)
        return {"message": "部门用户删除成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/admin/logs/{user_id}", response_model=List[DepartmentUserLog], summary="管理员获取部门用户操作日志")
async def admin_get_department_user_logs(
    user_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员获取部门用户的操作日志"""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        logs = department_users.get_department_user_logs(db, user_id, limit)
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取操作日志失败: {str(e)}"
        )
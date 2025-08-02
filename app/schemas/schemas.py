from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

# 用户相关
class UserBase(BaseModel):
    username: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 设备类别相关
class EquipmentCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class EquipmentCategoryCreate(EquipmentCategoryBase):
    pass

class EquipmentCategory(EquipmentCategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 部门相关
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 设备相关
class EquipmentBase(BaseModel):
    department_id: int
    category_id: int
    name: str
    model: str
    accuracy_level: str
    measurement_range: Optional[str] = None
    calibration_cycle: str  # "1年" 或 "2年"
    calibration_date: date
    calibration_method: Optional[str] = None
    serial_number: str
    installation_location: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[date] = None
    status: str = "在用"
    status_change_date: Optional[str] = None  # 添加状态变更时间字段
    notes: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    name: Optional[str] = None
    model: Optional[str] = None
    accuracy_level: Optional[str] = None
    measurement_range: Optional[str] = None
    calibration_cycle: Optional[str] = None
    calibration_date: Optional[date] = None
    calibration_method: Optional[str] = None
    serial_number: Optional[str] = None
    installation_location: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[date] = None
    status: Optional[str] = None
    status_change_date: Optional[str] = None  # 添加状态变更时间字段
    notes: Optional[str] = None

class Equipment(EquipmentBase):
    id: int
    next_calibration_date: date
    status_change_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    department: Department
    category: EquipmentCategory
    
    class Config:
        from_attributes = True

# 用户权限关联
class UserCategoryCreate(BaseModel):
    user_id: int
    category_id: int

class UserCategory(BaseModel):
    id: int
    user_id: int
    category_id: int
    category: EquipmentCategory
    
    class Config:
        from_attributes = True

# 操作日志
class AuditLogBase(BaseModel):
    action: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    equipment_id: Optional[int] = None
    created_at: datetime
    user: User
    
    class Config:
        from_attributes = True

# 认证相关
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 筛选和统计相关
class EquipmentFilter(BaseModel):
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    next_calibration_start: Optional[date] = None
    next_calibration_end: Optional[date] = None

class DashboardStats(BaseModel):
    monthly_due_count: int
    overdue_count: int
    inactive_count: int
    category_distribution: List[dict]

# 数据导入/导出
class ImportTemplate(BaseModel):
    filename: str
    url: str
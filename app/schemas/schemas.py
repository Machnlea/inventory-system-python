from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# 用户相关
class UserBase(BaseModel):
    username: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is None:
            return v
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 设备类别相关
class EquipmentCategoryBase(BaseModel):
    name: str
    category_code: str
    description: Optional[str] = None
    predefined_names: Optional[List[str]] = None
    
    @model_validator(mode='after')
    def validate_category_code(self):
        if not self.category_code or len(self.category_code) != 3:
            raise ValueError("类别代码必须是3个字符")
        if not self.category_code.isalnum():
            raise ValueError("类别代码只能包含字母和数字")
        return self

class EquipmentCategoryCreate(EquipmentCategoryBase):
    pass

class EquipmentCategory(EquipmentCategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    # 为了兼容数据库中的code字段，我们需要进行字段映射
    @model_validator(mode='before')
    @classmethod
    def map_fields(cls, data):
        if isinstance(data, dict):
            # 如果数据库返回的是code字段，映射为category_code
            if 'code' in data and 'category_code' not in data:
                data['category_code'] = data.pop('code')
        return data

# 部门相关
class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_department_code(self):
        if not self.code or len(self.code) != 2:
            raise ValueError("部门代码必须是2个字符")
        if not self.code.isalnum():
            raise ValueError("部门代码只能包含字母和数字")
        return self

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
    calibration_cycle: str  # "6个月", "12个月", "24个月", "36个月" 或 "随坏随换"
    calibration_date: Optional[date] = None  # 当检定周期不是"随坏随换"时必填
    calibration_method: str
    
    # 外检相关字段
    certificate_number: Optional[str] = None
    verification_result: Optional[str] = None
    verification_agency: Optional[str] = None
    certificate_form: Optional[str] = None
    internal_id: Optional[str] = None  # 内部编号 (自动生成)
    manufacturer_id: Optional[str] = None  # 厂家编号/序列号
    installation_location: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[date] = None
    scale_value: Optional[str] = None
    management_level: Optional[str] = None  # 管理级别
    original_value: Optional[float] = None  # 原值/元
    status: str = "在用"
    status_change_date: Optional[date] = None  # 状态变更时间
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_equipment_fields(self):
        # 验证检定周期
        valid_cycles = ["6个月", "12个月", "24个月", "36个月", "随坏随换"]
        if self.calibration_cycle not in valid_cycles:
            raise ValueError(f"检定周期必须是: {', '.join(valid_cycles)}")
        
        # 验证检定日期：当检定周期不是"随坏随换"时必填
        if self.calibration_cycle != "随坏随换" and not self.calibration_date:
            raise ValueError("当检定周期不是'随坏随换'时，检定日期为必填项")
        
        # 验证外检字段：当检定方式为"外检"时必填
        if self.calibration_method == "外检":
            if not self.certificate_form:
                raise ValueError("外检设备必须填写证书形式")
            if self.certificate_form not in ["校准证书", "检定证书"]:
                raise ValueError("证书形式必须是'校准证书'或'检定证书'")
            if not self.certificate_number:
                raise ValueError("外检设备必须填写证书编号")
            if not self.verification_result:
                raise ValueError("外检设备必须填写检定结果")
            if not self.verification_agency:
                raise ValueError("外检设备必须填写检定机构")
        
        # 状态变更时间：当状态为"停用"或"报废"时可选填，如果提供需要验证格式
        # 注：根据新需求，状态变更时间不再是必填项
        
        return self

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
    certificate_number: Optional[str] = None
    verification_result: Optional[str] = None
    verification_agency: Optional[str] = None
    certificate_form: Optional[str] = None
    internal_id: Optional[str] = None  # 内部编号 (自动生成)
    manufacturer_id: Optional[str] = None  # 厂家编号/序列号
    installation_location: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[date] = None
    scale_value: Optional[str] = None
    management_level: Optional[str] = None  # 管理级别
    original_value: Optional[float] = None  # 原值/元
    status: Optional[str] = None
    status_change_date: Optional[date] = None  # 状态变更时间
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_equipment_update_fields(self):
        # 验证检定周期（如果提供）
        if self.calibration_cycle:
            valid_cycles = ["6个月", "12个月", "24个月", "36个月", "随坏随换"]
            if self.calibration_cycle not in valid_cycles:
                raise ValueError(f"检定周期必须是: {', '.join(valid_cycles)}")
        
        # 验证检定日期：当检定周期不是"随坏随换"时必填
        if self.calibration_cycle and self.calibration_cycle != "随坏随换" and not self.calibration_date:
            raise ValueError("当检定周期不是'随坏随换'时，检定日期为必填项")
        
        # 验证外检字段：当检定方式为"外检"时必填
        if self.calibration_method == "外检":
            if not self.certificate_form:
                raise ValueError("外检设备必须填写证书形式")
            if self.certificate_form not in ["校准证书", "检定证书"]:
                raise ValueError("证书形式必须是'校准证书'或'检定证书'")
            if not self.certificate_number:
                raise ValueError("外检设备必须填写证书编号")
            if not self.verification_result:
                raise ValueError("外检设备必须填写检定结果")
            if not self.verification_agency:
                raise ValueError("外检设备必须填写检定机构")
        
        # 状态变更时间：当状态为"停用"或"报废"时可选填，如果提供需要验证格式
        # 注：根据新需求，状态变更时间不再是必填项
        
        return self

class Equipment(EquipmentBase):
    id: int
    valid_until: Optional[date] = None
    status_change_date: Optional[date] = None
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

# 器具权限相关
class UserEquipmentPermissionBase(BaseModel):
    user_id: int
    category_id: int
    equipment_name: str

class UserEquipmentPermissionCreate(UserEquipmentPermissionBase):
    pass

class UserEquipmentPermission(UserEquipmentPermissionBase):
    id: int
    
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
    equipment: Optional[Equipment] = None
    
    class Config:
        from_attributes = True

# 认证相关
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 分页响应
class PaginatedEquipment(BaseModel):
    items: List[Equipment]
    total: int
    skip: int
    limit: int

class PaginatedAuditLog(BaseModel):
    items: List[AuditLog]
    total: int
    skip: int
    limit: int

# 筛选和统计相关
class EquipmentFilter(BaseModel):
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    next_calibration_start: Optional[date] = None
    next_calibration_end: Optional[date] = None

class EquipmentSearch(BaseModel):
    query: str
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    next_calibration_start: Optional[date] = None
    next_calibration_end: Optional[date] = None

class DashboardStats(BaseModel):
    total_equipment_count: int
    active_equipment_count: int
    monthly_due_count: int
    overdue_count: int
    inactive_count: int
    category_distribution: List[dict]
    department_distribution: List[dict]

# 数据导入/导出
class ImportTemplate(BaseModel):
    filename: str
    url: str

# 设备附件相关
class EquipmentAttachmentBase(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None
    is_certificate: bool = False
    certificate_type: Optional[str] = None

class EquipmentAttachmentCreate(EquipmentAttachmentBase):
    equipment_id: int

class EquipmentAttachmentUpdate(BaseModel):
    description: Optional[str] = None
    is_certificate: Optional[bool] = None
    certificate_type: Optional[str] = None

class EquipmentAttachment(EquipmentAttachmentBase):
    id: int
    equipment_id: int
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
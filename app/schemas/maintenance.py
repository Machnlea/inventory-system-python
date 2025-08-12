from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class MaintenanceRecordBase(BaseModel):
    equipment_id: int = Field(..., description="设备ID")
    maintenance_type: str = Field(..., description="维护类型：定期维护/故障维修/校准/其他")
    maintenance_date: date = Field(..., description="维护日期")
    maintenance_person: str = Field(..., description="维护人员")
    maintenance_company: Optional[str] = Field(None, description="维护公司")
    description: str = Field(..., description="维护描述")
    result: str = Field(..., description="维护结果")
    cost: Optional[float] = Field(None, description="维护成本")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    notes: Optional[str] = Field(None, description="备注")

class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass

class MaintenanceRecordUpdate(BaseModel):
    maintenance_type: Optional[str] = Field(None, description="维护类型")
    maintenance_date: Optional[date] = Field(None, description="维护日期")
    maintenance_person: Optional[str] = Field(None, description="维护人员")
    maintenance_company: Optional[str] = Field(None, description="维护公司")
    description: Optional[str] = Field(None, description="维护描述")
    result: Optional[str] = Field(None, description="维护结果")
    cost: Optional[float] = Field(None, description="维护成本")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    notes: Optional[str] = Field(None, description="备注")

class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class MaintenanceAttachmentBase(BaseModel):
    maintenance_id: int = Field(..., description="维护记录ID")
    filename: str = Field(..., description="文件名")
    original_filename: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    file_type: Optional[str] = Field(None, description="文件类型")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    description: Optional[str] = Field(None, description="文件描述")

class MaintenanceAttachmentCreate(MaintenanceAttachmentBase):
    pass

class MaintenanceAttachmentResponse(MaintenanceAttachmentBase):
    id: int
    uploaded_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True
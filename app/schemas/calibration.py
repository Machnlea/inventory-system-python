"""
检定历史记录相关数据模式
定义API请求和响应的数据结构
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


class CalibrationHistoryBase(BaseModel):
    """检定历史记录基础模式"""
    equipment_id: int = Field(..., description="设备ID")
    calibration_date: date = Field(..., description="检定日期")
    valid_until: date = Field(..., description="有效期至")
    calibration_method: str = Field(..., description="检定方式", pattern="^(内检|外检)$")
    calibration_result: str = Field(..., description="检定结果", pattern="^(合格|不合格)$")
    certificate_number: Optional[str] = Field(None, description="证书编号", max_length=100)
    certificate_form: Optional[str] = Field(None, description="证书形式", max_length=50)
    verification_result: Optional[str] = Field(None, description="检定结果描述", max_length=100)
    verification_agency: Optional[str] = Field(None, description="检定机构", max_length=100)
    notes: Optional[str] = Field(None, description="检定备注")

    @validator('valid_until')
    def validate_valid_until(cls, v, values):
        """验证有效期不能早于检定日期"""
        if 'calibration_date' in values and v < values['calibration_date']:
            raise ValueError('有效期不能早于检定日期')
        return v

    @validator('certificate_number')
    def validate_certificate_number_for_external(cls, v, values):
        """外检设备的证书编号必填验证"""
        if values.get('calibration_method') == '外检' and not v:
            raise ValueError('外检设备的证书编号为必填项')
        return v

    @validator('verification_agency')
    def validate_verification_agency_for_external(cls, v, values):
        """外检设备的检定机构必填验证"""
        if values.get('calibration_method') == '外检' and not v:
            raise ValueError('外检设备的检定机构为必填项')
        return v

    @validator('certificate_form')
    def validate_certificate_form_for_external(cls, v, values):
        """外检设备的证书形式必填验证"""
        if values.get('calibration_method') == '外检' and not v:
            raise ValueError('外检设备的证书形式为必填项')
        return v


class CalibrationHistoryCreate(CalibrationHistoryBase):
    """创建检定历史记录模式"""
    pass


class CalibrationHistoryUpdate(BaseModel):
    """更新检定历史记录模式"""
    calibration_date: Optional[date] = None
    valid_until: Optional[date] = None
    calibration_method: Optional[str] = Field(None, pattern="^(内检|外检)$")
    calibration_result: Optional[str] = Field(None, pattern="^(合格|不合格)$")
    certificate_number: Optional[str] = Field(None, max_length=100)
    certificate_form: Optional[str] = Field(None, max_length=50)
    verification_result: Optional[str] = Field(None, max_length=100)
    verification_agency: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class CalibrationHistoryResponse(CalibrationHistoryBase):
    """检定历史记录响应模式"""
    id: int
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class CalibrationHistoryWithDetails(CalibrationHistoryResponse):
    """带详细信息的检定历史记录"""
    # 设备信息
    equipment_name: Optional[str] = None
    equipment_internal_id: Optional[str] = None
    equipment_model: Optional[str] = None
    department_name: Optional[str] = None
    category_name: Optional[str] = None
    
    # 创建者信息
    creator_username: Optional[str] = None

    class Config:
        from_attributes = True


class CalibrationStatistics(BaseModel):
    """检定统计信息模式"""
    total_count: int = Field(..., description="总检定记录数")
    method_distribution: dict = Field(..., description="按检定方式分布")
    result_distribution: dict = Field(..., description="按检定结果分布")
    recent_count: int = Field(..., description="近期检定数量")


class CalibrationUpdateRequest(BaseModel):
    """设备检定信息更新请求模式"""
    # 基础检定信息
    calibration_date: date = Field(..., description="检定日期")
    calibration_result: str = Field("合格", description="检定结果", pattern="^(合格|不合格)$")
    
    # 内检外检共有字段
    certificate_number: Optional[str] = Field(None, description="证书编号", max_length=100)
    certificate_form: Optional[str] = Field(None, description="证书形式", max_length=50)
    notes: Optional[str] = Field(None, description="检定备注")
    
    # 外检专有字段
    verification_result: Optional[str] = Field(None, description="检定结果描述", max_length=100)
    verification_agency: Optional[str] = Field(None, description="检定机构", max_length=100)
    
    # 报废相关字段（检定不合格时）
    status_change_date: Optional[date] = Field(None, description="状态变更时间")
    disposal_reason: Optional[str] = Field(None, description="报废原因")

    @validator('status_change_date')
    def validate_status_change_date_when_failed(cls, v, values):
        """检定不合格时状态变更时间必填"""
        if values.get('calibration_result') == '不合格' and not v:
            raise ValueError('检定不合格时状态变更时间为必填项')
        return v

    @validator('verification_result')
    def validate_verification_result_for_external(cls, v, values, **kwargs):
        """外检设备的检定结果描述必填验证（需要设备信息）"""
        # 这个验证需要在业务逻辑层进行，因为需要查询设备的检定方式
        return v


class BatchCalibrationUpdateRequest(BaseModel):
    """批量检定更新请求模式"""
    equipment_ids: List[int] = Field(..., description="设备ID列表")
    calibration_updates: List[CalibrationUpdateRequest] = Field(..., description="检定更新信息列表")

    @validator('calibration_updates')
    def validate_updates_count(cls, v, values):
        """验证更新信息数量与设备数量匹配"""
        equipment_ids = values.get('equipment_ids', [])
        if len(v) != len(equipment_ids):
            raise ValueError('检定更新信息数量必须与设备数量匹配')
        return v


class CalibrationDueReminder(BaseModel):
    """检定到期提醒模式"""
    equipment_id: int
    equipment_name: str
    internal_id: str
    department_name: str
    calibration_date: date
    valid_until: date
    days_until_due: int

    class Config:
        from_attributes = True


class CalibrationHistoryFilter(BaseModel):
    """检定历史记录过滤条件"""
    equipment_id: Optional[int] = None
    calibration_method: Optional[str] = Field(None, pattern="^(内检|外检)$")
    calibration_result: Optional[str] = Field(None, pattern="^(合格|不合格)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

    @validator('end_date')
    def validate_date_range(cls, v, values):
        """验证日期范围"""
        start_date = values.get('start_date')
        if start_date and v and v < start_date:
            raise ValueError('结束日期不能早于开始日期')
        return v
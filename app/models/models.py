from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 用户权限关联
    user_categories = relationship("UserCategory", back_populates="user")

class EquipmentCategory(Base):
    __tablename__ = "equipment_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # 类别代码
    description = Column(Text)
    predefined_names = Column(JSON)  # 预定义器具名称列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    equipments = relationship("Equipment", back_populates="category")
    user_categories = relationship("UserCategory", back_populates="category")
    
    # 为了兼容API的字段名，添加category_code属性
    @property
    def category_code(self):
        return self.code
    
    @category_code.setter
    def category_code(self, value):
        self.code = value

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # 部门代码
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    equipments = relationship("Equipment", back_populates="department")

class UserCategory(Base):
    __tablename__ = "user_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"), nullable=False)
    
    # 关联
    user = relationship("User", back_populates="user_categories")
    category = relationship("EquipmentCategory", back_populates="user_categories")

class Equipment(Base):
    __tablename__ = "equipments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 计量器具名称
    model = Column(String(100), nullable=False)  # 型号/规格
    accuracy_level = Column(String(50), nullable=False)  # 准确度等级
    measurement_range = Column(String(100))  # 测量范围
    
    # 检定信息
    calibration_cycle = Column(String(10), nullable=False)  # 检定周期(6个月/12个月/24个月/随坏随换)
    calibration_date = Column(Date)  # 检定日期(当检定周期不是"随坏随换"时必填)
    valid_until = Column(Date)  # 有效期至(根据检定周期自动计算)
    calibration_method = Column(String(50), nullable=False)  # 检定方式
    
    # 外检相关字段
    certificate_number = Column(String(100))  # 证书编号
    verification_result = Column(String(100))  # 检定结果
    verification_agency = Column(String(100))  # 检定机构
    certificate_form = Column(String(50))  # 证书形式
    
    # 设备信息
    internal_id = Column(String(20), unique=True, nullable=False)  # 内部编号 (自动生成)
    manufacturer_id = Column(String(100))  # 厂家编号/序列号
    installation_location = Column(String(100))  # 安装地点
    manufacturer = Column(String(100))  # 制造厂家
    manufacture_date = Column(Date)  # 出厂日期
    
    # 扩展字段
    scale_value = Column(String(50))  # 分度值
    management_level = Column(String(20))  # 管理级别
    original_value = Column(Float)  # 原值/元
    
    # 状态信息
    status = Column(String(20), default="在用")  # 设备状态：在用/停用/报废
    status_change_date = Column(Date)  # 状态变更时间
    notes = Column(Text)  # 备注
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联
    department = relationship("Department", back_populates="equipments")
    category = relationship("EquipmentCategory", back_populates="equipments")
    audit_logs = relationship("AuditLog", back_populates="equipment")
    attachments = relationship("EquipmentAttachment", back_populates="equipment")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    action = Column(String(50), nullable=False)  # 操作类型
    description = Column(Text, nullable=False)  # 操作描述
    old_value = Column(Text)  # 旧值
    new_value = Column(Text)  # 新值
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    user = relationship("User")
    equipment = relationship("Equipment", back_populates="audit_logs")


class EquipmentAttachment(Base):
    __tablename__ = "equipment_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # 文件大小（字节）
    file_type = Column(String(50))  # 文件类型：PDF, JPG, PNG, DOCX等
    mime_type = Column(String(100))  # MIME类型
    description = Column(Text)  # 文件描述
    is_certificate = Column(Boolean, default=False)  # 是否为证书文件
    certificate_type = Column(String(50))  # 证书类型：检定证书/校准证书
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联
    equipment = relationship("Equipment", back_populates="attachments")
    uploader = relationship("User")
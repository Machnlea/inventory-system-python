from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Boolean
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
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    equipments = relationship("Equipment", back_populates="category")
    user_categories = relationship("UserCategory", back_populates="category")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
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
    calibration_cycle = Column(String(10), nullable=False)  # 检定周期(半年/1年/2年)
    calibration_date = Column(Date, nullable=False)  # 检定日期
    next_calibration_date = Column(Date, nullable=False)  # 下次检定日期
    calibration_method = Column(String(50))  # 检定方式
    
    # 设备信息
    serial_number = Column(String(100), unique=True, nullable=False)  # 计量编号
    installation_location = Column(String(100))  # 安装地点
    manufacturer = Column(String(100))  # 制造厂家
    manufacture_date = Column(Date)  # 出厂日期
    
    # 扩展字段
    scale_value = Column(String(50))  # 分度值
    
    # 状态信息
    status = Column(String(20), default="在用")  # 设备状态：在用/停用/报废
    status_change_date = Column(DateTime(timezone=True))  # 状态变更时间
    notes = Column(Text)  # 备注
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联
    department = relationship("Department", back_populates="equipments")
    category = relationship("EquipmentCategory", back_populates="equipments")
    audit_logs = relationship("AuditLog", back_populates="equipment")

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
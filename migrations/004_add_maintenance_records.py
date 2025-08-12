"""
添加维护记录表和相关功能
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class MaintenanceRecord(Base):
    """维护记录表"""
    __tablename__ = "maintenance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    maintenance_type = Column(String(50), nullable=False)  # 定期维护、故障维修、校准、其他
    maintenance_date = Column(Date, nullable=False)
    maintenance_person = Column(String(100), nullable=False)
    maintenance_company = Column(String(100))
    description = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    cost = Column(Float)
    next_maintenance_date = Column(Date)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MaintenanceAttachment(Base):
    """维护记录附件表"""
    __tablename__ = "maintenance_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_records.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    mime_type = Column(String(100))
    description = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
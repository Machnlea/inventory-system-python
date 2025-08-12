#!/usr/bin/env python3
"""
Add equipment attachments table to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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

def main():
    # Create the table
    from app.db.database import engine
    EquipmentAttachment.metadata.create_all(bind=engine)
    print("Equipment attachments table created successfully")

if __name__ == "__main__":
    main()
"""
Add equipment attachments table migration
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


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


def upgrade():
    """Add equipment_attachments table to the database"""
    
    # Import here to avoid circular imports
    from app.db.database import engine
    from app.models.models import Base
    
    # Create the table
    EquipmentAttachment.metadata.create_all(bind=engine)
    
    print("Equipment attachments table created successfully")


def downgrade():
    """Remove equipment_attachments table from the database"""
    
    # Import here to avoid circular imports
    from app.db.database import engine
    from app.models.models import Base
    
    # Drop the table
    EquipmentAttachment.metadata.drop_all(bind=engine)
    
    print("Equipment attachments table dropped successfully")


if __name__ == "__main__":
    upgrade()
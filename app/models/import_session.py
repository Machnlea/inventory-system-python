"""
导入会话模型
用于跟踪和管理批量导入操作的进度和状态
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from datetime import datetime

from app.db.database import Base


class ImportStatus(str, enum.Enum):
    """导入状态枚举"""
    PENDING = "pending"        # 等待处理
    PROCESSING = "processing"  # 正在处理
    PAUSED = "paused"         # 已暂停
    CANCELLED = "cancelled"   # 已取消
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败


class ImportSession(Base):
    """导入会话表"""
    __tablename__ = "import_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    user_id = Column(Integer, nullable=False, comment="操作用户ID")
    filename = Column(String(255), nullable=False, comment="导入文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")

    # 状态信息
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PENDING, nullable=False, comment="导入状态")
    progress = Column(Integer, default=0, nullable=False, comment="处理进度（百分比）")

    # 处理统计
    total_rows = Column(Integer, default=0, nullable=False, comment="总行数")
    processed_rows = Column(Integer, default=0, nullable=False, comment="已处理行数")
    success_count = Column(Integer, default=0, nullable=False, comment="成功导入数量")
    update_count = Column(Integer, default=0, nullable=False, comment="更新设备数量")
    error_count = Column(Integer, default=0, nullable=False, comment="错误数量")

    # 详细结果
    detailed_results = Column(JSON, nullable=True, comment="详细处理结果")
    error_details = Column(JSON, nullable=True, comment="错误详情")

    # 配置选项
    overwrite_existing = Column(Boolean, default=False, nullable=False, comment="是否覆盖已存在的设备")
    batch_size = Column(Integer, default=50, nullable=False, comment="批处理大小")

    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始处理时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")

    # 其他信息
    notes = Column(Text, nullable=True, comment="备注信息")
    error_message = Column(Text, nullable=True, comment="错误信息")

    def __repr__(self):
        return f"<ImportSession(id={self.id}, filename='{self.filename}', status='{self.status}', progress={self.progress}%)>"

    @property
    def is_active(self) -> bool:
        """检查会话是否处于活跃状态"""
        return self.status in [ImportStatus.PENDING, ImportStatus.PROCESSING, ImportStatus.PAUSED]

    @property
    def duration(self) -> float:
        """获取处理持续时间（秒）"""
        if not self.started_at:
            return 0

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def success_rate(self) -> float:
        """获取成功率"""
        if self.processed_rows == 0:
            return 0
        return (self.success_count + self.update_count) / self.processed_rows * 100

    def get_summary(self) -> dict:
        """获取处理摘要"""
        return {
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "success_count": self.success_count,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "progress": self.progress,
            "status": self.status,
            "success_rate": self.success_rate,
            "duration": self.duration
        }
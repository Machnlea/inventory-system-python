from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImportJobStatus(BaseModel):
    id: str
    uploader_id: int
    filename: str
    status: str
    progress: int
    total_rows: int
    processed_rows: int
    error_summary: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_report_url: Optional[str] = None
    can_cancel: bool = False

    class Config:
        from_attributes = True

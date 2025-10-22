from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.models.models import ImportJob


def create_job(db: Session, job_id: str, uploader_id: int, filename: str) -> ImportJob:
    job = ImportJob(
        id=job_id,
        uploader_id=int(uploader_id),
        filename=filename,
        status="queued",
        progress=0,
        total_rows=0,
        processed_rows=0,
        error_summary=None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Optional[ImportJob]:
    return db.query(ImportJob).filter(ImportJob.id == job_id).first()


def set_status(
    db: Session,
    job_id: str,
    status: str,
    *,
    progress: Optional[int] = None,
    processed_rows: Optional[int] = None,
    total_rows: Optional[int] = None,
    error_summary: Optional[str] = None,
    set_started: bool = False,
    set_finished: bool = False,
) -> Optional[ImportJob]:
    job = get_job(db, job_id)
    if not job:
        return None
    job.status = status
    if progress is not None:
        job.progress = int(progress)
    if processed_rows is not None:
        job.processed_rows = int(processed_rows)
    if total_rows is not None:
        job.total_rows = int(total_rows)
    if error_summary is not None:
        job.error_summary = error_summary
    if set_started and job.started_at is None:
        job.started_at = datetime.now()
    if set_finished:
        job.finished_at = datetime.now()
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_progress(
    db: Session,
    job_id: str,
    processed_rows: int,
    total_rows: Optional[int] = None,
    *,
    status: Optional[str] = None,
    error_summary: Optional[str] = None,
):
    job = get_job(db, job_id)
    if not job:
        return None
    if total_rows is not None:
        job.total_rows = int(total_rows)
    job.processed_rows = int(processed_rows)
    if job.total_rows:
        job.progress = min(100, int(processed_rows * 100 / job.total_rows))
    if status:
        job.status = status
    if error_summary is not None:
        job.error_summary = error_summary
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

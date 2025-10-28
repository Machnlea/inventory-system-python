"""
导入会话 CRUD 操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.import_session import ImportSession, ImportStatus
from app.schemas.schemas import ImportSessionCreate, ImportSessionUpdate


def create_import_session(db: Session, session_data: ImportSessionCreate) -> ImportSession:
    """创建导入会话"""
    import_session = ImportSession(
        user_id=session_data.user_id,
        filename=session_data.filename,
        file_size=session_data.file_size,
        overwrite_existing=session_data.overwrite_existing,
        batch_size=session_data.batch_size,
        notes=session_data.notes
    )

    db.add(import_session)
    db.commit()
    db.refresh(import_session)
    return import_session


def get_import_session(db: Session, session_id: int) -> Optional[ImportSession]:
    """获取导入会话"""
    return db.query(ImportSession).filter(ImportSession.id == session_id).first()


def get_user_import_sessions(
    db: Session,
    user_id: Optional[int],
    skip: int = 0,
    limit: int = 100,
    status: Optional[ImportStatus] = None
) -> List[ImportSession]:
    """获取用户的导入会话列表"""
    query = db.query(ImportSession)

    # 如果指定了user_id，则只查看该用户的会话；否则查看所有会话（管理员权限）
    if user_id is not None:
        query = query.filter(ImportSession.user_id == user_id)

    if status:
        query = query.filter(ImportSession.status == status)

    return query.order_by(ImportSession.created_at.desc()).offset(skip).limit(limit).all()


def update_import_session(db: Session, session_id: int, update_data: Dict[str, Any]) -> Optional[ImportSession]:
    """更新导入会话"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    for field, value in update_data.items():
        if hasattr(import_session, field):
            setattr(import_session, field, value)

    # 如果状态开始处理，设置开始时间
    if import_session.status == ImportStatus.PROCESSING and not import_session.started_at:
        import_session.started_at = datetime.now()

    # 如果状态完成或失败，设置完成时间
    if import_session.status in [ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.CANCELLED]:
        import_session.completed_at = datetime.now()

    # 计算进度百分比
    if import_session.total_rows > 0:
        import_session.progress = int((import_session.processed_rows / import_session.total_rows) * 100)

    db.commit()
    db.refresh(import_session)
    return import_session


def update_progress(
    db: Session,
    session_id: int,
    processed_rows: int,
    success_count: int = None,
    update_count: int = None,
    error_count: int = None,
    detailed_result: dict = None
) -> Optional[ImportSession]:
    """更新导入进度"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    # 更新已处理行数
    import_session.processed_rows = processed_rows

    # 更新计数器
    if success_count is not None:
        import_session.success_count = success_count
    if update_count is not None:
        import_session.update_count = update_count
    if error_count is not None:
        import_session.error_count = error_count

    # 计算进度百分比
    if import_session.total_rows > 0:
        import_session.progress = int((import_session.processed_rows / import_session.total_rows) * 100)

    # 添加详细结果
    if detailed_result:
        if not import_session.detailed_results:
            import_session.detailed_results = []
        import_session.detailed_results.append(detailed_result)

    db.commit()
    db.refresh(import_session)
    return import_session


def add_error_detail(db: Session, session_id: int, error_detail: dict) -> Optional[ImportSession]:
    """添加错误详情"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    if not import_session.error_details:
        import_session.error_details = []

    import_session.error_details.append(error_detail)
    db.commit()
    db.refresh(import_session)
    return import_session


def complete_import_session(
    db: Session,
    session_id: int,
    success_count: int = None,
    update_count: int = None,
    error_count: int = None,
    detailed_results: List[dict] = None,
    error_details: List[dict] = None
) -> Optional[ImportSession]:
    """完成导入会话"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    import_session.status = ImportStatus.COMPLETED
    import_session.completed_at = datetime.now()
    import_session.progress = 100

    # 更新计数器
    if success_count is not None:
        import_session.success_count = success_count
    if update_count is not None:
        import_session.update_count = update_count
    if error_count is not None:
        import_session.error_count = error_count

    # 计算并更新processed_rows（成功+更新+失败的总数）
    total_processed = 0
    if success_count is not None:
        total_processed += success_count
    if update_count is not None:
        total_processed += update_count
    if error_count is not None:
        total_processed += error_count

    # 只有当total_processed大于0时才更新processed_rows
    if total_processed > 0:
        import_session.processed_rows = total_processed

    if detailed_results:
        import_session.detailed_results = detailed_results
    if error_details:
        import_session.error_details = error_details

    db.commit()
    db.refresh(import_session)
    return import_session


def fail_import_session(db: Session, session_id: int, error_message: str) -> Optional[ImportSession]:
    """标记导入会话失败"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    import_session.status = ImportStatus.FAILED
    import_session.completed_at = datetime.now()
    import_session.error_message = error_message

    db.commit()
    db.refresh(import_session)
    return import_session


def cancel_import_session(db: Session, session_id: int, reason: str = "用户取消") -> Optional[ImportSession]:
    """取消导入会话"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    import_session.status = ImportStatus.CANCELLED
    import_session.completed_at = datetime.now()
    import_session.notes = reason

    db.commit()
    db.refresh(import_session)
    return import_session


def pause_import_session(db: Session, session_id: int) -> Optional[ImportSession]:
    """暂停导入会话"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    import_session.status = ImportStatus.PAUSED

    db.commit()
    db.refresh(import_session)
    return import_session


def resume_import_session(db: Session, session_id: int) -> Optional[ImportSession]:
    """恢复导入会话"""
    import_session = get_import_session(db, session_id)
    if not import_session:
        return None

    import_session.status = ImportStatus.PROCESSING

    db.commit()
    db.refresh(import_session)
    return import_session


def delete_import_session(db: Session, session_id: int, user_id: int) -> bool:
    """删除导入会话"""
    import_session = db.query(ImportSession).filter(
        and_(ImportSession.id == session_id, ImportSession.user_id == user_id)
    ).first()

    if not import_session:
        return False

    db.delete(import_session)
    db.commit()
    return True


def get_active_sessions(db: Session, user_id: int = None) -> List[ImportSession]:
    """获取活跃的导入会话"""
    query = db.query(ImportSession).filter(
        ImportSession.status.in_([ImportStatus.PENDING, ImportStatus.PROCESSING, ImportStatus.PAUSED])
    )

    if user_id:
        query = query.filter(ImportSession.user_id == user_id)

    return query.order_by(ImportSession.created_at.desc()).all()


def get_import_statistics(db: Session, user_id: int = None, days: int = 30) -> Dict[str, Any]:
    """获取导入统计信息"""
    from datetime import timedelta

    cutoff_date = datetime.now() - timedelta(days=days)

    query = db.query(ImportSession).filter(ImportSession.created_at >= cutoff_date)

    if user_id:
        query = query.filter(ImportSession.user_id == user_id)

    sessions = query.all()

    total_sessions = len(sessions)
    completed_sessions = len([s for s in sessions if s.status == ImportStatus.COMPLETED])
    failed_sessions = len([s for s in sessions if s.status == ImportStatus.FAILED])
    cancelled_sessions = len([s for s in sessions if s.status == ImportStatus.CANCELLED])

    total_success = sum(s.success_count + s.update_count for s in sessions if s.success_count or s.update_count)
    total_errors = sum(s.error_count for s in sessions if s.error_count)

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "failed_sessions": failed_sessions,
        "cancelled_sessions": cancelled_sessions,
        "success_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        "total_success_imports": total_success,
        "total_errors": total_errors,
        "period_days": days
    }
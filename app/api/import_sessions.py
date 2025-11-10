"""
导入会话管理 API
提供导入进度跟踪、状态管理和结果查询功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.api.auth import get_current_user
from app.crud import import_session as import_crud
from app.schemas.schemas import (
    ImportSessionCreate, ImportSessionResponse, ImportSessionUpdate,
    ImportSessionSummary, ImportProgressUpdate
)
from app.models.models import User

router = APIRouter()


@router.post("/start", response_model=ImportSessionResponse)
def start_import_session(
    session_data: ImportSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始新的导入会话"""
    try:
        # 创建导入会话（使用当前用户ID）
        import_session = import_crud.create_import_session(db, session_data)

        return import_session

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建导入会话失败: {str(e)}"
        )


@router.get("/{session_id}", response_model=ImportSessionResponse)
def get_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导入会话详情"""
    import_session = import_crud.get_import_session(db, session_id)

    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限：用户只能查看自己的会话（管理员除外）
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此导入会话"
        )

    # 修复嵌套列表问题：如果 detailed_results 是嵌套列表，展平它
    if import_session.detailed_results and isinstance(import_session.detailed_results, list):
        if len(import_session.detailed_results) > 0 and isinstance(import_session.detailed_results[0], list):
            import_session.detailed_results = import_session.detailed_results[0]

    return import_session


@router.get("/", response_model=List[ImportSessionResponse])
def get_user_import_sessions(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的导入会话列表"""
    try:
        # 转换状态过滤器
        status = None
        if status_filter:
            from app.models.import_session import ImportStatus
            try:
                status = ImportStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的状态过滤器: {status_filter}"
                )

        # 检查权限：管理员可以查看所有会话，普通用户只能查看自己的
        user_id = None if current_user.is_admin else current_user.id

        sessions = import_crud.get_user_import_sessions(
            db, user_id=user_id, skip=skip, limit=limit, status=status
        )

        # 修复嵌套列表问题
        for session in sessions:
            if session.detailed_results and isinstance(session.detailed_results, list):
                if len(session.detailed_results) > 0 and isinstance(session.detailed_results[0], list):
                    session.detailed_results = session.detailed_results[0]

        return sessions

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导入会话列表失败: {str(e)}"
        )


@router.put("/{session_id}", response_model=ImportSessionResponse)
def update_import_session(
    session_id: int,
    update_data: ImportSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新导入会话"""
    # 获取原会话
    import_session = import_crud.get_import_session(db, session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此导入会话"
        )

    try:
        # 更新会话
        updated_session = import_crud.update_import_session(
            db, session_id, update_data.dict(exclude_unset=True)
        )

        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新导入会话失败"
            )

        return updated_session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新导入会话失败: {str(e)}"
        )


@router.post("/{session_id}/progress")
def update_import_progress(
    session_id: int,
    progress_data: ImportProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新导入进度"""
    # 获取会话
    import_session = import_crud.get_import_session(db, session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此导入会话进度"
        )

    try:
        # 更新进度
        updated_session = import_crud.update_progress(
            db,
            session_id,
            progress_data.processed_rows,
            progress_data.success_count,
            progress_data.update_count,
            progress_data.error_count,
            progress_data.detailed_result
        )

        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新进度失败"
            )

        return {"message": "进度更新成功", "progress": updated_session.progress}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新进度失败: {str(e)}"
        )


@router.post("/{session_id}/cancel")
def cancel_import_session(
    session_id: int,
    reason: str = "用户取消",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消导入会话"""
    # 获取会话
    import_session = import_crud.get_import_session(db, session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消此导入会话"
        )

    # 检查状态
    if not import_session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消活跃状态的导入会话"
        )

    try:
        # 取消会话
        cancelled_session = import_crud.cancel_import_session(db, session_id, reason)

        if not cancelled_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="取消导入会话失败"
            )

        return {"message": "导入会话已取消", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消导入会话失败: {str(e)}"
        )


@router.post("/{session_id}/pause")
def pause_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """暂停导入会话"""
    # 获取会话
    import_session = import_crud.get_import_session(db, session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权暂停此导入会话"
        )

    # 检查状态
    if import_session.status != "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能暂停正在处理的导入会话"
        )

    try:
        # 暂停会话
        paused_session = import_crud.pause_import_session(db, session_id)

        if not paused_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="暂停导入会话失败"
            )

        return {"message": "导入会话已暂停", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停导入会话失败: {str(e)}"
        )


@router.post("/{session_id}/resume")
def resume_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复导入会话"""
    # 获取会话
    import_session = import_crud.get_import_session(db, session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入会话不存在"
        )

    # 检查权限
    if not current_user.is_admin and import_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权恢复此导入会话"
        )

    # 检查状态
    if import_session.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能恢复已暂停的导入会话"
        )

    try:
        # 恢复会话
        resumed_session = import_crud.resume_import_session(db, session_id)

        if not resumed_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="恢复导入会话失败"
            )

        return {"message": "导入会话已恢复", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复导入会话失败: {str(e)}"
        )


@router.delete("/{session_id}")
def delete_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除导入会话"""
    try:
        success = import_crud.delete_import_session(db, session_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导入会话不存在或无权删除"
            )

        return {"message": "导入会话已删除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除导入会话失败: {str(e)}"
        )


@router.get("/statistics/summary", response_model=ImportSessionSummary)
def get_import_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导入统计信息"""
    try:
        # 检查权限：管理员可以查看所有统计，普通用户只能查看自己的
        user_id = None if current_user.is_admin else current_user.id

        statistics = import_crud.get_import_statistics(db, user_id=user_id, days=days)

        return statistics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/active/list", response_model=List[ImportSessionResponse])
def get_active_import_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取活跃的导入会话列表"""
    try:
        # 检查权限：管理员可以查看所有活跃会话，普通用户只能查看自己的
        user_id = None if current_user.is_admin else current_user.id

        active_sessions = import_crud.get_active_sessions(db, user_id=user_id)

        return active_sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活跃会话失败: {str(e)}"
        )
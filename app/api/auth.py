from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.crud import users
from app.schemas.schemas import Token, User
from app.core.security import create_access_token, verify_token, verify_token_with_session
from app.core.config import settings
from app.core.session_manager import session_manager
from typing import Optional, List

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class LoginRequest(BaseModel):
    username: str
    password: str
    force: Optional[bool] = False  # 是否强制登录（挤掉其他会话）

class SessionConflictResponse(BaseModel):
    has_conflict: bool
    active_sessions: List[dict]
    message: str

def get_current_user(token_data = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 处理两种情况：HTTPAuthorizationCredentials 对象或字符串
    if hasattr(token_data, 'credentials'):
        # 如果是 HTTPAuthorizationCredentials 对象
        token = token_data.credentials
    else:
        # 如果是字符串
        token = token_data
    
    # 使用带session验证的token验证
    username, session_id = verify_token_with_session(token)
    if username is None:
        raise credentials_exception
    
    user = users.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限"
        )
    return current_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = users.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json")
async def login_json(login_request: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = users.authenticate_user(db, login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 获取客户端信息
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else ""
    
    # 检查是否有活跃会话
    active_sessions = session_manager.get_user_active_sessions(int(user.id))
    
    if active_sessions and not login_request.force:
        # 有活跃会话且未强制登录，返回冲突信息
        sessions_info = []
        for session in active_sessions:
            sessions_info.append({
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "user_agent": session.user_agent,
                "ip_address": session.ip_address
            })
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "has_conflict": True,
                "active_sessions": sessions_info,
                "message": f"用户 {user.username} 已在其他位置登录",
                "conflict_type": "session_exists"
            }
        )
    
    # 如果强制登录，先清除其他会话
    if login_request.force and active_sessions:
        invalidated_count = session_manager.invalidate_user_sessions(int(user.id))
        print(f"强制登录：已清除 {invalidated_count} 个会话")
    
    # 创建新会话
    session_id = session_manager.create_session(
        user_id=int(user.id),
        username=str(user.username),
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # 创建JWT token（包含session_id）
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username, "session_id": session_id}, 
        expires_delta=access_token_expires
    )
    
    # 创建refresh token
    refresh_token = create_access_token(
        data={"sub": user.username, "type": "refresh", "session_id": session_id}, 
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_HOURS * 24)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "session_id": session_id,
        "user": {
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 从JWT token中获取session_id
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from app.core.security import decode_token
            payload = decode_token(token)
            session_id = payload.get("session_id") if payload else None
            
            if session_id:
                session_manager.invalidate_session(session_id)
                return {"message": "登出成功"}
        except Exception as e:
            print(f"Error during logout: {e}")
    
    return {"message": "登出完成"}

@router.get("/sessions")
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """获取用户的活跃会话"""
    active_sessions = session_manager.get_user_active_sessions(int(current_user.id))
    
    sessions_info = []
    for session in active_sessions:
        sessions_info.append({
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "user_agent": session.user_agent,
            "ip_address": session.ip_address
        })
    
    return {"sessions": sessions_info}

@router.delete("/sessions/{session_id}")
async def terminate_session(session_id: str, current_user: User = Depends(get_current_admin_user)):
    """终止指定会话（仅管理员）"""
    success = session_manager.invalidate_session(session_id)
    if success:
        return {"message": "会话终止成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话未找到"
        )

@router.get("/sessions/stats")
async def get_session_stats(current_user: User = Depends(get_current_admin_user)):
    """获取会话统计（仅管理员）"""
    return session_manager.get_session_stats()

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """用户修改密码"""
    # 获取数据库中的用户信息
    db_user = users.get_user(db, current_user.id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证当前密码
    if not users.verify_password(request.current_password, str(db_user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码和确认密码是否一致
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码和确认密码不一致"
        )
    
    # 验证新密码强度
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6个字符"
        )
    
    if not any(c.isalpha() for c in request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含字母"
        )
    
    if not any(c.isdigit() for c in request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含数字"
        )
    
    # 更新密码
    success = users.update_user_password(db, current_user.id, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码更新失败"
        )
    
        
    return {"message": "密码修改成功"}
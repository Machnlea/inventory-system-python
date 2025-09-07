from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.api.auth import get_current_user

security = HTTPBearer()

def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前管理员用户，如果不是管理员则抛出异常
    """
    current_user = get_current_user(credentials, db)
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可访问"
        )
    
    return current_user

def require_admin():
    """
    管理员权限验证装饰器依赖
    """
    return Depends(get_current_admin_user)
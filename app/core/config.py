import os
from datetime import timedelta

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-please-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 2
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")
    
    # 管理员默认账户
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

settings = Settings()
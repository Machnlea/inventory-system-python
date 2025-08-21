from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库URL（默认使用SQLite，生产环境可改为PostgreSQL）
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/inventory.db")

# 如果使用SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL 优化配置
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # 设置为 True 可以查看 SQL 调试信息
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 数据库连接测试函数
def test_database_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True, "数据库连接成功"
    except Exception as e:
        return False, f"数据库连接失败: {str(e)}"
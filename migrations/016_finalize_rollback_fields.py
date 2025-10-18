"""
完善回滚功能的数据库字段和约束

Revision ID: 016
Revises: 015
Create Date: 2025-10-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """完善回滚功能的数据库结构"""
    
    # 检查并确保回滚字段存在（防止重复执行）
    conn = op.get_bind()
    
    # 获取表结构信息
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('calibration_history')]
    
    # 如果字段不存在，则添加
    if 'is_rolled_back' not in columns:
        op.add_column('calibration_history', 
                      sa.Column('is_rolled_back', sa.Boolean(), nullable=False, default=False))
    
    if 'rolled_back_at' not in columns:
        op.add_column('calibration_history', 
                      sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True))
    
    if 'rolled_back_by' not in columns:
        op.add_column('calibration_history', 
                      sa.Column('rolled_back_by', sa.Integer(), nullable=True))
    
    if 'rollback_reason' not in columns:
        op.add_column('calibration_history', 
                      sa.Column('rollback_reason', sa.Text(), nullable=True))
    
    # 确保现有记录的默认值
    op.execute("UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL")
    
    # 添加外键约束（如果不存在）
    try:
        foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('calibration_history')]
        if 'fk_calibration_history_rolled_back_by' not in foreign_keys:
            op.create_foreign_key('fk_calibration_history_rolled_back_by', 
                                 'calibration_history', 'users', 
                                 ['rolled_back_by'], ['id'])
    except Exception as e:
        # 如果外键创建失败，记录但不中断迁移
        print(f"Warning: Could not create foreign key constraint: {e}")
    
    # 创建索引以提高查询性能
    try:
        op.create_index('idx_calibration_history_is_rolled_back', 
                       'calibration_history', ['is_rolled_back'])
    except Exception:
        # 索引可能已存在，忽略错误
        pass
    
    try:
        op.create_index('idx_calibration_history_rolled_back_at', 
                       'calibration_history', ['rolled_back_at'])
    except Exception:
        # 索引可能已存在，忽略错误
        pass


def downgrade():
    """回滚回滚功能的数据库更改"""
    
    # 删除索引
    try:
        op.drop_index('idx_calibration_history_rolled_back_at', 'calibration_history')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_calibration_history_is_rolled_back', 'calibration_history')
    except Exception:
        pass
    
    # 删除外键约束
    try:
        op.drop_constraint('fk_calibration_history_rolled_back_by', 'calibration_history', type_='foreignkey')
    except Exception:
        pass
    
    # 删除字段
    try:
        op.drop_column('calibration_history', 'rollback_reason')
        op.drop_column('calibration_history', 'rolled_back_by')
        op.drop_column('calibration_history', 'rolled_back_at')
        op.drop_column('calibration_history', 'is_rolled_back')
    except Exception as e:
        print(f"Warning: Could not drop columns: {e}")
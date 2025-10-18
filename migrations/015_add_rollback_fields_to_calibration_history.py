"""
添加回滚标记字段到检定历史记录表

Revision ID: 015
Revises: 014
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    """添加回滚相关字段到calibration_history表"""
    
    # 添加回滚标记字段
    op.add_column('calibration_history', 
                  sa.Column('is_rolled_back', sa.Boolean(), nullable=True, default=False))
    
    # 添加回滚时间字段
    op.add_column('calibration_history', 
                  sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True))
    
    # 添加回滚操作者字段
    op.add_column('calibration_history', 
                  sa.Column('rolled_back_by', sa.Integer(), nullable=True))
    
    # 添加回滚原因字段
    op.add_column('calibration_history', 
                  sa.Column('rollback_reason', sa.Text(), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key('fk_calibration_history_rolled_back_by', 
                         'calibration_history', 'users', 
                         ['rolled_back_by'], ['id'])
    
    # 为现有记录设置默认值
    op.execute("UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL")
    
    # 设置非空约束
    op.alter_column('calibration_history', 'is_rolled_back', nullable=False)


def downgrade():
    """移除回滚相关字段"""
    
    # 删除外键约束
    op.drop_constraint('fk_calibration_history_rolled_back_by', 'calibration_history', type_='foreignkey')
    
    # 删除字段
    op.drop_column('calibration_history', 'rollback_reason')
    op.drop_column('calibration_history', 'rolled_back_by')
    op.drop_column('calibration_history', 'rolled_back_at')
    op.drop_column('calibration_history', 'is_rolled_back')
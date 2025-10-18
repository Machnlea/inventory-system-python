"""
增强审计日志和回滚系统的数据库结构

Revision ID: 017
Revises: 016
Create Date: 2025-10-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    """增强审计日志和回滚系统"""
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. 确保audit_logs表有必要的字段
    audit_columns = [col['name'] for col in inspector.get_columns('audit_logs')]
    
    # 添加回滚相关的审计字段
    if 'rollback_target_id' not in audit_columns:
        op.add_column('audit_logs', 
                      sa.Column('rollback_target_id', sa.Integer(), nullable=True,
                               comment='被回滚的目标记录ID'))
    
    if 'rollback_target_type' not in audit_columns:
        op.add_column('audit_logs', 
                      sa.Column('rollback_target_type', sa.String(50), nullable=True,
                               comment='被回滚的目标记录类型'))
    
    if 'is_rollback_operation' not in audit_columns:
        op.add_column('audit_logs', 
                      sa.Column('is_rollback_operation', sa.Boolean(), nullable=False, default=False,
                               comment='是否为回滚操作'))
    
    # 2. 确保calibration_history表的回滚字段完整
    cal_columns = [col['name'] for col in inspector.get_columns('calibration_history')]
    
    # 添加回滚操作的审计日志关联
    if 'rollback_audit_log_id' not in cal_columns:
        op.add_column('calibration_history', 
                      sa.Column('rollback_audit_log_id', sa.Integer(), nullable=True,
                               comment='关联的回滚审计日志ID'))
    
    # 3. 创建性能优化索引
    try:
        # 审计日志索引
        op.create_index('idx_audit_logs_rollback_operation', 
                       'audit_logs', ['is_rollback_operation'])
        op.create_index('idx_audit_logs_rollback_target', 
                       'audit_logs', ['rollback_target_type', 'rollback_target_id'])
        
        # 检定历史索引
        op.create_index('idx_calibration_history_rollback_status', 
                       'calibration_history', ['is_rolled_back', 'rolled_back_at'])
        op.create_index('idx_calibration_history_equipment_rollback', 
                       'calibration_history', ['equipment_id', 'is_rolled_back'])
        
    except Exception as e:
        print(f"Warning: Some indexes may already exist: {e}")
    
    # 4. 添加外键约束
    try:
        # 回滚审计日志关联
        op.create_foreign_key('fk_calibration_history_rollback_audit_log', 
                             'calibration_history', 'audit_logs', 
                             ['rollback_audit_log_id'], ['id'])
    except Exception as e:
        print(f"Warning: Could not create foreign key: {e}")
    
    # 5. 更新现有数据的默认值
    op.execute("UPDATE audit_logs SET is_rollback_operation = 0 WHERE is_rollback_operation IS NULL")
    
    # 6. 创建视图以便于查询回滚相关信息
    try:
        op.execute("""
        CREATE VIEW IF NOT EXISTS v_rollback_summary AS
        SELECT 
            ch.id as calibration_history_id,
            ch.equipment_id,
            ch.calibration_date,
            ch.is_rolled_back,
            ch.rolled_back_at,
            ch.rollback_reason,
            u.username as rolled_back_by_user,
            al.action as rollback_action,
            al.timestamp as rollback_timestamp
        FROM calibration_history ch
        LEFT JOIN users u ON ch.rolled_back_by = u.id
        LEFT JOIN audit_logs al ON ch.rollback_audit_log_id = al.id
        WHERE ch.is_rolled_back = 1
        """)
    except Exception as e:
        print(f"Warning: Could not create view: {e}")


def downgrade():
    """回滚增强的审计日志和回滚系统"""
    
    # 删除视图
    try:
        op.execute("DROP VIEW IF EXISTS v_rollback_summary")
    except Exception:
        pass
    
    # 删除索引
    indexes_to_drop = [
        'idx_audit_logs_rollback_operation',
        'idx_audit_logs_rollback_target', 
        'idx_calibration_history_rollback_status',
        'idx_calibration_history_equipment_rollback'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name)
        except Exception:
            pass
    
    # 删除外键约束
    try:
        op.drop_constraint('fk_calibration_history_rollback_audit_log', 
                          'calibration_history', type_='foreignkey')
    except Exception:
        pass
    
    # 删除字段
    try:
        op.drop_column('calibration_history', 'rollback_audit_log_id')
        op.drop_column('audit_logs', 'is_rollback_operation')
        op.drop_column('audit_logs', 'rollback_target_type')
        op.drop_column('audit_logs', 'rollback_target_id')
    except Exception as e:
        print(f"Warning: Could not drop columns: {e}")
"""Add import sessions table

Revision ID: 018_add_import_sessions_table
Revises: 017_enhance_audit_and_rollback_system
Create Date: 2025-10-20 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '018_add_import_sessions_table'
down_revision = '017_enhance_audit_and_rollback_system'
branch_labels = None
depends_on = None


def upgrade():
    """创建导入会话表"""
    # 创建导入会话枚举类型
    op.execute("CREATE TYPE IF NOT EXISTS importstatus AS ENUM ('pending', 'processing', 'paused', 'cancelled', 'completed', 'failed')")

    # 创建导入会话表
    op.create_table(
        'import_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='操作用户ID'),
        sa.Column('filename', sa.String(length=255), nullable=False, comment='导入文件名'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('status', sa.Enum('pending', 'processing', 'paused', 'cancelled', 'completed', 'failed', name='importstatus'), nullable=False, comment='导入状态'),
        sa.Column('progress', sa.Integer(), nullable=False, default=0, comment='处理进度（百分比）'),
        sa.Column('total_rows', sa.Integer(), nullable=False, default=0, comment='总行数'),
        sa.Column('processed_rows', sa.Integer(), nullable=False, default=0, comment='已处理行数'),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0, comment='成功导入数量'),
        sa.Column('update_count', sa.Integer(), nullable=False, default=0, comment='更新设备数量'),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0, comment='错误数量'),
        sa.Column('detailed_results', sa.JSON(), nullable=True, comment='详细处理结果'),
        sa.Column('error_details', sa.JSON(), nullable=True, comment='错误详情'),
        sa.Column('overwrite_existing', sa.Boolean(), nullable=False, default=False, comment='是否覆盖已存在的设备'),
        sa.Column('batch_size', sa.Integer(), nullable=False, default=50, comment='批处理大小'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始处理时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        comment='导入会话表'
    )

    # 创建索引
    op.create_index('ix_import_sessions_id', 'import_sessions', ['id'], unique=False)
    op.create_index('ix_import_sessions_user_id', 'import_sessions', ['user_id'], unique=False)
    op.create_index('ix_import_sessions_status', 'import_sessions', ['status'], unique=False)
    op.create_index('ix_import_sessions_created_at', 'import_sessions', ['created_at'], unique=False)
    op.create_index('ix_import_sessions_user_status', 'import_sessions', ['user_id', 'status'], unique=False)


def downgrade():
    """删除导入会话表"""
    # 删除索引
    op.drop_index('ix_import_sessions_user_status', table_name='import_sessions')
    op.drop_index('ix_import_sessions_created_at', table_name='import_sessions')
    op.drop_index('ix_import_sessions_status', table_name='import_sessions')
    op.drop_index('ix_import_sessions_user_id', table_name='import_sessions')
    op.drop_index('ix_import_sessions_id', table_name='import_sessions')

    # 删除表
    op.drop_table('import_sessions')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS importstatus")
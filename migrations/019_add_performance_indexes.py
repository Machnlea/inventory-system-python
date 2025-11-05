"""Add performance indexes for equipment queries

Revision ID: 019
Revises: 018
Create Date: 2025-11-05 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加性能优化索引"""

    # 设备表主要查询索引
    # 1. 状态查询索引 - 高优先级（设备状态筛选）
    op.create_index(
        'idx_equipment_status',
        'equipments',
        ['status']
    )

    # 2. 部门ID索引 - 高优先级（权限控制和筛选）
    op.create_index(
        'idx_equipment_department_id',
        'equipments',
        ['department_id']
    )

    # 3. 类别ID索引 - 高优先级（权限控制和筛选）
    op.create_index(
        'idx_equipment_category_id',
        'equipments',
        ['category_id']
    )

    # 4. 有效期索引 - 高优先级（排序和仪表板查询）
    op.create_index(
        'idx_equipment_valid_until',
        'equipments',
        ['valid_until']
    )

    # 5. 复合索引：状态+有效期 - 高优先级（仪表板和即将到期设备）
    op.create_index(
        'idx_equipment_status_valid_until',
        'equipments',
        ['status', 'valid_until']
    )

    # 6. 复合索引：部门+状态 - 高优先级（部门视图）
    op.create_index(
        'idx_equipment_department_status',
        'equipments',
        ['department_id', 'status']
    )

    # 7. 复合索引：类别+状态 - 高优先级（类别视图）
    op.create_index(
        'idx_equipment_category_status',
        'equipments',
        ['category_id', 'status']
    )

    # 8. 内部编号索引 - 中优先级（搜索）
    op.create_index(
        'idx_equipment_internal_id',
        'equipments',
        ['internal_id']
    )

    # 9. 设备名称索引 - 中优先级（搜索）
    op.create_index(
        'idx_equipment_name',
        'equipments',
        ['name']
    )

    # 10. 管理级别索引 - 中优先级（筛选）
    op.create_index(
        'idx_equipment_management_level',
        'equipments',
        ['management_level']
    )

    # 11. 创建时间索引 - 低优先级（审计日志关联）
    op.create_index(
        'idx_equipment_created_at',
        'equipments',
        ['created_at']
    )

    # 12. 检定日期索引 - 低优先级（检定管理）
    op.create_index(
        'idx_equipment_calibration_date',
        'equipments',
        ['calibration_date']
    )

    # 13. 复合索引：部门+类别+状态 - 中优先级（复杂筛选）
    op.create_index(
        'idx_equipment_dept_cat_status',
        'equipments',
        ['department_id', 'category_id', 'status']
    )

    # 14. 复合索引：类别+有效期 - 中优先级（类别视图排序）
    op.create_index(
        'idx_equipment_category_valid_until',
        'equipments',
        ['category_id', 'valid_until']
    )

    # 用户设备权限表索引
    # 15. 用户权限复合索引 - 高优先级（权限检查）
    op.create_index(
        'idx_user_equipment_permissions_user_category',
        'user_equipment_permissions',
        ['user_id', 'category_id']
    )

    # 16. 设备名称权限索引 - 高优先级（权限检查）
    op.create_index(
        'idx_user_equipment_permissions_equipment_name',
        'user_equipment_permissions',
        ['equipment_name']
    )

    # 17. 用户权限复合索引 - 高优先级（权限检查）
    op.create_index(
        'idx_user_equipment_permissions_user_category_name',
        'user_equipment_permissions',
        ['user_id', 'category_id', 'equipment_name']
    )

    # 审计日志表索引
    # 18. 设备ID审计索引 - 高优先级（设备历史查询）
    op.create_index(
        'idx_audit_logs_equipment_id',
        'audit_logs',
        ['equipment_id']
    )

    # 19. 用户ID审计索引 - 中优先级（用户操作历史）
    op.create_index(
        'idx_audit_logs_user_id',
        'audit_logs',
        ['user_id']
    )

    # 20. 创建时间审计索引 - 中优先级（时间范围查询）
    op.create_index(
        'idx_audit_logs_created_at',
        'audit_logs',
        ['created_at']
    )

    # 21. 操作类型审计索引 - 低优先级（操作筛选）
    op.create_index(
        'idx_audit_logs_action',
        'audit_logs',
        ['action']
    )

    # 22. 复合索引：设备ID+创建时间 - 高优先级（设备历史排序）
    op.create_index(
        'idx_audit_logs_equipment_created',
        'audit_logs',
        ['equipment_id', 'created_at']
    )

    # 附件表索引
    # 23. 设备附件索引 - 高优先级（附件计数）
    op.create_index(
        'idx_equipment_attachments_equipment_id',
        'equipment_attachments',
        ['equipment_id']
    )

    # 24. 附件类型索引 - 中优先级（证书/文档筛选）
    op.create_index(
        'idx_equipment_attachments_file_type',
        'equipment_attachments',
        ['file_type']
    )

    # 25. 复合索引：设备ID+文件类型 - 中优先级（特定类型附件）
    op.create_index(
        'idx_equipment_attachments_equipment_type',
        'equipment_attachments',
        ['equipment_id', 'file_type']
    )

    # 26. 创建时间附件索引 - 低优先级（附件管理）
    op.create_index(
        'idx_equipment_attachments_created_at',
        'equipment_attachments',
        ['created_at']
    )


def downgrade() -> None:
    """移除性能优化索引"""

    # 设备表索引
    op.drop_index('idx_equipment_dept_cat_status', table_name='equipments')
    op.drop_index('idx_equipment_category_valid_until', table_name='equipments')
    op.drop_index('idx_equipment_calibration_date', table_name='equipments')
    op.drop_index('idx_equipment_created_at', table_name='equipments')
    op.drop_index('idx_equipment_management_level', table_name='equipments')
    op.drop_index('idx_equipment_name', table_name='equipments')
    op.drop_index('idx_equipment_internal_id', table_name='equipments')
    op.drop_index('idx_equipment_category_status', table_name='equipments')
    op.drop_index('idx_equipment_department_status', table_name='equipments')
    op.drop_index('idx_equipment_status_valid_until', table_name='equipments')
    op.drop_index('idx_equipment_valid_until', table_name='equipments')
    op.drop_index('idx_equipment_category_id', table_name='equipments')
    op.drop_index('idx_equipment_department_id', table_name='equipments')
    op.drop_index('idx_equipment_status', table_name='equipments')

    # 用户设备权限表索引
    op.drop_index('idx_user_equipment_permissions_user_category_name', table_name='user_equipment_permissions')
    op.drop_index('idx_user_equipment_permissions_equipment_name', table_name='user_equipment_permissions')
    op.drop_index('idx_user_equipment_permissions_user_category', table_name='user_equipment_permissions')

    # 审计日志表索引
    op.drop_index('idx_audit_logs_equipment_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_equipment_id', table_name='audit_logs')

    # 附件表索引
    op.drop_index('idx_equipment_attachments_created_at', table_name='equipment_attachments')
    op.drop_index('idx_equipment_attachments_equipment_type', table_name='equipment_attachments')
    op.drop_index('idx_equipment_attachments_file_type', table_name='equipment_attachments')
    op.drop_index('idx_equipment_attachments_equipment_id', table_name='equipment_attachments')
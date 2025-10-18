# 数据库迁移说明

本目录包含了设备台账管理系统的数据库迁移脚本。

## 迁移文件说明

### 最新迁移（回滚功能相关）

- **015_add_rollback_fields_to_calibration_history.py**: 添加回滚标记字段到检定历史记录表
- **016_finalize_rollback_fields.py**: 完善回滚功能的数据库字段和约束
- **017_enhance_audit_and_rollback_system.py**: 增强审计日志和回滚系统的数据库结构

### 回滚功能涉及的数据库字段

#### calibration_history 表新增字段：
- `is_rolled_back` (BOOLEAN): 是否已被回滚
- `rolled_back_at` (DATETIME): 回滚时间
- `rolled_back_by` (INTEGER): 回滚操作者ID（外键关联users表）
- `rollback_reason` (TEXT): 回滚原因
- `rollback_audit_log_id` (INTEGER): 关联的回滚审计日志ID

#### audit_logs 表新增字段：
- `rollback_target_id` (INTEGER): 被回滚的目标记录ID
- `rollback_target_type` (VARCHAR): 被回滚的目标记录类型
- `is_rollback_operation` (BOOLEAN): 是否为回滚操作

## 执行迁移

### 方法1：使用迁移执行脚本（推荐）

```bash
# 执行所有待执行的迁移
python run_migrations.py
```

### 方法2：验证和修复数据库结构

```bash
# 验证数据库结构是否正确
python verify_database_structure.py
```

### 方法3：手动执行（如果自动迁移失败）

```bash
# 手动执行特定迁移
python manual_migration.py
```

## 迁移验证

执行迁移后，可以使用以下方法验证：

1. **结构验证**：
   ```bash
   python verify_database_structure.py
   ```

2. **功能验证**：
   - 登录系统
   - 进入操作日志页面
   - 尝试执行回滚操作
   - 检查检定历史记录中的回滚状态显示

## 回滚迁移

如果需要回滚迁移，可以手动执行相应迁移文件中的 `downgrade()` 函数。

**注意**：回滚操作会删除相关字段和数据，请谨慎操作。

## 数据库索引

为了提高查询性能，迁移脚本会创建以下索引：

- `idx_calibration_history_is_rolled_back`: 检定历史回滚状态索引
- `idx_calibration_history_rolled_back_at`: 检定历史回滚时间索引
- `idx_audit_logs_rollback_operation`: 审计日志回滚操作索引
- `idx_calibration_history_rollback_status`: 检定历史回滚状态复合索引
- `idx_calibration_history_equipment_rollback`: 设备检定回滚状态索引

## 数据库视图

系统会创建以下视图以便于查询：

- `v_rollback_summary`: 回滚操作摘要视图，包含回滚记录的详细信息

## 故障排除

### 常见问题

1. **字段已存在错误**：
   - 这通常是因为之前已经手动添加了字段
   - 迁移脚本会检查字段是否存在，避免重复添加

2. **外键约束创建失败**：
   - 可能是因为数据完整性问题
   - 检查相关表中是否有无效的外键引用

3. **索引创建失败**：
   - 可能是因为索引已存在
   - 迁移脚本会忽略索引创建失败的错误

### 手动修复

如果自动迁移失败，可以手动执行以下SQL：

```sql
-- 添加回滚字段到calibration_history表
ALTER TABLE calibration_history ADD COLUMN is_rolled_back BOOLEAN DEFAULT 0;
ALTER TABLE calibration_history ADD COLUMN rolled_back_at DATETIME;
ALTER TABLE calibration_history ADD COLUMN rolled_back_by INTEGER;
ALTER TABLE calibration_history ADD COLUMN rollback_reason TEXT;
ALTER TABLE calibration_history ADD COLUMN rollback_audit_log_id INTEGER;

-- 添加回滚字段到audit_logs表
ALTER TABLE audit_logs ADD COLUMN rollback_target_id INTEGER;
ALTER TABLE audit_logs ADD COLUMN rollback_target_type VARCHAR(50);
ALTER TABLE audit_logs ADD COLUMN is_rollback_operation BOOLEAN DEFAULT 0;

-- 更新默认值
UPDATE calibration_history SET is_rolled_back = 0 WHERE is_rolled_back IS NULL;
UPDATE audit_logs SET is_rollback_operation = 0 WHERE is_rollback_operation IS NULL;
```

## 联系支持

如果在迁移过程中遇到问题，请：

1. 检查错误日志
2. 运行验证脚本确认当前数据库状态
3. 备份数据库后尝试手动修复
4. 如果问题持续存在，请联系技术支持
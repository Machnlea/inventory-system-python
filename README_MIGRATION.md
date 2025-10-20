# 数据库迁移指南

## 概述

本指南说明如何将老版本的设备台账数据库迁移到当前系统。

## 迁移脚本功能

`migrate_from_old_database.py` 是一个全自动化数据库迁移工具，支持：

- ✅ 部���数据迁移
- ✅ 设备类别数据迁移
- ✅ 用户数据迁移
- ✅ 用户权限数据迁移
- ✅ 设备台账数据迁移
- ✅ 检定历史记录迁移
- ✅ 审计日志迁移
- ✅ 自动备份当前数据库
- ✅ 重复数据检测和跳过
- ✅ 详细的迁移报告

## 数据映射

### 主要字段对应关系

| 老数据库字段 | 新数据库字段 | 说明 |
|-------------|-------------|------|
| `equipments.manufacturer_id` | `equipments.manufacturer_id` | 出厂编号 |
| `equipments.internal_id` | `equipments.internal_id` | 计量编号 |
| `equipments.name` | `equipments.name` | 设备名称 |
| `equipments.model` | `equipments.model` | 型号规格 |
| `audit_logs.is_rollback_operation` | `audit_logs.is_rollback` | 是否回滚操作 |

### 新增字段

当前系统新增了一些老数据库不存在的字段，迁移时会设置默认值：

- `audit_logs.operation_type`: 默认 "equipment"
- `audit_logs.target_table`: 默认 "equipments"
- `audit_logs.ip_address`: 默认 None
- `calibration_history.rollback_audit_log_id`: 默认 None

## 使用方法

### 方法一：交互式迁移（推荐）

```bash
source .venv/bin/activate
python migrate_from_old_database.py
```

脚本会提示确认后开始迁移。

### 方法二：自动模式

```bash
source .venv/bin/activate
python migrate_from_old_database.py --auto
```

跳过确认提示，直接开始迁移。

## 迁移前准备

1. **备份老数据库**
   ```bash
   cp old_inventory.db old_inventory_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **确保虚拟环境激活**
   ```bash
   source .venv/bin/activate
   ```

3. **检查老数据库文件**
   - 确保 `old_inventory.db` 在项目根目录
   - 确保文件可读且未损坏

## 迁移过程

迁移会按照以下顺序执行（保证数据依赖关系）：

1. 🏢 **部门数据** - 迁移部门和科室信息
2. 🏷️ **设备类别** - 迁移设备分类信息
3. 👥 **用户数据** - 迁移用户账户和权限
4. 🔐 **用户权限** - 迁移用户类别和设备权限
5. 📋 **设备台账** - 迁移设备基本信息
6. 📅 **检定历史** - 迁移设备检定记录
7. 📝 **审计日志** - 迁移操作日志记录

## 迁移报告

迁移完成后会显示详细报告：

```
📊 数据迁移汇总报告
============================================================
✅ departments               :   16 →   16 (错误:  0)
✅ equipment_categories      :   16 →   16 (错误:  0)
✅ users                     :    7 →    7 (错误:  0)
✅ user_categories           :   23 →   23 (错误:  0)
✅ user_equipment_permissions:   45 →   45 (错误:  0)
✅ equipments                : 1911 → 1911 (错误:  0)
✅ calibration_history       :   32 →   32 (错误:  0)
✅ audit_logs                : 1960 → 1960 (错误:  0)
------------------------------------------------------------
📈 总计: 4010 条记录 → 4010 条记录 (总错误: 0)
🎉 数据迁移完全成功！
```

## 错误处理

### 常见问题及解决方案

1. **连接老数据库失败**
   ```
   ❌ 错误：老数据库文件 old_inventory.db 不存在
   ```
   - 检查文件路径
   - 确保文件权限正确

2. **字段类型不匹配**
   ```
   ❌ 迁移设备 'XXX' 失败：...
   ```
   - 脚本会自动处理大部分类型转换
   - 检查数据完整性

3. **重复数据跳过**
   ```
   ⚠️  设备 'XXX' (ABC123) 已存在，跳过
   ```
   - 正常情况，脚本会避免重复导入

4. **权限错误**
   ```
   ❌ 迁移用户权限失败：...
   ```
   - 检查用户ID和类别ID是否存在

## 回滚策略

如果迁移失败需要回滚：

1. **使用自动备份**
   ```bash
   # 找到备份文件
   ls inventory_backup_*.db

   # 恢复数据库
   cp inventory_backup_YYYYMMDD_HHMMSS.db inventory.db
   ```

2. **手动恢复**
   - 删除当前数据库文件
   - 从备份恢复

## 迁移后验证

迁移完成后建议进行以下验证：

1. **数据完整性检查**
   ```bash
   source .venv/bin/activate
   python -c "
   from app.db.database import SessionLocal
   from app.models import models

   db = SessionLocal()

   # 检查设备数量
   equipment_count = db.query(models.Equipment).count()
   print(f'设备数量: {equipment_count}')

   # 检查部门数量
   dept_count = db.query(models.Department).count()
   print(f'部门数量: {dept_count}')

   db.close()
   "
   ```

2. **功能测试**
   - 启动应用程序
   - 登录系统
   - 查看设备列表
   - 检查设备详情页

3. **数据一致性**
   - 随机抽查几个设备记录
   - 验证关键字段是否正确
   - 检查关联关系是否完整

## 注意事项

⚠️ **重要提醒**：

1. **停机时间**：迁移期间建议停止应用程序访问
2. **数据备份**：务必在迁移前备份所有重要数据
3. **测试环境**：建议先在测试环境中验证迁移脚本
4. **磁盘空间**：确保有足够空间存储备份文件
5. **权限要求**：确保有数据库文件读写权限

## 技术细节

### 数据库版本兼容性

- **老数据库**：SQLite 3.x
- **新数据库**：SQLite 3.x（当前系统）
- **Python版本**：3.8+

### 迁移脚本依赖

- SQLAlchemy（项目已包含）
- 项目模型文件（app/models/models.py）
- 数据库连接配置（app/db/database.py）

### 性能考虑

- 迁移1911台设备大约需要1-2分钟
- 内存使用量较少（<100MB）
- 支持大批量数据迁移

## 故障排除

如果遇到问题：

1. **查看错误日志**：脚本会输出详细错误信息
2. **检查数据完整性**：使用SQLite工具直接检查数据库
3. **联系技术支持**：提供错误信息和数据库结构

---

**创建时间**：2025-10-20
**版本**：1.0
**维护者**：Claude AI Assistant
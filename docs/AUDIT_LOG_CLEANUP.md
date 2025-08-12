# 操作日志清理功能

## 功能说明

系统现在支持自动清理超过一年的操作日志数据，以防止数据库无限增长。

## 实现机制

### 1. 自动清理
- 每次创建新的操作日志时，系统会自动检查并清理超过一年的日志
- 这样确保日志数据不会超过一年期限

### 2. 手动清理
- 管理员可以通过API端点手动触发清理
- 端点：`POST /api/audit-logs/cleanup`
- 需要管理员权限

### 3. 定时任务
- 提供了独立的定时任务脚本 `cleanup_audit_logs.py`
- 可以设置为每天运行一次，确保数据及时清理

## 使用方法

### 手动清理API
```bash
curl -X POST "http://localhost:8000/api/audit-logs/cleanup" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 定时任务设置
可以通过cron设置每天运行：
```bash
# 每天凌晨2点运行
0 2 * * * /usr/bin/python3 /path/to/your/project/cleanup_audit_logs.py
```

### 直接运行脚本
```bash
python cleanup_audit_logs.py
```

## 保留策略

- 保留期限：365天（1年）
- 清理方式：删除超过期限的日志记录
- 触发时机：创建新日志时自动触发 + 定时任务

## 注意事项

1. 清理操作不可逆，请确保确实需要删除旧数据
2. 建议在系统负载较低的时间段执行清理操作
3. 可以定期备份重要的操作日志数据
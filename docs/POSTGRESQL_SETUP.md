# PostgreSQL 配置指南

## 1. 安装 PostgreSQL

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### CentOS/RHEL
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

## 2. 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL shell 中执行：
CREATE DATABASE inventory_system;
CREATE USER inventory_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_system TO inventory_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inventory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO inventory_user;

# 退出 PostgreSQL shell
\q
```

## 3. 配置环境变量

创建 `.env` 文件：
```bash
# 数据库配置
DATABASE_URL=postgresql://inventory_user:your_secure_password@localhost:5432/inventory_system

# 应用配置
SECRET_KEY=your-very-secure-secret-key-change-this-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
```

## 4. 测试数据库连接

```bash
# 安装依赖（如果还没安装）
uv sync

# 测试连接
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from app.core.config import settings

print(f'尝试连接到: {settings.DATABASE_URL}')
engine = create_engine(settings.DATABASE_URL)
try:
    with engine.connect() as conn:
        print('✅ 数据库连接成功！')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

## 5. 初始化数据库

```bash
# 运行数据库初始化脚本
uv run python scripts/init_db.py
```

## 6. 配置 PostgreSQL 优化（可选）

编辑 `/etc/postgresql/*/main/postgresql.conf`：
```ini
# 内存设置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

# 连接设置
max_connections = 100

# 日志设置
log_statement = 'all'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# 性能设置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

重启 PostgreSQL：
```bash
sudo systemctl restart postgresql
```

## 7. 备份策略

### 创建备份脚本 `backup_db.sh`：
```bash
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="inventory_system"
DB_USER="inventory_user"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U $DB_USER -h localhost -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/backup_$DATE.sql.gz"
```

设置定时任务：
```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨2点备份
0 2 * * * /path/to/backup_db.sh
```

## 8. 故障排除

### 常见问题：

1. **连接被拒绝**
   ```bash
   # 检查 PostgreSQL 服务状态
   sudo systemctl status postgresql
   
   # 检查端口监听
   sudo netstat -tlnp | grep 5432
   ```

2. **权限错误**
   ```bash
   # 检查用户权限
   sudo -u postgres psql -c "SELECT usename, usecreatedb, usesuper FROM pg_user;"
   ```

3. **数据库不存在**
   ```bash
   # 列出所有数据库
   sudo -u postgres psql -c "\l"
   ```

## 9. 使用 Docker PostgreSQL（替代方案）

```bash
# 运行 PostgreSQL 容器
docker run -d \
  --name postgres-db \
  -e POSTGRES_DB=inventory_system \
  -e POSTGRES_USER=inventory_user \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

# 连接到容器
docker exec -it postgres-db psql -U inventory_user -d inventory_system
```

## 10. 监控和维护

### 查看数据库状态：
```sql
-- 连接数据库后执行
SELECT version();
SELECT datname FROM pg_database;
SELECT count(*) FROM information_schema.tables;
```

### 清理日志：
```bash
# 清理 PostgreSQL 日志
sudo journalctl --rotate
sudo journalctl --vacuum-time=7d
```

### 更新统计信息：
```sql
-- 在 PostgreSQL shell 中执行
ANALYZE;
VACUUM;
```
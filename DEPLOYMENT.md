# 部署指南

## 开发环境快速启动

1. **一键启动**
```bash
./start.sh
```

2. **手动启动**
```bash
# 安装依赖
uv install

# 初始化数据库（仅首次）
uv run python init_db.py

# 启动服务
uv run python main.py
```

## 生产环境部署

### 1. 使用Docker部署

创建 Dockerfile：
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --frozen

# 初始化数据库
RUN uv run python init_db.py

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uv", "run", "python", "main.py"]
```

构建和运行：
```bash
docker build -t inventory-system .
docker run -p 8000:8000 inventory-system
```

### 2. 使用Nginx反向代理

nginx配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. PostgreSQL配置

安装PostgreSQL并创建数据库：
```sql
CREATE DATABASE inventory_system;
CREATE USER inventory_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_system TO inventory_user;
```

修改环境变量：
```bash
export DATABASE_URL="postgresql://inventory_user:your_password@localhost/inventory_system"
export SECRET_KEY="your-very-secure-secret-key"
```

### 4. systemd服务配置

创建 `/etc/systemd/system/inventory-system.service`：
```ini
[Unit]
Description=Inventory System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/inventory-system-python
Environment=DATABASE_URL=postgresql://user:pass@localhost/inventory_system
Environment=SECRET_KEY=your-secret-key
ExecStart=/path/to/uv run python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable inventory-system
sudo systemctl start inventory-system
```

### 5. SSL证书配置

使用Let's Encrypt：
```bash
sudo certbot --nginx -d your-domain.com
```

## 性能优化

1. **使用Gunicorn部署**
```bash
uv add gunicorn
uv run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Redis缓存**（可选）
```bash
uv add redis
# 在应用中集成Redis缓存
```

3. **数据库连接池**
```python
# 在database.py中配置连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0
)
```

## 监控和日志

1. **日志配置**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/inventory-system.log'),
        logging.StreamHandler()
    ]
)
```

2. **健康检查端点**
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

## 备份策略

1. **数据库备份**（PostgreSQL）
```bash
# 每日备份脚本
pg_dump inventory_system > backup_$(date +%Y%m%d).sql
```

2. **文件备份**
```bash
# 备份上传的文件和配置
tar -czf backup_files_$(date +%Y%m%d).tar.gz app/static/uploads/
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL环境变量
   - 确认数据库服务运行状态
   - 验证数据库用户权限

2. **静态文件404**
   - 检查静态文件路径配置
   - 确认Nginx配置正确

3. **权限错误**
   - 检查文件和目录权限
   - 确认服务运行用户

### 日志位置
- 应用日志：`/var/log/inventory-system.log`
- Nginx日志：`/var/log/nginx/access.log`
- 系统日志：`journalctl -u inventory-system`
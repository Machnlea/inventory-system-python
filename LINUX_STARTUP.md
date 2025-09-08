# Linux 启动脚本使用说明

本项目提供了多个Linux启动脚本，适用于不同的使用场景。所有脚本都使用 `uv` 工具链来管理Python环境和依赖。

## 系统要求

- **uv** - Python包管理器和环境管理器
- Linux (Ubuntu/CentOS/Debian等)
- 至少100MB可用磁盘空间
- 网络连接（用于安装依赖）

## 安装uv

如果尚未安装uv，请运行以下命令：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

或者访问：https://docs.astral.sh/uv/getting-started/installation/

安装后，确保将 `~/.cargo/bin` 添加到PATH中：
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

## 脚本文件说明

### 1. `start_simple.sh` - 简单启动脚本
**适用场景**：uv和项目依赖已安装，只需要快速启动服务

**功能**：
- 使用uv直接启动服务器
- 最简洁的启动方式

**使用方法**：
```bash
./start_simple.sh
```

### 2. `start_server.sh` - 标准启动脚本
**适用场景**：uv已安装，需要基本的错误检查

**功能**：
- 检查uv是否安装
- 检查主程序文件是否存在
- 使用uv启动服务器
- 友好的用户界面和彩色输出

**使用方法**：
```bash
./start_server.sh
```

### 3. `start_complete.sh` - 完整启动脚本
**适用场景**：首次部署或需要完整的环境检查

**功能**：
- 检查uv环境
- 自动初始化项目依赖（使用 `uv sync`）
- 自动初始化数据库（如不存在）
- 设置环境变量
- 启动服务器
- 详细的进度提示

**使用方法**：
```bash
./start_complete.sh
```

### 4. `start.sh` - 增强版启动脚本
**适用场景**：需要详细的状态信息和错误处理

**功能**：
- 完整的环境检查
- 详细的进度提示
- 使用uv管理依赖
- 错误处理和解决方案提示
- 彩色界面显示

**使用方法**：
```bash
./start.sh
```

## 使用建议

### 首次使用
1. 确保已安装uv
2. 使用 `./start_complete.sh` 或 `./start.sh` 进行首次启动
3. 脚本会自动初始化依赖、初始化数据库

### 日常使用
- 推荐使用 `./start_server.sh` 或 `./start_simple.sh`
- 这些脚本启动更快，适合日常开发使用

### 生产环境
- 使用 `./start_complete.sh` 确保环境完整性
- 可以考虑将脚本设置为systemd服务

## 常见问题

### 1. uv未找到
**错误**：`bash: uv: command not found`
**解决**：
- 安装uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
- 确保uv已添加到PATH中：`export PATH="$HOME/.cargo/bin:$PATH"`
- 重新启动终端或重新加载配置文件

### 2. 依赖初始化失败
**错误**：`uv sync` 失败
**解决**：
- 检查网络连接
- 确保有项目目录的写入权限
- 尝试手动运行：`uv sync -i https://mirrors.aliyun.com/pypi/simple/`

### 3. 数据库初始化失败
**错误**：数据库初始化失败
**解决**：
- 确保有data目录的写入权限
- 检查init_db.py文件是否存在
- 尝试手动运行：`uv run python init_db.py`

### 4. 服务器启动失败
**错误**：服务器启动失败
**解决**：
- 检查端口8000是否被占用：`netstat -tlnp | grep 8000`
- 确保main.py文件存在
- 查看错误日志获取详细信息

### 5. 权限问题
**错误**：`Permission denied`
**解决**：
- 确保脚本有执行权限：`chmod +x *.sh`
- 确保对项目目录有读写权限

## 手动启动命令

如果脚本启动失败，可以手动执行以下命令：

```bash
# 1. 初始化项目依赖（首次运行）
uv sync -i https://mirrors.aliyun.com/pypi/simple/

# 2. 初始化数据库（首次运行）
uv run python init_db.py

# 3. 启动服务器
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Systemd 服务配置（可选）

### 创建服务文件
```bash
sudo nano /etc/systemd/system/measuring-equipment.service
```

### 服务文件内容
```ini
[Unit]
Description=Measuring Equipment Ledger System
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
Environment=PYTHONIOENCODING=utf-8
Environment=PYTHONUTF8=1
ExecStart=/home/your_username/.cargo/bin/uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启用和启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable measuring-equipment
sudo systemctl start measuring-equipment
```

## 服务信息

- **服务地址**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **停止服务**：按 Ctrl+C

## 注意事项

1. 确保在项目根目录运行脚本
2. 首次运行可能需要几分钟时间安装依赖
3. 如果遇到权限问题，请检查文件权限
4. 建议定期备份数据库文件（data/inventory.db）
5. 生产环境建议使用systemd管理服务
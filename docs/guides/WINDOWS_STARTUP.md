# Windows 启动脚本使用说明

本项目提供了多个Windows启动脚本，适用于不同的使用场景。所有脚本都使用 `uv` 工具链来管理Python环境和依赖，用于启动计量器具台账系统。

## 系统要求

- **uv** - Python包管理器和环境管理器
- Windows 7/8/10/11
- 至少100MB可用磁盘空间
- 网络连接（用于安装依赖）

## 安装uv

如果尚未安装uv，请运行以下命令：
```powershell
powershell -c "irm https://astral.sh/uv/install.sh | iex"
```

或者访问：https://docs.astral.sh/uv/getting-started/installation/

## 脚本文件说明

### 1. `start_simple.bat` - 简单启动脚本
**适用场景**：uv和项目依赖已安装，只需要快速启动计量器具台账系统

**功能**：
- 使用uv直接启动计量器具台账系统
- 最简洁的启动方式

**使用方法**：
```cmd
start_simple.bat
```

### 2. `start_server.bat` - 标准启动脚本
**适用场景**：uv已安装，需要基本的错误检查

**功能**：
- 检查uv是否安装
- 检查主程序文件是否存在
- 使用uv启动计量器具台账系统
- 友好的用户界面

**使用方法**：
```cmd
start_server.bat
```

### 3. `start_complete.bat` - 完整启动脚本
**适用场景**：首次部署或需要完整的环境检查

**功能**：
- 检查uv环境
- 自动初始化项目依赖（使用 `uv sync`）
- 自动初始化数据库（如不存在）
- 设置环境变量
- 启动计量器具台账系统

**使用方法**：
```cmd
start_complete.bat
```

### 4. `start.bat` - 增强版启动脚本
**适用场景**：需要详细的状态信息和错误处理

**功能**：
- 完整的环境检查
- 详细的进度提示
- 使用uv管理依赖
- 错误处理和解决方案提示
- 美观的界面显示
- 启动计量器具台账系统

**使用方法**：
```cmd
start.bat
```

## 使用建议

### 首次使用
1. 确保已安装uv
2. 使用 `start_complete.bat` 或 `start.bat` 进行首次启动
3. 脚本会自动初始化依赖、初始化数据库

### 日常使用
- 推荐使用 `start_server.bat` 或 `start_simple.bat`
- 这些脚本启动更快，适合日常开发使用

### 生产环境
- 使用 `start_complete.bat` 确保环境完整性
- 可以考虑将脚本设置为Windows服务

## 常见问题

### 1. uv未找到
**错误**：`'uv' 不是内部或外部命令`
**解决**：
- 安装uv：`powershell -c "irm https://astral.sh/uv/install.sh | iex"`
- 确保uv已添加到系统PATH中
- 重启命令行或PowerShell

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
- 检查端口8000是否被占用
- 确保main.py文件存在
- 查看错误日志获取详细信息

## 手动启动命令

如果脚本启动失败，可以手动执行以下命令：

```cmd
# 1. 初始化项目依赖（首次运行）
uv sync -i https://mirrors.aliyun.com/pypi/simple/

# 2. 初始化数据库（首次运行）
uv run python init_db.py

# 3. 启动服务器
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 服务信息

- **服务地址**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **停止服务**：按 Ctrl+C

## 注意事项

1. 确保在项目根目录运行脚本
2. 首次运行可能需要几分钟时间安装依赖
3. 如果遇到权限问题，请以管理员身份运行脚本
4. 建议定期备份数据库文件（data/inventory.db）
5. 本系统专门用于管理计量器具台账数据
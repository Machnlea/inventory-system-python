# 项目结构说明

## 📁 根目录结构

本项目采用清晰的目录结构，便于维护和扩展。

### 🎯 核心文件
- `main.py` - 应用程序主入口
- `init_db.py` - 数据库初始化脚本
- `pyproject.toml` - 项目配置和依赖管理
- `README.md` - 项目主要文档
- `.gitignore` - Git版本控制忽略规则
- `.env.example` - 环境变量配置示例

### 🚀 启动脚本
- `start.sh` / `start.bat` - 基础启动脚本
- `start_complete.sh` / `start_complete.bat` - 完整启动脚本（包含数据库检查）
- `start_server.sh` / `start_server.bat` - 服务器专用启动脚本
- `start_simple.sh` / `start_simple.bat` - 简化启动脚本
- `deploy.sh` - 部署脚本

### 🐳 部署配置
- `docker-compose.yml` - Docker容器编排配置
- `Dockerfile` - Docker镜像构建配置
- `nginx.conf` - Nginx服务器配置

## 📁 目录详解

### 📂 `app/` - 应用程序核心
```
app/
├── api/           # API路由模块
├── core/          # 核心配置
├── crud/          # 数据操作层
├── db/            # 数据库配置
├── models/        # SQLAlchemy数据模型
├── schemas/       # Pydantic数据验证
├── static/        # 静态资源文件
└── templates/     # HTML模板文件
```

### 📂 `docs/` - 项目文档
```
docs/
├── README.md                    # 文档目录说明
├── DEPLOYMENT.md                # 部署指南
├── POSTGRESQL_SETUP.md          # PostgreSQL配置
├── external_api.md              # 外部API文档
├── guides/                      # 使用指南
│   ├── LINUX_STARTUP.md         # Linux启动指南
│   └── WINDOWS_STARTUP.md       # Windows启动指南
├── reports/                     # 技术报告
│   ├── COMPLETE_FIX_REPORT.md
│   ├── EDIT_FUNCTION_FIX_REPORT.md
│   ├── FINAL_COMPLETE_SOLUTION.md
│   └── SMART_NAME_MANAGEMENT_REPORT.md
└── requirements/                # 需求文档
    ├── 多标签页独立登录功能说明.md
    ├── 检定历史记录功能需求文档.md
    ├── 检定历史记录数据库字段扩展需求.md
    └── 设备生命周期需求文档.md
```

### 📂 `scripts/` - 工具脚本
```
scripts/
├── utils/                       # 工具脚本
│   └── final_verification.py    # 最终验证工具
├── backup_tool.py               # 备份工具
├── auto_backup.sh               # 自动备份脚本
├── auto_export.py               # 自动导出工具
├── restart_system.sh            # 系统重启脚本
├── setup_*.sh                  # 各种设置脚本
└── WebDAV_Config_Guide.md       # WebDAV配置指南
```

### 📂 `frontend/` - 前端资源
```
frontend/
├── node_modules/    # Node.js依赖包
├── package.json     # 前端项目配置
├── tailwind.config.js # Tailwind CSS配置
└── ...             # 其他前端资源
```

### 📂 `data/` - 数据存储
```
data/
├── uploads/         # 用户上传文件
└── logs/           # 应用日志文件
```

### 📂 `backups/` - 备份文件
- 数据库和应用备份文件存储目录

### 📂 `logs/` - 日志文件
- 应用运行日志文件

### 📂 `test_data/` - 测试数据
- 用于开发和测试的示例数据

## 🔧 开发规范

### 文件组织原则
1. **核心文件保留在根目录** - 便于快速访问
2. **文档分类存储** - 按类型和用途分类
3. **脚本集中管理** - 所有工具脚本放在scripts目录
4. **临时文件自动忽略** - 通过.gitignore排除版本控制

### 新增文件指南
- **文档文件** → 放入docs相应子目录
- **工具脚本** → 放入scripts或scripts/utils
- **配置文件** → 根目录或相应模块目录
- **测试文件** → 对应模块的tests子目录

### 清理维护
- 定期清理临时文件和日志
- 保持文档结构清晰和更新
- 遵循.gitignore规则避免提交不必要的文件

## 📋 目录用途总结

| 目录 | 用途 | 说明 |
|------|------|------|
| `app/` | 应用核心 | 主要业务逻辑和API |
| `docs/` | 项目文档 | 所有相关文档和说明 |
| `scripts/` | 工具脚本 | 自动化和管理脚本 |
| `frontend/` | 前端资源 | UI相关文件和依赖 |
| `data/` | 运行数据 | 用户数据和日志 |
| `backups/` | 备份文件 | 数据备份存储 |
| `logs/` | 日志文件 | 系统运行日志 |
| `test_data/` | 测试数据 | 开发测试用数据 |

这样的目录结构既保持了项目的整洁性，又提高了文件的可维护性和可访问性。
# 设备台账管理系统

一个基于 FastAPI + SQLite 的现代化设备管理系统，提供完整的设备台账管理、用户权限控制、部门管理等功能。

## 🚀 功能特性

### 核心功能
- **设备管理** - 设备的增删改查、状态管理、分类管理
- **用户管理** - 多角色用户系统（管理员/部门用户）、权限控制
- **部门管理** - 组织架构管理、部门用户分配
- **设备类别管理** - 设备分类、自定义编号规则
- **检定管理** - 设备检定周期管理、到期提醒
- **附件管理** - 设备相关文档、证书上传管理
- **系统管理** - 数据库备份恢复、系统设置、日志管理

### 高级功能
- **权限控制** - 基于角色的访问控制（RBAC）
- **数据导入导出** - Excel 批量导入、数据导出
- **审计日志** - 完整的操作记录和审计跟踪
- **统计报表** - 设备统计、部门报表、数据可视化
- **外部API集成** - 支持与其他系统对接

## 🛠 技术栈

### 后端技术
- **FastAPI** - 现代化的 Python Web 框架
- **SQLAlchemy 2.0** - Python SQL 工具包和 ORM
- **SQLite** - 轻量级数据库
- **Alembic** - 数据库迁移工具
- **Pydantic** - 数据验证和序列化
- **JWT** - JSON Web Token 认证
- **bcrypt** - 密码加密

### 前端技术
- **HTML5 + CSS3** - 响应式设计
- **JavaScript (ES6+)** - 现代前端开发
- **Jinja2** - 模板引擎
- **Bootstrap** - UI 框架
- **Font Awesome** - 图标库

### 开发工具
- **Uvicorn** - ASGI 服务器
- **Python 3.12+** - 编程语言
- **Git** - 版本控制

## 📦 项目结构

```
inventory-system-python/
├── app/                          # 应用主目录
│   ├── api/                      # API 路由
│   │   ├── auth.py              # 认证相关
│   │   ├── users.py             # 用户管理
│   │   ├── equipment.py         # 设备管理
│   │   ├── departments.py       # 部门管理
│   │   ├── categories.py       # 类别管理
│   │   ├── calibration.py       # 检定管理
│   │   ├── attachments.py      # 附件管理
│   │   ├── system.py           # 系统管理
│   │   ├── logs.py             # 日志管理
│   │   ├── reports.py          # 报表管理
│   │   └── ...
│   ├── core/                    # 核心功能
│   │   ├── config.py           # 配置管理
│   │   ├── security.py        # 安全相关
│   │   ├── logging.py         # 日志系统
│   │   └── middleware.py      # 中间件
│   ├── db/                     # 数据库相关
│   │   ├── database.py        # 数据库连接
│   │   └── migrations/        # 数据库迁移
│   ├── models/                 # 数据模型
│   │   └── models.py          # SQLAlchemy 模型
│   ├── schemas/               # Pydantic 模式
│   │   └── schemas.py        # 数据验证模式
│   ├── templates/             # HTML 模板
│   │   ├── index.html         # 首页
│   │   ├── login.html         # 登录页
│   │   ├── dashboard.html     # 仪表盘
│   │   ├── equipment_management.html  # 设备管理
│   │   ├── users.html         # 用户管理
│   │   ├── settings.html      # 系统设置
│   │   └── ...
│   └── static/                # 静态资源
│       ├── css/               # 样式文件
│       ├── js/                # JavaScript 文件
│       ├── images/           # 图片资源
│       └── ...
├── data/                      # 数据目录
│   ├── inventory.db           # SQLite 数据库
│   └── uploads/               # 上传文件
├── logs/                      # 日志目录
│   ├── app.log               # 应用日志
│   ├── access.log            # 访问日志
│   └── security.log          # 安全日志
├── migrations/               # 数据库迁移文件
├── frontend/                 # 前端资源（可选）
├── main.py                   # 应用入口
├── pyproject.toml           # 项目配置
└── README.md                # 项目说明
```

## 🗄️ 数据模型

系统包含以下主要数据模型：

1. **User** - 用户表
2. **Department** - 部门表
3. **Category** - 设备类别表
4. **Equipment** - 设备表
5. **CalibrationRecord** - 检定记录表
6. **Attachment** - 附件表
7. **AuditLog** - 审计日志表
8. **SystemSetting** - 系统设置表

## 🚀 快速开始

### 环境要求
- Python 3.12 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd inventory-system-python
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或者
   .venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   # 或者使用 pyproject.toml
   pip install .
   ```

4. **数据库初始化**
   ```bash
   # 数据库表会在首次运行时自动创建
   python main.py
   ```

5. **启动应用**
   ```bash
   # 开发模式
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   
   # 生产模式
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. **访问应用**
   - 主页: http://localhost:8000
   - API 文档: http://localhost:8000/docs
   - 管理员登录: 用户名 `admin`，密码 `admin123`

## 🔧 配置说明

### 环境变量
可以通过环境变量配置系统：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/inventory.db

# JWT 配置
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_HOURS=2

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 数据库配置
- 默认使用 SQLite 数据库
- 数据库文件位置: `data/inventory.db`
- 支持 PostgreSQL（通过环境变量配置）

## 📊 主要功能模块

### 1. 设备管理
- 设备信息录入、编辑、删除
- 设备状态管理（在用、维修、报废等）
- 设备分类和编号规则
- 设备搜索和筛选
- 批量导入导出

### 2. 用户管理
- 多角色用户系统
- 用户权限分配
- 部门用户关联
- 密码策略和安全控制

### 3. 部门管理
- 组织架构管理
- 部门用户分配
- 部门权限控制

### 4. 检定管理
- 设备检定周期设置
- 检定提醒和通知
- 检定记录管理

### 5. 附件管理
- 设备相关文档上传
- 证书和图片管理
- 文件分类和版本控制

### 6. 系统管理
- 数据库备份和恢复
- 系统设置配置
- 日志管理和监控
- 系统统计信息

## 🔐 安全特性

- **JWT 认证** - 无状态的用户认证
- **密码加密** - bcrypt 加密存储
- **权限控制** - 基于角色的访问控制
- **审计日志** - 完整的操作记录
- **安全中间件** - 防止常见Web攻击
- **会话管理** - 用户会话控制

## 📈 系统监控

### 日志系统
- **应用日志** (`logs/app.log`) - 系统运行日志
- **访问日志** (`logs/access.log`) - API访问记录
- **安全日志** (`logs/security.log`) - 安全事件记录

### 监控功能
- 系统状态监控
- 数据库性能监控
- 用户活动统计
- 错误日志分析

## 🔧 开发指南

### API 开发
- RESTful API 设计
- OpenAPI/Swagger 文档
- 统一的错误处理
- 请求/响应验证

### 数据库操作
- SQLAlchemy ORM
- 数据库迁移管理
- 事务处理
- 查询优化

### 前端开发
- 响应式设计
- 现代JavaScript开发
- 模块化组件
- API 集成

## 🚀 部署指南

### 开发环境
```bash
# 启动开发服务器
source .venv/bin/activate
python -m uvicorn main:app --reload
```

### 生产环境
```bash
# 使用 Gunicorn 部署
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# 或者使用 Docker
docker build -t inventory-system .
docker run -p 8000:8000 inventory-system
```

## 📝 更新日志

### v1.0.0 (2025-09-19)
- ✅ 完整的设备管理功能
- ✅ 用户权限管理系统
- ✅ 部门管理功能
- ✅ 设备类别管理
- ✅ 检定管理系统
- ✅ 附件管理系统
- ✅ 数据库管理工具
- ✅ 审计日志系统
- ✅ 统计报表功能
- ✅ 外部API集成

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看项目文档
2. 搜索已存在的 Issues
3. 创建新的 Issue 描述问题
4. 联系维护团队

## 🔗 相关链接

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://www.sqlalchemy.org/)
- [Bootstrap 文档](https://getbootstrap.com/docs/)
- [JWT 说明](https://jwt.io/)

---

**设备台账管理系统** - 让设备管理更简单、更高效！
# 计量器具台账系统

<div align="center">

![计量器具台账系统](https://img.shields.io/badge/计量器具台账系统-v1.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green)
![SQLite](https://img.shields.io/badge/SQLite-supported-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**一个现代化的计量器具管理系统，支持智能检定计划、权限控制和全文本搜索**

[功能特色](#-功能特色) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [使用说明](#-使用说明) • [API文档](#-api文档) • [部署指南](#-部署指南)

</div>

---

## 📖 项目简介

### 系统概述
计量器具台账系统是一个基于FastAPI + SQLite的现代化Web应用，专门用于管理企业的计量设备信息、检定记录和设备生命周期。系统提供完整的设备信息管理、智能检定计划、权限控制和全文本搜索功能。

### 核心特性
- 🏢 **智能设备管理**：支持设备台账的完整生命周期管理
- 📅 **检定周期管理**：自动计算检定日期，支持内检/外检区分
- 🔐 **权限控制系统**：基于角色的访问控制和设备类别权限分配
- 🔍 **全文本搜索**：支持多字段设备信息搜索
- 📊 **数据导入导出**：Excel格式的批量数据处理
- 📝 **审计日志**：完整的用户操作追踪
- 📈 **可视化统计**：Chart.js驱动的数据仪表盘

---

## 🚀 快速开始

### 环境要求
- **Python**: 3.12+
- **包管理器**: uv (推荐) 或 pip
- **操作系统**: Windows / Linux / macOS
- **内存**: 最少 512MB RAM
- **存储**: 最少 100MB 可用空间

### 快速启动

#### 方法一：使用启动脚本（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd inventory-system-python

# 赋予执行权限
chmod +x start.sh

# 启动系统
./start.sh
```

#### 方法二：手动启动
```bash
# 克隆项目
git clone <repository-url>
cd inventory-system-python

# 安装依赖
uv sync

# 初始化数据库
uv run python init_db.py

# 启动服务器
uv run python main.py
```

#### 方法三：使用传统pip
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动服务器
python main.py
```

### 访问系统
启动成功后，在浏览器中访问：`http://localhost:8000`

**默认管理员账户：**
- 用户名：`admin`
- 密码：`admin123`

---

## 🏗️ 技术架构

### 技术栈
<div align="center">

| 技术 | 版本 | 描述 |
|------|------|------|
| **后端框架** | FastAPI 0.116+ | 现代化Python Web框架 |
| **数据库** | SQLite / PostgreSQL | 数据存储 |
| **ORM** | SQLAlchemy 2.0+ | 数据库操作 |
| **认证** | JWT | 用户认证和授权 |
| **前端框架** | Tailwind CSS | 现代化CSS框架 |
| **UI组件** | Bootstrap 5 | 部分页面UI组件 |
| **图表库** | Chart.js | 数据可视化 |
| **ASGI服务器** | uvicorn | 应用服务器 |
| **密码加密** | bcrypt | 密码安全 |
| **图标库** | Font Awesome 6.0 | 图标资源 |

</div>

### 项目结构
```
inventory-system-python/
├── app/
│   ├── api/                  # API路由模块
│   │   ├── auth.py          # 认证接口
│   │   ├── equipment.py     # 设备管理接口
│   │   ├── users.py         # 用户管理接口
│   │   ├── categories.py    # 设备类别管理
│   │   ├── departments.py   # 部门管理
│   │   ├── calibration.py   # 检定管理
│   │   ├── dashboard.py     # 仪表盘
│   │   ├── audit_logs.py    # 操作日志
│   │   ├── import_export.py # 数据导入导出
│   │   ├── attachments.py   # 附件管理
│   │   ├── settings.py      # 系统设置
│   │   ├── reports.py       # 统计报表
│   │   ├── department_users.py # 部门用户管理
│   │   └── external_api.py  # 外部系统API
│   ├── core/                # 核心配置
│   │   ├── config.py        # 应用配置
│   │   ├── security.py      # 安全相关
│   │   ├── permissions.py   # 权限控制
│   │   └── session_manager.py # 会话管理
│   ├── crud/                # 数据操作层
│   │   ├── equipment.py     # 设备数据操作
│   │   ├── users.py         # 用户数据操作
│   │   ├── categories.py    # 类别数据操作
│   │   ├── departments.py   # 部门数据操作
│   │   └── calibration.py   # 检定数据操作
│   ├── models/              # SQLAlchemy模型
│   │   └── models.py        # 数据模型定义
│   ├── schemas/             # Pydantic模型
│   │   ├── schemas.py       # 基础数据模型
│   │   └── calibration.py   # 检定相关模型
│   ├── utils/               # 工具函数
│   │   ├── auto_id.py       # 自动编号生成
│   │   ├── predefined_name_manager.py # 预定义名称管理
│   │   ├── equipment_mapping.py # 设备映射
│   │   ├── audit.py         # 审计日志
│   │   └── files.py         # 文件处理
│   ├── static/              # 静态资源
│   │   ├── css/             # 样式文件
│   │   ├── js/              # JavaScript文件
│   │   └── images/          # 图片资源
│   └── templates/           # HTML模板
│       ├── components/      # 组件模板
│       ├── error/           # 错误页面
│       └── *.html           # 页面模板
├── data/                   # 数据目录
├── docs/                   # 文档目录
├── scripts/                # 脚本目录
├── main.py                 # 应用入口
├── init_db.py              # 数据库初始化
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── .env.example           # 环境变量示例
├── docker-compose.yml      # Docker配置
├── Dockerfile             # Docker镜像配置
└── 启动脚本               # 各种启动和部署脚本
```

### 数据库设计
系统采用关系型数据库设计，主要包含以下数据表：

#### 核心数据表
| 表名 | 描述 | 主要字段 |
|------|------|----------|
| `users` | 用户表 | 用户信息、权限、部门关联 |
| `equipments` | 设备表 | 设备基本信息、检定信息、状态 |
| `equipment_categories` | 设备类别表 | 类别信息、预定义名称 |
| `departments` | 部门表 | 组织架构信息 |
| `calibration_history` | 检定历史表 | 检定记录、结果追踪 |
| `audit_logs` | 操作日志表 | 用户操作审计 |
| `equipment_attachments` | 附件表 | 设备附件和证书 |

#### 数据关系
- 用户 ↔ 设备类别：多对多关系（权限控制）
- 设备 ↔ 部门：多对一关系
- 设备 ↔ 设备类别：多对一关系
- 设备 ↔ 检定历史：一对多关系
- 设备 ↔ 附件：一对多关系

---

## ✨ 功能特色

### 1. 智能编号系统
- **自动编号生成**：根据设备类别和器具名称自动生成内部编号
- **预定义名称管理**：支持预定义器具名称的智能编号分配
- **编号连续性保证**：确保编号的连续性和可追溯性
- **超过999台设备支持**：智能处理设备数量超过999台时的编号生成

### 2. 检定管理系统
- **检定周期管理**：支持6个月/12个月/24个月/随坏随换等多种周期
- **内检/外检区分**：不同检定方式的差异化处理
- **检定结果管理**：合格/不合格结果的自动状态更新
- **检定历史追踪**：完整的检定记录和历史查询
- **智能提醒**：自动计算并提醒即将到期的设备

### 3. 权限控制系统
- **基于角色的访问控制**：管理员/普通用户/部门用户三种角色
- **设备类别权限**：基于设备类别的细粒度权限控制
- **操作审计**：完整的用户操作日志记录
- **安全认证**：JWT Token认证和会话管理

### 4. 数据导入导出
- **Excel模板下载**：标准化的数据导入模板
- **批量数据导入**：支持Excel文件的批量导入
- **多格式导出**：月度计划、年度计划、筛选结果导出
- **数据验证**：导入时的数据完整性验证

### 5. 全文本搜索
- **多字段搜索**：支持设备名称、型号、编号等多字段搜索
- **智能搜索**：支持部门名称和设备类别名称搜索
- **组合筛选**：多条件组合筛选功能
- **搜索结果导出**：支持搜索结果的批量导出

### 6. 用户界面特色
- **响应式设计**：支持桌面和移动设备
- **模态框确认**：所有删除操作都有二次确认模态框
- **通知系统**：统一的浮动通知管理
- **多标签页支持**：支持多标签页独立登录和状态同步

---

## 📖 使用说明

### 系统登录
1. 打开浏览器访问系统地址
2. 使用管理员账户登录：
   - 用户名：`admin`
   - 密码：`admin123`
3. 登录成功后进入仪表盘页面

### 设备管理
#### 添加设备
1. 点击"设备管理"菜单
2. 点击"添加设备"按钮
3. 填写设备基本信息：
   - 选择所属部门和设备类别
   - 填写设备名称、型号等信息
   - 设置检定周期和检定日期
4. 点击"保存"完成添加

#### 设备查询
1. 在设备管理页面使用搜索功能
2. 支持按设备名称、型号、编号等字段搜索
3. 使用高级筛选功能进行多条件查询
4. 可以按部门、类别、状态等进行筛选

#### 批量操作
1. 选择要操作的设备（勾选复选框）
2. 点击批量操作按钮
3. 选择操作类型：删除、导出、转移、状态变更、检定更新
4. 确认操作并执行

### 检定管理
#### 更新检定信息
1. 在设备管理页面点击"检定"按钮
2. 填写检定信息：
   - 检定日期
   - 检定结果（合格/不合格）
   - 证书信息（外检时）
3. 系统自动更新设备状态和有效期

#### 批量检定更新
1. 选择要更新检定日期的设备
2. 点击"批量操作" → "检定更新"
3. 设置新的检定日期
4. 选择要更新的字段（检定结果、证书信息等）
5. 确认并执行批量更新

### 用户管理
#### 创建用户
1. 点击"用户管理"菜单
2. 点击"添加用户"按钮
3. 填写用户信息：
   - 用户名和密码
   - 用户类型（管理员/普通用户/部门用户）
   - 关联部门（部门用户）
4. 分配设备类别权限
5. 保存用户信息

#### 权限管理
1. 在用户管理页面选择用户
2. 点击"权限管理"按钮
3. 为用户分配可管理的设备类别
4. 保存权限设置

### 数据导入导出
#### 数据导入
1. 在设备管理页面点击"导入"按钮
2. 下载Excel模板
3. 按模板格式填写数据
4. 上传填写好的Excel文件
5. 系统自动验证并导入数据

#### 数据导出
1. 使用筛选功能选择要导出的设备
2. 点击"导出"按钮
3. 选择导出格式：
   - 月度检定计划
   - 年度检定计划
   - 当前筛选结果
4. 下载导出的Excel文件

### 统计报表
1. 点击"统计报表"菜单
2. 查看各种统计图表：
   - 设备按类别分布
   - 设备按部门分布
   - 检定到期统计
   - 设备状态统计
3. 支持图表类型切换（柱状图/饼图）

---

## 🔌 API文档

### 认证接口
#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### 获取当前用户信息
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### 设备管理接口
#### 获取设备列表
```http
GET /api/equipment/?page=1&page_size=20&sort_field=name&sort_order=asc
Authorization: Bearer <token>
```

#### 创建设备
```http
POST /api/equipment/
Authorization: Bearer <token>
Content-Type: application/json

{
  "department_id": 1,
  "category_id": 1,
  "name": "温度计",
  "model": "T-100",
  "calibration_cycle": 12,
  "calibration_date": "2024-01-01"
}
```

#### 设备筛选
```http
POST /api/equipment/filter
Authorization: Bearer <token>
Content-Type: application/json

{
  "department_id": 1,
  "category_id": 1,
  "status": "在用",
  "search_text": "温度计"
}
```

#### 全文本搜索
```http
POST /api/equipment/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "温度计",
  "page": 1,
  "page_size": 20
}
```

### 检定管理接口
#### 获取检定历史
```http
GET /api/calibration/equipment/{equipment_id}/history
Authorization: Bearer <token>
```

#### 更新检定信息
```http
POST /api/calibration/equipment/{equipment_id}/calibration
Authorization: Bearer <token>
Content-Type: application/json

{
  "calibration_date": "2024-01-01",
  "calibration_result": "合格",
  "calibration_method": "内检"
}
```

### 用户管理接口
#### 获取用户列表
```http
GET /api/users/?page=1&page_size=20
Authorization: Bearer <token>
```

#### 创建用户
```http
POST /api/users/
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "newuser",
  "password": "password123",
  "is_admin": false,
  "user_type": "department_user",
  "department_id": 1
}
```

### 统计接口
#### 获取统计数据
```http
GET /api/dashboard/stats
Authorization: Bearer <token>
```

#### 获取月度待检设备
```http
GET /api/dashboard/monthly-due-equipments
Authorization: Bearer <token>
```

### 外部系统API
#### 健康检查
```http
GET /api/external/health
X-API-Key: <api_key>
```

#### 获取所有设备信息
```http
GET /api/external/equipment
X-API-Key: <api_key>
```

---

## 🚀 部署指南

### 开发环境部署
#### 1. 环境准备
```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd inventory-system-python

# 安装依赖
uv sync
```

#### 2. 数据库初始化
```bash
# 初始化数据库
uv run python init_db.py

# 创建管理员账户
# 系统会提示输入管理员用户名和密码
```

#### 3. 启动开发服务器
```bash
# 启动开发服务器
uv run python main.py

# 或使用uvicorn
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 生产环境部署
#### Docker部署
```bash
# 构建镜像
docker build -t inventory-system .

# 使用docker-compose启动
docker-compose up -d
```

#### 手动部署
```bash
# 1. 安装依赖
uv sync --production

# 2. 设置环境变量
cp .env.example .env
# 编辑.env文件配置数据库等参数

# 3. 初始化数据库
uv run python init_db.py

# 4. 启动服务
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Nginx配置
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

    location /static {
        alias /path/to/your/project/app/static;
        expires 30d;
    }
}
```

### 环境变量配置
```bash
# .env文件示例
DATABASE_URL=sqlite:///./inventory.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
API_KEY=your-api-key-here
```

### 数据库配置
#### SQLite（默认）
```python
DATABASE_URL = "sqlite:///./inventory.db"
```

#### PostgreSQL（生产环境推荐）
```python
DATABASE_URL = "postgresql://username:password@localhost/inventory"
```

---

## 🔧 系统配置

### 基础配置
编辑 `app/core/config.py` 文件：

```python
class Settings(BaseSettings):
    # 应用配置
    app_name: str = "计量器具台账系统"
    app_version: str = "1.0.0"
    
    # 数据库配置
    database_url: str = "sqlite:///./inventory.db"
    
    # 安全配置
    secret_key: str = "your-secret-key"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # 文件上传配置
    upload_dir: str = "data/uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # API配置
    api_key: str = "your-api-key"
```

### 权限配置
系统支持三种用户角色：
1. **管理员**：拥有所有权限
2. **普通用户**：可以查看和管理所有设备
3. **部门用户**：只能管理指定部门的设备

### 设备类别配置
支持预定义器具名称的智能编号：
- 每个设备类别可以设置预定义器具名称
- 系统根据类别和器具名称自动生成内部编号
- 支持编号连续性管理

---

## 🛠️ 开发指南

### 代码结构
- **api/**：API路由定义
- **core/**：核心配置和安全逻辑
- **crud/**：数据库操作层
- **models/**：SQLAlchemy模型定义
- **schemas/**：Pydantic数据模型
- **utils/**：工具函数
- **templates/**：HTML模板
- **static/**：静态资源

### 开发规范
1. **代码风格**：遵循PEP 8规范
2. **类型注解**：使用Python类型注解
3. **异步处理**：API接口使用async/await
4. **错误处理**：统一的错误处理机制
5. **日志记录**：使用logging模块记录日志

### 添加新功能
1. 在 `models/models.py` 中定义数据模型
2. 在 `schemas/schemas.py` 中定义Pydantic模型
3. 在 `crud/` 中创建数据操作函数
4. 在 `api/` 中创建API路由
5. 在 `templates/` 中创建前端页面

### 数据库迁移
```bash
# 创建迁移脚本
uv run python create_migration.py "migration_description"

# 应用迁移
uv run python apply_migrations.py
```

---

## 🔍 故障排除

### 常见问题
#### 1. 数据库连接失败
```bash
# 检查数据库文件是否存在
ls -la data/

# 检查数据库权限
chmod 755 data/
chmod 644 data/inventory.db
```

#### 2. 文件上传失败
```bash
# 检查上传目录权限
mkdir -p data/uploads
chmod 755 data/uploads
```

#### 3. JWT认证失败
```bash
# 检查SECRET_KEY配置
echo $SECRET_KEY

# 重新生成密钥
openssl rand -hex 32
```

#### 4. 前端页面无法访问
```bash
# 检查静态文件权限
chmod -R 755 app/static/

# 检查模板文件权限
chmod -R 755 app/templates/
```

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看访问日志
tail -f logs/access.log
```

### 性能优化
```bash
# 创建数据库索引
uv run python create_indexes.py

# 清理过期日志
uv run python cleanup_logs.py

# 优化数据库
uv run python optimize_database.py
```

---

## 📊 性能监控

### 系统指标
- **响应时间**：API响应时间监控
- **并发连接**：数据库连接池状态
- **内存使用**：应用内存使用情况
- **磁盘空间**：上传文件和数据库存储

### 监控工具
```bash
# 查看系统状态
uv run python system_status.py

# 性能测试
uv run python performance_test.py

# 数据库健康检查
uv run python database_health.py
```

---

## 🤝 贡献指南

### 贡献流程
1. Fork项目
2. 创建功能分支
3. 提交代码更改
4. 创建Pull Request
5. 代码审查
6. 合并到主分支

### 代码规范
- 遵循PEP 8代码风格
- 使用类型注解
- 编写单元测试
- 更新相关文档

### 问题反馈
- 使用GitHub Issues报告问题
- 提供详细的问题描述
- 包含复现步骤和环境信息

---

## 📄 许可证

本项目采用MIT许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包和ORM
- [Bootstrap](https://getbootstrap.com/) - 响应式前端框架
- [Chart.js](https://www.chartjs.org/) - 数据可视化图表库

---

## 📞 联系方式

- **项目地址**：[GitHub Repository](https://github.com/your-username/inventory-system-python)
- **问题反馈**：[GitHub Issues](https://github.com/your-username/inventory-system-python/issues)
- **邮件联系**：your-email@example.com

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请考虑给我们一个Star！**

![Star History](https://img.shields.io/github/stars/your-username/inventory-system-python?style=social)

</div>
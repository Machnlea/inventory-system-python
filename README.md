# 设备台账管理系统

<div align="center">

![设备台账管理系统](https://img.shields.io/badge/设备台账管理系统-v1.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange)
![SQLite](https://img.shields.io/badge/SQLite-supported-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.x-cyan)
![Python](https://img.shields.io/badge/Python-3.12+-yellow)
![License](https://img.shields.io/badge/License-MIT-red)

**基于 FastAPI + SQLite 的现代化设备管理系统，提供完整的设备台账管理、用户权限控制、部门管理和系统监控功能**

[功能特色](#-功能特色) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [使用说明](#-使用说明) • [API文档](#-api文档) • [部署指南](#-部署指南) • [系统监控](#-系统监控)

</div>

---

## 📖 项目简介

### 系统概述
设备台账管理系统是一个基于 FastAPI + SQLAlchemy 2.0 的现代化 Web 应用，专门用于管理企业的设备台账信息、检定记录、用户权限和系统监控。系统提供完整的设备生命周期管理、智能检定计划、多层级权限控制、审计日志追踪和实时系统监控功能。

### 核心特性
- 🏢 **智能设备管理**：支持设备的完整生命周期管理，包括添加、编辑、删除、状态变更
- 📅 **智能检定系统**：自动计算检定周期，支持内检/外检区分，到期提醒和历史记录
- 🔐 **多级权限控制**：基于角色的访问控制（RBAC），支持管理员、普通用户、部门用户三种角色
- 🏗️ **组织架构管理**：完整的部门管理功能，支持部门用户分配和权限控制
- 📊 **数据导入导出**：Excel 格式的批量数据处理，支持模板下载和数据验证
- 📝 **审计日志系统**：完整的用户操作追踪，包括访问日志、安全日志和应用日志
- 📈 **统计报表分析**：Chart.js 驱动的数据可视化，支持多维度统计分析
- 🔧 **系统管理工具**：数据库备份恢复、系统配置管理、日志监控和分析
- 📎 **附件管理系统**：设备相关文档、证书上传管理，支持文件分类和版本控制
- 🔌 **外部 API 集成**：RESTful API 接口，支持与其他系统对接和数据交换

---

## 🚀 快速开始

### 环境要求
- **Python**: 3.12 或更高版本
- **包管理器**: pip (推荐) 或 uv
- **操作系统**: Windows / Linux / macOS
- **内存**: 最少 1GB RAM
- **存储**: 最少 500MB 可用空间
- **数据库**: SQLite 3.x (默认) 或 PostgreSQL 12+

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd inventory-system-python
```

#### 2. 创建虚拟环境
```bash
# 使用 Python 内置 venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者
.venv\Scripts\activate     # Windows

# 或者使用 uv (推荐)
uv venv
source .venv/bin/activate
```

#### 3. 安装依赖
```bash
# 使用 pip
pip install -r requirements.txt

# 或者使用 uv
uv pip install -r requirements.txt

# 或者使用 pyproject.toml
pip install .
```

#### 4. 数据库初始化
```bash
# 数据库表会在首次运行时自动创建
# 系统会自动创建管理员账户
python -c "from app.db.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"
```

#### 5. 启动应用
```bash
# 开发模式（推荐）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 或者直接运行
python main.py
```

#### 6. 访问系统
启动成功后，在浏览器中访问：
- **系统主页**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **API 文档(ReDoc)**: http://localhost:8000/redoc

**默认管理员账户：**
- 用户名：`admin`
- 密码：`admin123`

#### 7. 系统验证
登录后，请验证以下核心功能：
- ✅ 仪表盘数据加载正常
- ✅ 设备管理页面可访问
- ✅ 用户权限控制生效
- ✅ 日志系统正常运行
- ✅ 系统设置页面可用

---

## 🏗️ 技术架构

### 技术栈
<div align="center">

| 类别 | 技术 | 版本 | 描述 |
|------|------|------|------|
| **后端框架** | FastAPI | 0.116+ | 现代化 Python Web 框架，自动 API 文档生成 |
| **ORM 框架** | SQLAlchemy | 2.0+ | Python SQL 工具包和对象关系映射 |
| **数据库** | SQLite / PostgreSQL | 3.x / 12+ | 轻量级数据库 / 生产级数据库 |
| **认证授权** | JWT + bcrypt | - | JSON Web Token 认证和密码加密 |
| **数据验证** | Pydantic | 2.0+ | 数据验证和序列化 |
| **模板引擎** | Jinja2 | 3.1+ | HTML 模板渲染 |
| **前端框架** | Tailwind CSS | 3.x | 实用优先的 CSS 框架 |
| **图表库** | Chart.js | 3.x | 数据可视化图表库 |
| **图标库** | Font Awesome | 6.x | 矢量图标库 |
| **ASGI 服务器** | Uvicorn | 0.35+ | 高性能 ASGI 服务器 |
| **数据库迁移** | Alembic | 1.16+ | 数据库版本控制工具 |
| **Excel 处理** | openpyxl + pandas | 3.1+ / 2.3+ | 数据导入导出支持 |
| **系统监控** | psutil | 5.9+ | 系统性能监控 |
| **日志管理** | Python logging | - | 多级别日志系统 |

</div>

### 项目结构
```
inventory-system-python/
├── app/                           # 应用主目录
│   ├── api/                      # API 路由模块 (18个模块)
│   │   ├── auth.py              # 用户认证和授权
│   │   ├── users.py             # 用户管理 (22个接口)
│   │   ├── equipment.py         # 设备管理 (16个接口)
│   │   ├── departments.py       # 部门管理 (6个接口)
│   │   ├── categories.py        # 设备类别管理 (11个接口)
│   │   ├── calibration.py       # 检定管理 (9个接口)
│   │   ├── dashboard.py         # 仪表盘统计 (2个接口)
│   │   ├── audit_logs.py        # 操作日志 (4个接口)
│   │   ├── import_export.py     # 数据导入导出 (5个接口)
│   │   ├── attachments.py       # 附件管理 (8个接口)
│   │   ├── settings.py          # 系统设置 (3个接口)
│   │   ├── reports.py           # 统计报表 (8个接口)
│   │   ├── department_users.py  # 部门用户管理 (15个接口)
│   │   ├── external_api.py      # 外部系统 API (7个接口)
│   │   ├── logs.py              # 日志管理 (8个接口)
│   │   └── system.py            # 系统管理工具 (16个接口)
│   ├── core/                    # 核心功能模块 (7个模块)
│   │   ├── config.py           # 应用配置管理
│   │   ├── security.py         # 安全相关功能
│   │   ├── permissions.py      # 权限控制逻辑
│   │   ├── logging.py          # 日志系统配置
│   │   ├── middleware.py       # 中间件组件
│   │   └── session_manager.py # 会话管理
│   ├── models/                 # 数据模型 (10个核心模型)
│   │   └── models.py          # SQLAlchemy 数据模型定义
│   ├── schemas/               # Pydantic 数据模型
│   │   └── schemas.py        # API 请求/响应模型
│   ├── templates/             # HTML 模板 (16个页面)
│   │   ├── index.html         # 系统首页
│   │   ├── login.html         # 用户登录
│   │   ├── dashboard.html     # 仪表盘
│   │   ├── equipment_management.html # 设备管理
│   │   ├── users.html         # 用户管理
│   │   ├── departments.html   # 部门管理
│   │   ├── categories.html    # 类别管理
│   │   ├── settings.html      # 系统设置
│   │   ├── reports.html       # 统计报表
│   │   ├── audit.html         # 操作日志
│   │   ├── logs.html          # 日志管理
│   │   ├── equipment_edit.html # 设备编辑
│   │   ├── equipment_view.html # 设备详情
│   │   ├── forgot_password.html # 密码重置
│   │   ├── department_login.html # 部门登录
│   │   └── department_dashboard.html # 部门仪表盘
│   └── static/                # 静态资源
│       ├── css/               # 样式文件
│       ├── js/                # JavaScript 文件
│       ├── images/           # 图片资源
│       └── js/api-client.js   # API 客户端
├── data/                       # 数据目录
│   ├── inventory.db           # SQLite 数据库文件
│   └── uploads/               # 文件上传目录
├── logs/                      # 日志目录
│   ├── app.log               # 应用运行日志
│   ├── access.log            # API 访问日志
│   └── security.log          # 安全事件日志
├── migrations/               # 数据库迁移文件
├── main.py                   # 应用入口文件
├── pyproject.toml           # Python 项目配置
└── README.md                # 项目文档
```

### 数据库设计
系统采用关系型数据库设计，包含 10 个核心数据模型：

#### 核心数据模型
| 模型名 | 表名 | 描述 | 主要字段 |
|--------|------|------|----------|
| **User** | users | 用户表 | 用户信息、权限、角色、部门关联 |
| **Department** | departments | 部门表 | 组织架构信息、部门设置 |
| **Category** | equipment_categories | 设备类别表 | 类别信息、预定义名称、编号规则 |
| **Equipment** | equipments | 设备表 | 设备基本信息、检定信息、状态、位置 |
| **CalibrationRecord** | calibration_history | 检定历史表 | 检定记录、结果追踪、证书信息 |
| **Attachment** | equipment_attachments | 附件表 | 设备附件、证书、文档管理 |
| **AuditLog** | audit_logs | 审计日志表 | 用户操作记录、系统事件追踪 |
| **SystemSetting** | system_settings | 系统设置表 | 系统配置、参数管理 |
| **UserCategory** | user_categories | 用户类别权限表 | 用户对设备类别的访问权限 |
| **DepartmentUserLog** | department_user_logs | 部门用户日志表 | 部门用户操作记录 |

#### 数据关系设计
- **用户 ↔ 部门**：多对一关系（一个用户属于一个部门）
- **用户 ↔ 设备类别**：多对多关系（通过 UserCategory 表实现权限控制）
- **设备 ↔ 部门**：多对一关系（设备归属部门）
- **设备 ↔ 设备类别**：多对一关系（设备分类管理）
- **设备 ↔ 检定历史**：一对多关系（设备多次检定记录）
- **设备 ↔ 附件**：一对多关系（设备多个附件）
- **用户 ↔ 审计日志**：一对多关系（用户操作记录）

#### 索引设计
- 用户表：username (唯一)、department_id、is_active
- 设备表：name、model、status、department_id、category_id
- 检定历史表：equipment_id、calibration_date
- 审计日志表：user_id、action_type、timestamp
- 附件表：equipment_id、file_type

---

## ✨ 功能特色

### 1. 智能设备管理
- **完整生命周期管理**：设备添加、编辑、删除、状态变更全流程管理
- **智能编号系统**：根据设备类别和器具名称自动生成内部编号
- **预定义名称管理**：支持预定义器具名称的智能编号分配
- **编号连续性保证**：确保编号的连续性和可追溯性
- **大规模设备支持**：智能处理设备数量超过999台时的编号生成
- **设备信息管理**：型号、规格、制造商、购买日期等详细信息
- **设备位置管理**：所属部门、存放位置、使用人管理
- **设备状态跟踪**：在用、备用、维修、报废等状态管理

### 2. 检定管理系统
- **智能检定周期管理**：支持6个月/12个月/24个月/随坏随换等多种周期
- **内检/外检区分**：不同检定方式的差异化处理和记录
- **检定结果管理**：合格/不合格结果的自动状态更新和设备状态变更
- **检定历史追踪**：完整的检定记录和历史查询，支持证书信息管理
- **智能提醒系统**：自动计算并提醒即将到期的设备，支持批量提醒
- **检定证书管理**：内检/外检证书信息存储和查阅
- **检定结果统计**：按期间、部门、类别等维度统计检定结果
- **检定计划导出**：支持月度、年度检定计划Excel导出

### 3. 权限控制系统
- **多级权限控制**：管理员/普通用户/部门用户三种角色
- **设备类别权限**：基于设备类别的细粒度权限控制
- **部门权限管理**：部门用户只能访问和管理本部门设备
- **操作审计追踪**：完整的用户操作日志记录和安全事件监控
- **会话管理**：JWT Token认证和活跃会话管理，支持强制登录
- **权限继承**：支持权限模板和批量权限分配
- **安全认证**：多重身份验证和密码加密存储
- **访问控制**：基于IP地址和访问时间的安全控制

### 4. 数据导入导出
- **Excel模板下载**：标准化的数据导入模板，包含数据验证规则
- **批量数据导入**：支持Excel文件的批量导入和验证
- **多格式导出**：月度计划、年度计划、筛选结果导出
- **数据验证机制**：导入时的数据完整性验证和错误提示
- **格式兼容**：支持Excel 2007+格式，兼容多种办公软件
- **导入日志**：记录导入过程中的所有操作和错误信息
- **数据映射**：智能数据字段映射和自动纠错
- **批量操作**：支持导入数据的预览和确认

### 5. 全文本搜索与筛选
- **多字段搜索**：支持设备名称、型号、编号等多字段搜索
- **智能搜索**：支持部门名称和设备类别名称搜索
- **组合筛选**：多条件组合筛选功能（部门+类别+状态+日期范围）
- **搜索结果导出**：支持搜索结果的批量导出和格式化
- **搜索历史**：记录用户搜索历史，支持快速重复搜索
- **高级筛选**：支持复杂条件的组合筛选和保存筛选条件
- **搜索统计**：提供搜索结果的统计分析和趋势图表
- **搜索建议**：基于用户搜索历史提供智能搜索建议

### 6. 数据库管理工具
- **数据库状态监控**：实时监控数据库连接状态、类型、表数量和大小
- **数据库备份**：支持数据库文件备份和完整备份（包含上传文件）
- **数据库优化**：自动清理和优化数据库性能
- **数据统计**：详细的数据库表统计信息和记录分析
- **备份历史管理**：完整的备份记录管理和版本控制
- **ZIP压缩备份**：支持上传文件和数据库的完整打包备份
- **备份下载**：安全的备份文件下载机制
- **数据库健康检查**：定期检查数据库完整性和性能指标

### 7. 日志管理系统
- **操作日志**：完整的用户操作记录和审计追踪
- **访问日志**：API访问日志记录和统计分析
- **安全日志**：登录失败、未授权访问等安全事件记录
- **系统日志**：应用运行状态和错误信息记录
- **日志查询**：支持按时间、用户、操作类型等多条件查询
- **日志导出**：支持日志文件的导出和归档
- **日志清理**：自动清理过期日志文件
- **日志分析**：提供日志统计分析和异常检测

### 8. 系统管理功能
- **系统设置管理**：应用配置、参数设置和系统选项
- **用户会话管理**：活跃会话监控和管理
- **系统状态监控**：系统资源使用情况监控
- **文件上传管理**：证书、文档等文件上传和管理
- **系统备份恢复**：完整系统备份和恢复功能
- **性能优化**：数据库性能优化和索引重建
- **系统诊断**：系统运行状态诊断和问题排查
- **配置管理**：系统配置的导入导出和版本管理

### 9. 用户界面特色
- **响应式设计**：完美支持桌面和移动设备
- **现代化界面**：Tailwind CSS驱动的现代化UI设计，支持自定义主题和样式
- **模态框确认**：所有删除操作都有二次确认模态框
- **通知系统**：统一的浮动通知管理和消息提醒
- **多标签页支持**：支持多标签页独立登录和状态同步
- **数据可视化**：Chart.js驱动的图表和统计展示
- **实时更新**：AJAX驱动的实时数据更新
- **操作便捷**：快捷键支持和拖拽操作
- **渐变效果**：美观的渐变背景和毛玻璃效果
- **动画效果**：流畅的页面过渡和交互动画

### 10. 统计分析功能
- **设备统计**：按类别、部门、状态等维度统计分析
- **检定统计**：检定合格率、到期提醒等统计分析
- **用户统计**：用户活跃度、操作统计等
- **系统统计**：系统使用情况、性能统计等
- **图表展示**：柱状图、饼图、折线图等多种图表类型
- **数据导出**：统计结果导出和报告生成
- **趋势分析**：历史数据趋势分析和预测
- **自定义报表**：支持自定义报表和仪表盘

---

## 📖 使用说明

### 系统登录
1. 打开浏览器访问系统地址
2. 使用管理员账户登录：
   - 用户名：`admin`
   - 密码：`admin123`
3. 登录成功后进入仪表盘页面
4. 支持多标签页独立登录和会话管理

### 设备管理
#### 添加设备
1. 点击"设备管理"菜单
2. 点击"添加设备"按钮
3. 填写设备基本信息：
   - 选择所属部门和设备类别
   - 填写设备名称、型号、规格、制造商等信息
   - 设置检定周期、检定日期和设备位置
   - 上传相关证书和文档（可选）
4. 点击"保存"完成添加
5. 系统自动生成设备内部编号

#### 设备查询与筛选
1. 在设备管理页面使用搜索功能
2. 支持按设备名称、型号、编号等多字段搜索
3. 使用高级筛选功能进行多条件查询：
   - 按部门筛选
   - 按设备类别筛选
   - 按设备状态筛选（在用、备用、维修、报废）
   - 按检定状态筛选（正常、即将到期、已过期）
4. 保存筛选条件供后续使用
5. 支持搜索历史记录

#### 设备编辑与查看
1. 在设备管理页面点击"编辑"按钮修改设备信息
2. 点击"查看"按钮查看设备详细信息
3. 查看设备检定历史记录
4. 管理设备附件和证书

#### 批量操作
1. 选择要操作的设备（勾选复选框）
2. 点击批量操作按钮
3. 选择操作类型：
   - 删除：批量删除选中的设备
   - 导出：批量导出设备信息到Excel
   - 转移：批量转移设备到其他部门
   - 状态变更：批量更改设备状态
   - 检定更新：批量更新检定信息
4. 确认操作并执行

### 检定管理
#### 更新检定信息
1. 在设备管理页面点击"检定"按钮
2. 填写检定信息：
   - 检定日期
   - 检定结果（合格/不合格）
   - 检定方法（内检/外检）
   - 证书信息（外检时）
   - 检定机构（外检时）
3. 系统自动更新设备状态和有效期
4. 支持检定证书上传

#### 批量检定更新
1. 选择要更新检定日期的设备
2. 点击"批量操作" → "检定更新"
3. 设置新的检定日期
4. 选择要更新的字段：
   - 检定结果
   - 检定方法
   - 证书信息
   - 检定机构
5. 确认并执行批量更新

#### 检定计划管理
1. 在仪表盘查看即将到期的设备
2. 生成月度/年度检定计划
3. 导出检定计划Excel文件
4. 发送检定提醒通知

### 用户管理
#### 创建用户
1. 点击"用户管理"菜单
2. 点击"添加用户"按钮
3. 填写用户信息：
   - 用户名和密码
   - 用户类型（管理员/普通用户/部门用户）
   - 关联部门（部门用户）
   - 用户状态和有效期
4. 分配设备类别权限
5. 保存用户信息
6. 系统自动发送激活邮件（可选）

#### 权限管理
1. 在用户管理页面选择用户
2. 点击"权限管理"按钮
3. 为用户分配可管理的设备类别
4. 设置权限级别（查看、编辑、删除）
5. 保存权限设置
6. 支持权限模板应用

#### 会话管理
1. 在系统设置中查看活跃会话
2. 管理用户登录状态
3. 支持强制用户下线
4. 查看登录历史记录

### 部门管理
1. 点击"部门管理"菜单
2. 创建、编辑、删除部门信息
3. 设置部门管理员
4. 管理部门用户
5. 统计部门设备数量

### 设备类别管理
1. 点击"类别管理"菜单
2. 管理设备类别和子类别
3. 设置预定义器具名称
4. 配置编号规则
5. 管理类别权限

### 数据导入导出
#### 数据导入
1. 在设备管理页面点击"导入"按钮
2. 下载Excel模板文件
3. 按模板格式填写数据（包含数据验证规则）
4. 上传填写好的Excel文件
5. 系统自动验证并导入数据
6. 查看导入日志和错误报告

#### 数据导出
1. 使用筛选功能选择要导出的设备
2. 点击"导出"按钮
3. 选择导出格式：
   - 月度检定计划
   - 年度检定计划
   - 当前筛选结果
   - 完整设备台账
   - 自定义导出模板
4. 下载导出的Excel文件
5. 导出文件包含完整数据和格式

### 系统管理
#### 数据库管理
1. 进入"系统设置"页面
2. 查看数据库状态和统计信息
3. 创建数据库备份：
   - 选择仅备份数据库
   - 或包含上传文件的完整备份
4. 优化数据库性能
5. 查看备份历史和下载备份文件

#### 日志管理
1. 进入"日志管理"页面
2. 查看操作日志、访问日志、安全日志
3. 按时间、用户、操作类型筛选日志
4. 导出日志文件
5. 清理过期日志

#### 系统设置
1. 配置系统参数和选项
2. 管理文件上传设置
3. 配置备份策略
4. 设置系统通知和提醒
5. 管理API密钥和集成设置

### 统计报表
1. 点击"统计报表"菜单
2. 查看各种统计图表：
   - 设备按类别分布
   - 设备按部门分布
   - 检定到期统计
   - 设备状态统计
   - 用户活跃度统计
   - 系统使用统计
3. 支持图表类型切换（柱状图/饼图/折线图）
4. 自定义报表和仪表盘
5. 导出统计报告

### 附件管理
1. 在设备详情页管理附件
2. 上传设备证书、文档、图片等文件
3. 查看和下载附件
4. 管理附件版本和分类
5. 批量上传和下载附件

### 部门用户管理
1. 部门用户专属登录界面
2. 部门用户专用仪表盘
3. 只能访问本部门设备
4. 简化的设备管理界面
5. 部门数据统计和报表

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

#### 用户注销
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

#### 强制登录（清除其他会话）
```http
POST /api/auth/force-login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
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

#### 更新设备信息
```http
PUT /api/equipment/{equipment_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "温度计",
  "model": "T-100",
  "status": "在用"
}
```

#### 删除设备
```http
DELETE /api/equipment/{equipment_id}
Authorization: Bearer <token>
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

#### 获取设备详情
```http
GET /api/equipment/{equipment_id}
Authorization: Bearer <token>
```

#### 获取待检定设备
```http
GET /api/equipment/due-calibration
Authorization: Bearer <token>
```

#### 批量操作设备
```http
POST /api/equipment/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "delete",
  "equipment_ids": [1, 2, 3]
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
  "calibration_method": "内检",
  "certificate_info": "证书编号：12345"
}
```

#### 批量更新检定信息
```http
POST /api/calibration/batch-update
Authorization: Bearer <token>
Content-Type: application/json

{
  "equipment_ids": [1, 2, 3],
  "calibration_date": "2024-01-01",
  "calibration_result": "合格"
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

#### 更新用户信息
```http
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "newuser",
  "is_active": true
}
```

#### 删除用户
```http
DELETE /api/users/{user_id}
Authorization: Bearer <token>
```

#### 管理用户权限
```http
POST /api/users/{user_id}/permissions
Authorization: Bearer <token>
Content-Type: application/json

{
  "category_ids": [1, 2, 3]
}
```

### 部门管理接口
#### 获取部门列表
```http
GET /api/departments/
Authorization: Bearer <token>
```

#### 创建部门
```http
POST /api/departments/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "质量部",
  "description": "负责质量控制"
}
```

#### 更新部门
```http
PUT /api/departments/{department_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "质量部",
  "description": "负责质量控制"
}
```

#### 删除部门
```http
DELETE /api/departments/{department_id}
Authorization: Bearer <token>
```

### 设备类别管理接口
#### 获取类别列表
```http
GET /api/categories/
Authorization: Bearer <token>
```

#### 创建类别
```http
POST /api/categories/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "温度计量器具",
  "predefined_names": ["温度计", "温湿度计"]
}
```

#### 更新类别
```http
PUT /api/categories/{category_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "温度计量器具",
  "predefined_names": ["温度计", "温湿度计"]
}
```

#### 删除类别
```http
DELETE /api/categories/{category_id}
Authorization: Bearer <token>
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

#### 获取年度待检设备
```http
GET /api/dashboard/yearly-due-equipments
Authorization: Bearer <token>
```

### 数据导入导出接口
#### 获取导入模板
```http
GET /api/import/template
Authorization: Bearer <token>
```

#### 导入数据
```http
POST /api/import/equipment
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <excel_file>
```

#### 导出数据
```http
POST /api/export/equipment
Authorization: Bearer <token>
Content-Type: application/json

{
  "export_type": "monthly_plan",
  "filters": {
    "department_id": 1,
    "category_id": 2
  }
}
```

### 系统管理接口
#### 数据库状态
```http
GET /api/system/database/status
Authorization: Bearer <token>
```

#### 创建数据库备份
```http
POST /api/system/database/backup
Authorization: Bearer <token>
Content-Type: multipart/form-data

include_files: false
```

#### 优化数据库
```http
POST /api/system/database/optimize
Authorization: Bearer <token>
```

#### 获取数据库统计
```http
GET /api/system/database/statistics
Authorization: Bearer <token>
```

#### 获取备份历史
```http
GET /api/system/database/backup-history
Authorization: Bearer <token>
```

#### 下载备份文件
```http
GET /api/system/database/backup/{filename}/download-with-token
Authorization: Bearer <token>
```

#### 删除备份文件
```http
DELETE /api/system/database/backup/{filename}
Authorization: Bearer <token>
```

### 日志管理接口
#### 获取操作日志
```http
GET /api/logs/operations?page=1&page_size=20
Authorization: Bearer <token>
```

#### 获取访问日志
```http
GET /api/logs/api?page=1&page_size=20
Authorization: Bearer <token>
```

#### 获取安全日志
```http
GET /api/logs/security?page=1&page_size=20
Authorization: Bearer <token>
```

#### 获取日志统计
```http
GET /api/logs/stats
Authorization: Bearer <token>
```

#### 清理日志
```http
POST /api/logs/cleanup
Authorization: Bearer <token>
Content-Type: application/json

{
  "log_type": "operations",
  "days_to_keep": 30
}
```

### 附件管理接口
#### 上传附件
```http
POST /api/attachments/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

equipment_id: 1
file: <file>
file_type: certificate
```

#### 获取设备附件
```http
GET /api/attachments/equipment/{equipment_id}
Authorization: Bearer <token>
```

#### 下载附件
```http
GET /api/attachments/{attachment_id}/download
Authorization: Bearer <token>
```

#### 删除附件
```http
DELETE /api/attachments/{attachment_id}
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

#### 同步设备信息
```http
POST /api/external/sync
X-API-Key: <api_key>
Content-Type: application/json

{
  "equipment": [...]
}
```

### 报表接口
#### 获取设备统计报表
```http
GET /api/reports/equipment-stats
Authorization: Bearer <token>
```

#### 获取检定统计报表
```http
GET /api/reports/calibration-stats
Authorization: Bearer <token>
```

#### 生成自定义报表
```http
POST /api/reports/custom
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "equipment",
  "filters": {...},
  "format": "excel"
}
```

### 部门用户接口
#### 部门用户登录
```http
POST /api/department/login
Content-Type: application/json

{
  "username": "dept_user",
  "password": "password123",
  "department_code": "DEPT001"
}
```

#### 获取部门统计
```http
GET /api/department/stats
Authorization: Bearer <token>
```

#### 获取部门设备
```http
GET /api/department/equipment
Authorization: Bearer <token>
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
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的CSS框架
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
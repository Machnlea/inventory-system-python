# 设备台账管理系统

<div align="center">

![设备台账管理系统](https://img.shields.io/badge/设备台账管理系统-v1.0-blue)
![技术栈](https://img.shields.io/badge/技术栈-FastAPI%20%7C%20SQLite%20%7C%20Bootstrap-green)
![许可证](https://img.shields.io/badge/许可证-MIT-yellow)

**基于 FastAPI + SQLite 的综合设备台账管理系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [API文档](#-api文档) • [部署指南](#-生产部署)

</div>

基于 FastAPI + SQLite 的现代化设备台账管理系统，提供完整的设备信息管理、智能检定计划、权限控制和全文本搜索功能。

## 🚀 功能特性

### 🔐 安全与权限
- ✅ **用户认证和权限管理**：支持管理员/普通用户两种角色
- ✅ **JWT Token认证**：安全的无状态认证机制
- ✅ **细粒度权限控制**：基于设备类别的权限分配
- ✅ **操作审计日志**：完整的用户操作追踪

### 📋 设备管理
- ✅ **完整的设备台账管理**：支持CRUD操作和全字段管理
- ✅ **全文本搜索功能**：支持设备名称、型号、编号等多字段搜索
- ✅ **智能检定日期计算**：根据检定周期自动计算下次检定时间
- ✅ **设备状态管理**：在用/停用/报废状态跟踪
- ✅ **批量操作**：支持批量更新检定日期和状态变更

### 📊 数据处理
- ✅ **多条件筛选导出**：支持Excel格式的月度/年度计划导出
- ✅ **Excel批量导入**：支持模板下载和数据批量导入
- ✅ **数据可视化**：Chart.js驱动的仪表盘统计图表
- ✅ **实时统计**：关键指标和设备分布实时更新

### 🎨 用户体验
- ✅ **响应式界面**：Bootstrap 5构建的现代化Web界面
- ✅ **分页浏览**：大数据量的友好分页展示
- ✅ **交互式API文档**：Swagger UI和ReDoc双重文档支持
- ✅ **快捷操作**：便捷的启动脚本和配置管理

## 🛠 技术栈

<div align="center">

**后端技术栈**

| 技术 | 用途 | 版本 |
|------|------|------|
| ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) | Web框架 | 0.104+ |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F26?style=for-the-badge&logo=sqlalchemy) | ORM框架 | 2.0+ |
| ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite) | 数据库 | 3.35+ |
| ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic) | 数据验证 | 2.0+ |
| ![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge) | 用户认证 | - |
| ![uv](https://img.shields.io/badge/uv-0B57D0?style=for-the-badge) | 包管理器 | 0.1+ |

**前端技术栈**

| 技术 | 用途 | 版本 |
|------|------|------|
| ![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap) | UI框架 | 5.1+ |
| ![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chart.js) | 图表库 | 3.9+ |
| ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript) | 前端逻辑 | ES6+ |

</div>

## 📦 快速开始

<div align="center">

![安装步骤](https://img.shields.io/badge/安装步骤-5%20步-green)
![部署时间](https://img.shields.io/badge/部署时间-<3%20分钟-blue)
![兼容性](https://img.shields.io/badge/兼容性-Windows%20%7C%20Linux%20%7C%20macOS-purple)

</div>

### 📋 环境要求

- **Python**: 3.12+
- **包管理器**: uv (推荐) 或 pip
- **操作系统**: Windows / Linux / macOS
- **内存**: 最少 512MB RAM
- **存储**: 最少 100MB 可用空间

### 🚀 安装步骤

#### 方法一：使用启动脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/Machnlea/inventory-system-python.git
cd inventory-system-python

# 赋予执行权限
chmod +x start.sh

# 一键启动
./start.sh
```

#### 方法二：手动安装

```bash
# 1. 克隆项目
git clone https://github.com/Machnlea/inventory-system-python.git
cd inventory-system-python

# 2. 安装依赖
uv install
uv sync -i https://mirrors.aliyun.com/pypi/simple/
uv sync -i https://pypi.tuna.tsinghua.edu.cn/simple/


# 3. 初始化数据库
uv run python init_db.py

# 4. 启动服务
uv run python main.py

uv run python -m uvicorn main:app --workers 4 --host 0.0.0.0 --port 8080
```

### 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **主页面** | http://localhost:8000 | 系统主界面 |
| **Swagger UI** | http://localhost:8000/docs | 交互式API文档 |
| **ReDoc** | http://localhost:8000/redoc | 专业API文档 |
| **API重定向** | http://localhost:8000/api | 重定向到文档 |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | API规范文件 |

### 🔑 默认账户

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| **管理员** | `admin` | `admin123` | 全系统管理权限 |
| **普通用户** | `user` | `user123` | 基础操作权限 |

> 💡 **提示**: 首次启动后，建议立即修改默认密码以提高安全性。

## 📋 主要功能

### 🔍 1. 全文本搜索功能
- **多字段搜索**：支持设备名称、型号、计量编号、制造厂家、安装地点、备注等
- **智能搜索**：支持部门名称和设备类别名称搜索
- **组合筛选**：可结合部门、类别、状态进行筛选
- **分页支持**：搜索结果支持分页浏览
- **实时反馈**：搜索结果数量提示和清除搜索功能

### 📊 2. 设备台账管理
- **完整字段支持**：部门、计量器具名称、型号规格、准确度等级、测量范围等
- **检定周期管理**：支持1年/2年检定周期设置
- **智能日期计算**：下次检定日期 = 检定日期 + 检定周期 - 1天
- **设备状态跟踪**：在用/停用/报废状态管理
- **批量操作**：支持批量更新检定日期和状态变更

### 🔐 3. 权限控制系统
- **管理员权限**：全系统管理，包括用户、设备类别、部门管理
- **普通用户权限**：仅能管理被授权的设备类别
- **细粒度控制**：基于设备类别的权限分配
- **操作审计**：完整记录所有关键操作

### 📤 4. 数据导入导出
- **Excel模板下载**：提供标准数据导入模板
- **批量数据导入**：支持Excel文件批量导入设备信息
- **多种导出格式**：月度计划、年度计划、筛选结果导出
- **数据验证**：导入时进行完整性和格式验证

### 📈 5. 统计分析
- **关键指标监控**：本月待检、超期未检、停用设备统计
- **可视化图表**：在用设备类别分布图表
- **实时更新**：数据变更后实时更新统计信息
- **庆祝效果**：完成目标时的动画庆祝效果
- **数据一致性**：图表数据与统计数字保持一致

### 🎨 6. 用户界面
- **响应式设计**：适配桌面和移动设备
- **现代化UI**：Bootstrap 5构建的专业界面
- **交互体验**：直观的操作流程和用户反馈
- **多语言支持**：中文界面，符合国内使用习惯

### 🧹 7. 系统维护
- **操作日志清理**：自动清理超过一年的操作日志
- **数据保留策略**：最多保留365天的操作记录
- **手动清理功能**：管理员可手动触发日志清理
- **定时任务支持**：支持定时自动清理任务

## 🗄️ 数据库设计

### 核心数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| users | 用户信息 | username, is_admin, hashed_password |
| equipment_categories | 设备类别 | name, description |
| departments | 部门信息 | name, description |
| equipments | 设备台账 | name, model, calibration_date, next_calibration_date |
| user_categories | 用户权限关联 | user_id, category_id |
| audit_logs | 操作日志 | user_id, action, description, created_at |

### 数据关系
- 用户 ↔ 设备类别：多对多关系（权限控制）
- 设备 ↔ 部门：多对一关系
- 设备 ↔ 设备类别：多对一关系
- 操作日志 ↔ 用户：多对一关系

## 📚 API文档

### 访问方式
系统提供了完整的API文档，支持多种格式：

- **Swagger UI**：http://localhost:8000/docs
  - 交互式API测试界面
  - 支持在线调试API
  - 提供请求/响应示例

- **ReDoc**：http://localhost:8000/redoc
  - 专业的API文档展示
  - 支持Markdown描述
  - 适合集成到技术文档

- **OpenAPI JSON**：http://localhost:8000/openapi.json
  - 标准的OpenAPI 3.0规范
  - 支持第三方工具集成

### API模块总览

#### 1. 认证模块 (`/api/auth`)
- `POST /login` - 用户登录，返回JWT Token
- `GET /me` - 获取当前用户信息

#### 2. 用户管理 (`/api/users`)
- `GET /` - 获取用户列表（管理员）
- `POST /` - 创建用户（管理员）
- `GET /{id}` - 获取用户详情（管理员）
- `PUT /{id}` - 更新用户信息（管理员）
- `DELETE /{id}` - 删除用户（管理员）
- `GET /{id}/categories` - 获取用户权限（管理员）
- `POST /{id}/categories/{category_id}` - 分配权限（管理员）
- `PUT /{id}/categories` - 批量更新权限（管理员）

#### 3. 设备管理 (`/api/equipment`)
- `GET /` - 获取设备列表（支持分页）
- `POST /` - 创建设备
- `GET /{id}` - 获取设备详情
- `PUT /{id}` - 更新设备信息
- `DELETE /{id}` - 删除设备
- `POST /filter` - 多条件筛选设备
- `POST /search` - **全文本搜索设备** 🔥
- `GET /export/monthly-plan` - 导出月度检定计划
- `GET /export/yearly-plan` - 导出年度检定计划
- `POST /export/filtered` - 导出筛选结果
- `POST /batch/update-calibration` - 批量更新检定日期
- `POST /batch/change-status` - 批量变更设备状态

#### 🔍 全文本搜索API详情
```bash
POST /api/equipment/search
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "压力表",
  "department_id": 1,
  "category_id": 2,
  "status": "在用"
}
```

**搜索范围**：
- 设备名称、型号、计量编号
- 制造厂家、安装地点、备注
- 准确度等级、测量范围、检定方式
- 部门名称、设备类别名称

#### 4. 部门管理 (`/api/departments`)
- `GET /` - 获取部门列表
- `POST /` - 创建部门（管理员）
- `GET /{id}` - 获取部门详情
- `PUT /{id}` - 更新部门信息（管理员）
- `DELETE /{id}` - 删除部门（管理员）

#### 5. 设备类别管理 (`/api/categories`)
- `GET /` - 获取类别列表
- `POST /` - 创建类别（管理员）
- `GET /{id}` - 获取类别详情
- `PUT /{id}` - 更新类别信息（管理员）
- `DELETE /{id}` - 删除类别（管理员）

#### 6. 仪表盘 (`/api/dashboard`)
- `GET /stats` - 获取统计数据
- `GET /monthly-due-equipments` - 获取月度待检设备
- `GET /overdue-equipments` - 获取超期设备
- `GET /equipment-by-category` - 按类别统计设备
- `GET /equipment-by-department` - 按部门统计设备

#### 7. 操作日志 (`/api/audit`)
- `GET /` - 获取操作日志列表
- `GET /stats` - 获取操作统计信息
- `POST /cleanup` - 清理超过一年的操作日志（管理员）

#### 8. 数据导入导出 (`/api/import`)
- `GET /template` - 下载导入模板
- `POST /excel` - 导入Excel数据

### 认证方式
所有API请求都需要在Header中携带JWT Token：
```
Authorization: Bearer <your-jwt-token>
```

### 权限说明
- **管理员**：拥有所有API的访问权限
- **普通用户**：只能操作被授权的设备类别下的设备

### 响应格式
所有API返回统一的JSON格式：
```json
{
  "data": {},
  "message": "success",
  "status": 200
}
```

## 📁 项目结构

```
inventory-system-python/
├── app/
│   ├── api/                  # API路由模块
│   │   ├── auth.py          # 认证接口
│   │   ├── equipment.py     # 设备管理接口
│   │   ├── users.py         # 用户管理接口
│   │   └── ...
│   ├── core/                # 核心配置
│   │   ├── config.py        # 应用配置
│   │   └── security.py      # 安全相关
│   ├── crud/                # 数据操作层
│   ├── db/                  # 数据库配置
│   ├── models/              # SQLAlchemy模型
│   ├── schemas/             # Pydantic模型
│   ├── static/              # 静态资源
│   └── templates/           # HTML模板
├── main.py                  # 应用入口
├── init_db.py              # 数据库初始化
└── README.md               # 项目文档
```

## 🔒 安全特性

1. **密码加密**：使用bcrypt加密存储用户密码
2. **JWT认证**：基于Token的无状态认证
3. **权限控制**：严格的基于角色的访问控制
4. **SQL注入防护**：使用ORM防止SQL注入攻击
5. **操作审计**：完整记录所有关键操作

## 🚀 生产部署

### 环境变量配置
```bash
export SECRET_KEY="your-production-secret-key"
export DATABASE_URL="postgresql://user:pass@localhost/inventory"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-admin-password"
```

### 推荐部署方案
1. 使用PostgreSQL替代SQLite
2. 配置Nginx反向代理
3. 启用HTTPS安全连接
4. 设置定期数据备份
5. 配置日志轮转

## 📈 业务流程

### 设备检定流程
1. **设备录入**：录入设备基本信息和检定信息
2. **自动计算**：系统自动计算下次检定日期
3. **计划导出**：定期导出月度/年度检定计划
4. **状态更新**：检定完成后更新设备状态
5. **记录追踪**：所有操作自动记录日志

### 权限分配流程
1. **用户创建**：管理员创建普通用户账户
2. **权限分配**：为用户分配可管理的设备类别
3. **范围限制**：用户只能操作授权类别下的设备
4. **审计监控**：管理员可查看所有操作日志

## 🔧 使用说明

### 📝 设备管理流程

#### 1. 设备录入
1. 登录系统 → 进入"设备管理"页面
2. 点击"添加设备"按钮
3. 填写设备信息（带*为必填项）
4. 系统自动计算下次检定日期
5. 保存设备信息

#### 2. 设备搜索
1. 在"设备管理"页面顶部的搜索区域
2. 输入搜索关键词（支持模糊搜索）
3. 可选择部门、类别、状态进行筛选
4. 点击"搜索"或按回车键执行搜索
5. 搜索结果支持分页浏览

#### 3. 检定管理
1. **月度计划**：仪表盘查看本月待检设备
2. **批量更新**：选择多个设备，点击"批量更新检定日期"
3. **状态变更**：设备停用或报废时，记录状态变更时间
4. **导出计划**：导出月度/年度检定计划Excel文件

### 👥 权限管理

#### 管理员操作
- 创建用户账户
- 分配设备类别权限
- 管理部门和设备类别
- 查看操作日志

#### 普通用户操作
- 管理授权设备类别的设备
- 查看相关统计数据
- 导出数据报表

## 🚨 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库文件是否存在
ls -la inventory.db

# 重新初始化数据库
uv run python init_db.py
```

#### 2. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>
```

#### 3. 依赖包问题
```bash
# 重新安装依赖
uv install

# 更新依赖包
uv sync
```

#### 4. 搜索功能异常
- 检查搜索关键词是否为空
- 确认网络连接正常
- 刷新页面重试

### 日志查看
```bash
# 查看系统日志
tail -f app.log

# 查看错误日志
grep ERROR app.log
```

## 📈 性能优化

### 数据库优化
- 定期清理过期日志
- 创建数据库索引
- 优化查询语句

### 系统优化
- 启用缓存机制
- 优化静态资源
- 监控系统资源

## 🔄 版本更新

### v1.1.1 (2024-08-05)
- ✅ **修复导出月度计划422错误**：解决API路径参数验证失败问题
- ✅ **优化缓存处理**：添加版本参数避免浏览器缓存影响
- ✅ **提升系统稳定性**：完善错误处理和服务器重启机制

### v1.1.0 (2024-08-04)
- ✅ **图表数据优化**：设备类别分布图表改为仅显示在用设备
- ✅ **操作日志清理**：实现超过一年的操作日志自动清理功能
- ✅ **系统维护功能**：添加手动清理和定时任务支持
- ✅ **数据一致性**：确保图表数据与统计数字保持一致

### v1.0.0 (2024-08-03)
- ✅ 实现全文本搜索功能
- ✅ 完善用户权限控制
- ✅ 优化用户界面体验
- ✅ 添加数据导入导出
- ✅ 实现操作日志记录
- ✅ 支持批量操作功能

## 📞 技术支持

### 获取帮助
1. **API文档**: http://localhost:8000/docs
2. **系统日志**: 检查操作日志排查问题
3. **GitHub Issues**: 提交问题反馈
4. **邮件支持**: 联系开发团队

### 贡献指南
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

### 许可证
本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

<div align="center">

**基于FastAPI构建的现代化设备台账管理系统**

[⭐ Star](https://github.com/Machnlea/inventory-system-python) | [🐛 报告问题](https://github.com/Machnlea/inventory-system-python/issues) | [📖 文档](https://github.com/Machnlea/inventory-system-python/wiki)

Made with ❤️ by 设备台账管理团队

</div>
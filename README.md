# 设备台账管理系统

基于 FastAPI + SQLite 的综合设备台账管理系统，实现设备信息管理、检定计划制定、权限控制等功能。

## 🚀 功能特性

- ✅ **用户认证和权限管理**：支持管理员/普通用户两种角色
- ✅ **设备台账管理**：完整的设备信息CRUD操作
- ✅ **自动计算检定日期**：根据检定周期自动计算下次检定时间
- ✅ **多条件筛选导出**：支持Excel格式的月度/年度计划导出
- ✅ **仪表盘统计**：直观展示关键指标和设备分布
- ✅ **操作日志记录**：完整的审计追踪功能
- ✅ **Excel批量导入**：支持模板下载和数据批量导入
- ✅ **响应式界面**：Bootstrap构建的现代化Web界面

## 🛠 技术栈

**后端**
- FastAPI - 高性能异步Web框架
- SQLAlchemy - Python ORM框架
- SQLite - 轻量级数据库
- Pydantic - 数据验证和序列化
- JWT - 安全的用户认证
- Redoc - API文档生成

**前端**
- Bootstrap 5 - 响应式UI框架
- Chart.js - 数据可视化图表
- JavaScript ES6+ - 现代前端逻辑

## 📦 快速开始

### 环境要求
- Python 3.12+
- uv包管理器

### 安装步骤

1. **安装依赖**
```bash
uv install
```

2. **初始化数据库**
```bash
uv run python init_db.py
```

3. **启动服务**
```bash
uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或者使用便捷启动脚本：
```bash
chmod +x start.sh
./start.sh
```

4. **访问系统**
- 主页面：http://localhost:8000
- Swagger UI文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc
- API文档重定向：http://localhost:8000/api
- OpenAPI JSON：http://localhost:8000/openapi.json

### 默认登录
- 用户名：`admin`
- 密码：`admin123`

## 📋 主要功能

### 1. 设备台账管理
- **完整字段支持**：部门、计量器具名称、型号规格、准确度等级、测量范围等
- **检定周期管理**：支持1年/2年检定周期设置
- **自动日期计算**：下次检定日期 = 检定日期 + 检定周期 - 1天
- **设备状态跟踪**：在用/停用/报废状态管理

### 2. 权限控制系统
- **管理员权限**：全系统管理，包括用户、设备类别、部门管理
- **普通用户权限**：仅能管理被授权的设备类别
- **细粒度控制**：基于设备类别的权限分配

### 3. 数据导入导出
- **Excel模板下载**：提供标准数据导入模板
- **批量数据导入**：支持Excel文件批量导入设备信息
- **多种导出格式**：月度计划、年度计划、筛选结果导出
- **数据验证**：导入时进行完整性和格式验证

### 4. 统计分析
- **关键指标监控**：下月待检、超期未检、停用设备统计
- **可视化图表**：设备类别分布图表
- **实时更新**：数据变更后实时更新统计信息

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
- `GET /` - 获取设备列表
- `POST /` - 创建设备
- `GET /{id}` - 获取设备详情
- `PUT /{id}` - 更新设备信息
- `DELETE /{id}` - 删除设备
- `POST /filter` - 多条件筛选设备
- `GET /export/monthly-plan` - 导出月度检定计划
- `GET /export/yearly-plan` - 导出年度检定计划
- `POST /export/filtered` - 导出筛选结果
- `POST /batch/update-calibration` - 批量更新检定日期
- `POST /batch/change-status` - 批量变更设备状态

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

## ✅ 系统验证

系统已完全按照需求分析文档实现：

- ✅ 用户角色和权限系统
- ✅ 设备分类和部门管理  
- ✅ 完整的设备台账字段
- ✅ 自动化检定日期计算
- ✅ 多条件筛选和导出
- ✅ 仪表盘统计展示
- ✅ 操作日志记录
- ✅ Excel导入导出功能
- ✅ 响应式Web界面

**系统现已完成并可投入使用！**

## 📞 技术支持

如有问题或需要技术支持，请：
1. 查看API文档：http://localhost:8000/docs
2. 检查操作日志排查问题
3. 联系开发团队获取支持

---
*基于FastAPI构建的现代化设备台账管理系统 v1.0*
# 开发指南

## 📖 概述

本指南为设备台账管理系统的开发人员提供详细的开发规范、最佳实践和工作流程。

## 🛠️ 开发环境设置

### 环境要求
- Python 3.12+
- uv 包管理器（推荐）
- Git
- 代码编辑器（VS Code推荐）

### 初始化开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd inventory-system-python

# 2. 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
# 或者
.venv\Scripts\activate     # Windows

# 3. 安装依赖
uv sync

# 4. 初始化数据库（首次运行）
uv run python -c "from app.db.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"

# 5. 启动开发服务器
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🏗️ 项目架构

### 目录结构说明

```
inventory-system-python/
├── app/                        # 应用主目录
│   ├── api/                   # API路由层
│   ├── core/                  # 核心功能模块
│   ├── crud/                  # 数据库操作层
│   ├── models/                # 数据模型定义
│   ├── schemas/               # API数据模型
│   ├── templates/             # HTML模板
│   └── static/                # 静态资源
├── alembic/                   # 数据库迁移系统
├── data/                      # 数据目录
├── logs/                      # 日志目录
└── tests/                     # 测试文件（待添加）
```

### 技术栈

- **后端框架**: FastAPI 0.116+
- **ORM**: SQLAlchemy 2.0+
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **认证**: JWT + bcrypt
- **数据验证**: Pydantic 2.0+
- **前端**: HTML + Tailwind CSS + JavaScript
- **数据库迁移**: Alembic 1.16+

## 📝 开发规范

### 代码风格

1. **Python代码规范**
   - 遵循 PEP 8 标准
   - 使用类型注解
   - 函数和类必须有文档字符串
   - 行长度限制：88字符

2. **命名规范**
   ```python
   # 变量和函数：snake_case
   user_name = "admin"
   def get_user_data():

   # 类名：PascalCase
   class UserService:

   # 常量：UPPER_CASE
   MAX_FILE_SIZE = 10 * 1024 * 1024

   # 私有变量：前缀下划线
   _private_variable = "internal"
   ```

3. **API端点命名**
   ```python
   # RESTful API规范
   @router.get("/equipment/")              # 获取列表
   @router.get("/equipment/{equipment_id}") # 获取单个
   @router.post("/equipment/")             # 创建
   @router.put("/equipment/{equipment_id}") # 更新
   @router.delete("/equipment/{equipment_id}") # 删除
   ```

### 数据库操作规范

1. **CRUD操作**
   ```python
   # 在app/crud/目录下创建对应模块
   # app/crud/equipment.py

   def get_equipment(db: Session, equipment_id: int):
       return db.query(Equipment).filter(Equipment.id == equipment_id).first()

   def create_equipment(db: Session, equipment: EquipmentCreate):
       db_equipment = Equipment(**equipment.dict())
       db.add(db_equipment)
       db.commit()
       db.refresh(db_equipment)
       return db_equipment
   ```

2. **查询优化**
   ```python
   # 使用索引字段进行查询
   db.query(Equipment).filter(Equipment.status == "在用")

   # 避免N+1查询问题
   db.query(Equipment).options(joinedload(Equipment.department))
   ```

### 错误处理规范

1. **API错误响应**
   ```python
   from fastapi import HTTPException

   try:
       # 业务逻辑
       result = process_data(data)
       return result
   except ValueError as e:
       raise HTTPException(status_code=400, detail=str(e))
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       raise HTTPException(status_code=500, detail="Internal server error")
   ```

2. **日志记录**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   def some_function():
       logger.info("Function started")
       try:
           # 业务逻辑
           logger.info("Function completed successfully")
       except Exception as e:
           logger.error(f"Function failed: {e}")
           raise
   ```

## 🔧 开发工作流

### 功能开发流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/new-equipment-management
   ```

2. **数据模型修改**
   ```python
   # 1. 在 app/models/models.py 中修改模型
   class Equipment(Base):
       # 添加新字段
       new_field = Column(String(100), nullable=True)

   # 2. 生成数据库迁移
   uv run alembic revision --autogenerate -m "添加设备新字段"

   # 3. 执行迁移
   uv run alembic upgrade head
   ```

3. **API开发**
   ```python
   # 1. 在 app/schemas/schemas.py 中定义数据模型
   class EquipmentUpdate(BaseModel):
       new_field: Optional[str] = None

   # 2. 在 app/crud/ 中实现数据库操作
   # 3. 在 app/api/ 中实现API端点
   ```

4. **前端开发**
   ```html
   <!-- 在 app/templates/ 中修改HTML模板 -->
   <!-- 在 app/static/js/ 中修改JavaScript -->
   ```

5. **测试和提交**
   ```bash
   # 测试功能
   # 提交代码
   git add .
   git commit -m "feat: 添加设备管理新功能"
   git push origin feature/new-equipment-management
   ```

### 数据库迁移最佳实践

1. **生成迁移文件**
   ```bash
   # 自动检测模型变更
   uv run alembic revision --autogenerate -m "描述变更内容"

   # 手动创建迁移
   uv run alembic revision -m "手动迁移"
   ```

2. **检查迁移文件**
   - 确保生成的迁移文件正确
   - 测试迁移的up和down操作
   - 在开发环境中验证

3. **执行迁移**
   ```bash
   # 升级到最新
   uv run alembic upgrade head

   # 降级到上一个版本（如需）
   uv run alembic downgrade -1
   ```

### 调试和测试

1. **调试技巧**
   ```python
   # 使用日志记录
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Debug info: {variable}")

   # 使用断点调试
   import pdb; pdb.set_trace()
   ```

2. **API测试**
   ```bash
   # 使用curl测试
   curl -X GET "http://localhost:8000/api/equipment/" \
        -H "Authorization: Bearer <token>"

   # 使用FastAPI文档页面
   # 访问 http://localhost:8000/docs
   ```

## 🎯 性能优化

### 数据库优化

1. **索引使用**
   ```python
   # 确保查询字段有索引
   class Equipment(Base):
       status = Column(String(20), index=True)  # 添加索引
   ```

2. **查询优化**
   ```python
   # 使用join避免N+1查询
   equipments = db.query(Equipment).options(
       joinedload(Equipment.department),
       joinedload(Equipment.category)
   ).all()

   # 分页查询
   equipments = db.query(Equipment).offset(skip).limit(limit).all()
   ```

### API性能优化

1. **响应优化**
   ```python
   # 使用响应模型减少数据传输
   @router.get("/equipment/", response_model=List[EquipmentResponse])

   # 缓存频繁查询的数据
   @router.get("/categories/", response_model=List[CategoryResponse])
   @cache(expire=300)  # 缓存5分钟
   ```

2. **异步处理**
   ```python
   # 使用异步API
   @router.get("/equipment/")
   async def get_equipments(skip: int = 0, limit: int = 100):
       return await get_equipments_async(skip=skip, limit=limit)
   ```

## 🔒 安全考虑

### 认证和授权

1. **JWT Token**
   ```python
   # 设置合理的过期时间
   ACCESS_TOKEN_EXPIRE_MINUTES = 30

   # 使用强密钥
   SECRET_KEY = "your-very-strong-secret-key"
   ```

2. **权限检查**
   ```python
   # 在API端点中添加权限检查
   @router.delete("/equipment/{equipment_id}")
   def delete_equipment(
       equipment_id: int,
       db: Session = Depends(get_db),
       current_user = Depends(get_current_user)
   ):
       # 检查用户权限
       if not check_permission(current_user, equipment_id):
           raise HTTPException(status_code=403, detail="Permission denied")
   ```

### 数据验证

1. **输入验证**
   ```python
   # 使用Pydantic进行数据验证
   class EquipmentCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=100)
       model: str = Field(..., min_length=1, max_length=100)

       @validator('name')
       def validate_name(cls, v):
           if not v.strip():
               raise ValueError('名称不能为空')
           return v.strip()
   ```

2. **SQL注入防护**
   ```python
   # 使用SQLAlchemy ORM，避免原生SQL
   # 安全的查询方式
   equipments = db.query(Equipment).filter(Equipment.name == search_term)

   # 如需使用原生SQL，使用参数化查询
   result = db.execute(
       text("SELECT * FROM equipment WHERE name = :name"),
       {"name": search_term}
   )
   ```

## 🧪 测试指南

### 单元测试（待实现）

```python
# tests/test_equipment.py
import pytest
from app.crud import equipment
from app.schemas import EquipmentCreate

def test_create_equipment(db_session):
    equipment_data = EquipmentCreate(
        name="测试设备",
        model="TEST-001"
    )
    result = equipment.create_equipment(db_session, equipment_data)
    assert result.name == "测试设备"
    assert result.model == "TEST-001"
```

### 集成测试（待实现）

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_equipment_list():
    response = client.get("/api/equipment/")
    assert response.status_code == 200
    assert "items" in response.json()
```

## 📝 代码审查清单

### 提交前检查

- [ ] 代码符合PEP 8规范
- [ ] 所有函数都有类型注解
- [ ] 关键函数有文档字符串
- [ ] 错误处理完善
- [ ] 日志记录适当
- [ ] 数据库迁移已生成并测试
- [ ] API接口已测试
- [ ] 安全性考虑充分
- [ ] 性能影响已评估

### 功能审查

- [ ] 功能需求完整实现
- [ ] 用户体验良好
- [ ] 错误提示清晰
- [ ] 边界情况处理
- [ ] 数据一致性保证

## 🚀 部署准备

### 生产环境检查

1. **环境变量配置**
   ```bash
   # 设置生产环境变量
   DATABASE_URL=postgresql://user:pass@localhost/inventory
   SECRET_KEY=production-secret-key
   DEBUG=False
   ```

2. **数据库准备**
   ```bash
   # 执行数据库迁移
   uv run alembic upgrade head

   # 创建索引
   uv run python create_indexes.py
   ```

3. **静态文件优化**
   ```bash
   # 压缩CSS和JS文件
   # 优化图片资源
   ```

## 🔍 故障排除

### 常见开发问题

1. **数据库连接问题**
   ```bash
   # 检查数据库文件权限
   ls -la data/inventory.db

   # 检查数据库状态
   uv run alembic current
   ```

2. **导入错误**
   ```python
   # 检查Python路径
   import sys
   print(sys.path)

   # 检查模块导入
   from app.models import models  # 确保能正常导入
   ```

3. **静态文件404**
   ```bash
   # 检查静态文件目录权限
   chmod -R 755 app/static/

   # 检查FastAPI静态文件配置
   ```

## 📚 学习资源

### 官方文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Alembic文档](https://alembic.sqlalchemy.org/)
- [Pydantic文档](https://pydantic-docs.helpmanual.io/)

### 最佳实践
- [Python代码规范PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [FastAPI最佳实践](https://fastapi.tiangolo.com/tutorial/best-practices/)
- [SQLAlchemy最佳实践](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)

## 🤝 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 编写代码和测试
4. 确保代码通过所有检查
5. 提交Pull Request
6. 参与代码审查

---

## 📞 获取帮助

- 查看项目README文档
- 阅读相关技术文档
- 在GitHub Issues中提问
- 联系项目维护者

**Happy Coding! 🎉**
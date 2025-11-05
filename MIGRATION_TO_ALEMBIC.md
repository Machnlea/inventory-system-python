# 标准Alembic迁移指南

## 📋 迁移步骤总结

### 1. 安装Alembic ✅
```bash
uv add alembic
```

### 2. 初始化Alembic环境 ✅
```bash
uv run alembic init alembic
```

### 3. 配置alembic.ini ✅
- 修改数据库URL为: `sqlite:///./inventory.db`
- 可选: 启用时间戳版本命名

### 4. 配置env.py ✅
- 添加项目路径到sys.path
- 导入项目模型Base.metadata
- 配置target_metadata

## 📁 新的文件结构

```
project/
├── alembic.ini              # Alembic主配置文件
├── alembic/                 # Alembic目录
│   ├── env.py              # 环境配置脚本
│   ├── script.py.mako      # 迁移文件模板
│   ├── versions/           # 迁移文件存储目录
│   └── README              # Alembic说明文档
├── app/                    # 应用代码
└── migrations/             # 旧的迁移目录（可保留或删除）
```

## 🚀 标准Alembic命令

### 创建新迁移
```bash
# 自动生成迁移（推荐）
uv run alembic revision --autogenerate -m "添加新表"

# 手动创建迁移
uv run alembic revision -m "手动迁移"
```

### 执行迁移
```bash
# 升级到最新版本
uv run alembic upgrade head

# 升级到特定版本
uv run alembic upgrade +1
uv run alembic upgrade 002_add_user_table

# 降级
uv run alembic downgrade -1
uv run alembic downgrade base
```

### 查看迁移状态
```bash
# 查看当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history

# 查看待执行的迁移
uv run alembic heads
```

## 🔄 从旧系统迁移

### 选项1: 保留现有迁移（推荐）
1. 保留旧migrations目录作为历史记录
2. 从当前数据库状态开始使用新Alembic
3. 标记当前数据库状态:

```bash
uv run alembic stamp head
```

### 选项2: 重新创建所有迁移
1. 删除数据库文件
2. 使用Alembic重新生成所有迁移
3. 重新执行所有迁移

## 📝 配置文件示例

### alembic.ini关键配置
```ini
[alembic]
script_location = %(here)s/alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### env.py关键配置
```python
# 导入项目模型
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.database import Base
from app.models import models

# 配置元数据
target_metadata = Base.metadata
```

## 🎯 优势对比

### 标准Alembic vs 当前系统

| 特性 | 当前系统 | 标准Alembic |
|------|----------|-------------|
| 版本控制 | 简单数字 | UUID + 描述 |
| 自动生成 | ❌ | ✅ |
| 复杂变更检测 | ❌ | ✅ |
| 团队协作 | 有限 | 优秀 |
| 回滚支持 | 基础 | 完整 |
| 文档和社区 | 有限 | 丰富 |

## 🔄 建议的迁移策略

### 阶段1: 并行运行（当前阶段）
- 保留旧的migrations目录
- 配置新的Alembic系统
- 标记当前数据库状态

### 阶段2: 逐步迁移
- 新功能使用Alembic管理
- 保留旧迁移作为参考

### 阶段3: 完全迁移（可选）
- 评估是否需要重新创建历史迁移
- 统一使用Alembic管理所有变更

## 🛠️ 下一步操作

1. **测试Alembic配置**:
   ```bash
   uv run alembic current
   uv run alembic history
   ```

2. **标记当前状态**:
   ```bash
   uv run alembic stamp head
   ```

3. **创建第一个Alembic迁移**:
   ```bash
   uv run alembic revision --autogenerate -m "迁移到标准Alembic"
   ```

4. **更新项目文档**:
   - 更新README.md
   - 添加开发指南
   - 更新部署文档

## 📚 参考资源

- [Alembic官方文档](https://alembic.sqlalchemy.org/)
- [FastAPI + Alembic教程](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [SQLAlchemy Alembic指南](https://docs.sqlalchemy.org/en/14/orm/extensions/alembic.html)
#!/bin/bash

# PostgreSQL 数据库初始化脚本
echo "🗄️ PostgreSQL 数据库初始化"
echo "============================"

# 检查必要的依赖
if ! command -v psql &> /dev/null; then
    echo "❌ 错误：未找到 PostgreSQL 客户端"
    echo "请先安装 PostgreSQL：sudo apt install postgresql-client"
    exit 1
fi

# 从环境变量获取配置，如果没有则使用默认值
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-inventory_system}
DB_USER=${DB_USER:-inventory_user}
DB_PASSWORD=${DB_PASSWORD}

# 检查是否提供了密码
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ 错误：请设置 DB_PASSWORD 环境变量"
    echo "例如：export DB_PASSWORD='your_secure_password'"
    exit 1
fi

# 测试连接
echo "🔍 测试数据库连接..."
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ 数据库连接失败，请检查："
    echo "  - 数据库服务是否运行"
    echo "  - 连接参数是否正确"
    echo "  - 用户权限是否足够"
    exit 1
fi

echo "✅ 数据库连接成功"

# 创建数据库（如果不存在）
echo "📋 检查数据库..."
DB_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
if [ -z "$DB_EXISTS" ]; then
    echo "🆕 创建数据库 $DB_NAME..."
    PGPASSWORD=$DB_PASSWORD createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
    echo "✅ 数据库创建成功"
else
    echo "✅ 数据库已存在"
fi

# 设置环境变量供后续使用
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

echo ""
echo "🚀 运行数据库迁移..."
uv run python scripts/init_db.py

echo ""
echo "📊 验证数据库表..."
TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
echo "✅ 数据库表数量: $TABLES"

echo ""
echo "🔍 显示数据库信息..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt"

echo ""
echo "✅ PostgreSQL 数据库初始化完成！"
echo "================================"
echo "📋 数据库信息："
echo "  主机: $DB_HOST:$DB_PORT"
echo "  数据库: $DB_NAME"
echo "  用户: $DB_USER"
echo ""
echo "🔗 连接字符串："
echo "  $DATABASE_URL"
echo ""
echo "📝 后续操作："
echo "  1. 启动应用: uv run python main.py"
echo "  2. 访问系统: http://localhost:8000"
echo "  3. 默认账户: admin / admin123"
echo "================================"
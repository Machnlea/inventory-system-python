#!/bin/bash

# PostgreSQL 快速设置脚本
echo "🚀 PostgreSQL 快速设置"
echo "====================="

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then
    echo "❌ 请不要使用 root 用户运行此脚本"
    echo "请使用普通用户: ./scripts/setup_postgres.sh"
    exit 1
fi

# 安装 PostgreSQL
echo "📦 安装 PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 启动服务
echo "🔄 启动 PostgreSQL 服务..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
echo "🗄️ 创建数据库和用户..."
sudo -u postgres psql << EOF
CREATE DATABASE inventory_system;
CREATE USER inventory_user WITH PASSWORD 'postgres123';
GRANT ALL PRIVILEGES ON DATABASE inventory_system TO inventory_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inventory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO inventory_user;
EOF

# 创建环境变量文件
echo "⚙️ 创建环境变量文件..."
if [ ! -f .env ]; then
    cp .env.example .env
    # 更新数据库密码
    sed -i 's/your_secure_password/postgres123/g' .env
    echo "✅ 已创建 .env 文件，数据库密码: postgres123"
else
    echo "⚠️ .env 文件已存在，请手动配置"
fi

# 测试连接
echo "🔍 测试数据库连接..."
if PGPASSWORD=postgres123 psql -h localhost -U inventory_user -d inventory_system -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ 数据库连接成功"
else
    echo "❌ 数据库连接失败"
    exit 1
fi

# 初始化数据库
echo "🏗️ 初始化数据库结构..."
export DB_PASSWORD=postgres123
./scripts/init_postgres.sh

echo ""
echo "✅ PostgreSQL 设置完成！"
echo "================================"
echo "📋 配置信息："
echo "  数据库: inventory_system"
echo "  用户: inventory_user"
echo "  密码: postgres123"
echo "  主机: localhost:5432"
echo ""
echo "🔧 后续操作："
echo "  1. 编辑 .env 文件修改配置"
echo "  2. 启动应用: uv run python main.py"
echo "  3. 访问系统: http://localhost:8000"
echo ""
echo "⚠️ 安全提醒："
echo "  - 请修改默认密码 postgres123"
echo "  - 请修改 SECRET_KEY"
echo "  - 生产环境请使用强密码"
echo "================================"
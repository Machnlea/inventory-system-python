#!/bin/bash

# 生产环境部署脚本
echo "🚀 设备台账管理系统生产环境部署"
echo "================================"

# 检查必要工具
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未找到Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：未找到Docker Compose"
    exit 1
fi

# 创建必要目录
echo "📁 创建数据目录..."
mkdir -p data app/static/uploads/certificates app/static/uploads/documents

# 设置权限
echo "🔐 设置文件权限..."
chmod 755 scripts/*.sh
chmod 644 app/static/uploads/.gitkeep

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建和启动
echo "🏗️ 构建服务..."
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "✅ 部署完成！"
echo "================================"
echo "🌐 访问地址：http://localhost"
echo "📚 API文档：http://localhost/docs"
echo "🔧 管理界面：http://localhost/admin"
echo ""
echo "🔑 默认账户："
echo "用户名：admin"
echo "密码：admin123"
echo ""
echo "📋 常用命令："
echo "查看日志：docker-compose logs -f"
echo "停止服务：docker-compose down"
echo "重启服务：docker-compose restart"
echo "================================"
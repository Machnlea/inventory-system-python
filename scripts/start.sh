#!/bin/bash

# 设备台账管理系统启动脚本

echo "🚀 设备台账管理系统启动脚本"
echo "=============================="

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误：未找到uv包管理器"
    echo "请先安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ 检测到uv包管理器"

# 检查数据库是否存在
if [ ! -f "inventory.db" ]; then
    echo "🔧 首次运行，正在初始化数据库..."
    uv run python init_db.py
    echo "✅ 数据库初始化完成"
else
    echo "✅ 数据库已存在"
fi
uv run python init_db.py
echo ""
echo "🌐 启动Web服务器..."
echo "访问地址：http://localhost:8000"
echo "API文档：http://localhost:8000/docs"
echo ""
echo "默认账户："
echo "用户名：admin"
echo "密码：admin123"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=============================="

# 启动服务器
# uv run python main.py
uv run python -m uvicorn main:app --reload
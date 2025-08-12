#!/bin/bash

# 重启设备台账管理系统
echo "=== 重启设备台账管理系统 ==="

# 检查端口占用
if lsof -i :8000 >/dev/null 2>&1; then
    echo "发现端口8000被占用，正在停止现有服务..."
    # 查找并终止占用端口的进程
    pid=$(lsof -ti :8000)
    if [ ! -z "$pid" ]; then
        kill -9 $pid
        echo "已终止进程 $pid"
    fi
fi

# 等待端口释放
sleep 2

# 启动服务
echo "正在启动服务..."
nohup uv run python main.py > app.log 2>&1 &

# 等待服务启动
sleep 3

# 检查服务状态
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ 服务启动成功！"
    echo "✓ 访问地址: http://localhost:8000"
    echo "✓ API文档: http://localhost:8000/docs"
    echo "✓ 分度值字段功能已启用"
    echo ""
    echo "功能特点:"
    echo "- 分度值字段支持"
    echo "- 导出功能包含分度值"
    echo "- 简化的字段结构"
else
    echo "✗ 服务启动失败，请检查日志："
    tail -20 app.log
fi
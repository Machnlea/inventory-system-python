#!/bin/bash

# 计量器具台账系统 - 增强版启动脚本
# Measuring Equipment Ledger System - Enhanced Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示欢迎信息
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║            计量器具台账系统 - Linux 启动脚本                  ║"
echo "║                                                              ║"
echo "║              Measuring Equipment Ledger System                ║"
echo "║                                                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}[错误] 未检测到uv，请先安装uv${NC}"
    echo "安装命令：curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "下载地址：https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# 检查并初始化项目依赖
echo -e "${CYAN}[信息] 检查项目依赖...${NC}"
if [ ! -f "uv.lock" ]; then
    echo -e "${YELLOW}[信息] 初始化项目依赖...${NC}"
    if uv sync -i https://mirrors.aliyun.com/pypi/simple/; then
        echo -e "${GREEN}[成功] 依赖初始化完成${NC}"
    else
        echo -e "${RED}[错误] 依赖初始化失败${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[成功] 依赖已初始化${NC}"
fi

# 检查数据库文件是否存在
if [ ! -f "data/inventory.db" ]; then
    echo -e "${YELLOW}[警告] 数据库文件不存在，正在初始化数据库...${NC}"
    mkdir -p data
    if uv run python init_db.py; then
        echo -e "${GREEN}[成功] 数据库初始化完成${NC}"
    else
        echo -e "${RED}[错误] 数据库初始化失败${NC}"
        exit 1
    fi
fi

# 设置环境变量
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 显示启动信息
echo
echo -e "${CYAN}[信息] 启动计量器具台账系统...${NC}"
echo -e "${CYAN}[信息] 服务地址：http://localhost:8000${NC}"
echo -e "${CYAN}[信息] API文档：http://localhost:8000/docs${NC}"
echo -e "${CYAN}[信息] 按Ctrl+C停止服务${NC}"
echo

# 启动服务器
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 如果服务器停止，显示信息
echo
echo -e "${GREEN}[信息] 服务已停止${NC}"
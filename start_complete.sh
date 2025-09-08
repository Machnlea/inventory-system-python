#!/bin/bash

# 计量器具台账系统 - 完整启动脚本
# Measuring Equipment Ledger System - Complete Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示欢迎信息
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              计量器具台账系统 - 完整启动脚本                  ║"
echo "║           Measuring Equipment Ledger System                   ║"
echo "║                                                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# 检查uv是否安装
echo -e "${BLUE}[检查] 正在检查uv环境...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}[错误] 未检测到uv，请先安装uv${NC}"
    echo "安装命令：curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "下载地址：https://docs.astral.sh/uv/getting-started/installation/"
    echo
    echo "安装后请确保将uv添加到系统PATH中"
    exit 1
fi
echo -e "${GREEN}[成功] uv环境检查通过${NC}"

# 检查并初始化项目依赖
echo -e "${BLUE}[检查] 正在检查项目依赖...${NC}"
if [ ! -f "uv.lock" ]; then
    echo -e "${YELLOW}[信息] 正在初始化项目依赖...${NC}"
    uv sync -i https://mirrors.aliyun.com/pypi/simple/
    echo -e "${GREEN}[成功] 依赖初始化完成${NC}"
else
    echo -e "${GREEN}[成功] 依赖已初始化${NC}"
fi

# 检查数据库
echo -e "${BLUE}[检查] 正在检查数据库...${NC}"
if [ ! -f "data/inventory.db" ]; then
    echo -e "${YELLOW}[警告] 数据库文件不存在，正在初始化...${NC}"
    mkdir -p data
    uv run python init_db.py
    echo -e "${GREEN}[成功] 数据库初始化完成${NC}"
else
    echo -e "${GREEN}[成功] 数据库已就绪${NC}"
fi

# 设置环境变量
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 显示启动信息
echo
echo -e "${BLUE}[启动] 计量器具台账系统正在启动...${NC}"
echo -e "${BLUE}[信息] 服务地址：http://localhost:8000${NC}"
echo -e "${BLUE}[信息] API文档：http://localhost:8000/docs${NC}"
echo -e "${BLUE}[信息] 按Ctrl+C停止服务${NC}"
echo

# 启动服务器
echo -e "${BLUE}[运行] 启动服务器...${NC}"
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 服务停止后的提示
echo
echo -e "${GREEN}[信息] 服务已停止${NC}"
echo
echo "感谢使用计量器具台账系统！"
#!/bin/bash

# 计量器具台账系统 - 标准启动脚本
# Measuring Equipment Ledger System - Standard Startup Script

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
echo "║                  计量器具台账系统                             ║"
echo "║            Measuring Equipment Ledger System                   ║"
echo "║                                                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}[错误] 未检测到uv，请先安装uv${NC}"
    echo "安装命令：curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "下载地址：https://docs.astral.sh/uv/getting-started/installation/"
    echo
    exit 1
fi
echo -e "${GREEN}[成功] uv环境检查通过${NC}"

# 检查主程序文件
if [ ! -f "main.py" ]; then
    echo -e "${RED}[错误] 主程序文件 main.py 不存在${NC}"
    echo "请确保在项目根目录运行此脚本"
    exit 1
fi

# 使用uv启动服务器
echo -e "${BLUE}[信息] 使用uv启动服务器...${NC}"
echo -e "${BLUE}[信息] 服务地址：http://localhost:8000${NC}"
echo -e "${BLUE}[信息] API文档：http://localhost:8000/docs${NC}"
echo -e "${BLUE}[信息] 按Ctrl+C停止服务${NC}"
echo

# 使用uv启动服务
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 服务停止后的提示
echo
echo -e "${GREEN}[信息] 服务已停止${NC}"
echo
echo "感谢使用计量器具台账系统！"
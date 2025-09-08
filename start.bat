@echo off
chcp 65001 >nul
title 库存管理系统启动脚本

:: 设置颜色
color 0A

:: 显示欢迎信息
echo.
echo     ╔══════════════════════════════════════════════════════════════╗
echo     ║                                                              ║
echo     ║            库存管理系统 - Windows 启动脚本                   ║
echo     ║                                                              ║
echo     ║                    Inventory Management System               ║
echo     ║                                                              ║
echo     ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查uv是否安装
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到uv，请先安装uv
    echo 安装命令：powershell -c "irm https://astral.sh/uv/install.sh | iex"
    echo 下载地址：https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

:: 检查并初始化项目依赖
echo [信息] 检查项目依赖...
if not exist "uv.lock" (
    echo [信息] 初始化项目依赖...
    uv sync -i https://mirrors.aliyun.com/pypi/simple/
    if %errorlevel% neq 0 (
        echo [错误] 依赖初始化失败
        pause
        exit /b 1
    )
    echo [成功] 依赖初始化完成
)

:: 检查数据库文件是否存在
if not exist "data\inventory.db" (
    echo [警告] 数据库文件不存在，正在初始化数据库...
    if not exist "data" mkdir data
    uv run python init_db.py
    if %errorlevel% neq 0 (
        echo [错误] 数据库初始化失败
        pause
        exit /b 1
    )
    echo [成功] 数据库初始化完成
)

:: 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: 显示启动信息
echo.
echo [信息] 启动库存管理系统...
echo [信息] 服务地址：http://localhost:8000
echo [信息] API文档：http://localhost:8000/docs
echo [信息] 按Ctrl+C停止服务
echo.

:: 启动服务器
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 如果服务器停止，显示信息
echo.
echo [信息] 服务已停止
pause
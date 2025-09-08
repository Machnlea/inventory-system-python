@echo off
chcp 65001 >nul
title 库存管理系统启动脚本

:: 设置颜色
color 0A

:: 显示欢迎信息
echo.
echo     ╔══════════════════════════════════════════════════════════════╗
echo     ║                                                              ║
echo     ║            库存管理系统 - Windows 启动脚本                    ║
echo     ║                                                              ║
echo     ║                    Inventory Management System               ║
echo     ║                                                              ║
echo     ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.12或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查虚拟环境是否存在
if not exist ".venv" (
    echo [信息] 创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

:: 检查并安装依赖
echo [信息] 检查项目依赖...
pip list | findstr "fastapi" >nul
if %errorlevel% neq 0 (
    echo [信息] 安装项目依赖...
    pip install -e .
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
)

:: 检查数据库文件是否存在
if not exist "data\inventory.db" (
    echo [警告] 数据库文件不存在，正在初始化数据库...
    if not exist "data" mkdir data
    python init_db.py
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
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 如果服务器停止，显示信息
echo.
echo [信息] 服务已停止
pause
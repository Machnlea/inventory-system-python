@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置窗口标题和颜色
title 库存管理系统 - 完整启动脚本
color 0A

:: 显示欢迎信息
echo.
echo     ╔══════════════════════════════════════════════════════════════╗
echo     ║                                                              ║
echo     ║                库存管理系统 - 完整启动脚本                      ║
echo     ║               Inventory Management System                    ║
echo     ║                                                              ║
echo     ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查uv是否安装
echo [检查] 正在检查uv环境...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到uv，请先安装uv
    echo 安装命令：powershell -c "irm https://astral.sh/uv/install.sh | iex"
    echo 下载地址：https://docs.astral.sh/uv/getting-started/installation/
    echo.
    echo 安装后请确保将uv添加到系统PATH中
    pause
    exit /b 1
)
echo [成功] uv环境检查通过

:: 检查并初始化项目依赖
echo [检查] 正在检查项目依赖...
if not exist "uv.lock" (
    echo [信息] 正在初始化项目依赖...
    uv sync -i https://mirrors.aliyun.com/pypi/simple/
    if %errorlevel% neq 0 (
        echo [错误] 依赖初始化失败
        pause
        exit /b 1
    )
    echo [成功] 依赖初始化完成
) else (
    echo [成功] 依赖已初始化
)

:: 检查数据库
echo [检查] 正在检查数据库...
if not exist "data\inventory.db" (
    echo [警告] 数据库文件不存在，正在初始化...
    if not exist "data" mkdir data
    uv run python init_db.py
    if %errorlevel% neq 0 (
        echo [错误] 数据库初始化失败
        pause
        exit /b 1
    )
    echo [成功] 数据库初始化完成
) else (
    echo [成功] 数据库已就绪
)

:: 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: 显示启动信息
echo.
echo [启动] 库存管理系统正在启动...
echo [信息] 服务地址：http://localhost:8000
echo [信息] API文档：http://localhost:8000/docs
echo [信息] 按Ctrl+C停止服务
echo.

:: 启动服务器
echo [运行] 启动服务器...
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 服务停止后的提示
echo.
echo [信息] 服务已停止
echo.
echo 感谢使用库存管理系统！
pause
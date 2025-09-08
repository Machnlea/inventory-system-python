@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置窗口标题和颜色
title 库存管理系统服务
color 0A

:: 显示欢迎信息
echo.
echo     ╔══════════════════════════════════════════════════════════════╗
echo     ║                                                              ║
echo     ║                      库存管理系统                             ║
echo     ║                    Inventory Management System                 ║
echo     ║                                                              ║
echo     ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在，请先创建虚拟环境
    echo.
    echo 创建命令：
    echo   python -m venv .venv
    echo.
    pause
    exit /b 1
)

:: 检查主程序文件
if not exist "main.py" (
    echo [错误] 主程序文件 main.py 不存在
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

:: 激活虚拟环境并启动服务器
echo [信息] 激活虚拟环境并启动服务器...
echo [信息] 服务地址：http://localhost:8000
echo [信息] API文档：http://localhost:8000/docs
echo [信息] 按Ctrl+C停止服务
echo.

:: 激活虚拟环境并启动服务
call .venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 服务停止后的提示
echo.
echo [信息] 服务已停止
echo.
echo 感谢使用库存管理系统！
pause
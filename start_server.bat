@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置窗口标题和颜色
title 计量器具台账系统服务
color 0A

:: 显示欢迎信息
echo.
echo     ╔══════════════════════════════════════════════════════════════╗
echo     ║                                                              ║
echo     ║                    计量器具台账系统                          ║
echo     ║              Measuring Equipment Ledger System               ║
echo     ║                                                              ║
echo     ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查uv是否安装
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到uv，请先安装uv
    echo 安装命令：powershell -c "irm https://astral.sh/uv/install.sh | iex"
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

:: 使用uv启动服务器
echo [信息] 使用uv启动服务器...
echo [信息] 服务地址：http://localhost:8000
echo [信息] API文档：http://localhost:8000/docs
echo [信息] 按Ctrl+C停止服务
echo.

:: 使用uv启动服务
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 服务停止后的提示
echo.
echo [信息] 服务已停止
echo.
echo 感谢使用计量器具台账系统！
pause
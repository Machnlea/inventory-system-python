@echo off
title 计量器具台账系统

:: 使用uv启动服务器
echo 正在启动计量器具台账系统...
echo 服务地址：http://localhost:8000
echo 按Ctrl+C停止服务
echo.

uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
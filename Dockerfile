FROM python:3.12-slim

WORKDIR /app

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --frozen

# 创建上传目录
RUN mkdir -p app/static/uploads/certificates app/static/uploads/documents

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
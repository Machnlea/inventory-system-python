#!/bin/bash

# PostgreSQL 数据库备份脚本
echo "💾 PostgreSQL 数据库备份"
echo "========================="

# 配置
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-inventory_system}
DB_USER=${DB_USER:-inventory_user}
BACKUP_DIR="./data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

# 检查必要工具
if ! command -v pg_dump &> /dev/null; then
    echo "❌ 错误：未找到 pg_dump 工具"
    echo "请先安装 PostgreSQL 客户端工具"
    exit 1
fi

# 检查密码
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ 错误：请设置 DB_PASSWORD 环境变量"
    exit 1
fi

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "📁 备份目录: $BACKUP_DIR"
echo "🗄️ 数据库: $DB_NAME"
echo "⏰ 备份时间: $(date)"

# 执行备份
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"
echo "💾 正在备份数据库..."

if PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE; then
    echo "✅ 备份成功: $BACKUP_FILE"
    
    # 压缩备份文件
    gzip $BACKUP_FILE
    echo "🗜️ 压缩完成: $BACKUP_FILE.gz"
    
    # 删除旧备份
    echo "🧹 清理 $KEEP_DAYS 天前的备份..."
    find $BACKUP_DIR -name "backup_${DB_NAME}_*.sql.gz" -mtime +$KEEP_DAYS -delete
    
    # 显示备份文件列表
    echo ""
    echo "📋 现有备份文件："
    ls -lah $BACKUP_DIR/backup_${DB_NAME}_*.sql.gz 2>/dev/null || echo "暂无备份文件"
    
else
    echo "❌ 备份失败！"
    exit 1
fi

echo ""
echo "✅ 备份完成！"
echo "================================"
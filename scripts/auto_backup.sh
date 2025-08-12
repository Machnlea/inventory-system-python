#!/bin/bash

# 自动备份脚本
# 用于定时备份数据库

# 设置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/inventory.db"
BACKUP_TOOL="$SCRIPT_DIR/backup_tool.py"
LOG_FILE="$SCRIPT_DIR/backups/backup.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查数据库文件是否存在
if [ ! -f "$DB_PATH" ]; then
    log "错误: 数据库文件不存在: $DB_PATH"
    exit 1
fi

# 检查备份工具是否存在
if [ ! -f "$BACKUP_TOOL" ]; then
    log "错误: 备份工具不存在: $BACKUP_TOOL"
    exit 1
fi

# 获取当前时间信息
DAY_OF_WEEK=$(date +%u)  # 1-7 (1是周一)
DAY_OF_MONTH=$(date +%d)  # 01-31
HOUR=$(date +%H)         # 00-23

log "开始自动备份任务"

# 根据时间决定备份类型
if [ "$DAY_OF_MONTH" = "01" ]; then
    # 每月1号执行月度备份
    BACKUP_TYPE="monthly"
    log "执行月度备份"
elif [ "$DAY_OF_WEEK" = "1" ]; then
    # 每周一执行周度备份
    BACKUP_TYPE="weekly"
    log "执行周度备份"
else
    # 每天执行日备份
    BACKUP_TYPE="daily"
    log "执行日备份"
fi

# 执行备份
cd "$SCRIPT_DIR"
python3 "$BACKUP_TOOL" --action backup --type "$BACKUP_TYPE" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "备份任务完成成功"
else
    log "备份任务失败"
    exit 1
fi

# 清理旧备份
log "清理旧备份文件"
python3 "$BACKUP_TOOL" --action clean >> "$LOG_FILE" 2>&1

# 显示备份状态
log "当前备份状态:"
python3 "$BACKUP_TOOL" --action status >> "$LOG_FILE" 2>&1

log "自动备份任务完成"
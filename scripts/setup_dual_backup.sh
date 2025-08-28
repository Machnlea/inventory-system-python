#!/bin/bash

# 内网双备份系统部署脚本
# 适用于20人以下内网环境

echo "=== 设备台账系统 - 内网双备份部署 ==="

# 设置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/data/backups/inventory"
SECONDARY_BACKUP="/backup/inventory_secondary"

# 创建备份目录
echo "创建备份目录..."
sudo mkdir -p "$BACKUP_DIR"/{monthly,weekly,daily,attachments}
sudo mkdir -p "$SECONDARY_BACKUP"/{monthly,weekly,daily,attachments}
sudo mkdir -p /data/archive/inventory

# 设置权限
sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR" "$SECONDARY_BACKUP" /data/archive

# 创建双备份脚本
echo "创建双备份脚本..."
cat > "$SCRIPT_DIR/dual_backup.sh" << 'EOF'
#!/bin/bash

# 内网双备份脚本
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# 备份路径
PRIMARY_BACKUP="/data/backups/inventory"
SECONDARY_BACKUP="/backup/inventory_secondary"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$PRIMARY_BACKUP/backup.log"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SECONDARY_BACKUP/backup.log"
}

log "开始执行双备份..."

# 1. 备份数据库
log "备份数据库..."
DB_NAME="inventory_${TIMESTAMP}.db"
cp "$PROJECT_DIR/data/inventory.db" "$PRIMARY_BACKUP/monthly/$DB_NAME"
cp "$PROJECT_DIR/data/inventory.db" "$SECONDARY_BACKUP/monthly/$DB_NAME"

# 2. 备份附件文件
log "备份附件文件..."
ATTACHMENTS_NAME="attachments_${TIMESTAMP}.tar.gz"
if [ -d "$PROJECT_DIR/app/static/uploads" ]; then
    tar -czf "$PRIMARY_BACKUP/attachments/$ATTACHMENTS_NAME" -C "$PROJECT_DIR" app/static/uploads/ 2>/dev/null
    tar -czf "$SECONDARY_BACKUP/attachments/$ATTACHMENTS_NAME" -C "$PROJECT_DIR" app/static/uploads/ 2>/dev/null
fi

# 3. 备份配置文件
log "备份配置文件..."
CONFIG_NAME="config_${TIMESTAMP}.tar.gz"
tar -czf "$PRIMARY_BACKUP/monthly/$CONFIG_NAME" -C "$PROJECT_DIR" data/system_settings.json scripts/ 2>/dev/null
tar -czf "$SECONDARY_BACKUP/monthly/$CONFIG_NAME" -C "$PROJECT_DIR" data/system_settings.json scripts/ 2>/dev/null

# 4. 创建备份清单
log "创建备份清单..."
cat > "$PRIMARY_BACKUP/backup_manifest_${TIMESTAMP}.txt" << EOL
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
数据库文件: $DB_NAME ($(du -h "$PRIMARY_BACKUP/monthly/$DB_NAME" | cut -f1))
附件文件: $ATTACHMENTS_NAME ($(du -h "$PRIMARY_BACKUP/attachments/$ATTACHMENTS_NAME" 2>/dev/null | cut -f1 || echo "无"))
配置文件: $CONFIG_NAME ($(du -h "$PRIMARY_BACKUP/monthly/$CONFIG_NAME" | cut -f1))
备份状态: 成功
EOL

cp "$PRIMARY_BACKUP/backup_manifest_${TIMESTAMP}.txt" "$SECONDARY_BACKUP/"

# 5. 验证备份
log "验证备份完整性..."
PRIMARY_SIZE=$(du -s "$PRIMARY_BACKUP/monthly/$DB_NAME" | cut -f1)
SECONDARY_SIZE=$(du -s "$SECONDARY_BACKUP/monthly/$DB_NAME" | cut -f1)

if [ "$PRIMARY_SIZE" = "$SECONDARY_SIZE" ] && [ "$PRIMARY_SIZE" -gt 0 ]; then
    log "备份验证成功: 主备份($PRIMARY_SIZE) = 从备份($SECONDARY_SIZE)"
else
    log "警告: 备份大小不一致或文件为空!"
    exit 1
fi

# 6. 清理超过12个月的备份
log "清理旧备份..."
find "$PRIMARY_BACKUP/monthly" -name "inventory_*.db" -mtime +365 -delete 2>/dev/null
find "$SECONDARY_BACKUP/monthly" -name "inventory_*.db" -mtime +365 -delete 2>/dev/null
find "$PRIMARY_BACKUP/attachments" -name "attachments_*.tar.gz" -mtime +365 -delete 2>/dev/null
find "$SECONDARY_BACKUP/attachments" -name "attachments_*.tar.gz" -mtime +365 -delete 2>/dev/null

log "双备份完成!"

# 7. 发送备份报告（可选）
BACKUP_REPORT="$PRIMARY_BACKUP/latest_backup_report.txt"
cat > "$BACKUP_REPORT" << EOL
=== 库存系统备份报告 ===
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
主备份位置: $PRIMARY_BACKUP
从备份位置: $SECONDARY_BACKUP
数据库大小: $(du -h "$PRIMARY_BACKUP/monthly/$DB_NAME" | cut -f1)
附件大小: $(du -h "$PRIMARY_BACKUP/attachments/$ATTACHMENTS_NAME" 2>/dev/null | cut -f1 || echo "无附件")
总备份大小: $(du -sh "$PRIMARY_BACKUP" | cut -f1)
状态: ✓ 成功

备份清单:
- 数据库: $DB_NAME
- 附件: $ATTACHMENTS_NAME
- 配置: $CONFIG_NAME

下次备份: $(date -d "+1 month" '+%Y-%m-%d %H:%M:%S')
EOL

log "备份报告已生成: $BACKUP_REPORT"
EOF

chmod +x "$SCRIPT_DIR/dual_backup.sh"

# 创建月度定时任务
echo "设置定时任务..."
cat > "$SCRIPT_DIR/monthly_cron.conf" << EOF
# 内网月度双备份任务
# 每月1号和15号凌晨3点执行
0 3 1,15 * * $SCRIPT_DIR/dual_backup.sh

# 每天凌晨2点快速数据库备份
0 2 * * * cp $PROJECT_DIR/data/inventory.db /data/backups/inventory/daily/inventory_\$(date +\%Y\%m\%d).db
EOF

echo "部署完成!"
echo ""
echo "下一步操作:"
echo "1. 安装定时任务: crontab $SCRIPT_DIR/monthly_cron.conf"
echo "2. 测试备份脚本: $SCRIPT_DIR/dual_backup.sh"
echo "3. 查看备份目录: ls -la $BACKUP_DIR"
echo ""
echo "备份策略:"
echo "- 月度完整备份: 每月1号和15号"
echo "- 日常数据库备份: 每天"
echo "- 保留期限: 12个月"
echo "- 存储位置: $BACKUP_DIR (主) + $SECONDARY_BACKUP (从)"
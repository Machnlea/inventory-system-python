#!/bin/bash

# 三重备份系统：本地硬盘 + U盘 + WebDAV
# 适用于内网环境的数据安全保障

# =============================================================================
# 配置区域 - 请根据实际环境修改
# =============================================================================

# 基础路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 备份路径配置
LOCAL_BACKUP="/data/backups/inventory"           # 本地硬盘备份
USB_BACKUP="/media/usb_backup/inventory"         # U盘备份路径
USB_DEVICE="/dev/sdb1"                           # U盘设备路径（需要根据实际调整）

# 坚果云WebDAV配置
JIANGUOYUN_URL="https://dav.jianguoyun.com/dav/inventory"  # 坚果云WebDAV地址
JIANGUOYUN_USER="your_email@company.com"                   # 坚果云账号邮箱
JIANGUOYUN_PASS="your_app_password"                        # 坚果云应用密码（非登录密码）
JIANGUOYUN_LOCAL="/tmp/jianguoyun_mount"                    # 本地挂载点

# 备份保留策略
KEEP_MONTHLY=12                                  # 保留12个月月度备份
KEEP_DAILY=30                                   # 保留30天日常备份

# =============================================================================
# 工具函数
# =============================================================================

# 日志记录
log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$timestamp][$level] $message" | tee -a "$LOCAL_BACKUP/logs/backup.log"
}

# 错误处理
handle_error() {
    local error_message="$1"
    log "ERROR" "$error_message"
    
    # 发送错误通知（可选）
    echo "备份失败: $error_message" >> "$LOCAL_BACKUP/logs/error_notifications.txt"
    exit 1
}

# 检查依赖
check_dependencies() {
    log "INFO" "检查系统依赖..."
    
    # 检查必要工具
    local tools=("curl" "davfs2" "tar" "gzip")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            handle_error "缺少必要工具: $tool，请安装后重试"
        fi
    done
    
    # 检查项目文件
    if [ ! -f "$PROJECT_DIR/data/inventory.db" ]; then
        handle_error "找不到数据库文件: $PROJECT_DIR/data/inventory.db"
    fi
    
    log "INFO" "依赖检查完成"
}

# 创建备份目录
setup_directories() {
    log "INFO" "创建备份目录结构..."
    
    # 本地备份目录
    mkdir -p "$LOCAL_BACKUP"/{monthly,daily,attachments,logs,temp}
    
    # 设置权限
    chmod 755 "$LOCAL_BACKUP"
    chown -R $(whoami):$(whoami) "$LOCAL_BACKUP"
    
    log "INFO" "目录结构创建完成"
}

# =============================================================================
# 第一层：本地硬盘备份
# =============================================================================

backup_local() {
    log "INFO" "开始本地硬盘备份..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_date=$(date +%Y%m%d)
    
    # 1. 备份数据库
    local db_backup="$LOCAL_BACKUP/monthly/inventory_${timestamp}.db"
    cp "$PROJECT_DIR/data/inventory.db" "$db_backup"
    
    if [ $? -eq 0 ]; then
        log "INFO" "数据库备份成功: $(basename "$db_backup")"
    else
        handle_error "数据库备份失败"
    fi
    
    # 2. 备份附件
    if [ -d "$PROJECT_DIR/data/uploads" ]; then
        local attachments_backup="$LOCAL_BACKUP/attachments/attachments_${timestamp}.tar.gz"
        tar -czf "$attachments_backup" -C "$PROJECT_DIR" data/uploads/ 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "INFO" "附件备份成功: $(basename "$attachments_backup")"
        else
            log "WARN" "附件备份失败或无附件文件"
        fi
    fi
    
    # 3. 备份配置
    local config_backup="$LOCAL_BACKUP/monthly/config_${timestamp}.tar.gz"
    tar -czf "$config_backup" -C "$PROJECT_DIR" data/system_settings.json scripts/ app/core/config.py 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "INFO" "配置备份成功: $(basename "$config_backup")"
    else
        log "WARN" "配置备份失败"
    fi
    
    # 4. 创建备份清单
    cat > "$LOCAL_BACKUP/backup_manifest_${timestamp}.txt" << EOL
=== 库存管理系统备份清单 ===
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份类型: 完整备份
服务器: $(hostname)

文件清单:
- 数据库: $(basename "$db_backup") ($(du -h "$db_backup" | cut -f1))
- 附件: $(basename "$attachments_backup" 2>/dev/null || echo "无附件") ($(du -h "$attachments_backup" 2>/dev/null | cut -f1 || echo "0"))
- 配置: $(basename "$config_backup") ($(du -h "$config_backup" | cut -f1))

数据库记录数:
$(sqlite3 "$db_backup" "SELECT 
    'Users: ' || COUNT(*) FROM users 
    UNION ALL SELECT 'Equipment: ' || COUNT(*) FROM equipment 
    UNION ALL SELECT 'Departments: ' || COUNT(*) FROM departments;" 2>/dev/null || echo "无法读取数据库统计")

备份验证: $(sqlite3 "$db_backup" "PRAGMA integrity_check;" 2>/dev/null || echo "验证失败")
EOL
    
    log "INFO" "本地备份完成，大小: $(du -sh "$LOCAL_BACKUP/monthly" | cut -f1)"
    
    # 返回最新备份路径供其他函数使用
    echo "$db_backup:$attachments_backup:$config_backup"
}

# =============================================================================
# 第二层：U盘备份
# =============================================================================

backup_usb() {
    local backup_files="$1"
    log "INFO" "开始U盘备份..."
    
    # 检测U盘
    if [ ! -b "$USB_DEVICE" ]; then
        log "WARN" "未检测到U盘设备: $USB_DEVICE，跳过U盘备份"
        return 1
    fi
    
    # 挂载U盘
    if ! mountpoint -q "$USB_BACKUP" 2>/dev/null; then
        mkdir -p "$USB_BACKUP"
        mount "$USB_DEVICE" "$USB_BACKUP" 2>/dev/null
        
        if [ $? -ne 0 ]; then
            log "WARN" "U盘挂载失败，跳过U盘备份"
            return 1
        fi
        log "INFO" "U盘挂载成功"
    fi
    
    # 创建U盘目录结构
    mkdir -p "$USB_BACKUP"/{monthly,emergency,manifest}
    
    # 复制备份文件
    IFS=':' read -ra FILES <<< "$backup_files"
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$USB_BACKUP/monthly/"
            log "INFO" "U盘复制成功: $(basename "$file")"
        fi
    done
    
    # 复制最新的备份清单
    find "$LOCAL_BACKUP" -name "backup_manifest_*.txt" -type f -exec cp {} "$USB_BACKUP/manifest/" \; 2>/dev/null
    
    # 创建紧急恢复说明
    cat > "$USB_BACKUP/emergency/恢复说明.txt" << EOL
=== 紧急恢复指南 ===

1. 恢复数据库:
   cp monthly/inventory_*.db /path/to/project/data/inventory.db

2. 恢复附件:
   cd /path/to/project
   tar -xzf /media/usb_backup/inventory/monthly/attachments_*.tar.gz

3. 恢复配置:
   tar -xzf /path/to/project monthly/config_*.tar.gz

4. 重启服务:
   systemctl restart inventory-system

恢复完成后请验证系统功能是否正常。
EOL
    
    # 计算U盘使用空间
    local usb_usage=$(df -h "$USB_BACKUP" | awk 'NR==2 {print $3"/"$2" ("$5")"}')
    log "INFO" "U盘备份完成，使用空间: $usb_usage"
    
    # 安全卸载U盘（可选）
    # umount "$USB_BACKUP"
    # log "INFO" "U盘已安全卸载"
}

# =============================================================================
# 第三层：坚果云备份
# =============================================================================

backup_jianguoyun() {
    local backup_files="$1"
    log "INFO" "开始坚果云备份..."
    
    # 创建坚果云凭据文件
    local cred_file="/tmp/.jianguoyun_credentials"
    echo "$JIANGUOYUN_URL $JIANGUOYUN_USER $JIANGUOYUN_PASS" > "$cred_file"
    chmod 600 "$cred_file"
    
    # 创建挂载点
    mkdir -p "$JIANGUOYUN_LOCAL"
    
    # 测试坚果云连接
    if ! curl -s --user "$JIANGUOYUN_USER:$JIANGUOYUN_PASS" "$JIANGUOYUN_URL" > /dev/null; then
        log "WARN" "坚果云连接测试失败，跳过坚果云备份"
        rm -f "$cred_file"
        return 1
    fi
    
    log "INFO" "坚果云连接测试成功"
    
    # 尝试挂载坚果云（需要安装davfs2）
    if command -v mount.davfs &> /dev/null; then
        mount -t davfs "$JIANGUOYUN_URL" "$JIANGUOYUN_LOCAL" -o credentials="$cred_file" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "INFO" "坚果云挂载成功"
            
            # 创建远程目录
            mkdir -p "$JIANGUOYUN_LOCAL"/{latest,archive}
            
            # 上传备份文件
            IFS=':' read -ra FILES <<< "$backup_files"
            for file in "${FILES[@]}"; do
                if [ -f "$file" ]; then
                    cp "$file" "$JIANGUOYUN_LOCAL/latest/" 2>/dev/null
                    if [ $? -eq 0 ]; then
                        log "INFO" "坚果云上传成功: $(basename "$file")"
                    else
                        log "WARN" "坚果云上传失败: $(basename "$file")"
                    fi
                fi
            done
            
            # 上传备份清单
            find "$LOCAL_BACKUP" -name "backup_manifest_*.txt" -type f -exec cp {} "$JIANGUOYUN_LOCAL/latest/" \; 2>/dev/null
            
            # 卸载坚果云
            umount "$JIANGUOYUN_LOCAL" 2>/dev/null
            log "INFO" "坚果云备份完成并卸载"
        else
            log "WARN" "坚果云挂载失败，使用curl直接上传..."
            jianguoyun_curl_upload "$backup_files"
        fi
    else
        log "WARN" "未安装davfs2，使用curl直接上传..."
        jianguoyun_curl_upload "$backup_files"
    fi
    
    # 清理凭据文件
    rm -f "$cred_file"
}

# 坚果云curl直接上传
jianguoyun_curl_upload() {
    local backup_files="$1"
    
    log "INFO" "使用curl直接上传到坚果云..."
    
    # 首先创建远程目录
    curl -X MKCOL -u "$JIANGUOYUN_USER:$JIANGUOYUN_PASS" \
         "$JIANGUOYUN_URL/latest" --silent 2>/dev/null
    
    IFS=':' read -ra FILES <<< "$backup_files"
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local upload_url="$JIANGUOYUN_URL/latest/$filename"
            
            # 显示上传进度
            log "INFO" "正在上传: $filename ($(du -h "$file" | cut -f1))"
            
            curl -T "$file" -u "$JIANGUOYUN_USER:$JIANGUOYUN_PASS" \
                 "$upload_url" --silent --show-error
            
            if [ $? -eq 0 ]; then
                log "INFO" "坚果云上传成功: $filename"
            else
                log "WARN" "坚果云上传失败: $filename"
            fi
        fi
    done
    
    # 上传备份清单
    local manifest_file=$(find "$LOCAL_BACKUP" -name "backup_manifest_*.txt" -type f | head -1)
    if [ -n "$manifest_file" ]; then
        local manifest_name=$(basename "$manifest_file")
        curl -T "$manifest_file" -u "$JIANGUOYUN_USER:$JIANGUOYUN_PASS" \
             "$JIANGUOYUN_URL/latest/$manifest_name" --silent
        log "INFO" "备份清单已上传: $manifest_name"
    fi
}

# =============================================================================
# 清理函数
# =============================================================================

cleanup_old_backups() {
    log "INFO" "清理过期备份..."
    
    # 清理本地旧备份
    find "$LOCAL_BACKUP/monthly" -name "inventory_*.db" -mtime +$((KEEP_MONTHLY * 30)) -delete 2>/dev/null
    find "$LOCAL_BACKUP/attachments" -name "attachments_*.tar.gz" -mtime +$((KEEP_MONTHLY * 30)) -delete 2>/dev/null
    find "$LOCAL_BACKUP/daily" -name "*.db" -mtime +$KEEP_DAILY -delete 2>/dev/null
    
    # 清理U盘旧备份（如果挂载）
    if mountpoint -q "$USB_BACKUP" 2>/dev/null; then
        find "$USB_BACKUP/monthly" -name "inventory_*.db" -mtime +$((KEEP_MONTHLY * 30)) -delete 2>/dev/null
    fi
    
    log "INFO" "清理完成"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    log "INFO" "=== 三重备份系统启动 ==="
    log "INFO" "本地硬盘 + U盘 + WebDAV 备份方案"
    
    # 检查依赖和环境
    check_dependencies
    setup_directories
    
    # 第一层：本地硬盘备份
    local backup_files
    backup_files=$(backup_local)
    
    if [ -z "$backup_files" ]; then
        handle_error "本地备份失败，中止后续备份"
    fi
    
    # 第二层：U盘备份
    backup_usb "$backup_files"
    
    # 第三层：坚果云备份
    backup_jianguoyun "$backup_files"
    
    # 清理过期备份
    cleanup_old_backups
    
    # 生成备份报告
    generate_backup_report
    
    log "INFO" "=== 三重备份完成 ==="
}

# 备份报告
generate_backup_report() {
    local report_file="$LOCAL_BACKUP/logs/backup_report_$(date +%Y%m%d).txt"
    
    cat > "$report_file" << EOL
=== 三重备份系统报告 ===
执行时间: $(date '+%Y-%m-%d %H:%M:%S')
主机名: $(hostname)

备份状态:
✓ 本地硬盘: $LOCAL_BACKUP
$([ -d "$USB_BACKUP/monthly" ] && echo "✓ U盘备份: $USB_BACKUP" || echo "✗ U盘备份: 失败或跳过")
$(curl -s --user "$JIANGUOYUN_USER:$JIANGUOYUN_PASS" "$JIANGUOYUN_URL" > /dev/null && echo "✓ 坚果云: $JIANGUOYUN_URL" || echo "✗ 坚果云: 失败或跳过")

存储使用情况:
- 本地备份: $(du -sh "$LOCAL_BACKUP" 2>/dev/null | cut -f1 || echo "未知")
- U盘使用: $(df -h "$USB_BACKUP" 2>/dev/null | awk 'NR==2 {print $5}' || echo "未知")

下次备份: $(date -d "+1 month" '+%Y-%m-%d %H:%M:%S')

备份验证建议:
1. 定期检查备份文件完整性
2. 测试数据库文件可用性: sqlite3 backup.db ".schema"
3. 验证WebDAV连接状态
4. 确保U盘设备正常识别
EOL
    
    log "INFO" "备份报告已生成: $report_file"
    
    # 显示报告内容
    cat "$report_file"
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
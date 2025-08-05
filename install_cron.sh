#!/bin/bash

# 定时备份任务安装脚本
# 用于配置系统的定时备份任务

echo "🔄 设备台账管理系统 - 定时备份任务安装"
echo "================================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_BACKUP_SCRIPT="$SCRIPT_DIR/auto_backup.sh"
CRONTAB_FILE="$SCRIPT_DIR/crontab.conf"

# 检查文件是否存在
if [ ! -f "$AUTO_BACKUP_SCRIPT" ]; then
    echo "❌ 错误: 自动备份脚本不存在: $AUTO_BACKUP_SCRIPT"
    exit 1
fi

if [ ! -f "$CRONTAB_FILE" ]; then
    echo "❌ 错误: 定时任务配置文件不存在: $CRONTAB_FILE"
    exit 1
fi

# 确保脚本有执行权限
chmod +x "$AUTO_BACKUP_SCRIPT"

# 检查是否已经安装了定时任务
echo "📋 检查当前定时任务..."
current_crontab=$(crontab -l 2>/dev/null || echo "")

if echo "$current_crontab" | grep -q "inventory-system-python.*auto_backup.sh"; then
    echo "⚠️  检测到已存在的备份定时任务"
    echo "是否要重新安装？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 0
    fi
    
    # 删除现有的相关定时任务
    echo "🗑️  删除现有定时任务..."
    temp_crontab=$(echo "$current_crontab" | grep -v "inventory-system-python.*auto_backup.sh")
    echo "$temp_crontab" | crontab -
fi

# 添加新的定时任务
echo "📝 添加新的定时任务..."
{
    echo "# 设备台账管理系统 - 定时备份任务"
    echo "# 添加时间: $(date)"
    echo ""
    # 每天凌晨2点执行备份
    echo "0 2 * * * $AUTO_BACKUP_SCRIPT"
    # 每周一凌晨3点执行完整备份
    echo "0 3 * * 1 $AUTO_BACKUP_SCRIPT"
    # 每月1号凌晨4点执行月度备份
    echo "0 4 1 * * $AUTO_BACKUP_SCRIPT"
    echo ""
} | crontab -

# 验证安装
echo "✅ 验证定时任务安装..."
if crontab -l | grep -q "inventory-system-python.*auto_backup.sh"; then
    echo "✅ 定时任务安装成功！"
    echo ""
    echo "📅 已配置的备份计划："
    echo "   - 每天凌晨 2:00 执行日备份"
    echo "   - 每周一凌晨 3:00 执行周备份"
    echo "   - 每月1号凌晨 4:00 执行月备份"
    echo ""
    echo "📁 备份文件将保存在: $SCRIPT_DIR/backups/"
    echo "📄 日志文件位置: $SCRIPT_DIR/backups/backup.log"
    echo ""
    echo "🔧 管理命令："
    echo "   - 查看定时任务: crontab -l"
    echo "   - 删除定时任务: crontab -e (手动删除相关行)"
    echo "   - 手动执行备份: $AUTO_BACKUP_SCRIPT"
    echo "   - 查看备份日志: tail -f $SCRIPT_DIR/backups/backup.log"
    echo ""
    echo "🧪 测试备份功能..."
    # 执行一次测试备份
    $AUTO_BACKUP_SCRIPT
    
    if [ $? -eq 0 ]; then
        echo "✅ 备份功能测试成功！"
        echo "🎉 定时备份系统安装完成！"
    else
        echo "❌ 备份功能测试失败，请检查配置"
        exit 1
    fi
else
    echo "❌ 定时任务安装失败"
    exit 1
fi
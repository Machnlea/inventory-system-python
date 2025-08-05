#!/bin/bash

# 定时备份任务卸载脚本
# 用于移除系统的定时备份任务

echo "🔄 设备台账管理系统 - 定时备份任务卸载"
echo "================================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查是否存在定时任务
echo "📋 检查当前定时任务..."
current_crontab=$(crontab -l 2>/dev/null || echo "")

if echo "$current_crontab" | grep -q "inventory-system-python.*auto_backup.sh"; then
    echo "⚠️  检测到备份定时任务"
    echo ""
    echo "即将删除以下定时任务："
    echo "$current_crontab" | grep "inventory-system-python.*auto_backup.sh" | while read -r line; do
        echo "   - $line"
    done
    echo ""
    echo "确定要删除这些定时任务吗？(y/N)"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ 卸载已取消"
        exit 0
    fi
    
    # 删除定时任务
    echo "🗑️  删除定时任务..."
    temp_crontab=$(echo "$current_crontab" | grep -v "inventory-system-python.*auto_backup.sh")
    echo "$temp_crontab" | crontab -
    
    # 验证删除
    if crontab -l 2>/dev/null | grep -q "inventory-system-python.*auto_backup.sh"; then
        echo "❌ 定时任务删除失败"
        exit 1
    else
        echo "✅ 定时任务删除成功"
    fi
else
    echo "ℹ️  未检测到备份定时任务"
fi

echo ""
echo "📁 备份文件位置: $SCRIPT_DIR/backups/"
echo "📄 日志文件位置: $SCRIPT_DIR/backups/backup.log"
echo ""
echo "⚠️  注意：此脚本只删除定时任务，不会删除备份文件"
echo "如需删除备份文件，请手动删除: rm -rf $SCRIPT_DIR/backups/"
echo ""
echo "🎉 定时备份系统卸载完成！"
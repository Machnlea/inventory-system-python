#!/bin/bash

# 自动导出定时任务安装脚本
# 用于配置系统的定时Excel导出任务

echo "🔄 设备台账管理系统 - 定时Excel导出任务安装"
echo "================================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_EXPORT_SCRIPT="$SCRIPT_DIR/auto_export.py"
CONFIG_FILE="$SCRIPT_DIR/export_config.json"

# 检查文件是否存在
if [ ! -f "$AUTO_EXPORT_SCRIPT" ]; then
    echo "❌ 错误: 自动导出脚本不存在: $AUTO_EXPORT_SCRIPT"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 确保脚本有执行权限
chmod +x "$AUTO_EXPORT_SCRIPT"

# 检查是否已经安装了定时任务
echo "📋 检查当前定时任务..."
current_crontab=$(crontab -l 2>/dev/null || echo "")

if echo "$current_crontab" | grep -q "inventory-system-python.*auto_export.py"; then
    echo "⚠️  检测到已存在的导出定时任务"
    echo "是否要重新安装？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 0
    fi
    
    # 删除现有的相关定时任务
    echo "🗑️  删除现有定时任务..."
    temp_crontab=$(echo "$current_crontab" | grep -v "inventory-system-python.*auto_export.py")
    echo "$temp_crontab" | crontab -
fi

# 读取配置文件中的时间设置
if command -v jq &> /dev/null; then
    DAILY_SCHEDULE=$(jq -r '.export_schedules.daily // "0 8 * * *"' "$CONFIG_FILE")
    WEEKLY_SCHEDULE=$(jq -r '.export_schedules.weekly // "0 9 * * 1"' "$CONFIG_FILE")
    MONTHLY_SCHEDULE=$(jq -r '.export_schedules.monthly // "0 10 1 * *"' "$CONFIG_FILE")
else
    echo "⚠️  jq未安装，使用默认时间设置"
    DAILY_SCHEDULE="0 8 * * *"
    WEEKLY_SCHEDULE="0 9 * * 1"
    MONTHLY_SCHEDULE="0 10 1 * *"
fi

# 添加新的定时任务
echo "📝 添加新的定时任务..."
{
    echo "# 设备台账管理系统 - 定时Excel导出任务"
    echo "# 添加时间: $(date)"
    echo ""
    # 每天日度报告
    echo "$DAILY_SCHEDULE $AUTO_EXPORT_SCRIPT --action daily --config $CONFIG_FILE"
    # 每周周度报告
    echo "$WEEKLY_SCHEDULE $AUTO_EXPORT_SCRIPT --action weekly --config $CONFIG_FILE"
    # 每月月度报告
    echo "$MONTHLY_SCHEDULE $AUTO_EXPORT_SCRIPT --action monthly --config $CONFIG_FILE"
    echo ""
} | crontab -

# 验证安装
echo "✅ 验证定时任务安装..."
if crontab -l | grep -q "inventory-system-python.*auto_export.py"; then
    echo "✅ 定时任务安装成功！"
    echo ""
    echo "📅 已配置的导出计划："
    echo "   - 日度报告: $(echo "$DAILY_SCHEDULE" | awk '{print $2":"$1}')"
    echo "   - 周度报告: $(echo "$WEEKLY_SCHEDULE" | awk '{print $2":"$1" 每周一"}')"
    echo "   - 月度报告: $(echo "$MONTHLY_SCHEDULE" | awk '{print $2":"$1" 每月1号"}')"
    echo ""
    echo "📁 导出文件将保存在: $(python3 -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); print(config.get('export_dir', './auto_exports')); f.close()")"
    echo "📄 日志文件位置: $(python3 -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); export_dir=config.get('export_dir', './auto_exports'); print(f'{export_dir}/auto_export.log'); f.close()")"
    echo ""
    echo "🔧 管理命令："
    echo "   - 查看定时任务: crontab -l"
    echo "   - 删除定时任务: crontab -e (手动删除相关行)"
    echo "   - 手动导出全部: $AUTO_EXPORT_SCRIPT --action all --config $CONFIG_FILE"
    echo "   - 查看导出状态: $AUTO_EXPORT_SCRIPT --action status --config $CONFIG_FILE"
    echo "   - 查看导出日志: tail -f $(python3 -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); export_dir=config.get('export_dir', './auto_exports'); print(f'{export_dir}/auto_export.log'); f.close()")"
    echo ""
    echo "🧪 测试导出功能..."
    
    # 创建导出目录
    export_dir=$(python3 -c "import json; f=open('$CONFIG_FILE'); config=json.load(f); print(config.get('export_dir', './auto_exports')); f.close()")
    mkdir -p "$export_dir"
    
    # 执行一次测试导出
    $AUTO_EXPORT_SCRIPT --action all --config $CONFIG_FILE
    
    if [ $? -eq 0 ]; then
        echo "✅ 导出功能测试成功！"
        echo "🎉 定时Excel导出系统安装完成！"
    else
        echo "❌ 导出功能测试失败，请检查配置"
        exit 1
    fi
else
    echo "❌ 定时任务安装失败"
    exit 1
fi
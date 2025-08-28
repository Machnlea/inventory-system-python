#!/bin/bash

# 三重备份系统配置脚本
# 自动配置本地硬盘 + U盘 + WebDAV 备份环境

echo "=== 库存管理系统三重备份配置 ==="
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 检查系统环境
check_system() {
    echo "1. 检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   ✓ Linux系统检测成功"
    else
        echo "   ✗ 仅支持Linux系统"
        exit 1
    fi
    
    # 检查是否为root权限（部分操作需要）
    if [ "$EUID" -eq 0 ]; then
        echo "   ✓ 具有管理员权限"
        SUDO=""
    else
        echo "   ✓ 使用sudo权限"
        SUDO="sudo"
    fi
}

# 安装依赖包
install_dependencies() {
    echo ""
    echo "2. 安装必要依赖..."
    
    # 检测包管理器
    if command -v apt-get &> /dev/null; then
        PACKAGE_MANAGER="apt-get"
        UPDATE_CMD="apt-get update"
        INSTALL_CMD="apt-get install -y"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
        UPDATE_CMD="yum update -y"
        INSTALL_CMD="yum install -y"
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
        UPDATE_CMD="dnf update -y"
        INSTALL_CMD="dnf install -y"
    else
        echo "   ✗ 不支持的包管理器"
        exit 1
    fi
    
    echo "   - 检测到包管理器: $PACKAGE_MANAGER"
    
    # 更新包索引
    echo "   - 更新包索引..."
    $SUDO $UPDATE_CMD > /dev/null 2>&1
    
    # 安装必要工具
    local packages=(
        "curl"          # WebDAV访问
        "davfs2"        # WebDAV文件系统
        "sqlite3"       # 数据库工具
        "cron"          # 定时任务
        "util-linux"    # 挂载工具
    )
    
    for package in "${packages[@]}"; do
        if ! command -v "$package" &> /dev/null && ! dpkg -l | grep -q "^ii  $package "; then
            echo "   - 安装 $package..."
            $SUDO $INSTALL_CMD "$package" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "     ✓ $package 安装成功"
            else
                echo "     ✗ $package 安装失败"
            fi
        else
            echo "     ✓ $package 已安装"
        fi
    done
}

# 配置目录结构
setup_directories() {
    echo ""
    echo "3. 配置备份目录..."
    
    # 创建主备份目录
    local backup_dirs=(
        "/data/backups/inventory"
        "/data/backups/inventory/monthly"
        "/data/backups/inventory/daily"
        "/data/backups/inventory/attachments"
        "/data/backups/inventory/logs"
        "/data/backups/inventory/temp"
    )
    
    for dir in "${backup_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            $SUDO mkdir -p "$dir"
            echo "   ✓ 创建目录: $dir"
        else
            echo "   - 目录已存在: $dir"
        fi
    done
    
    # 设置权限
    $SUDO chown -R $(whoami):$(whoami) /data/backups/
    $SUDO chmod -R 755 /data/backups/
    echo "   ✓ 权限设置完成"
}

# 配置U盘自动挂载
configure_usb() {
    echo ""
    echo "4. 配置U盘备份..."
    
    # 创建挂载点
    if [ ! -d "/media/usb_backup" ]; then
        $SUDO mkdir -p "/media/usb_backup"
        echo "   ✓ 创建U盘挂载点: /media/usb_backup"
    fi
    
    # 检查当前连接的USB设备
    echo "   - 当前USB设备:"
    lsblk -f | grep -E "(sd[b-z]|usb)" || echo "     未检测到USB设备"
    
    echo ""
    echo "   📝 U盘配置说明:"
    echo "      1. 插入专用备份U盘"
    echo "      2. 格式化为ext4文件系统（推荐）: sudo mkfs.ext4 /dev/sdX1"
    echo "      3. 修改脚本中的USB_DEVICE变量为实际设备路径"
    echo "      4. 测试挂载: sudo mount /dev/sdX1 /media/usb_backup"
}

# 配置坚果云WebDAV
configure_jianguoyun() {
    echo ""
    echo "5. 配置坚果云WebDAV备份..."
    
    # 创建坚果云配置目录
    if [ ! -d "/etc/davfs2" ]; then
        $SUDO mkdir -p /etc/davfs2
    fi
    
    # 创建坚果云挂载点
    if [ ! -d "/tmp/jianguoyun_mount" ]; then
        mkdir -p "/tmp/jianguoyun_mount"
        echo "   ✓ 创建坚果云挂载点"
    fi
    
    echo ""
    echo "   📱 坚果云配置步骤:"
    echo "      1. 登录坚果云网页版 (https://www.jianguoyun.com)"
    echo "      2. 账户信息 → 安全选项 → 第三方应用管理"
    echo "      3. 添加应用密码，应用名称填写: 库存系统备份"
    echo "      4. 记录生成的应用密码（16位字符）"
    echo ""
    echo "   ⚙️  配置参数模板:"
    echo "      JIANGUOYUN_URL=\"https://dav.jianguoyun.com/dav/inventory\""
    echo "      JIANGUOYUN_USER=\"your_email@company.com\"    # 坚果云账号"
    echo "      JIANGUOYUN_PASS=\"abcd1234efgh5678\"          # 应用密码"
    echo ""
    echo "   🔗 测试连接命令:"
    echo "      curl -u \"邮箱:应用密码\" \"https://dav.jianguoyun.com/dav/\""
    echo ""
    echo "   💾 存储容量:"
    echo "      - 免费版: 1GB存储空间"
    echo "      - 付费版: 42GB起，适合长期备份"
}

# 配置定时任务
configure_cron() {
    echo ""
    echo "6. 配置定时任务..."
    
    # 创建cron配置文件
    cat > "$SCRIPT_DIR/triple_backup_cron.conf" << EOF
# 库存管理系统三重备份定时任务
# 
# 备份策略:
# - 每月1号和15号执行完整备份
# - 每天凌晨执行数据库快照
#
# 格式: 分 时 日 月 周 命令

# 月度完整备份 (每月1号和15号凌晨3点)
0 3 1,15 * * $SCRIPT_DIR/triple_backup.sh >> /data/backups/inventory/logs/cron.log 2>&1

# 日常数据库备份 (每天凌晨2点)  
0 2 * * * cp $PROJECT_DIR/data/inventory.db /data/backups/inventory/daily/inventory_\$(date +\%Y\%m\%d).db

# 每周清理日志 (每周日凌晨1点)
0 1 * * 0 find /data/backups/inventory/logs -name "*.log" -mtime +30 -delete
EOF
    
    echo "   ✓ 定时任务配置文件已创建: triple_backup_cron.conf"
    echo ""
    echo "   📝 安装定时任务:"
    echo "      crontab $SCRIPT_DIR/triple_backup_cron.conf"
    echo ""
    echo "   📝 查看定时任务:"
    echo "      crontab -l"
}

# 创建测试脚本
create_test_script() {
    echo ""
    echo "7. 创建测试脚本..."
    
    cat > "$SCRIPT_DIR/test_backup.sh" << 'EOF'
#!/bin/bash

# 备份系统测试脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 备份系统测试 ==="

# 1. 测试本地备份目录
echo "1. 测试本地备份..."
if [ -w "/data/backups/inventory" ]; then
    echo "   ✓ 本地备份目录可写"
    echo "测试文件" > "/data/backups/inventory/test_$(date +%s).txt"
    echo "   ✓ 测试文件创建成功"
else
    echo "   ✗ 本地备份目录不可写"
fi

# 2. 测试U盘检测
echo ""
echo "2. 测试U盘检测..."
if [ -b "/dev/sdb1" ]; then
    echo "   ✓ 检测到USB设备: /dev/sdb1"
else
    echo "   ✗ 未检测到USB设备 /dev/sdb1"
    echo "     可用设备:"
    lsblk | grep -E "sd[b-z]" || echo "     无"
fi

# 3. 测试WebDAV连接（需要先配置）
echo ""
echo "3. 测试WebDAV连接..."
echo "   请先在 triple_backup.sh 中配置WebDAV参数"

# 4. 测试数据库访问
echo ""
echo "4. 测试数据库访问..."
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$PROJECT_DIR/data/inventory.db" ]; then
    echo "   ✓ 数据库文件存在"
    if command -v sqlite3 &> /dev/null; then
        local table_count=$(sqlite3 "$PROJECT_DIR/data/inventory.db" "SELECT count(name) FROM sqlite_master WHERE type='table';" 2>/dev/null)
        echo "   ✓ 数据库表数量: $table_count"
    else
        echo "   ✗ sqlite3 命令未安装"
    fi
else
    echo "   ✗ 数据库文件不存在"
fi

# 5. 测试备份脚本语法
echo ""
echo "5. 测试备份脚本..."
if bash -n "$SCRIPT_DIR/triple_backup.sh"; then
    echo "   ✓ 备份脚本语法正确"
else
    echo "   ✗ 备份脚本语法错误"
fi

echo ""
echo "=== 测试完成 ==="
echo ""
echo "下一步操作:"
echo "1. 配置 triple_backup.sh 中的WebDAV参数"
echo "2. 插入并配置U盘设备"
echo "3. 运行测试备份: $SCRIPT_DIR/triple_backup.sh"
echo "4. 安装定时任务: crontab $SCRIPT_DIR/triple_backup_cron.conf"
EOF
    
    chmod +x "$SCRIPT_DIR/test_backup.sh"
    echo "   ✓ 测试脚本已创建: test_backup.sh"
}

# 显示配置摘要
show_summary() {
    echo ""
    echo "=== 配置完成摘要 ==="
    echo ""
    echo "📁 备份路径配置:"
    echo "   本地硬盘: /data/backups/inventory"
    echo "   U盘挂载: /media/usb_backup"
    echo "   WebDAV: /tmp/webdav_mount"
    echo ""
    echo "📋 创建的文件:"
    echo "   ✓ $SCRIPT_DIR/triple_backup.sh           # 主备份脚本"
    echo "   ✓ $SCRIPT_DIR/triple_backup_cron.conf    # 定时任务配置"
    echo "   ✓ $SCRIPT_DIR/test_backup.sh             # 测试脚本"
    echo ""
    echo "⚙️  下一步操作:"
    echo "   1. 编辑 triple_backup.sh 配置WebDAV参数"
    echo "   2. 准备专用U盘并格式化"
    echo "   3. 运行测试: ./test_backup.sh"
    echo "   4. 手动测试备份: ./triple_backup.sh"
    echo "   5. 安装定时任务: crontab triple_backup_cron.conf"
    echo ""
    echo "📞 技术支持:"
    echo "   查看日志: tail -f /data/backups/inventory/logs/backup.log"
    echo "   测试WebDAV: curl -u user:pass https://your-webdav-url"
    echo ""
}

# 主函数
main() {
    check_system
    install_dependencies
    setup_directories
    configure_usb
    configure_webdav
    configure_cron
    create_test_script
    show_summary
    
    echo "🎉 三重备份系统配置完成！"
    echo ""
}

# 执行主函数
main "$@"
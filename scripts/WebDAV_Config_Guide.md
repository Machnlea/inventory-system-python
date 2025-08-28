# WebDAV配置指南

## 支持的WebDAV服务提供商

### 1. 坚果云（推荐 - 国内稳定）
```bash
# 配置参数
WEBDAV_URL="https://dav.jianguoyun.com/dav/inventory"
WEBDAV_USER="your_email@company.com"
WEBDAV_PASS="应用密码"  # 注意：不是登录密码！

# 获取应用密码步骤:
1. 登录坚果云网页版
2. 账户信息 → 安全选项 → 第三方应用管理
3. 生成应用密码
4. 记录应用密码用于WebDAV配置
```

### 2. 阿里云盘WebDAV
```bash
# 需要使用第三方工具aliyundrive-webdav
WEBDAV_URL="http://localhost:8080/dav"
WEBDAV_USER="your_phone_number"
WEBDAV_PASS="refresh_token"

# 安装步骤:
1. 下载 aliyundrive-webdav
2. 获取refresh_token
3. 启动服务: ./aliyundrive-webdav --refresh-token=xxx
```

### 3. Nextcloud/ownCloud
```bash
# 自建或企业Nextcloud
WEBDAV_URL="https://your-nextcloud.com/remote.php/dav/files/username/inventory"
WEBDAV_USER="your_username"
WEBDAV_PASS="your_password"  # 或应用密码
```

### 4. 群晖NAS WebDAV
```bash
# Synology DiskStation
WEBDAV_URL="https://your-nas:5006/inventory"  # HTTPS端口5006，HTTP端口5005
WEBDAV_USER="nas_username"  
WEBDAV_PASS="nas_password"

# 配置步骤:
1. 控制面板 → 文件服务 → WebDAV → 启用WebDAV
2. 创建共享文件夹 "inventory"
3. 设置用户权限
```

## WebDAV连接测试

### 使用curl测试
```bash
# 测试基本连接
curl -u "username:password" "https://dav.jianguoyun.com/dav/" 

# 测试目录创建
curl -X MKCOL -u "username:password" "https://dav.jianguoyun.com/dav/inventory"

# 测试文件上传
echo "test" > test.txt
curl -T test.txt -u "username:password" "https://dav.jianguoyun.com/dav/inventory/test.txt"

# 测试文件下载
curl -u "username:password" "https://dav.jianguoyun.com/dav/inventory/test.txt"
```

### 使用cadaver测试（可选）
```bash
# 安装cadaver
sudo apt-get install cadaver

# 连接测试
cadaver https://dav.jianguoyun.com/dav/
> open inventory
> ls
> put local_file.txt
> get remote_file.txt
> quit
```

## 配置文件模板

### 坚果云配置示例
```bash
# 在 triple_backup.sh 中修改这些变量:

# WebDAV配置 - 坚果云
WEBDAV_URL="https://dav.jianguoyun.com/dav/inventory"
WEBDAV_USER="admin@yourcompany.com"           # 你的坚果云邮箱
WEBDAV_PASS="abcd1234efgh5678"                # 应用密码（非登录密码）
WEBDAV_LOCAL="/tmp/webdav_mount"
```

### 自建Nextcloud配置示例  
```bash
# WebDAV配置 - Nextcloud
WEBDAV_URL="https://cloud.yourcompany.com/remote.php/dav/files/admin/inventory"
WEBDAV_USER="admin"
WEBDAV_PASS="your_app_password"
WEBDAV_LOCAL="/tmp/webdav_mount"
```

## 安全建议

### 1. 使用应用密码
- ✅ 创建专用的应用密码
- ✅ 定期轮换密码
- ❌ 不要使用主账号密码

### 2. 网络安全
- ✅ 使用HTTPS连接
- ✅ 配置防火墙规则
- ✅ 限制访问IP（如果可能）

### 3. 权限控制
- ✅ 创建专用备份目录
- ✅ 设置最小必要权限
- ✅ 定期检查访问日志

## 故障排除

### 常见错误及解决方案

#### 1. 连接超时
```bash
# 错误: curl: (28) Operation timed out
# 解决: 检查网络连接和防火墙设置

# 测试网络连通性
ping dav.jianguoyun.com
telnet dav.jianguoyun.com 443
```

#### 2. 认证失败
```bash
# 错误: 401 Unauthorized
# 解决: 检查用户名密码，确保使用应用密码

# 坚果云用户常见错误：
# ❌ 使用登录密码 
# ✅ 使用应用密码
```

#### 3. 挂载失败
```bash
# 错误: mount.davfs: mounting failed; the server does not support WebDAV
# 解决: 
1. 检查URL是否正确
2. 安装davfs2: sudo apt-get install davfs2
3. 检查/etc/davfs2/davfs2.conf配置
```

#### 4. 文件上传失败
```bash
# 错误: 413 Request Entity Too Large
# 解决: 检查服务器文件大小限制

# 对于大文件，可以分块上传或压缩后上传
```

## 监控和维护

### 1. 备份状态检查脚本
```bash
#!/bin/bash
# webdav_health_check.sh

WEBDAV_URL="your_webdav_url"
WEBDAV_USER="your_user"
WEBDAV_PASS="your_pass"

# 检查WebDAV连接
if curl -s -u "$WEBDAV_USER:$WEBDAV_PASS" "$WEBDAV_URL" > /dev/null; then
    echo "✓ WebDAV连接正常"
else
    echo "✗ WebDAV连接失败"
    # 发送告警邮件或通知
fi
```

### 2. 定期验证备份
```bash
# 每月验证一次备份完整性
0 0 1 * * /path/to/verify_backup.sh
```

### 3. 存储空间监控
```bash
# 检查WebDAV存储空间使用情况
# 根据服务商提供的API或WebDAV PROPFIND方法检查
```

## 企业级建议

### 1. 多云备份策略
- 主要WebDAV: 坚果云（国内访问快）
- 备用WebDAV: 自建Nextcloud（完全控制）
- 归档存储: 阿里云OSS冷存储（成本低）

### 2. 自动化监控
- 备份成功率监控
- 存储空间告警  
- 网络连接状态检查
- 定期恢复测试

### 3. 灾难恢复预案
- 完整的恢复文档
- 备份数据验证流程
- 应急联系人制度
- 定期恢复演练

---

配置完成后，建议先进行小规模测试，确保所有组件正常工作后再投入生产使用。
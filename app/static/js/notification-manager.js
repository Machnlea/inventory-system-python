// 统一通知组件
// 基于系统设置页面的优雅设计风格

class NotificationManager {
    constructor() {
        this.container = null;
        // 延迟初始化，确保DOM已加载
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initContainer());
        } else {
            this.initContainer();
        }
    }

    // 初始化容器
    initContainer() {
        if (document.body) {
            this.ensureContainer();
        } else {
            // 如果body还不存在，等待一下再试
            setTimeout(() => this.initContainer(), 100);
        }
    }

    // 确保通知容器存在
    ensureContainer() {
        if (!this.container) {
            this.container = document.getElementById('notification-container');
            if (!this.container && document.body) {
                this.container = document.createElement('div');
                this.container.id = 'notification-container';
                this.container.className = 'fixed top-4 right-4 z-[9999] space-y-2 w-72';
                this.container.style.pointerEvents = 'none'; // 让容器不阻挡点击
                document.body.appendChild(this.container);
            }
        }
        return this.container;
    }

    // 关闭通知的方法
    closeNotification(notification) {
        if (!notification || !notification.parentNode) return;
        
        // 清除自动关闭定时器
        if (notification.autoCloseTimer) {
            clearTimeout(notification.autoCloseTimer);
            notification.autoCloseTimer = null;
        }
        
        // 添加关闭动画
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        notification.style.transition = 'all 0.3s ease-out';
        
        // 等待动画完成后移除元素
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
                this.repositionNotifications();
            }
        }, 300);
    }

    // 显示通知
    show(message, type = 'info') {
        const container = this.ensureContainer();
        const notification = document.createElement('div');
        
        // 设置颜色方案 - 更美观的样式
        const colors = {
            success: {
                bg: 'bg-gradient-to-r from-green-50 to-emerald-50',
                border: 'border-l-4 border-green-500',
                icon: 'fas fa-check-circle text-green-600',
                text: 'text-green-900',
                shadow: 'shadow-green-500/20'
            },
            error: {
                bg: 'bg-gradient-to-r from-red-50 to-rose-50',
                border: 'border-l-4 border-red-500',
                icon: 'fas fa-exclamation-circle text-red-600',
                text: 'text-red-900',
                shadow: 'shadow-red-500/20'
            },
            warning: {
                bg: 'bg-gradient-to-r from-yellow-50 to-amber-50',
                border: 'border-l-4 border-yellow-500',
                icon: 'fas fa-exclamation-triangle text-yellow-600',
                text: 'text-yellow-900',
                shadow: 'shadow-yellow-500/20'
            },
            info: {
                bg: 'bg-gradient-to-r from-blue-50 to-sky-50',
                border: 'border-l-4 border-blue-500',
                icon: 'fas fa-info-circle text-blue-600',
                text: 'text-blue-900',
                shadow: 'shadow-blue-500/20'
            }
        };
        
        const colorScheme = colors[type] || colors.info;
        
        // 优化样式，让通知更美观 - 减少上下边距，保持左右边距
        notification.className = `notification-item ${colorScheme.bg} ${colorScheme.border} ${colorScheme.shadow} rounded-xl shadow-xl transform transition-all duration-300 translate-x-full w-full px-4 py-2`;
        notification.style.pointerEvents = 'auto'; // 让通知可以接收点击事件
        notification.style.minHeight = '48px'; // 减少最小高度
        
        // 创建唯一ID用于关闭
        const notificationId = 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        notification.id = notificationId;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0 mr-3">
                    <i class="${colorScheme.icon} text-lg"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="${colorScheme.text} font-medium text-lg leading-snug break-words">${message}</p>
                </div>
                <div class="flex-shrink-0 ml-3">
                    <button onclick="window.notificationManager && window.notificationManager.closeNotification(document.getElementById('${notificationId}'))" class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-full transition-colors">
                        <i class="fas fa-times text-xs"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(notification);
        
        // 触发动画
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // 5秒后自动消失（增加时间让用户有足够时间阅读）
        const autoCloseTimer = setTimeout(() => {
            this.closeNotification(notification);
        }, 5000);
        
        // 将定时器保存到元素上，以便手动关闭时可以清除
        notification.autoCloseTimer = autoCloseTimer;
    }

    // 关闭所有通知
    closeAllNotifications() {
        const container = this.ensureContainer();
        const notifications = container.querySelectorAll('.notification-item');
        notifications.forEach(notification => {
            this.closeNotification(notification);
        });
    }

    // 重新计算通知位置（现在使用简单的垂直堆叠）
    repositionNotifications() {
        // 由于我们使用了 space-y-2 类和自然的文档流，不需要手动定位
        // 这个函数保留用于未来可能的扩展
    }

    // 显示成功通知
    success(message) {
        this.show(message, 'success');
    }

    // 显示错误通知
    error(message) {
        this.show(message, 'error');
    }

    // 显示警告通知
    warning(message) {
        this.show(message, 'warning');
    }

    // 显示信息通知
    info(message) {
        this.show(message, 'info');
    }
}

// 延迟创建全局通知管理器实例，确保DOM已准备好
let notificationManager = null;

// 初始化函数
function initNotificationManager() {
    if (!notificationManager) {
        notificationManager = new NotificationManager();
        window.notificationManager = notificationManager;
    }
    return notificationManager;
}

// 全局函数，保持向后兼容
function showNotification(message, type = 'info') {
    // 确保通知管理器已初始化
    const manager = notificationManager || initNotificationManager();
    manager.show(message, type);
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
} else if (typeof window !== 'undefined') {
    window.NotificationManager = NotificationManager;
    window.showNotification = showNotification;
    
    // 当DOM准备好时初始化通知管理器
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotificationManager);
    } else {
        initNotificationManager();
    }
}
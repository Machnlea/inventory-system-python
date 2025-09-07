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
                this.container.className = 'fixed top-4 right-4 z-[9999] space-y-2 max-w-md';
                document.body.appendChild(this.container);
            }
        }
        return this.container;
    }

    // 显示通知
    show(message, type = 'info') {
        const container = this.ensureContainer();
        const notification = document.createElement('div');
        
        // 设置颜色方案 - 基于设置页面的设计
        const colors = {
            success: {
                bg: 'bg-white',
                border: 'border-l-green-500',
                icon: 'fas fa-check-circle text-green-600',
                text: 'text-green-900'
            },
            error: {
                bg: 'bg-white',
                border: 'border-l-red-500',
                icon: 'fas fa-exclamation-circle text-red-600',
                text: 'text-red-900'
            },
            warning: {
                bg: 'bg-white',
                border: 'border-l-yellow-500',
                icon: 'fas fa-exclamation-triangle text-yellow-600',
                text: 'text-yellow-900'
            },
            info: {
                bg: 'bg-white',
                border: 'border-l-blue-500',
                icon: 'fas fa-info-circle text-blue-600',
                text: 'text-blue-900'
            }
        };
        
        const colorScheme = colors[type] || colors.info;
        
        notification.className = `${colorScheme.bg} ${colorScheme.border} border-l-4 px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
        notification.style.marginBottom = '12px';
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="${colorScheme.icon} text-xl mr-3"></i>
                <span class="${colorScheme.text} font-medium">${message}</span>
                <div class="ml-auto pl-3">
                    <button onclick="this.closest('.transform').remove()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(notification);
        
        // 重新排列所有通知的位置
        this.repositionNotifications();
        
        // 触发动画
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // 3秒后自动消失
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                    // 重新计算剩余通知的位置
                    this.repositionNotifications();
                }
            }, 300);
        }, 3000);
    }

    // 重新计算通知位置
    repositionNotifications() {
        const container = this.ensureContainer();
        const notifications = Array.from(container.querySelectorAll('.transform.translate-x-full')).reverse();
        
        let topPosition = 16; // 初始位置距离顶部16px
        
        notifications.forEach((notification, index) => {
            notification.style.top = `${topPosition}px`;
            topPosition += 92; // 每个通知高度约80px + 间距12px
        });
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
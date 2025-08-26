// 会话管理器 - 处理用户会话和权限验证
class SessionManager {
    constructor() {
        this.currentUser = null;
        this.token = null;
        this.init();
    }

    init() {
        // 优先从sessionStorage获取用户信息和token，然后回退到localStorage（兼容多标签页登录）
        const userInfo = sessionStorage.getItem('user_info') || localStorage.getItem('user_info');
        const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        
        if (userInfo && token) {
            try {
                this.currentUser = JSON.parse(userInfo);
                this.token = token;
                this.updateUI();
            } catch (error) {
                console.error('解析用户信息失败:', error);
                this.clearSession();
            }
        } else {
            // 如果没有登录信息，重定向到登录页
            this.redirectToLogin();
        }
    }

    // 更新UI显示当前用户信息
    updateUI() {
        if (this.currentUser) {
            const currentUserElement = document.getElementById('current-user');
            if (currentUserElement) {
                currentUserElement.textContent = this.currentUser.username || '用户';
            }
        }
    }

    // 检查用户权限
    hasPermission(permission) {
        if (!this.currentUser) return false;
        
        // 管理员拥有所有权限
        if (this.currentUser.is_admin) return true;
        
        // 检查具体权限
        return this.currentUser.permissions && this.currentUser.permissions.includes(permission);
    }

    // 检查是否为管理员
    isAdmin() {
        return this.currentUser && this.currentUser.is_admin;
    }

    // 获取当前用户ID
    getCurrentUserId() {
        return this.currentUser ? this.currentUser.id : null;
    }

    // 获取当前用户名
    getCurrentUsername() {
        return this.currentUser ? this.currentUser.username : null;
    }

    // 验证token是否有效
    async validateToken() {
        if (!this.token) return false;
        
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                localStorage.setItem('user_info', JSON.stringify(userData));
                this.updateUI();
                return true;
            } else {
                this.clearSession();
                return false;
            }
        } catch (error) {
            console.error('验证token失败:', error);
            this.clearSession();
            return false;
        }
    }

    // 清除会话
    clearSession() {
        // 清除sessionStorage（优先）
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user_info');
        
        // 兼容旧系统：也清除localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        
        this.currentUser = null;
        this.token = null;
    }

    // 重定向到登录页
    redirectToLogin() {
        window.location.href = '/login';
    }

    // 登出
    logout() {
        this.clearSession();
        this.redirectToLogin();
    }

    // 显示通知消息
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        
        const bgColor = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        }[type] || 'bg-blue-500';
        
        const icon = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        }[type] || 'fa-info-circle';
        
        notification.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 transform transition-all duration-300 translate-x-full`;
        notification.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(notification);
        
        // 动画显示
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // 自动隐藏
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // API请求封装
    async apiRequest(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${window.location.origin}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const config = {
            ...options,
            headers
        };
        
        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                this.clearSession();
                this.redirectToLogin();
                throw new Error('登录已过期，请重新登录');
            }
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `请求失败: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
}

// 创建全局实例
const sessionManager = new SessionManager();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置登出按钮事件
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            if (confirm('确定要退出登录吗？')) {
                sessionManager.logout();
            }
        });
    }
    
    // 设置系统管理下拉菜单
    const systemMenuBtn = document.getElementById('system-menu-btn');
    const systemSubmenu = document.getElementById('system-submenu');
    const systemMenuArrow = document.getElementById('system-menu-arrow');
    
    if (systemMenuBtn && systemSubmenu && systemMenuArrow) {
        systemMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // 切换子菜单显示
            systemSubmenu.classList.toggle('hidden');
            
            // 旋转箭头
            if (systemSubmenu.classList.contains('hidden')) {
                systemMenuArrow.style.transform = 'rotate(0deg)';
            } else {
                systemMenuArrow.style.transform = 'rotate(180deg)';
            }
        });
    }
});

// 导出全局实例
window.sessionManager = sessionManager;
/**
 * Tailwind CSS 组件库集成文件
 * 替代 Bootstrap 组件库
 */

// 全局配置
const TailwindConfig = {
    // 默认配置
    defaults: {
        modal: {
            backdrop: true,
            keyboard: true,
            animation: true
        },
        alert: {
            autoClose: true,
            duration: 5000,
            showCloseButton: true,
            container: 'notification-container'
        },
        button: {
            type: 'primary',
            size: null
        }
    },

    // 初始化函数
    init() {
        this.initModals();
        this.initButtons();
        this.initAlerts();
        this.createGlobalStyles();
    },

    // 初始化模态框
    initModals() {
        // 查找所有模态框并初始化
        const modals = document.querySelectorAll('.modal, [data-tw-modal]');
        modals.forEach(modal => {
            const modalId = modal.id || `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            if (!modal.id) {
                modal.id = modalId;
            }
            
            // 确保模态框有正确的Tailwind类
            if (!modal.classList.contains('fixed')) {
                modal.classList.add('fixed', 'inset-0', 'z-50', 'hidden');
            }
            
            // 初始化模态框实例
            if (!window.tailwindModals) {
                window.tailwindModals = {};
            }
            window.tailwindModals[modalId] = new TailwindModal(modalId);
        });

        // 初始化模态框触发器
        const triggers = document.querySelectorAll('[data-tw-toggle="modal"]');
        triggers.forEach(trigger => {
            const targetId = trigger.getAttribute('data-tw-target');
            if (targetId) {
                trigger.addEventListener('click', (e) => {
                    e.preventDefault();
                    const modal = window.tailwindModals[targetId.replace('#', '')];
                    if (modal) {
                        modal.show();
                    }
                });
            }
        });
    },

    // 初始化按钮
    initButtons() {
        // 转换所有带有Bootstrap类的按钮
        const bootstrapButtons = document.querySelectorAll('[class*="btn-"]');
        bootstrapButtons.forEach(button => {
            this.convertBootstrapButton(button);
        });

        // 转换按钮组
        const buttonGroups = document.querySelectorAll('.btn-group');
        buttonGroups.forEach(group => {
            group.classList.remove('btn-group');
            group.classList.add('inline-flex', 'rounded-md', 'shadow-sm', 'role', 'group');
        });
    },

    // 初始化提示框
    initAlerts() {
        // 转换Bootstrap提示框
        const bootstrapAlerts = document.querySelectorAll('[class*="alert-"]');
        bootstrapAlerts.forEach(alert => {
            this.convertBootstrapAlert(alert);
        });
    },

    // 创建全局样式
    createGlobalStyles() {
        if (document.getElementById('tailwind-components-styles')) {
            return; // 样式已存在
        }

        const style = document.createElement('style');
        style.id = 'tailwind-components-styles';
        style.textContent = `
            /* 模态框动画 */
            .modal-transition {
                transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
            }
            
            /* 提示框动画 */
            .alert-transition {
                transition: all 0.3s ease-in-out;
            }
            
            /* 按钮悬停效果 */
            .btn-hover-lift {
                transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            }
            
            .btn-hover-lift:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            /* 焦点样式 */
            .focus-ring {
                transition: box-shadow 0.2s ease-in-out;
            }
            
            /* 模态框背景 */
            .modal-backdrop {
                backdrop-filter: blur(4px);
                -webkit-backdrop-filter: blur(4px);
            }
            
            /* 禁用状态 */
            .disabled {
                pointer-events: none;
                opacity: 0.5;
            }
            
            /* 加载动画 */
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .animate-spin {
                animation: spin 1s linear infinite;
            }
            
            /* 淡入动画 */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .animate-fade-in {
                animation: fadeIn 0.3s ease-out;
            }
        `;
        
        document.head.appendChild(style);
    },

    // 转换Bootstrap按钮到Tailwind按钮
    convertBootstrapButton(button) {
        const classList = button.classList;
        let tailwindClasses = [];
        let type = 'primary';
        let size = null;

        // 解析Bootstrap类
        Array.from(classList).forEach(cls => {
            if (cls.startsWith('btn-')) {
                if (cls === 'btn-primary') type = 'primary';
                else if (cls === 'btn-secondary') type = 'secondary';
                else if (cls === 'btn-success') type = 'success';
                else if (cls === 'btn-danger') type = 'danger';
                else if (cls === 'btn-warning') type = 'warning';
                else if (cls === 'btn-info') type = 'info';
                else if (cls === 'btn-light') type = 'light';
                else if (cls === 'btn-dark') type = 'dark';
                else if (cls === 'btn-link') type = 'link';
                else if (cls === 'btn-sm') size = 'sm';
                else if (cls === 'btn-lg') size = 'lg';
                else if (cls.startsWith('btn-outline-')) {
                    type = 'outline-' + cls.replace('btn-outline-', '');
                }
            }
        });

        // 生成Tailwind类
        button.className = this.createButtonClass(type, size, button.className.replace(/btn-\S+/g, '').trim());
    },

    // 创建按钮类名
    createButtonClass(type = 'primary', size = null, additionalClasses = '') {
        const types = {
            primary: 'bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
            secondary: 'bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
            success: 'bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
            danger: 'bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
            warning: 'bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2',
            info: 'bg-cyan-600 hover:bg-cyan-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2',
            light: 'bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
            dark: 'bg-gray-800 hover:bg-gray-900 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
            link: 'text-blue-600 hover:text-blue-800 font-medium underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
            
            // 轮廓按钮
            'outline-primary': 'border border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
            'outline-secondary': 'border border-gray-600 text-gray-600 hover:bg-gray-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
            'outline-success': 'border border-green-600 text-green-600 hover:bg-green-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
            'outline-danger': 'border border-red-600 text-red-600 hover:bg-red-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
            'outline-warning': 'border border-yellow-500 text-yellow-500 hover:bg-yellow-500 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2',
            'outline-info': 'border border-cyan-600 text-cyan-600 hover:bg-cyan-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2'
        };
        
        let classes = types[type] || types.primary;
        
        if (size) {
            if (size === 'sm') {
                classes = classes.replace('py-2 px-4', 'py-1 px-3').replace('text-medium', 'text-sm');
            } else if (size === 'lg') {
                classes = classes.replace('py-2 px-4', 'py-3 px-6').replace('text-medium', 'text-lg');
            }
        }
        
        return `${classes} ${additionalClasses}`.trim();
    },

    // 转换Bootstrap提示框到Tailwind提示框
    convertBootstrapAlert(alert) {
        const classList = alert.classList;
        let type = 'info';
        let message = alert.textContent.trim();
        let closeButton = alert.querySelector('[data-bs-dismiss="alert"]');

        // 解析Bootstrap类
        Array.from(classList).forEach(cls => {
            if (cls.startsWith('alert-')) {
                if (cls === 'alert-success') type = 'success';
                else if (cls === 'alert-danger') type = 'danger';
                else if (cls === 'alert-warning') type = 'warning';
                else if (cls === 'alert-info') type = 'info';
            }
        });

        // 创建新的Tailwind提示框
        const newAlert = new TailwindAlert(message, type, {
            autoClose: false,
            showCloseButton: !!closeButton
        }).show();

        // 替换原提示框
        alert.parentNode.replaceChild(newAlert, alert);
    },

    // Bootstrap兼容性API
    bootstrap: {
        Modal: class {
            constructor(element, options = {}) {
                this.element = typeof element === 'string' ? document.querySelector(element) : element;
                this.options = options;
                this.modal = new TailwindModal(this.element.id, options);
            }

            show() { this.modal.show(); }
            hide() { this.modal.hide(); }
            toggle() { this.modal.toggle(); }
            dispose() { this.modal.dispose(); }

            static getInstance(element) {
                const modalId = typeof element === 'string' ? element.replace('#', '') : element.id;
                return TailwindModal.getInstance(modalId);
            }
        }
    }
};

// Tailwind Modal 类定义
class TailwindModal {
    constructor(modalId, options = {}) {
        this.modalId = modalId;
        this.modal = document.getElementById(modalId);
        this.options = {
            backdrop: true,
            keyboard: true,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.modal) {
            console.error(`Modal with id '${this.modalId}' not found`);
            return;
        }

        // 创建背景遮罩
        this.createBackdrop();
        
        // 绑定事件
        this.bindEvents();
    }

    createBackdrop() {
        if (!this.backdrop) {
            this.backdrop = document.createElement('div');
            this.backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 z-40 hidden';
            this.backdrop.id = `${this.modalId}-backdrop`;
            document.body.appendChild(this.backdrop);
        }
    }

    bindEvents() {
        // ESC键关闭
        if (this.options.keyboard) {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isVisible()) {
                    this.hide();
                }
            });
        }

        // 背景点击关闭
        if (this.options.backdrop) {
            this.backdrop.addEventListener('click', () => {
                this.hide();
            });

            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });
        }

        // 关闭按钮事件
        const closeButtons = this.modal.querySelectorAll('[data-tw-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.hide();
            });
        });
    }

    show() {
        this.modal.classList.remove('hidden');
        this.backdrop.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // 触发shown事件
        this.modal.dispatchEvent(new Event('shown.tw.modal'));
    }

    hide() {
        this.modal.classList.add('hidden');
        this.backdrop.classList.add('hidden');
        document.body.style.overflow = '';
        
        // 触发hidden事件
        this.modal.dispatchEvent(new Event('hidden.tw.modal'));
    }

    isVisible() {
        return !this.modal.classList.contains('hidden');
    }

    toggle() {
        if (this.isVisible()) {
            this.hide();
        } else {
            this.show();
        }
    }

    dispose() {
        this.hide();
        if (this.backdrop) {
            this.backdrop.remove();
        }
    }
}

// 静态方法：获取模态框实例
TailwindModal.getInstance = (modalId) => {
    return window.tailwindModals?.[modalId] || null;
};

// Tailwind Alert 类定义
class TailwindAlert {
    constructor(message, type = 'info', options = {}) {
        this.message = message;
        this.type = type;
        this.options = {
            autoClose: true,
            duration: 5000,
            container: 'notification-container',
            showCloseButton: true,
            ...options
        };
        this.alertElement = null;
        this.timer = null;
    }

    // 获取Alert样式配置
    getAlertStyles() {
        const styles = {
            info: {
                bg: 'bg-blue-50',
                border: 'border-blue-200',
                text: 'text-blue-800',
                icon: 'fa-info-circle',
                iconColor: 'text-blue-500'
            },
            success: {
                bg: 'bg-green-50',
                border: 'border-green-200',
                text: 'text-green-800',
                icon: 'fa-check-circle',
                iconColor: 'text-green-500'
            },
            warning: {
                bg: 'bg-yellow-50',
                border: 'border-yellow-200',
                text: 'text-yellow-800',
                icon: 'fa-exclamation-triangle',
                iconColor: 'text-yellow-500'
            },
            error: {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-800',
                icon: 'fa-exclamation-circle',
                iconColor: 'text-red-500'
            },
            danger: {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-800',
                icon: 'fa-exclamation-circle',
                iconColor: 'text-red-500'
            }
        };

        return styles[this.type] || styles.info;
    }

    // 创建Alert元素
    createElement() {
        const styles = this.getAlertStyles();
        
        this.alertElement = document.createElement('div');
        this.alertElement.className = `${styles.bg} ${styles.border} ${styles.text} border rounded-lg p-4 mb-4 relative transition-all duration-300 transform translate-x-full`;
        this.alertElement.setAttribute('role', 'alert');
        
        const content = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas ${styles.icon} ${styles.iconColor} text-lg"></i>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium">${this.message}</p>
                </div>
                ${this.options.showCloseButton ? `
                <div class="ml-4 flex-shrink-0">
                    <button type="button" class="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none" data-tw-dismiss="alert">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                ` : ''}
            </div>
        `;
        
        this.alertElement.innerHTML = content;
        
        // 绑定关闭按钮事件
        if (this.options.showCloseButton) {
            const closeButton = this.alertElement.querySelector('[data-tw-dismiss="alert"]');
            closeButton.addEventListener('click', () => this.close());
        }
    }

    // 显示Alert
    show() {
        this.createElement();
        
        // 确保容器存在
        let container = document.getElementById(this.options.container);
        if (!container) {
            container = this.createContainer();
        }
        
        container.appendChild(this.alertElement);
        
        // 触发动画
        setTimeout(() => {
            this.alertElement.classList.remove('translate-x-full');
            this.alertElement.classList.add('translate-x-0');
        }, 10);
        
        // 自动关闭
        if (this.options.autoClose) {
            this.timer = setTimeout(() => this.close(), this.options.duration);
        }
        
        return this.alertElement;
    }

    // 关闭Alert
    close() {
        if (!this.alertElement) return;
        
        // 清除定时器
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        // 添加关闭动画
        this.alertElement.classList.add('translate-x-full');
        this.alertElement.classList.remove('translate-x-0');
        
        // 动画结束后移除元素
        setTimeout(() => {
            if (this.alertElement && this.alertElement.parentNode) {
                this.alertElement.parentNode.removeChild(this.alertElement);
            }
        }, 300);
    }

    // 创建通知容器
    createContainer() {
        const container = document.createElement('div');
        container.id = this.options.container;
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        container.style.maxWidth = '400px';
        document.body.appendChild(container);
        return container;
    }
}

// 导出到全局
window.TailwindConfig = TailwindConfig;
window.tw = TailwindConfig;
window.TailwindModal = TailwindModal;
window.TailwindAlert = TailwindAlert;

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TailwindConfig.init());
} else {
    TailwindConfig.init();
}

// 创建全局Bootstrap别名以实现兼容性
window.bootstrap = TailwindConfig.bootstrap;

// 兼容性别名
window.showAlert = window.showAlert || ((message, type = 'info') => {
    return new TailwindAlert(message, type).show();
});
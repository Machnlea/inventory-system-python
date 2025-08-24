/**
 * 多标签页会话管理器
 * 支持一个浏览器内多个标签页独立登录不同账号
 * 提供登录冲突检测和"挤掉"原有登录的功能
 */
class TabSessionManager {
    constructor() {
        this.tabId = this.generateTabId();
        this.channel = new BroadcastChannel('tab-session-manager');
        this.currentUser = null;
        this.loginConflictHandler = null;
        
        // 监听其他标签页的消息
        this.channel.addEventListener('message', (event) => {
            this.handleMessage(event.data);
        });
        
        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // 页面可见性变化时检查会话
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkSessionValidity();
            }
        });
        
        console.log('TabSessionManager initialized, Tab ID:', this.tabId);
    }
    
    /**
     * 生成唯一的标签页ID
     */
    generateTabId() {
        return `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * 获取当前标签页的用户信息
     */
    getCurrentUser() {
        const userInfo = sessionStorage.getItem('user_info');
        const accessToken = sessionStorage.getItem('access_token');
        
        if (userInfo && accessToken) {
            try {
                this.currentUser = JSON.parse(userInfo);
                return this.currentUser;
            } catch (e) {
                console.error('解析用户信息失败:', e);
                this.clearSession();
                return null;
            }
        }
        return null;
    }
    
    /**
     * 检查是否有同一用户在其他标签页登录
     */
    async checkLoginConflict(username) {
        return new Promise((resolve) => {
            const requestId = this.generateTabId();
            const timeout = 1000; // 1秒超时
            
            // 收集响应
            const responses = [];
            const messageHandler = (event) => {
                const data = event.data;
                if (data.type === 'login_check_response' && data.requestId === requestId) {
                    responses.push(data);
                }
            };
            
            this.channel.addEventListener('message', messageHandler);
            
            // 发送检查请求
            this.channel.postMessage({
                type: 'login_check_request',
                username: username,
                requestId: requestId,
                fromTab: this.tabId
            });
            
            // 等待响应
            setTimeout(() => {
                this.channel.removeEventListener('message', messageHandler);
                
                // 查找冲突的标签页
                const conflicts = responses.filter(resp => resp.hasUser && resp.username === username);
                resolve({
                    hasConflict: conflicts.length > 0,
                    conflicts: conflicts
                });
            }, timeout);
        });
    }
    
    /**
     * 处理来自其他标签页的消息
     */
    handleMessage(data) {
        switch (data.type) {
            case 'login_check_request':
                this.handleLoginCheckRequest(data);
                break;
            case 'force_logout':
                this.handleForceLogout(data);
                break;
            case 'session_update':
                this.handleSessionUpdate(data);
                break;
        }
    }
    
    /**
     * 处理登录检查请求
     */
    handleLoginCheckRequest(data) {
        const currentUser = this.getCurrentUser();
        
        this.channel.postMessage({
            type: 'login_check_response',
            requestId: data.requestId,
            hasUser: !!currentUser,
            username: currentUser ? currentUser.username : null,
            tabId: this.tabId
        });
    }
    
    /**
     * 处理强制退出登录
     */
    handleForceLogout(data) {
        // 检查当前用户是否与被强制退出的用户匹配
        const currentUser = this.getCurrentUser();
        
        if (!currentUser || currentUser.username !== data.username) {
            return; // 不是同一用户，不处理
        }
        
        // 检查是否应该被强制退出
        const shouldLogout = data.targetTabs === null || // null表示所有其他标签页
                           (data.targetTabs && data.targetTabs.includes(this.tabId));
        
        // 排除发送消息的标签页（不要退出自己）
        if (data.fromTab === this.tabId) {
            return;
        }
        
        if (shouldLogout) {
            console.log('被其他标签页强制退出登录');
            this.clearSession();
            
            // 显示通知
            if (typeof showNotification === 'function') {
                showNotification('您的账号在其他标签页登录，当前会话已结束', 'warning');
            }
            
            // 跳转到登录页面
            setTimeout(() => {
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
            }, 2000);
        }
    }
    
    /**
     * 处理会话更新
     */
    handleSessionUpdate(data) {
        // 可以在这里处理会话状态的同步更新
        console.log('收到会话更新:', data);
    }
    
    /**
     * 登录用户
     */
    async login(credentials) {
        const { username, password } = credentials;
        
        // 首先尝试正常登录（不强制）
        try {
            const response = await this.attemptLogin(username, password, false);
            return response;
        } catch (error) {
            // 检查是否是409冲突错误（服务器端检测到会话冲突）
            if (error.response && error.response.status === 409) {
                const conflictData = error.response.data;
                console.log('检测到服务器端会话冲突:', conflictData);
                
                if (conflictData && conflictData.conflict_type === 'session_exists') {
                    // 显示服务器端会话冲突对话框
                    const shouldForceLogin = await this.showServerSessionConflictDialog(
                        username, 
                        conflictData.active_sessions,
                        conflictData.message
                    );
                    
                    if (shouldForceLogin) {
                        // 用户选择强制登录
                        try {
                            const response = await this.attemptLogin(username, password, true);
                            return response;
                        } catch (forceError) {
                            console.error('强制登录失败:', forceError);
                            throw forceError;
                        }
                    } else {
                        throw new Error('登录已取消');
                    }
                }
            }
            
            // 其他错误，回退到客户端检测逻辑
            console.log('服务器端冲突检测失败，使用客户端检测:', error);
            return this.handleClientSideLogin(username, password);
        }
    }
    
    /**
     * 处理客户端登录逻辑（原逻辑的备份）
     */
    async handleClientSideLogin(username, password) {
        // 检查登录冲突
        const conflictResult = await this.checkLoginConflict(username);
        
        if (conflictResult.hasConflict) {
            // 有冲突，询问用户是否要挤掉其他登录
            const shouldForceLogin = await this.showLoginConflictDialog(username, conflictResult.conflicts);
            
            if (shouldForceLogin) {
                // 用户选择强制登录，发送退出消息给其他标签页
                this.forceLogoutOtherTabs(username);
            } else {
                // 用户取消登录
                throw new Error('登录已取消');
            }
        }
        
        // 执行实际登录
        const response = await this.attemptLogin(username, password, false);
        return response;
    }
    
    /**
     * 尝试登录
     */
    async attemptLogin(username, password, force = false) {
        try {
            const loginData = {
                username: username,
                password: password
            };
            
            // 如果是强制登录，添加force参数
            if (force) {
                loginData.force = true;
            }
            
            const response = await api.post('/api/auth/login/json', loginData);
            
            // 将数据存储到sessionStorage（标签页独立）
            this.setSession(response);
            
            // 通知其他标签页会话更新
            this.channel.postMessage({
                type: 'session_update',
                action: 'login',
                username: response.user.username,
                tabId: this.tabId
            });
            
            return response;
            
        } catch (error) {
            console.error('登录失败:', error);
            throw error;
        }
    }
    
    /**
     * 显示服务器端会话冲突对话框
     */
    async showServerSessionConflictDialog(username, activeSessions, message) {
        return new Promise((resolve) => {
            // 创建模态框
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]';
            
            // 格式化会话信息
            const sessionsInfo = activeSessions.map(session => {
                const createdTime = new Date(session.created_at * 1000).toLocaleString();
                const lastActivity = new Date(session.last_activity * 1000).toLocaleString();
                const userAgent = session.user_agent.substring(0, 50) + (session.user_agent.length > 50 ? '...' : '');
                
                return `
                    <div class="bg-gray-50 rounded p-2 text-xs">
                        <div><strong>IP:</strong> ${session.ip_address}</div>
                        <div><strong>浏览器:</strong> ${userAgent}</div>
                        <div><strong>登录时间:</strong> ${createdTime}</div>
                        <div><strong>最后活动:</strong> ${lastActivity}</div>
                    </div>
                `;
            }).join('');
            
            modal.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
                    <div class="flex items-center mb-4">
                        <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mr-3"></i>
                        <h3 class="text-lg font-semibold text-gray-900">检测到活跃会话</h3>
                    </div>
                    <div class="mb-6">
                        <p class="text-gray-700 mb-3">
                            用户 <span class="font-semibold text-blue-600">${username}</span> 已在其他设备登录。
                        </p>
                        <div class="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
                            <p class="text-sm text-yellow-800">
                                <i class="fas fa-info-circle mr-2"></i>
                                ${message}
                            </p>
                        </div>
                        <div class="space-y-2">
                            <p class="text-sm font-medium text-gray-700">活跃会话详情：</p>
                            ${sessionsInfo}
                        </div>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-3">
                        <button id="cancelLogin" class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors">
                            <i class="fas fa-times mr-2"></i>取消登录
                        </button>
                        <button id="forceLogin" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                            <i class="fas fa-sign-in-alt mr-2"></i>强制登录
                        </button>
                    </div>
                    <div class="mt-4 text-xs text-gray-500 text-center">
                        选择"强制登录"将会终止其他设备的登录会话
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 绑定事件
            modal.querySelector('#cancelLogin').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(false);
            });
            
            modal.querySelector('#forceLogin').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(true);
            });
            
            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    resolve(false);
                }
            });
        });
    }
    
    /**
     * 显示登录冲突对话框
     */
    async showLoginConflictDialog(username, conflicts) {
        return new Promise((resolve) => {
            // 创建模态框
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]';
            modal.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
                    <div class="flex items-center mb-4">
                        <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mr-3"></i>
                        <h3 class="text-lg font-semibold text-gray-900">账号冲突提醒</h3>
                    </div>
                    <div class="mb-6">
                        <p class="text-gray-700 mb-3">
                            用户 <span class="font-semibold text-blue-600">${username}</span> 已在其他标签页登录。
                        </p>
                        <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
                            <p class="text-sm text-yellow-800">
                                <i class="fas fa-info-circle mr-2"></i>
                                检测到 ${conflicts.length} 个标签页正在使用此账号
                            </p>
                        </div>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-3">
                        <button id="cancelLogin" class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors">
                            <i class="fas fa-times mr-2"></i>取消登录
                        </button>
                        <button id="forceLogin" class="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                            <i class="fas fa-sign-in-alt mr-2"></i>强制登录
                        </button>
                    </div>
                    <div class="mt-4 text-xs text-gray-500 text-center">
                        选择"强制登录"将会退出其他标签页的登录状态
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 绑定事件
            modal.querySelector('#cancelLogin').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(false);
            });
            
            modal.querySelector('#forceLogin').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(true);
            });
            
            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    resolve(false);
                }
            });
        });
    }
    
    /**
     * 强制退出其他标签页的登录
     */
    forceLogoutOtherTabs(username) {
        this.channel.postMessage({
            type: 'force_logout',
            username: username,
            fromTab: this.tabId,
            targetTabs: null // null表示所有其他标签页
        });
    }
    
    /**
     * 设置会话信息
     */
    setSession(response) {
        // 使用sessionStorage实现标签页独立存储
        sessionStorage.setItem('access_token', response.access_token);
        sessionStorage.setItem('refresh_token', response.refresh_token);
        sessionStorage.setItem('user_info', JSON.stringify(response.user));
        sessionStorage.setItem('tab_id', this.tabId);
        
        this.currentUser = response.user;
        
        // 更新API客户端的token
        if (window.api) {
            api.token = response.access_token;
        }
    }
    
    /**
     * 清除会话信息
     */
    clearSession() {
        const username = this.currentUser ? this.currentUser.username : null;
        
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user_info');
        sessionStorage.removeItem('tab_id');
        
        this.currentUser = null;
        
        // 更新API客户端
        if (window.api) {
            api.token = null;
        }
        
        // 通知其他标签页
        if (username) {
            this.channel.postMessage({
                type: 'session_update',
                action: 'logout',
                username: username,
                tabId: this.tabId
            });
        }
    }
    
    /**
     * 检查会话有效性
     */
    checkSessionValidity() {
        const user = this.getCurrentUser();
        const accessToken = sessionStorage.getItem('access_token');
        
        if (!user || !accessToken) {
            // 如果没有有效会话且不在登录页面，跳转到登录页面
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    }
    
    /**
     * 获取访问令牌
     */
    getAccessToken() {
        return sessionStorage.getItem('access_token');
    }
    
    /**
     * 获取刷新令牌
     */
    getRefreshToken() {
        return sessionStorage.getItem('refresh_token');
    }
    
    /**
     * 页面卸载时的清理工作
     */
    cleanup() {
        if (this.channel) {
            this.channel.close();
        }
    }
    
    /**
     * 注册登录冲突处理器
     */
    setLoginConflictHandler(handler) {
        this.loginConflictHandler = handler;
    }
}

// 创建全局会话管理器实例
const tabSessionManager = new TabSessionManager();

// 导出到全局作用域
window.TabSessionManager = TabSessionManager;
window.tabSessionManager = tabSessionManager;
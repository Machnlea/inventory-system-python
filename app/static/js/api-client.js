// API 客户端工具
class ApiClient {
    constructor() {
        this.baseURL = '';
        // 优先从sessionStorage获取token（支持多标签页独立登录）
        this.token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        this.retryCount = 3;
        this.retryDelay = 1000;
    }

    // 获取请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // 每次获取请求头时都重新获取token，确保使用最新的token
        const currentToken = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        if (currentToken) {
            this.token = currentToken; // 同步更新实例的token
            headers['Authorization'] = `Bearer ${currentToken}`;
        }
        
        return headers;
    }

    // 检查网络连接
    async checkNetworkConnection() {
        if (!navigator.onLine) {
            throw new Error('网络连接已断开, 请检查网络设置');
        }
    }

    // 延迟函数
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 通用请求方法(带重试机制)
    async request(endpoint, options = {}, retryCount = this.retryCount) {
        await this.checkNetworkConnection();
        
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        let lastError;
        
        for (let attempt = 1; attempt <= retryCount; attempt++) {
            try {
                const response = await fetch(url, config);
                
                // 处理401未授权错误
                if (response.status === 401) {
                    // 如果是登录接口，不要调用handleUnauthorized，避免重定向循环
                    if (endpoint.includes('/api/auth/login')) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.detail || '用户名或密码错误');
                    } else {
                        // 对于非登录接口的401错误，如果是第一次尝试，延迟重试一次
                        if (attempt === 1) {
                            console.log('第一次收到401错误，延迟重试...');
                            await this.delay(500); // 延迟500ms重试
                            continue; // 继续下一次尝试
                        } else {
                            // 第二次还是401，则处理未授权
                            this.handleUnauthorized();
                            throw new Error('登录已过期, 请重新登录');
                        }
                    }
                }

                // 处理409冲突错误（会话冲突），不要当作常规错误
                if (response.status === 409) {
                    const errorData = await response.json().catch(() => ({}));
                    console.log('409冲突错误详情:', errorData);
                    
                    // 构造错误对象，确保数据结构正确
                    const conflictData = errorData.detail || errorData;
                    const error = new Error(conflictData.message || '会话冲突');
                    error.response = { 
                        status: 409, 
                        data: conflictData
                    };
                    throw error;
                }

                // 处理其他HTTP错误
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || `请求失败: ${response.status}`);
                }

                return await response.json();
                
            } catch (error) {
                lastError = error;
                console.error(`API请求失败 (尝试 ${attempt}/${retryCount}):`, error);
                
                // 409冲突错误不重试，直接抛出
                if (error.response && error.response.status === 409) {
                    break;
                }
                
                // 如果是网络错误且还有重试次数, 则等待后重试
                if ((error.name === 'TypeError' || error.message.includes('网络')) && attempt < retryCount) {
                    const delayTime = this.retryDelay * Math.pow(2, attempt - 1); // 指数退避
                    console.log(`等待 ${delayTime}ms 后重试...`);
                    await this.delay(delayTime);
                    continue;
                }
                
                // 如果是其他错误或者重试次数用完, 直接抛出
                break;
            }
        }
        
        throw lastError;
    }

    // GET请求
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST请求
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT请求
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // 处理未授权访问
    handleUnauthorized() {
        console.warn('收到401未授权错误，检查会话状态...');
        
        // 在清除会话前，检查是否是临时会话问题
        const currentToken = sessionStorage.getItem('access_token');
        const userInfo = sessionStorage.getItem('user_info');
        
        if (currentToken && userInfo) {
            console.log('检测到可能的服务器端会话失效，尝试重新同步...');
            
            // 如果有tabSessionManager，让它处理会话恢复
            if (window.tabSessionManager && typeof tabSessionManager.checkSessionValidity === 'function') {
                // 延迟一点时间让会话管理器处理
                setTimeout(async () => {
                    try {
                        await tabSessionManager.checkSessionValidity();
                    } catch (error) {
                        console.error('会话验证失败:', error);
                        // 如果验证失败，清除会话并重定向
                        this.clearSessionAndRedirect();
                    }
                }, 100);
                return;
            }
        }
        
        // 如果没有会话管理器或无法恢复，则清除会话
        this.clearSessionAndRedirect();
    }
    
    // 清除会话并重定向
    clearSessionAndRedirect() {
        console.log('清除会话数据并重定向到登录页');
        
        // 清除当前标签页的会话数据
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user_info');
        
        // 兼容旧系统：同时清除localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        
        // 通知标签页会话管理器
        if (window.tabSessionManager) {
            tabSessionManager.clearSession();
        }
        
        // 只有不在登录页时才跳转
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    }

    // 文件上传
    async uploadFile(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        
        return new Promise((resolve, reject) => {
            xhr.open('POST', `${this.baseURL}${endpoint}`, true);
            // 动态获取最新的token
            const currentToken = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
            if (currentToken) {
                xhr.setRequestHeader('Authorization', `Bearer ${currentToken}`);
            }

            if (onProgress) {
                xhr.upload.onprogress = (event) => {
                    if (event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        onProgress(percentComplete);
                    }
                };
            }

            xhr.onload = () => {
                if (xhr.status === 401) {
                    this.handleUnauthorized();
                    reject(new Error('登录已过期, 请重新登录'));
                    return;
                }

                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        resolve({ success: true });
                    }
                } else {
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        reject(new Error(errorData.detail || `上传失败: ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`上传失败: ${xhr.status}`));
                    }
                }
            };

            xhr.onerror = () => {
                reject(new Error('网络错误, 请检查连接'));
            };

            xhr.send(formData);
        });
    }

    // 文件下载
    async downloadFile(endpoint, filename, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                method: options.method || 'GET',
                headers: this.getHeaders(),
                body: options.body
            });

            if (response.status === 401) {
                this.handleUnauthorized();
                throw new Error('登录已过期, 请重新登录');
            }

            if (!response.ok) {
                throw new Error(`下载失败: ${response.status}`);
            }

            // 获取文件blob
            const blob = await response.blob();
            
            // 创建下载链接
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'download';
            
            // 触发下载
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 清理URL对象
            window.URL.revokeObjectURL(downloadUrl);
            
            return { success: true };
        } catch (error) {
            console.error('文件下载失败:', error);
            throw error;
        }
    }
}

// 创建全局API客户端实例
const api = new ApiClient();

// 设备管理API
const EquipmentAPI = {
    // 获取设备列表
    async getEquipments(params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.skip) queryParams.append('skip', params.skip);
        if (params.limit) queryParams.append('limit', params.limit);
        if (params.sort_field) queryParams.append('sort_field', params.sort_field);
        if (params.sort_order) queryParams.append('sort_order', params.sort_order);
        
        const endpoint = `/api/equipment/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return api.get(endpoint);
    },

    // 获取单个设备详情
    async getEquipment(id) {
        return api.get(`/api/equipment/${id}`);
    },

    // 创建设备
    async createEquipment(data) {
        return api.post('/api/equipment/', data);
    },

    // 更新设备
    async updateEquipment(id, data) {
        return api.put(`/api/equipment/${id}`, data);
    },

    // 删除设备
    async deleteEquipment(id) {
        return api.delete(`/api/equipment/${id}`);
    },

    // 筛选设备
    async filterEquipments(filters, params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.skip) queryParams.append('skip', params.skip);
        if (params.limit) queryParams.append('limit', params.limit);
        if (params.sort_field) queryParams.append('sort_field', params.sort_field);
        if (params.sort_order) queryParams.append('sort_order', params.sort_order);
        
        const endpoint = `/api/equipment/filter${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return api.post(endpoint, filters);
    },

    // 搜索设备
    async searchEquipments(searchParams, params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.skip) queryParams.append('skip', params.skip);
        if (params.limit) queryParams.append('limit', params.limit);
        
        const endpoint = `/api/equipment/search${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return api.post(endpoint, searchParams);
    },

    // 批量操作
    async batchUpdateCalibration(data) {
        return api.post('/api/equipment/batch/update-calibration', data);
    },

    async batchChangeStatus(data) {
        return api.post('/api/equipment/batch/change-status', data);
    },

    async batchDelete(data) {
        return api.post('/api/equipment/batch/delete', data);
    },

    async batchExport(data) {
        return api.downloadFile('/api/equipment/batch/export-selected', '选中设备.xlsx', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async batchTransfer(data) {
        return api.post('/api/equipment/batch/transfer', data);
    },

    // 导出功能
    async exportMonthlyPlan() {
        return api.downloadFile('/api/equipment/export/monthly-plan', '月度检定计划.xlsx');
    },

    async exportFiltered(filters) {
        const response = await fetch('/api/equipment/export/filtered', {
            method: 'POST',
            headers: api.getHeaders(),
            body: JSON.stringify(filters)
        });

        if (response.status === 401) {
            api.handleUnauthorized();
            throw new Error('登录已过期, 请重新登录');
        }

        if (!response.ok) {
            throw new Error(`导出失败: ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `设备台账_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
    }
};

// 部门API
const DepartmentAPI = {
    // 获取所有部门
    async getDepartments() {
        return api.get('/api/departments/');
    },

    // 获取部门及其设备数量
    async getDepartmentsWithCounts() {
        return api.get('/api/departments/with-counts');
    },

    // 获取单个部门
    async getDepartment(id) {
        return api.get(`/api/departments/${id}`);
    },

    // 创建部门
    async createDepartment(data) {
        return api.post('/api/departments/', data);
    },

    // 更新部门
    async updateDepartment(id, data) {
        return api.put(`/api/departments/${id}`, data);
    },

    // 删除部门
    async deleteDepartment(id) {
        return api.delete(`/api/departments/${id}`);
    }
};

// 设备类别API
const CategoryAPI = {
    // 获取所有类别
    async getCategories() {
        return api.get('/api/categories/');
    },

    // 获取类别及其设备数量
    async getCategoriesWithCounts() {
        return api.get('/api/categories/with-counts');
    },

    // 获取单个类别
    async getCategory(id) {
        return api.get(`/api/categories/${id}`);
    },

    // 创建类别
    async createCategory(data) {
        return api.post('/api/categories/', data);
    },

    // 更新类别
    async updateCategory(id, data) {
        return api.put(`/api/categories/${id}`, data);
    },

    // 删除类别
    async deleteCategory(id) {
        return api.delete(`/api/categories/${id}`);
    },

    // 预定义器具名称管理
    async getPredefinedNames(categoryId) {
        return api.get(`/api/categories/${categoryId}/predefined-names`);
    },

    async addPredefinedName(categoryId, name) {
        return api.post(`/api/categories/${categoryId}/predefined-names`, { name });
    },

    async removePredefinedName(categoryId, name) {
        return api.delete(`/api/categories/${categoryId}/predefined-names/${encodeURIComponent(name)}`);
    },

    async updatePredefinedNames(categoryId, names) {
        return api.put(`/api/categories/${categoryId}/predefined-names`, { names });
    },

    // 获取类别下设备使用情况
    async getEquipmentUsage(categoryId) {
        return api.get(`/api/categories/${categoryId}/equipment-usage`);
    }
};

// 仪表盘API
const DashboardAPI = {
    async getStats() {
        return api.get('/api/dashboard/stats');
    },
    
    async getMonthlyDueEquipments() {
        return api.get('/api/dashboard/monthly-due-equipments');
    }
};

// 附件API
const AttachmentAPI = {
    // 获取设备附件
    async getEquipmentAttachments(equipmentId) {
        return api.get(`/api/attachments/equipment/${equipmentId}/attachments`);
    },

    // 获取单个附件信息
    async getAttachment(attachmentId) {
        return api.get(`/api/attachments/${attachmentId}`);
    },

    // 上传附件
    async uploadAttachment(equipmentId, file, onProgress) {
        const endpoint = `/api/attachments/equipment/${equipmentId}/attachments`;
        return api.uploadFile(endpoint, file, onProgress);
    },

    // 删除附件
    async deleteAttachment(attachmentId) {
        return api.delete(`/api/attachments/${attachmentId}`);
    },

    // 下载附件
    async downloadAttachment(attachmentId, filename) {
        return api.downloadFile(`/api/attachments/${attachmentId}/download`, filename);
    },

    // 预览附件
    async previewAttachment(attachmentId) {
        const url = `${api.baseURL}/api/attachments/${attachmentId}/preview`;
        
        try {
            const response = await fetch(url, {
                headers: api.getHeaders()
            });

            if (response.status === 401) {
                api.handleUnauthorized();
                throw new Error('登录已过期, 请重新登录');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `预览失败: ${response.status}`);
            }

            // 获取文件blob
            const blob = await response.blob();
            
            // 创建预览URL
            return window.URL.createObjectURL(blob);
            
        } catch (error) {
            console.error('文件预览失败:', error);
            throw error;
        }
    }
};

// 导入导出API
const ImportExportAPI = {
    // 导出所有数据
    async exportAll() {
        return api.downloadFile('/api/import/export/all', '设备台账数据.xlsx');
    },

    // 导出筛选后的数据
    async exportFiltered(filters) {
        const response = await fetch('/api/import/export/filtered', {
            method: 'POST',
            headers: api.getHeaders(),
            body: JSON.stringify(filters)
        });

        if (response.status === 401) {
            api.handleUnauthorized();
            throw new Error('登录已过期, 请重新登录');
        }

        if (!response.ok) {
            throw new Error(`导出失败: ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '设备台账数据_筛选.xlsx';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
    },

    // 下载导入模板
    async downloadTemplate() {
        return api.downloadFile('/api/import/template/download', '设备台账导入模板.xlsx');
    },

    // 上传导入文件
    async uploadImportFile(file, overwrite = false) {
        const formData = new FormData();
        formData.append('file', file);
        // 将布尔值转换为字符串传递给FastAPI
        formData.append('overwrite', overwrite.toString());

        console.log('上传文件参数:', {
            filename: file.name,
            overwrite: overwrite,
            overwriteType: typeof overwrite
        });

        // 动态获取最新的token
        const currentToken = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        const headers = {};
        if (currentToken) {
            headers['Authorization'] = `Bearer ${currentToken}`;
        }

        const response = await fetch('/api/import/upload', {
            method: 'POST',
            headers: headers,
            body: formData
        });

        if (response.status === 401) {
            api.handleUnauthorized();
            throw new Error('登录已过期, 请重新登录');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `上传失败: ${response.status}`);
        }

        return await response.json();
    }
};

// 通知工具 - 使用统一通知管理器
// 如果通知管理器已加载，使用它；否则使用简化版本
function showNotification(message, type = 'info') {
    // 优先使用全局通知管理器
    if (window.notificationManager) {
        window.notificationManager.show(message, type);
        return;
    }
    
    // 备用实现：如果通知管理器未加载
    const container = document.getElementById('notification-container') || 
                     document.body;
    
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
    
    notification.className = `${colorScheme.bg} ${colorScheme.border} border-l-4 px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full fixed right-4 z-[99999] max-w-md`;
    notification.style.marginBottom = '12px';
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="${colorScheme.icon} text-xl mr-3"></i>
            <span class="${colorScheme.text} font-medium">${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
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
            }
        }, 300);
    }, 3000);
}

// 网络状态监听
window.addEventListener('online', function() {
    console.log('网络已恢复连接');
    showNotification('网络已恢复连接', 'success');
});

window.addEventListener('offline', function() {
    console.log('网络连接已断开');
    showNotification('网络连接已断开, 请检查网络设置', 'warning');
});

// 全局错误处理
window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise拒绝:', event.reason);
    showNotification('操作失败, 请稍后重试', 'error');
    event.preventDefault();
});

window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
    // 不显示所有错误, 避免过多的错误提示
    if (event.error instanceof TypeError || event.error instanceof ReferenceError) {
        console.warn('忽略JavaScript错误:', event.error.message);
    } else {
        showNotification('系统错误, 请刷新页面重试', 'error');
    }
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // 页面重新变为可见时, 检查token是否仍然有效
        // 优先检查sessionStorage（支持多标签页独立登录）
        const token = sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        const userInfo = sessionStorage.getItem('user_info') || localStorage.getItem('user_info');
        
        if (!token || !userInfo) {
            // 如果没有token或用户信息, 跳转到登录页
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        } else if (window.tabSessionManager) {
            // 如果有会话管理器，异步检查会话有效性
            tabSessionManager.checkSessionValidity().catch(error => {
                console.error('检查会话有效性时发生错误:', error);
            });
        }
    }
});

// 系统设置API
const SystemAPI = {
    // 获取系统设置
    async getSettings() {
        return api.get('/api/settings/');
    },

    // 更新系统设置
    async updateSettings(settings) {
        return api.put('/api/settings/', settings);
    },

    // 重置系统设置
    async resetSettings() {
        return api.post('/api/settings/reset');
    }
};

// 统计报表API
const ReportsAPI = {
    // 获取报表概览
    async getOverview() {
        return api.get('/api/reports/overview');
    },

    // 获取检定统计
    async getCalibrationStats(start_date, end_date) {
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        
        const endpoint = `/api/reports/calibration-stats${params.toString() ? '?' + params.toString() : ''}`;
        return api.get(endpoint);
    },

    // 获取设备趋势
    async getEquipmentTrends(start_date, end_date) {
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        
        const endpoint = `/api/reports/equipment-trends${params.toString() ? '?' + params.toString() : ''}`;
        return api.get(endpoint);
    },

    // 获取部门对比
    async getDepartmentComparison(start_date, end_date) {
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        
        const endpoint = `/api/reports/department-comparison${params.toString() ? '?' + params.toString() : ''}`;
        return api.get(endpoint);
    },

    // 获取检定记录明细
    async getCalibrationRecords(start_date, end_date, page = 1, page_size = 20) {
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        params.append('page', page);
        params.append('page_size', page_size);
        
        const endpoint = `/api/reports/calibration-records${params.toString() ? '?' + params.toString() : ''}`;
        return api.get(endpoint);
    },

    // 导出报表
    async exportReport(start_date, end_date, format = 'excel') {
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        params.append('format', format);
        
        const endpoint = `/api/reports/export${params.toString() ? '?' + params.toString() : ''}`;
        
        try {
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: api.getHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`导出失败: ${response.status}`);
            }
            
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = '统计报表.xlsx';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }
            
            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            return { success: true, message: '导出成功' };
        } catch (error) {
            console.error('导出报表失败:', error);
            throw error;
        }
    },

    // 导出报表数据
    async exportData(report_type, start_date, end_date, format = 'excel') {
        const params = new URLSearchParams();
        params.append('report_type', report_type);
        params.append('format', format);
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        
        const endpoint = `/api/reports/export-data?${params.toString()}`;
        const filename = `${report_type}_report_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`;
        return api.downloadFile(endpoint, filename);
    },

    // 获取设备统计数据
    async getEquipmentStats(sort_by = 'original_value', sort_order = 'desc', page = 1, page_size = 20, sort_by2 = '', sort_order2 = 'desc') {
        const params = new URLSearchParams();
        params.append('sort_by', sort_by);
        params.append('sort_order', sort_order);
        params.append('page', page);
        params.append('page_size', page_size);
        
        // 只在提供了次排序字段时才添加次排序参数
        if (sort_by2) {
            params.append('sort_by2', sort_by2);
            params.append('sort_order2', sort_order2);
        }
        
        const endpoint = `/api/reports/equipment-stats?${params.toString()}`;
        return api.get(endpoint);
    }
};

// 导出全局对象
window.ApiClient = ApiClient;
window.api = api;
window.EquipmentAPI = EquipmentAPI;
window.DepartmentAPI = DepartmentAPI;
window.CategoryAPI = CategoryAPI;
window.DashboardAPI = DashboardAPI;
window.AttachmentAPI = AttachmentAPI;
window.ImportExportAPI = ImportExportAPI;
window.SystemAPI = SystemAPI;
window.ReportsAPI = ReportsAPI;
window.showNotification = showNotification;
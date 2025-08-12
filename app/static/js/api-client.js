// API 客户端工具
class ApiClient {
    constructor() {
        this.baseURL = '';
        this.token = localStorage.getItem('access_token');
        this.retryCount = 3;
        this.retryDelay = 1000;
    }

    // 获取请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
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
                    this.handleUnauthorized();
                    throw new Error('登录已过期, 请重新登录');
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
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
    }

    // 文件上传
    async uploadFile(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        
        return new Promise((resolve, reject) => {
            xhr.open('POST', `${this.baseURL}${endpoint}`, true);
            xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);

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
    async downloadFile(endpoint, filename) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: this.getHeaders()
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
        return api.post('/api/equipment/batch/export-selected', data);
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
        formData.append('overwrite', overwrite);

        const response = await fetch('/api/import/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${api.token}`
            },
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

// 通知工具
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container') || 
                     document.body;
    
    const notification = document.createElement('div');
    
    const bgColor = type === 'success' ? 'bg-green-500' : 
                   type === 'error' ? 'bg-red-500' : 
                   type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500';
    
    const icon = type === 'success' ? 'check-circle' : 
                type === 'error' ? 'exclamation-circle' : 
                type === 'warning' ? 'exclamation-triangle' : 'info-circle';
    
    notification.className = `${bgColor} text-white px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full fixed right-4 z-[99999] max-w-md`;
    notification.style.marginBottom = '8px'; // 通知之间的间距
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${icon} mr-3"></i>
            <span>${message}</span>
        </div>
    `;
    
    // 将通知添加到容器中
    container.appendChild(notification);
    
    // 重新排列所有通知的位置
    repositionNotifications();
    
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
                repositionNotifications();
            }
        }, 300);
    }, 3000);
}

// 重新计算通知位置
function repositionNotifications() {
    const container = document.getElementById('notification-container') || document.body;
    const notifications = Array.from(container.querySelectorAll('.fixed.right-4.z-\\[99999\\]')).reverse();
    
    let topPosition = 16; // 初始位置距离顶部16px
    
    notifications.forEach((notification, index) => {
        notification.style.top = `${topPosition}px`;
        topPosition += 88; // 每个通知高度80px + 间距8px
    });
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
        const token = localStorage.getItem('access_token');
        const userInfo = localStorage.getItem('user_info');
        
        if (!token || !userInfo) {
            // 如果没有token或用户信息, 跳转到登录页
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    }
});

// 导出全局对象
window.ApiClient = ApiClient;
window.api = api;
window.EquipmentAPI = EquipmentAPI;
window.DepartmentAPI = DepartmentAPI;
window.CategoryAPI = CategoryAPI;
window.DashboardAPI = DashboardAPI;
window.AttachmentAPI = AttachmentAPI;
window.ImportExportAPI = ImportExportAPI;
window.showNotification = showNotification;
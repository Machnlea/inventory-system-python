// 全局变量
let currentUser = null;
let authToken = null;
let categoryChart = null;
let currentPagination = null;
let currentEquipments = null;

// 分页配置
const ITEMS_PER_PAGE = 50;

// API基础URL
const API_BASE = '/api';

// 工具函数
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 检查通知容器是否存在，不存在则创建
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }
    
    // 添加通知到容器
    container.insertAdjacentHTML('beforeend', alertHtml);
    
    // 限制同时显示的通知数量（最多3个）
    const alerts = container.querySelectorAll('.alert');
    if (alerts.length > 3) {
        alerts[0].remove();
    }
    
    // 自动关闭
    setTimeout(() => {
        const alertElement = container.querySelector('.alert:last-child');
        if (alertElement) {
            alertElement.classList.add('fade-out');
            setTimeout(() => {
                alertElement.remove();
            }, 300);
        }
    }, 5000);
}

// 庆祝效果函数
function showCelebration() {
    const container = document.getElementById('celebration-container');
    if (!container) return;
    
    // 显示庆祝效果
    container.style.display = 'block';
    
    // 触发五彩纸屑效果
    fireCannonAtElement(container);
    
    // 1.5秒后自动隐藏
    setTimeout(() => {
        container.style.display = 'none';
    }, 1500);
}

// 五彩纸屑大炮效果
function fireCannonAtElement(element) {
    var rect = element.getBoundingClientRect();
    var btnCenterX = rect.left + rect.width / 2;
    var btnCenterY = rect.top + rect.height / 2;
    var originX = btnCenterX / window.innerWidth;
    var originY = btnCenterY / window.innerHeight;

    var ribbonColors = [
        '#e67e22', '#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c'
    ];

    confetti({
        particleCount: 80,
        angle: 90,
        spread: 180,
        startVelocity: 70,
        origin: { x: originX, y: originY },
        colors: ribbonColors,
        shapes: ['square', 'circle'],
        scalar: 1.4,
        ticks: 240
    });
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

function isDateOverdue(dateString) {
    if (!dateString) return false;
    const date = new Date(dateString);
    const today = new Date();
    return date < today;
}

function isDateDueSoon(dateString, days = 30) {
    if (!dateString) return false;
    const date = new Date(dateString);
    const today = new Date();
    const dueSoonDate = new Date(today.getTime() + (days * 24 * 60 * 60 * 1000));
    return date <= dueSoonDate && date >= today;
}

// API调用函数
async function apiCall(endpoint, method = 'GET', data = null, requireAuth = true) {
    const config = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (requireAuth && authToken) {
        config.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        
        if (response.status === 401) {
            logout();
            return null;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API调用失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API调用错误:', error);
        showAlert(error.message, 'danger');
        return null;
    }
}

// 认证相关函数
async function login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error('用户名或密码错误');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        sessionStorage.setItem('authToken', authToken);
        
        // 获取用户信息
        const userInfo = await apiCall('/auth/me');
        if (userInfo) {
            currentUser = userInfo;
            sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
            showMainContent();
            loadDashboard();
            showAlert('登录成功！', 'success');
        }
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('currentUser');
    showLoginForm();
}

function checkAuth() {
    const token = sessionStorage.getItem('authToken');
    const user = sessionStorage.getItem('currentUser');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        showMainContent();
        loadDashboard();
    } else {
        showLoginForm();
    }
}

// UI显示函数
function showLoginForm() {
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('main-content').style.display = 'none';
}

function showMainContent() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('main-content').style.display = 'block';
    document.getElementById('current-user').textContent = currentUser.username;
    
    // 显示/隐藏管理员菜单
    if (currentUser.is_admin) {
        document.getElementById('admin-menu').style.display = 'block';
    }
}

function showSection(sectionId) {
    // 隐藏所有section
    document.querySelectorAll('[id$="-section"]').forEach(section => {
        section.style.display = 'none';
    });
    
    // 显示指定section
    document.getElementById(sectionId).style.display = 'block';
    
    // 更新导航状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
}

// 仪表盘相关函数
async function loadDashboard() {
    showSection('dashboard-section');
    document.getElementById('dashboard-link').classList.add('active');
    
    await refreshDashboardData();
}

async function refreshDashboardData() {
    try {
        const stats = await apiCall('/dashboard/stats');
        if (stats) {
            document.getElementById('monthly-due-count').textContent = stats.monthly_due_count;
            document.getElementById('overdue-count').textContent = stats.overdue_count;
            document.getElementById('inactive-count').textContent = stats.inactive_count;
            document.getElementById('category-count').textContent = stats.category_distribution.length;
            
            // 绘制图表
            drawCategoryChart(stats.category_distribution);
        }
        
        // 加载当月待检设备列表
        await loadMonthlyDueEquipments();
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }
}

async function loadMonthlyDueEquipments() {
    try {
        console.log('开始加载当月待检设备...');
        const equipments = await apiCall('/dashboard/monthly-due-equipments');
        console.log('当月待检设备API响应:', equipments);
        if (equipments) {
            renderMonthlyDueTable(equipments);
        } else {
            console.error('未获取到设备数据');
            const tbody = document.getElementById('monthly-due-tbody');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            <i class="bi bi-exclamation-triangle"></i> 加载失败
                        </td>
                    </tr>
                `;
            }
        }
    } catch (error) {
        console.error('加载当月待检设备失败:', error);
        const tbody = document.getElementById('monthly-due-tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="bi bi-exclamation-triangle"></i> 加载失败: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

function renderMonthlyDueTable(equipments) {
    const tbody = document.getElementById('monthly-due-tbody');
    tbody.innerHTML = '';
    
    if (equipments.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="6" class="text-center text-muted">
                <i class="bi bi-check-circle"></i> 本月无待检设备
            </td>
        `;
        tbody.appendChild(row);
        
        // 触发庆祝效果
        showCelebration();
        return;
    }
    
    equipments.forEach(equipment => {
        const row = document.createElement('tr');
        
        // 本月待检设备统一使用黄色背景
        row.classList.add('equipment-due-soon');
        
        row.innerHTML = `
            <td>${equipment.serial_number}</td>
            <td>${equipment.name}</td>
            <td>${equipment.department.name}</td>
            <td>${equipment.category.name}</td>
            <td>${formatDate(equipment.next_calibration_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-success" onclick="updateCalibrationDate(${equipment.id})" title="更新检定日期">
                        <i class="bi bi-calendar-check"></i>
                    </button>
                    <button class="btn btn-outline-warning" onclick="editEquipment(${equipment.id})" title="编辑设备">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function drawCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: [
                    '#FF3B30', // 鲜红
                    '#FF9500', // 橙
                    '#FFCC00', // 亮黄
                    '#34C759', // 鲜绿
                    '#30B0FF', // 亮蓝
                    '#AF52DE', // 紫
                    '#5856D6', // 深蓝紫
                    '#5AC8FA', // 天蓝
                    '#4CD964', // 青绿
                    '#FFD60A', // 金黄
                    '#FF375F', // 粉红
                    '#FF9F0A', // 橙黄
                    '#32D74B', // 草绿
                    '#64D2FF', // 浅蓝
                    '#BF5AF2', // 亮紫
                    '#D1D1D6', // 灰
                    '#FFB6B9', // 浅粉
                    '#B5EAD7', // 浅绿
                    '#C7CEEA', // 浅紫
                    '#FFD6A5', // 浅橙
                    '#A0CED9', // 天蓝
                    '#B5B9FF', // 浅蓝紫
                    '#77DD77', // 草绿
                    '#FF6961'  // 鲜红
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: 0
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        // padding: 2,
                        // font: {
                        //     size: 8
                        // }
                    }
                }
            },
            // cutout: '20%'  // 调整内圈大小，让圆环更粗，视觉上更大
        }
    });
}

// 设备管理相关函数
let sortDirection = {}; // 存储各列的排序方向

async function loadEquipmentSection() {
    showSection('equipment-section');
    document.getElementById('equipment-link').classList.add('active');
    
    // 加载筛选选项
    await loadFilterOptions();
    // 加载设备列表，默认显示在用状态
    await loadEquipmentList();
}

async function loadFilterOptions() {
    try {
        // 加载部门选项
        const departments = await apiCall('/departments/');
        const departmentSelect = document.getElementById('filter-department');
        departmentSelect.innerHTML = '<option value="">全部部门</option>';
        departments.forEach(dept => {
            departmentSelect.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
        });
        
        // 加载设备类别选项
        const categories = await apiCall('/categories/');
        const categorySelect = document.getElementById('filter-category');
        categorySelect.innerHTML = '<option value="">全部类别</option>';
        categories.forEach(cat => {
            categorySelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
        });
    } catch (error) {
        console.error('加载筛选选项失败:', error);
    }
}

async function loadEquipmentList(filters = {}, page = 1) {
    try {
        let response;
        const skip = (page - 1) * ITEMS_PER_PAGE;
        
        // 获取筛选器的值，如果没有提供filters或filters为undefined，则使用当前筛选器的值
        if (!filters || Object.keys(filters).length === 0) {
            filters = getFilterValues();
        }
        
        if (Object.keys(filters).length > 0) {
            const params = new URLSearchParams({
                skip: skip,
                limit: ITEMS_PER_PAGE
            });
            response = await apiCall(`/equipment/filter?${params.toString()}`, 'POST', filters);
        } else {
            response = await apiCall(`/equipment/?skip=${skip}&limit=${ITEMS_PER_PAGE}`);
        }
        
        if (response) {
            currentEquipments = response.items; // 保存当前设备列表用于排序
            currentPagination = {
                total: response.total,
                skip: response.skip,
                limit: response.limit,
                page: page
            };
            renderEquipmentTable(response.items);
            renderPagination('equipment', currentPagination);
        }
    } catch (error) {
        console.error('加载设备列表失败:', error);
    }
}

function sortEquipmentTable(column) {
    if (!currentEquipments || currentEquipments.length === 0) return;
    
    // 确定排序方向
    const currentDirection = sortDirection[column] || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    sortDirection[column] = newDirection;
    
    // 排序设备列表
    const sortedEquipments = [...currentEquipments].sort((a, b) => {
        let valueA, valueB;
        
        switch(column) {
            case 'name':
                valueA = a.name;
                valueB = b.name;
                break;
            case 'department':
                valueA = a.department.name;
                valueB = b.department.name;
                break;
            case 'category':
                valueA = a.category.name;
                valueB = b.category.name;
                break;
            case 'next_calibration_date':
                valueA = new Date(a.next_calibration_date);
                valueB = new Date(b.next_calibration_date);
                break;
            default:
                return 0;
        }
        
        // 处理日期比较
        if (valueA instanceof Date && valueB instanceof Date) {
            return newDirection === 'asc' ? valueA - valueB : valueB - valueA;
        }
        
        // 处理字符串比较
        const comparison = valueA.localeCompare(valueB, 'zh-CN');
        return newDirection === 'asc' ? comparison : -comparison;
    });
    
    // 更新排序图标
    updateSortIcons(column, newDirection);
    
    // 重新渲染表格
    renderEquipmentTable(sortedEquipments);
}

function updateSortIcons(activeColumn, direction) {
    // 重置所有排序图标
    document.querySelectorAll('#equipment-table th i').forEach(icon => {
        icon.className = 'bi bi-arrow-down-up';
    });
    
    // 更新当前列的排序图标
    const activeHeader = document.querySelector(`th[onclick="sortEquipmentTable('${activeColumn}')"] i`);
    if (activeHeader) {
        activeHeader.className = direction === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    }
}

function renderEquipmentTable(equipments) {
    const tbody = document.getElementById('equipment-tbody');
    tbody.innerHTML = '';
    
    equipments.forEach(equipment => {
        const row = document.createElement('tr');
        
        // 根据检定日期添加样式
        if (isDateOverdue(equipment.next_calibration_date)) {
            row.classList.add('equipment-overdue');
        } else if (isDateDueSoon(equipment.next_calibration_date)) {
            row.classList.add('equipment-due-soon');
        }
        
        row.innerHTML = `
            <td>
                <input type="checkbox" class="equipment-checkbox" value="${equipment.id}" onchange="updateSelectedCount()">
            </td>
            <td>${equipment.serial_number}</td>
            <td>${equipment.name}</td>
            <td>${equipment.department.name}</td>
            <td>${equipment.category.name}</td>
            <td>${equipment.model}</td>
            <td>${formatDate(equipment.next_calibration_date)}</td>
            <td>
                <span class="badge status-${equipment.status}">${equipment.status}</span>
                ${equipment.status !== '在用' && equipment.status_change_date ? 
                    `<br><small class="text-muted">${formatDate(equipment.status_change_date)}</small>` : ''}
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-success" onclick="updateCalibrationDate(${equipment.id})" title="更新检定日期">
                        <i class="bi bi-calendar-check"></i>
                    </button>
                    <button class="btn btn-outline-warning" onclick="editEquipment(${equipment.id})" title="编辑设备">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteEquipment(${equipment.id})" title="删除设备">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// 批量选择功能
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const equipmentCheckboxes = document.querySelectorAll('.equipment-checkbox');
    
    equipmentCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.equipment-checkbox:checked');
    const count = selectedCheckboxes.length;
    const selectedCountSpan = document.getElementById('selected-count');
    const batchOperations = document.getElementById('batch-operations');
    
    if (selectedCountSpan) {
        selectedCountSpan.textContent = count;
    }
    
    if (batchOperations) {
        batchOperations.style.display = count > 0 ? 'block' : 'none';
    }
    
    // 更新全选复选框状态
    const selectAllCheckbox = document.getElementById('select-all');
    const allCheckboxes = document.querySelectorAll('.equipment-checkbox');
    if (selectAllCheckbox && allCheckboxes.length > 0) {
        if (count === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (count === allCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
            selectAllCheckbox.checked = false;
        }
    }
}

// 分页功能
function renderPagination(type, pagination) {
    const totalPages = Math.ceil(pagination.total / pagination.limit);
    const container = document.getElementById(`${type}-pagination`);
    
    if (!container || pagination.total === 0) {
        if (container) container.style.display = 'none';
        return;
    }
    
    container.className = 'd-flex justify-content-between align-items-center mt-3';
    container.style.display = 'flex';
    
    let paginationHtml = `
        <div class="text-muted">
            显示 ${pagination.skip + 1}-${Math.min(pagination.skip + pagination.limit, pagination.total)} 条，共 ${pagination.total} 条
        </div>
        <nav>
            <ul class="pagination mb-0">
                <li class="page-item ${pagination.page === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage('${type}', ${pagination.page - 1}); return false;">上一页</a>
                </li>
    `;
    
    // 显示页码
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(totalPages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage('${type}', ${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    paginationHtml += `
                <li class="page-item ${pagination.page === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage('${type}', ${pagination.page + 1}); return false;">下一页</a>
                </li>
            </ul>
        </nav>
    `;
    
    container.innerHTML = paginationHtml;
}

function changePage(type, page) {
    if (type === 'equipment') {
        // 不传递空对象，让loadEquipmentList使用当前的筛选器值
        loadEquipmentList(undefined, page);
    } else if (type === 'audit') {
        loadAuditLogs({}, page);
    }
}

function clearSelection() {
    const checkboxes = document.querySelectorAll('.equipment-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = false);
    document.getElementById('select-all').checked = false;
    updateSelectedCount();
}

function getSelectedEquipmentIds() {
    const selectedCheckboxes = document.querySelectorAll('.equipment-checkbox:checked');
    return Array.from(selectedCheckboxes).map(checkbox => parseInt(checkbox.value));
}

// 批量更新检定日期
function showBatchUpdateCalibrationModal() {
    const selectedIds = getSelectedEquipmentIds();
    if (selectedIds.length === 0) {
        showAlert('请先选择要更新的设备', 'warning');
        return;
    }
    
    const modalHtml = `
        <div class="modal fade" id="batchUpdateCalibrationModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">批量更新检定日期</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="batch-update-calibration-form">
                            <div class="mb-3">
                                <label class="form-label">新的检定日期 *</label>
                                <input type="date" class="form-control" name="calibration_date" required>
                                <div class="form-text">将为选中的 ${selectedIds.length} 台设备更新检定日期，并自动计算下次检定日期</div>
                            </div>
                            <div class="alert alert-info">
                                <strong>注意：</strong>此操作将同时更新所有选中设备的检定日期和下次检定日期。
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitBatchUpdateCalibration()">更新</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('batchUpdateCalibrationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('#batchUpdateCalibrationModal input[name="calibration_date"]').value = today;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('batchUpdateCalibrationModal'));
    modal.show();
}

async function submitBatchUpdateCalibration() {
    const form = document.getElementById('batch-update-calibration-form');
    const formData = new FormData(form);
    const calibrationDate = formData.get('calibration_date');
    
    if (!calibrationDate) {
        showAlert('请选择检定日期', 'warning');
        return;
    }
    
    const selectedIds = getSelectedEquipmentIds();
    
    try {
        const result = await apiCall('/equipment/batch/update-calibration', 'POST', {
            equipment_ids: selectedIds,
            calibration_date: calibrationDate
        });
        
        if (result) {
            showAlert(`批量更新成功！更新了 ${result.success_count} 台设备的检定日期`, 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchUpdateCalibrationModal'));
            modal.hide();
            clearSelection();
            loadEquipmentList();
            refreshDashboardData(); // 只刷新仪表盘数据，不切换页面
        }
    } catch (error) {
        showAlert('批量更新失败：' + error.message, 'danger');
    }
}

// 批量变更状态
function showBatchChangeStatusModal() {
    const selectedIds = getSelectedEquipmentIds();
    if (selectedIds.length === 0) {
        showAlert('请先选择要变更状态的设备', 'warning');
        return;
    }
    
    const modalHtml = `
        <div class="modal fade" id="batchChangeStatusModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">批量变更设备状态</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="batch-change-status-form">
                            <div class="mb-3">
                                <label class="form-label">新状态 *</label>
                                <select class="form-select" name="status" onchange="toggleBatchStatusChangeDate(this)" required>
                                    <option value="">请选择状态</option>
                                    <option value="在用">在用</option>
                                    <option value="停用">停用</option>
                                    <option value="报废">报废</option>
                                </select>
                            </div>
                            <div class="mb-3" id="batch-status-change-date" style="display: none;">
                                <label class="form-label">状态变更时间 *</label>
                                <input type="date" class="form-control" name="status_change_date">
                                <div class="form-text">停用或报废状态时必填</div>
                            </div>
                            <div class="alert alert-info">
                                <strong>将变更 ${selectedIds.length} 台设备的状态</strong>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitBatchChangeStatus()">变更</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('batchChangeStatusModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('batchChangeStatusModal'));
    modal.show();
}

function toggleBatchStatusChangeDate(selectElement) {
    const value = selectElement.value;
    const container = document.getElementById('batch-status-change-date');
    const input = container.querySelector('input[name="status_change_date"]');
    
    if (value === '停用' || value === '报废') {
        container.style.display = 'block';
        input.required = true;
        // 设置默认值为今天
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    } else {
        container.style.display = 'none';
        input.required = false;
        input.value = '';
    }
}

async function submitBatchChangeStatus() {
    const form = document.getElementById('batch-change-status-form');
    const formData = new FormData(form);
    const status = formData.get('status');
    const statusChangeDate = formData.get('status_change_date');
    
    if (!status) {
        showAlert('请选择状态', 'warning');
        return;
    }
    
    if ((status === '停用' || status === '报废') && !statusChangeDate) {
        showAlert('停用或报废状态时，状态变更时间为必填项', 'warning');
        return;
    }
    
    const selectedIds = getSelectedEquipmentIds();
    const requestData = {
        equipment_ids: selectedIds,
        status: status
    };
    
    if (statusChangeDate) {
        requestData.status_change_date = statusChangeDate;
    }
    
    try {
        const result = await apiCall('/equipment/batch/change-status', 'POST', requestData);
        
        if (result) {
            showAlert(`批量状态变更成功！更新了 ${result.success_count} 台设备的状态`, 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchChangeStatusModal'));
            modal.hide();
            clearSelection();
            loadEquipmentList();
            refreshDashboardData(); // 只刷新仪表盘数据，不切换页面
        }
    } catch (error) {
        showAlert('批量状态变更失败：' + error.message, 'danger');
    }
}

// 导出功能
async function exportMonthlyPlan() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 2; // 下个月
    
    try {
        const response = await fetch(`${API_BASE}/equipment/export/monthly-plan?year=${year}&month=${month}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${year}年${month}月检定计划.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('导出成功！', 'success');
        }
    } catch (error) {
        showAlert('导出失败：' + error.message, 'danger');
    }
}

async function exportFiltered() {
    const filters = getFilterValues();
    
    try {
        const response = await fetch(`${API_BASE}/equipment/export/filtered`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filters)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `设备台账_${new Date().toISOString().slice(0, 10)}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('导出成功！', 'success');
        }
    } catch (error) {
        showAlert('导出失败：' + error.message, 'danger');
    }
}

function getFilterValues() {
    const filters = {};
    
    const departmentId = document.getElementById('filter-department').value;
    if (departmentId) filters.department_id = parseInt(departmentId);
    
    const categoryId = document.getElementById('filter-category').value;
    if (categoryId) filters.category_id = parseInt(categoryId);
    
    const status = document.getElementById('filter-status').value;
    if (status) {
        filters.status = status;
    }
    
    const startDate = document.getElementById('filter-start-date').value;
    if (startDate) filters.next_calibration_start = startDate;
    
    const endDate = document.getElementById('filter-end-date').value;
    if (endDate) filters.next_calibration_end = endDate;
    
    return filters;
}

// 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 检查认证状态
    checkAuth();
    
    // 登录表单提交
    document.getElementById('login-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        login(username, password);
    });
    
    // 导航链接
    document.getElementById('dashboard-link').addEventListener('click', function(e) {
        e.preventDefault();
        loadDashboard();
    });
    
    document.getElementById('equipment-link').addEventListener('click', function(e) {
        e.preventDefault();
        loadEquipmentSection();
    });
    
    // 退出登录
    document.getElementById('logout-link').addEventListener('click', function(e) {
        e.preventDefault();
        logout();
    });
    
    // 筛选表单
    document.getElementById('filter-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const filters = getFilterValues();
        loadEquipmentList(filters);
    });
    
    // 清除筛选
    document.getElementById('clear-filter').addEventListener('click', function() {
        document.getElementById('filter-form').reset();
        loadEquipmentList();
    });
    
    // 导出按钮
    document.getElementById('export-monthly-btn').addEventListener('click', exportMonthlyPlan);
    document.getElementById('export-filtered').addEventListener('click', exportFiltered);
    
    // 添加设备按钮
    document.getElementById('add-equipment-btn').addEventListener('click', function() {
        loadEquipmentSection();
        showAddEquipmentModal();
    });
    
    document.getElementById('add-equipment-modal-btn').addEventListener('click', showAddEquipmentModal);
    
    // 导入数据按钮
    document.getElementById('import-data-btn').addEventListener('click', showImportDataModal);
    
    // 下载模板按钮
    document.getElementById('download-template-btn').addEventListener('click', downloadImportTemplate);
    
    // 系统管理链接
    const usersLink = document.getElementById('users-link');
    const categoriesLink = document.getElementById('categories-link');
    const departmentsLink = document.getElementById('departments-link');
    const auditLink = document.getElementById('audit-link');
    
    if (usersLink) {
        usersLink.addEventListener('click', function(e) {
            e.preventDefault();
            loadUsersSection();
        });
    }
    
    if (categoriesLink) {
        categoriesLink.addEventListener('click', function(e) {
            e.preventDefault();
            loadCategoriesSection();
        });
    }
    
    if (departmentsLink) {
        departmentsLink.addEventListener('click', function(e) {
            e.preventDefault();
            loadDepartmentsSection();
        });
    }
    
    if (auditLink) {
        auditLink.addEventListener('click', function(e) {
            e.preventDefault();
            loadAuditSection();
        });
    }
    
    // 添加用户按钮
    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', showAddUserModal);
    }
    
    // 添加设备类别按钮
    const addCategoryBtn = document.getElementById('add-category-btn');
    if (addCategoryBtn) {
        addCategoryBtn.addEventListener('click', showAddCategoryModal);
    }
    
    // 添加部门按钮
    const addDepartmentBtn = document.getElementById('add-department-btn');
    if (addDepartmentBtn) {
        addDepartmentBtn.addEventListener('click', showAddDepartmentModal);
    }
    
    // 操作日志筛选表单
    const auditFilterForm = document.getElementById('audit-filter-form');
    if (auditFilterForm) {
        auditFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const filters = getAuditFilterValues();
            loadAuditLogs(filters, 1);
        });
    }
    
    // 清除操作日志筛选
    const clearAuditFilter = document.getElementById('clear-audit-filter');
    if (clearAuditFilter) {
        clearAuditFilter.addEventListener('click', function() {
            document.getElementById('audit-filter-form').reset();
            loadAuditLogs({}, 1);
        });
    }
    
    // 批量操作按钮事件监听
    const batchUpdateCalibrationBtn = document.getElementById('batch-update-calibration');
    if (batchUpdateCalibrationBtn) {
        batchUpdateCalibrationBtn.addEventListener('click', showBatchUpdateCalibrationModal);
    }
    
    const batchChangeStatusBtn = document.getElementById('batch-change-status');
    if (batchChangeStatusBtn) {
        batchChangeStatusBtn.addEventListener('click', showBatchChangeStatusModal);
    }
    
    const clearSelectionBtn = document.getElementById('clear-selection');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', clearSelection);
    }
});

// 设备操作函数
async function editEquipment(id) {
    try {
        const equipment = await apiCall(`/equipment/${id}`);
        if (equipment) {
            showEditEquipmentModal(equipment);
        }
    } catch (error) {
        showAlert('获取设备信息失败：' + error.message, 'danger');
    }
}

function showEditEquipmentModal(equipment) {
    const modalHtml = `
        <div class="modal fade" id="editEquipmentModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">编辑设备</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-equipment-form">
                            <input type="hidden" name="equipment_id" value="${equipment.id}">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备名称 *</label>
                                    <input type="text" class="form-control" name="name" value="${equipment.name}" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">计量编号 *</label>
                                    <input type="text" class="form-control" name="serial_number" value="${equipment.serial_number}" required>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">部门 *</label>
                                    <select class="form-select" name="department_id" required>
                                        <option value="">请选择部门</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备类别 *</label>
                                    <select class="form-select" name="category_id" required>
                                        <option value="">请选择类别</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">型号/规格</label>
                                    <input type="text" class="form-control" name="model" value="${equipment.model || ''}">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">准确度等级</label>
                                    <input type="text" class="form-control" name="accuracy_level" value="${equipment.accuracy_level || ''}">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">测量范围</label>
                                    <input type="text" class="form-control" name="measurement_range" value="${equipment.measurement_range || ''}">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">制造厂家</label>
                                    <input type="text" class="form-control" name="manufacturer" value="${equipment.manufacturer || ''}">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">检定周期 *</label>
                                    <select class="form-select" name="calibration_cycle" required>
                                        <option value="">请选择检定周期</option>
                                        <option value="1年" ${equipment.calibration_cycle === '1年' ? 'selected' : ''}>1年</option>
                                        <option value="2年" ${equipment.calibration_cycle === '2年' ? 'selected' : ''}>2年</option>
                                    </select>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">检定日期 *</label>
                                    <input type="date" class="form-control" name="calibration_date" 
                                           value="${equipment.calibration_date}" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">出厂日期</label>
                                    <input type="date" class="form-control" name="manufacture_date" 
                                           value="${equipment.manufacture_date || ''}">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">安装地点</label>
                                    <input type="text" class="form-control" name="installation_location" 
                                           value="${equipment.installation_location || ''}">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">检定方式</label>
                                    <select class="form-select" name="calibration_method">
                                        <option value="内部检定" ${equipment.calibration_method === '内部检定' ? 'selected' : ''}>内部检定</option>
                                        <option value="外部检定" ${equipment.calibration_method === '外部检定' ? 'selected' : ''}>外部检定</option>
                                        <option value="校准" ${equipment.calibration_method === '校准' ? 'selected' : ''}>校准</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备状态</label>
                                    <select class="form-select" name="status" onchange="toggleStatusChangeDate(this, 'edit')">
                                        <option value="在用" ${equipment.status === '在用' ? 'selected' : ''}>在用</option>
                                        <option value="停用" ${equipment.status === '停用' ? 'selected' : ''}>停用</option>
                                        <option value="报废" ${equipment.status === '报废' ? 'selected' : ''}>报废</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3" id="edit-status-change-date" style="display: ${equipment.status !== '在用' ? 'block' : 'none'};">
                                    <label class="form-label">状态变更时间 ${equipment.status !== '在用' ? '*' : ''}</label>
                                    <input type="date" class="form-control" name="status_change_date" 
                                           value="${equipment.status_change_date ? equipment.status_change_date.split('T')[0] : ''}" 
                                           ${equipment.status !== '在用' ? 'required' : ''}>
                                    <div class="form-text">停用或报废状态时必填</div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">备注</label>
                                <textarea class="form-control" name="notes" rows="3">${equipment.notes || ''}</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitEditEquipment()">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('editEquipmentModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 加载部门和类别选项
    loadEditEquipmentOptions(equipment);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('editEquipmentModal'));
    modal.show();
}

async function loadEditEquipmentOptions(equipment) {
    try {
        // 加载部门选项
        const departments = await apiCall('/departments/');
        const departmentSelect = document.querySelector('#editEquipmentModal select[name="department_id"]');
        if (departments && departmentSelect) {
            departmentSelect.innerHTML = '<option value="">请选择部门</option>';
            departments.forEach(dept => {
                const selected = dept.id === equipment.department_id ? 'selected' : '';
                departmentSelect.innerHTML += `<option value="${dept.id}" ${selected}>${dept.name}</option>`;
            });
        }
        
        // 加载设备类别选项
        const categories = await apiCall('/categories/');
        const categorySelect = document.querySelector('#editEquipmentModal select[name="category_id"]');
        if (categories && categorySelect) {
            categorySelect.innerHTML = '<option value="">请选择类别</option>';
            categories.forEach(cat => {
                const selected = cat.id === equipment.category_id ? 'selected' : '';
                categorySelect.innerHTML += `<option value="${cat.id}" ${selected}>${cat.name}</option>`;
            });
        }
    } catch (error) {
        console.error('加载选项失败:', error);
    }
}

async function submitEditEquipment() {
    const form = document.getElementById('edit-equipment-form');
    const formData = new FormData(form);
    
    const equipmentData = {};
    for (const [key, value] of formData.entries()) {
        if (key !== 'equipment_id') {
            // 对于状态变更时间，即使为空也要包含在数据中
            if (key === 'status_change_date' || value !== '') {
                if (key === 'department_id' || key === 'category_id') {
                    equipmentData[key] = parseInt(value);
                } else {
                    equipmentData[key] = value;
                }
            }
        }
    }
    
    // 验证状态变更时间
    if ((equipmentData.status === '停用' || equipmentData.status === '报废') && !equipmentData.status_change_date) {
        showAlert('停用或报废状态时，状态变更时间为必填项', 'warning');
        return;
    }
    
    const equipmentId = formData.get('equipment_id');
    
    try {
        const result = await apiCall(`/equipment/${equipmentId}`, 'PUT', equipmentData);
        if (result) {
            showAlert('设备更新成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editEquipmentModal'));
            modal.hide();
            loadEquipmentList();
            refreshDashboardData(); // 只刷新仪表盘数据，不切换页面
        }
    } catch (error) {
        showAlert('更新设备失败：' + error.message, 'danger');
    }
}

async function updateCalibrationDate(id) {
    const modalHtml = `
        <div class="modal fade" id="updateCalibrationModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">更新检定日期</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="update-calibration-form">
                            <input type="hidden" name="equipment_id" value="${id}">
                            <div class="mb-3">
                                <label class="form-label">新的检定日期 *</label>
                                <input type="date" class="form-control" name="calibration_date" required>
                                <div class="form-text">更新检定日期将自动计算下次检定日期</div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-success" onclick="submitUpdateCalibration()">更新</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('updateCalibrationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('#updateCalibrationModal input[name="calibration_date"]').value = today;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('updateCalibrationModal'));
    modal.show();
}

async function submitUpdateCalibration() {
    const form = document.getElementById('update-calibration-form');
    const formData = new FormData(form);
    
    const equipmentId = formData.get('equipment_id');
    const calibrationDate = formData.get('calibration_date');
    
    if (!calibrationDate) {
        showAlert('请选择检定日期', 'warning');
        return;
    }
    
    try {
        const result = await apiCall(`/equipment/${equipmentId}`, 'PUT', {
            calibration_date: calibrationDate
        });
        
        if (result) {
            showAlert('检定日期更新成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('updateCalibrationModal'));
            modal.hide();
            loadEquipmentList();
            refreshDashboardData(); // 只刷新仪表盘数据，不切换页面
        }
    } catch (error) {
        showAlert('更新检定日期失败：' + error.message, 'danger');
    }
}

async function deleteEquipment(id) {
    if (confirm('确定要删除这个设备吗？')) {
        try {
            const result = await apiCall(`/equipment/${id}`, 'DELETE');
            if (result) {
                showAlert('设备删除成功！', 'success');
                loadEquipmentList();
            }
        } catch (error) {
            showAlert('删除设备失败：' + error.message, 'danger');
        }
    }
}

// 添加设备模态框
function showAddEquipmentModal() {
    // 创建模态框HTML
    const modalHtml = `
        <div class="modal fade" id="addEquipmentModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加设备</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-equipment-form">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备名称 *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">计量编号 *</label>
                                    <input type="text" class="form-control" name="serial_number" required>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">部门 *</label>
                                    <select class="form-select" name="department_id" required>
                                        <option value="">请选择部门</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备类别 *</label>
                                    <select class="form-select" name="category_id" required>
                                        <option value="">请选择类别</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">型号/规格</label>
                                    <input type="text" class="form-control" name="model">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">准确度等级</label>
                                    <input type="text" class="form-control" name="accuracy_level">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">测量范围</label>
                                    <input type="text" class="form-control" name="measurement_range">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">制造厂家</label>
                                    <input type="text" class="form-control" name="manufacturer">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">检定周期 *</label>
                                    <select class="form-select" name="calibration_cycle" required>
                                        <option value="">请选择检定周期</option>
                                        <option value="1年">1年</option>
                                        <option value="2年">2年</option>
                                    </select>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">检定日期 *</label>
                                    <input type="date" class="form-control" name="calibration_date" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">出厂日期</label>
                                    <input type="date" class="form-control" name="manufacture_date">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">安装地点</label>
                                    <input type="text" class="form-control" name="installation_location">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">检定方式</label>
                                    <select class="form-select" name="calibration_method">
                                        <option value="内部检定">内部检定</option>
                                        <option value="外部检定">外部检定</option>
                                        <option value="校准">校准</option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">设备状态</label>
                                    <select class="form-select" name="status" onchange="toggleStatusChangeDate(this, 'add')">
                                        <option value="在用">在用</option>
                                        <option value="停用">停用</option>
                                        <option value="报废">报废</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3" id="add-status-change-date" style="display: none;">
                                    <label class="form-label">状态变更时间 *</label>
                                    <input type="date" class="form-control" name="status_change_date">
                                    <div class="form-text">停用或报废状态时必填</div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">备注</label>
                                <textarea class="form-control" name="notes" rows="3"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitAddEquipment()">添加</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('addEquipmentModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 加载部门和类别选项
    loadAddEquipmentOptions();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('addEquipmentModal'));
    modal.show();
}

async function loadAddEquipmentOptions() {
    try {
        // 加载部门选项
        const departments = await apiCall('/departments/');
        const departmentSelect = document.querySelector('#addEquipmentModal select[name="department_id"]');
        if (departments && departmentSelect) {
            departmentSelect.innerHTML = '<option value="">请选择部门</option>';
            departments.forEach(dept => {
                departmentSelect.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
            });
        }
        
        // 加载设备类别选项
        const categories = await apiCall('/categories/');
        const categorySelect = document.querySelector('#addEquipmentModal select[name="category_id"]');
        if (categories && categorySelect) {
            categorySelect.innerHTML = '<option value="">请选择类别</option>';
            categories.forEach(cat => {
                categorySelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
            });
        }
    } catch (error) {
        console.error('加载选项失败:', error);
    }
}

// 状态变更时间显示控制
function toggleStatusChangeDate(selectElement, formType) {
    const value = selectElement.value;
    const container = document.getElementById(`${formType}-status-change-date`);
    const input = container.querySelector('input[name="status_change_date"]');
    const label = container.querySelector('label');
    
    if (value === '停用' || value === '报废') {
        container.style.display = 'block';
        input.required = true;
        label.textContent = '状态变更时间 *';
        // 只在添加设备时且没有值时设置为今天，编辑时不覆盖原有值
        if (!input.value && formType === 'add') {
            input.value = new Date().toISOString().split('T')[0];
        }
    } else {
        container.style.display = 'none';
        input.required = false;
        // 只在添加模式下清空值，编辑模式下保留原值以便用户参考
        if (formType === 'add') {
            input.value = '';
        }
        label.textContent = '状态变更时间';
    }
}

async function submitAddEquipment() {
    const form = document.getElementById('add-equipment-form');
    const formData = new FormData(form);
    
    const equipmentData = {};
    for (const [key, value] of formData.entries()) {
        if (value !== '') {
            if (key === 'department_id' || key === 'category_id') {
                equipmentData[key] = parseInt(value);
            } else {
                equipmentData[key] = value;
            }
        }
    }
    
    // 验证必填字段
    const requiredFields = ['name', 'serial_number', 'department_id', 'category_id', 'model', 'accuracy_level', 'calibration_cycle', 'calibration_date'];
    const missingFields = [];
    
    for (const field of requiredFields) {
        if (!equipmentData[field]) {
            missingFields.push(field);
        }
    }
    
    // 验证状态变更时间
    if ((equipmentData.status === '停用' || equipmentData.status === '报废') && !equipmentData.status_change_date) {
        showAlert('停用或报废状态时，状态变更时间为必填项', 'warning');
        return;
    }
    
    if (missingFields.length > 0) {
        showAlert('请填写所有必填字段', 'warning');
        return;
    }
    
    try {
        const result = await apiCall('/equipment/', 'POST', equipmentData);
        if (result) {
            showAlert('设备添加成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addEquipmentModal'));
            modal.hide();
            loadEquipmentList();
        }
    } catch (error) {
        showAlert('添加设备失败：' + error.message, 'danger');
    }
}

// 导入数据模态框
function showImportDataModal() {
    const modalHtml = `
        <div class="modal fade" id="importDataModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">导入数据</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="import-form">
                            <div class="mb-3">
                                <label class="form-label">选择Excel文件</label>
                                <input type="file" class="form-control" accept=".xlsx,.xls" required>
                                <div class="form-text">支持.xlsx和.xls格式文件</div>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="overwrite-check">
                                    <label class="form-check-label" for="overwrite-check">
                                        覆盖重复数据
                                    </label>
                                    <div class="form-text">如果勾选此选项，当计量编号重复时将更新现有设备数据</div>
                                </div>
                            </div>
                            <div class="alert alert-info">
                                <small>
                                    <strong>注意：</strong><br>
                                    1. 请确保Excel文件包含正确的列标题<br>
                                    2. 必填字段：设备名称、计量编号、部门、设备类别、检定周期、检定日期<br>
                                    3. 日期格式：YYYY-MM-DD<br>
                                    4. 检定周期只能填写：1年 或 2年
                                </small>
                            </div>
                            <div class="mb-3">
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="downloadImportTemplate()">
                                    <i class="bi bi-download"></i> 下载导入模板
                                </button>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitImportData()">导入</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('importDataModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('importDataModal'));
    modal.show();
}

async function submitImportData() {
    const fileInput = document.querySelector('#importDataModal input[type="file"]');
    const overwriteCheck = document.getElementById('overwrite-check');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('请选择要导入的文件', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('overwrite', overwriteCheck.checked);
    
    try {
        const response = await fetch(`${API_BASE}/import/upload?overwrite=${overwriteCheck.checked}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showImportResultModal(result);
            const modal = bootstrap.Modal.getInstance(document.getElementById('importDataModal'));
            modal.hide();
            loadEquipmentList();
            refreshDashboardData(); // 只刷新仪表盘数据，不切换页面
        } else {
            const error = await response.json();
            showAlert('导入失败：' + error.detail, 'danger');
        }
    } catch (error) {
        showAlert('导入失败：' + error.message, 'danger');
    }
}

function showImportResultModal(result) {
    const modalHtml = `
        <div class="modal fade" id="importResultModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">导入结果</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card text-white bg-success">
                                    <div class="card-body text-center">
                                        <h5>新增</h5>
                                        <h3>${result.success_count}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-info">
                                    <div class="card-body text-center">
                                        <h5>更新</h5>
                                        <h3>${result.update_count}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-danger">
                                    <div class="card-body text-center">
                                        <h5>失败</h5>
                                        <h3>${result.error_count}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-secondary">
                                    <div class="card-body text-center">
                                        <h5>成功率</h5>
                                        <h3>${result.summary.success_rate}%</h3>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        <th>行号</th>
                                        <th>计量编号</th>
                                        <th>设备名称</th>
                                        <th>状态</th>
                                        <th>说明</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.detailed_results.map(item => `
                                        <tr class="${getStatusRowClass(item.status)}">
                                            <td>${item.row}</td>
                                            <td>${item.serial_number}</td>
                                            <td>${item.name}</td>
                                            <td>
                                                <span class="badge ${getStatusBadgeClass(item.status)}">${item.status}</span>
                                            </td>
                                            <td>${item.message}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">确定</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的模态框
    const existingModal = document.getElementById('importResultModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('importResultModal'));
    modal.show();
}

function getStatusRowClass(status) {
    switch(status) {
        case '成功': return 'table-success';
        case '更新': return 'table-info';
        case '失败': return 'table-danger';
        case '跳过': return 'table-warning';
        default: return '';
    }
}

function getStatusBadgeClass(status) {
    switch(status) {
        case '成功': return 'bg-success';
        case '更新': return 'bg-info';
        case '失败': return 'bg-danger';
        case '跳过': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

// 下载导入模板
async function downloadImportTemplate() {
    try {
        const response = await fetch(`${API_BASE}/import/template/download`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '设备台账导入模板.xlsx';
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('模板下载成功！', 'success');
        } else {
            showAlert('模板下载失败', 'danger');
        }
    } catch (error) {
        showAlert('下载失败：' + error.message, 'danger');
    }
}

// 系统管理页面加载函数
async function loadUsersSection() {
    showSection('users-section');
    // 移除所有管理菜单项的active类
    document.getElementById('users-link').classList.remove('active');
    document.getElementById('categories-link').classList.remove('active');
    document.getElementById('departments-link').classList.remove('active');
    document.getElementById('audit-link').classList.remove('active');
    // 为当前项添加active类
    document.getElementById('users-link').classList.add('active');
    await loadUsersList();
}

async function loadUsersList() {
    try {
        const users = await apiCall('/users/');
        if (users) {
            renderUsersTable(users);
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.username}</td>
            <td>-</td>
            <td>-</td>
            <td><span class="badge ${user.is_admin ? 'bg-danger' : 'bg-primary'}">${user.is_admin ? '管理员' : '普通用户'}</span></td>
            <td><span class="badge bg-success">正常</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editUser(${user.id})" title="编辑用户">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${!user.is_admin ? `<button class="btn btn-outline-warning" onclick="manageUserPermissions(${user.id})" title="权限管理">
                        <i class="bi bi-gear"></i>
                    </button>` : ''}
                    ${!user.is_admin ? `<button class="btn btn-outline-danger" onclick="deleteUser(${user.id})" title="删除用户">
                        <i class="bi bi-trash"></i>
                    </button>` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddUserModal() {
    const modalHtml = `
        <div class="modal fade" id="addUserModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加用户</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-user-form">
                            <div class="mb-3">
                                <label class="form-label">用户名 *</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">密码 *</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="is_admin" id="is_admin">
                                    <label class="form-check-label" for="is_admin">
                                        管理员权限
                                    </label>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitAddUser()">添加</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
    modal.show();
}

async function submitAddUser() {
    const form = document.getElementById('add-user-form');
    const formData = new FormData(form);
    
    const userData = {
        username: formData.get('username'),
        password: formData.get('password'),
        is_admin: formData.has('is_admin')
    };
    
    try {
        const result = await apiCall('/users/', 'POST', userData);
        if (result) {
            showAlert('用户添加成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
            modal.hide();
            loadUsersList();
        }
    } catch (error) {
        showAlert('添加用户失败：' + error.message, 'danger');
    }
}

async function editUser(userId) {
    try {
        const user = await apiCall(`/users/${userId}`);
        if (user) {
            showEditUserModal(user);
        }
    } catch (error) {
        showAlert('获取用户信息失败：' + error.message, 'danger');
    }
}

function showEditUserModal(user) {
    const modalId = `editUserModal_${user.id}`;
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">编辑用户</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-user-form-${user.id}">
                            <input type="hidden" name="user_id" value="${user.id}">
                            <div class="mb-3">
                                <label class="form-label">用户名</label>
                                <input type="text" class="form-control" name="username" value="${user.username}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">新密码（不修改请留空）</label>
                                <input type="password" class="form-control" name="password">
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="is_admin" id="edit_is_admin_${user.id}" ${user.is_admin ? 'checked' : ''}>
                                    <label class="form-check-label" for="edit_is_admin_${user.id}">
                                        管理员权限
                                    </label>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitEditUser(${user.id})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的相同模态框
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

async function submitEditUser(userId) {
    const form = document.getElementById(`edit-user-form-${userId}`);
    const formData = new FormData(form);
    
    const userData = {
        is_admin: formData.has('is_admin')
    };
    
    if (formData.get('password')) {
        userData.password = formData.get('password');
    }
    
    try {
        const result = await apiCall(`/users/${userId}`, 'PUT', userData);
        if (result) {
            showAlert('用户更新成功！', 'success');
            const modalId = `editUserModal_${userId}`;
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            modal.hide();
            loadUsersList();
        }
    } catch (error) {
        showAlert('更新用户失败：' + error.message, 'danger');
    }
}

async function deleteUser(userId) {
    if (confirm('确定要删除这个用户吗？此操作不可恢复。')) {
        try {
            const result = await apiCall(`/users/${userId}`, 'DELETE');
            if (result) {
                showAlert('用户删除成功！', 'success');
                loadUsersList();
            }
        } catch (error) {
            showAlert('删除用户失败：' + error.message, 'danger');
        }
    }
}

async function manageUserPermissions(userId) {
    try {
        const [user, categories, userCategories] = await Promise.all([
            apiCall(`/users/${userId}`),
            apiCall('/categories/'),
            apiCall(`/users/${userId}/categories`)
        ]);
        
        console.log('User:', user);
        console.log('Categories:', categories);
        console.log('User categories:', userCategories);
        
        if (user && categories) {
            showUserPermissionsModal(user, categories, userCategories || []);
        }
    } catch (error) {
        console.error('获取权限信息失败:', error);
        showAlert('获取权限信息失败：' + error.message, 'danger');
    }
}

function showUserPermissionsModal(user, categories, userCategories) {
    const userCategoryIds = userCategories.map(uc => uc.category_id);
    const modalId = `userPermissionsModal_${user.id}`;
    
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">管理用户权限 - ${user.username}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="user-permissions-form-${user.id}">
                            <input type="hidden" name="user_id" value="${user.id}">
                            <div class="mb-3">
                                <label class="form-label">可管理的设备类别</label>
                                <div class="form-check-container">
                                    ${categories.map(category => `
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" name="category_ids" value="${category.id}" 
                                                   id="cat_${user.id}_${category.id}" ${userCategoryIds.includes(category.id) ? 'checked' : ''}>
                                            <label class="form-check-label" for="cat_${user.id}_${category.id}">
                                                ${category.name}
                                            </label>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitUserPermissions(${user.id})">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除现有的相同模态框
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

async function submitUserPermissions(userId) {
    const form = document.getElementById(`user-permissions-form-${userId}`);
    const formData = new FormData(form);
    
    const categoryIds = formData.getAll('category_ids').map(id => parseInt(id));
    
    try {
        const result = await apiCall(`/users/${userId}/categories`, 'PUT', { category_ids: categoryIds });
        if (result) {
            showAlert('权限更新成功！', 'success');
            const modalId = `userPermissionsModal_${userId}`;
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            modal.hide();
        }
    } catch (error) {
        showAlert('更新权限失败：' + error.message, 'danger');
    }
}

async function loadCategoriesSection() {
    showSection('categories-section');
    // 移除所有管理菜单项的active类
    document.getElementById('users-link').classList.remove('active');
    document.getElementById('categories-link').classList.remove('active');
    document.getElementById('departments-link').classList.remove('active');
    document.getElementById('audit-link').classList.remove('active');
    // 为当前项添加active类
    document.getElementById('categories-link').classList.add('active');
    await loadCategoriesList();
}

async function loadCategoriesList() {
    try {
        const categories = await apiCall('/categories/with-counts');
        console.log('Categories response:', categories); // 调试信息
        if (categories && Array.isArray(categories)) {
            renderCategoriesTable(categories);
        } else {
            console.error('Categories response is not an array:', categories);
            // 尝试常规API
            const regularCategories = await apiCall('/categories/');
            if (regularCategories && Array.isArray(regularCategories)) {
                const categoriesWithCount = regularCategories.map(cat => ({
                    ...cat,
                    equipment_count: 0
                }));
                renderCategoriesTable(categoriesWithCount);
            }
        }
    } catch (error) {
        console.error('加载设备类别列表失败:', error);
        showAlert('加载设备类别列表失败：' + error.message, 'danger');
    }
}

function renderCategoriesTable(categories) {
    const tbody = document.getElementById('categories-tbody');
    tbody.innerHTML = '';
    
    categories.forEach(category => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${category.name}</td>
            <td>${category.description || '-'}</td>
            <td>${category.equipment_count}</td>
            <td>${formatDate(category.created_at)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editCategory(${category.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteCategory(${category.id}, ${category.equipment_count})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddCategoryModal() {
    const modalHtml = `
        <div class="modal fade" id="addCategoryModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加设备类别</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-category-form">
                            <div class="mb-3">
                                <label class="form-label">类别名称 *</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">描述</label>
                                <textarea class="form-control" name="description" rows="3"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitAddCategory()">添加</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
    modal.show();
}

async function submitAddCategory() {
    const form = document.getElementById('add-category-form');
    const formData = new FormData(form);
    
    const categoryData = {
        name: formData.get('name'),
        description: formData.get('description') || ''
    };
    
    try {
        const result = await apiCall('/categories/', 'POST', categoryData);
        if (result) {
            showAlert('设备类别添加成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addCategoryModal'));
            modal.hide();
            loadCategoriesList();
        }
    } catch (error) {
        showAlert('添加设备类别失败：' + error.message, 'danger');
    }
}

async function editCategory(categoryId) {
    try {
        const category = await apiCall(`/categories/${categoryId}`);
        if (category) {
            showEditCategoryModal(category);
        }
    } catch (error) {
        showAlert('获取类别信息失败：' + error.message, 'danger');
    }
}

function showEditCategoryModal(category) {
    const modalHtml = `
        <div class="modal fade" id="editCategoryModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">编辑设备类别</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-category-form">
                            <input type="hidden" name="category_id" value="${category.id}">
                            <div class="mb-3">
                                <label class="form-label">类别名称 *</label>
                                <input type="text" class="form-control" name="name" value="${category.name}" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">描述</label>
                                <textarea class="form-control" name="description" rows="3">${category.description || ''}</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitEditCategory()">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('editCategoryModal'));
    modal.show();
}

async function submitEditCategory() {
    const form = document.getElementById('edit-category-form');
    const formData = new FormData(form);
    
    const categoryData = {
        name: formData.get('name'),
        description: formData.get('description') || ''
    };
    
    const categoryId = formData.get('category_id');
    
    try {
        const result = await apiCall(`/categories/${categoryId}`, 'PUT', categoryData);
        if (result) {
            showAlert('设备类别更新成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editCategoryModal'));
            modal.hide();
            loadCategoriesList();
        }
    } catch (error) {
        showAlert('更新设备类别失败：' + error.message, 'danger');
    }
}

async function deleteCategory(categoryId, equipmentCount) {
    if (equipmentCount > 0) {
        showAlert('无法删除该类别，因为还有设备使用此类别', 'warning');
        return;
    }
    
    if (confirm('确定要删除这个设备类别吗？此操作不可恢复。')) {
        try {
            const result = await apiCall(`/categories/${categoryId}`, 'DELETE');
            if (result) {
                showAlert('设备类别删除成功！', 'success');
                loadCategoriesList();
            }
        } catch (error) {
            showAlert('删除设备类别失败：' + error.message, 'danger');
        }
    }
}

async function loadDepartmentsSection() {
    showSection('departments-section');
    // 移除所有管理菜单项的active类
    document.getElementById('users-link').classList.remove('active');
    document.getElementById('categories-link').classList.remove('active');
    document.getElementById('departments-link').classList.remove('active');
    document.getElementById('audit-link').classList.remove('active');
    // 为当前项添加active类
    document.getElementById('departments-link').classList.add('active');
    await loadDepartmentsList();
}

async function loadDepartmentsList() {
    try {
        const departments = await apiCall('/departments/with-counts');
        console.log('Departments response:', departments); // 调试信息
        if (departments && Array.isArray(departments)) {
            renderDepartmentsTable(departments);
        } else {
            console.error('Departments response is not an array:', departments);
            // 尝试常规API
            const regularDepartments = await apiCall('/departments/');
            if (regularDepartments && Array.isArray(regularDepartments)) {
                const departmentsWithCount = regularDepartments.map(dept => ({
                    ...dept,
                    equipment_count: 0
                }));
                renderDepartmentsTable(departmentsWithCount);
            }
        }
    } catch (error) {
        console.error('加载部门列表失败:', error);
        showAlert('加载部门列表失败：' + error.message, 'danger');
    }
}

function renderDepartmentsTable(departments) {
    const tbody = document.getElementById('departments-tbody');
    tbody.innerHTML = '';
    
    departments.forEach(department => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${department.name}</td>
            <td>${department.description || '-'}</td>
            <td>-</td>
            <td>${department.equipment_count}</td>
            <td>${formatDate(department.created_at)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editDepartment(${department.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteDepartment(${department.id}, ${department.equipment_count})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAddDepartmentModal() {
    const modalHtml = `
        <div class="modal fade" id="addDepartmentModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加部门</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-department-form">
                            <div class="mb-3">
                                <label class="form-label">部门名称 *</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">描述</label>
                                <textarea class="form-control" name="description" rows="3"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitAddDepartment()">添加</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('addDepartmentModal'));
    modal.show();
}

async function submitAddDepartment() {
    const form = document.getElementById('add-department-form');
    const formData = new FormData(form);
    
    const departmentData = {
        name: formData.get('name'),
        description: formData.get('description') || ''
    };
    
    try {
        const result = await apiCall('/departments/', 'POST', departmentData);
        if (result) {
            showAlert('部门添加成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addDepartmentModal'));
            modal.hide();
            loadDepartmentsList();
        }
    } catch (error) {
        showAlert('添加部门失败：' + error.message, 'danger');
    }
}

async function editDepartment(departmentId) {
    try {
        const department = await apiCall(`/departments/${departmentId}`);
        if (department) {
            showEditDepartmentModal(department);
        }
    } catch (error) {
        showAlert('获取部门信息失败：' + error.message, 'danger');
    }
}

function showEditDepartmentModal(department) {
    const modalHtml = `
        <div class="modal fade" id="editDepartmentModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">编辑部门</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-department-form">
                            <input type="hidden" name="department_id" value="${department.id}">
                            <div class="mb-3">
                                <label class="form-label">部门名称 *</label>
                                <input type="text" class="form-control" name="name" value="${department.name}" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">描述</label>
                                <textarea class="form-control" name="description" rows="3">${department.description || ''}</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitEditDepartment()">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('editDepartmentModal'));
    modal.show();
}

async function submitEditDepartment() {
    const form = document.getElementById('edit-department-form');
    const formData = new FormData(form);
    
    const departmentData = {
        name: formData.get('name'),
        description: formData.get('description') || ''
    };
    
    const departmentId = formData.get('department_id');
    
    try {
        const result = await apiCall(`/departments/${departmentId}`, 'PUT', departmentData);
        if (result) {
            showAlert('部门更新成功！', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editDepartmentModal'));
            modal.hide();
            loadDepartmentsList();
        }
    } catch (error) {
        showAlert('更新部门失败：' + error.message, 'danger');
    }
}

async function deleteDepartment(departmentId, equipmentCount) {
    if (equipmentCount > 0) {
        showAlert('无法删除该部门，因为还有设备属于此部门', 'warning');
        return;
    }
    
    if (confirm('确定要删除这个部门吗？此操作不可恢复。')) {
        try {
            const result = await apiCall(`/departments/${departmentId}`, 'DELETE');
            if (result) {
                showAlert('部门删除成功！', 'success');
                loadDepartmentsList();
            }
        } catch (error) {
            showAlert('删除部门失败：' + error.message, 'danger');
        }
    }
}

async function loadAuditSection() {
    showSection('audit-section');
    // 移除所有管理菜单项的active类
    document.getElementById('users-link').classList.remove('active');
    document.getElementById('categories-link').classList.remove('active');
    document.getElementById('departments-link').classList.remove('active');
    document.getElementById('audit-link').classList.remove('active');
    // 为当前项添加active类
    document.getElementById('audit-link').classList.add('active');
    await loadAuditUsers();
    await loadAuditLogs({}, 1);
}

async function loadAuditUsers() {
    try {
        const users = await apiCall('/audit/users');
        if (users) {
            const userSelect = document.getElementById('audit-filter-user');
            userSelect.innerHTML = '<option value="">全部用户</option>';
            users.forEach(user => {
                userSelect.innerHTML += `<option value="${user.id}">${user.username}</option>`;
            });
        }
    } catch (error) {
        console.error('加载审计用户列表失败:', error);
    }
}

async function loadAuditLogs(filters = {}, page = 1) {
    try {
        const params = new URLSearchParams();
        const skip = (page - 1) * ITEMS_PER_PAGE;
        
        params.append('skip', skip);
        params.append('limit', ITEMS_PER_PAGE);
        
        if (filters.user_id) params.append('user_id', filters.user_id);
        if (filters.action) params.append('action', filters.action);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        const url = `/audit/?${params.toString()}`;
        const response = await apiCall(url);
        if (response) {
            renderAuditTable(response.items);
            currentPagination = {
                total: response.total,
                skip: response.skip,
                limit: response.limit,
                page: page
            };
            renderPagination('audit', currentPagination);
        }
    } catch (error) {
        console.error('加载操作日志失败:', error);
    }
}

function renderAuditTable(logs) {
    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="6" class="text-center text-muted">
                <i class="bi bi-info-circle"></i> 暂无操作日志
            </td>
        `;
        tbody.appendChild(row);
        return;
    }
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        const equipmentInfo = log.equipment ? 
            `${log.equipment.name} (${log.equipment.serial_number})` : '-';
        
        row.innerHTML = `
            <td>${formatDateTime(log.created_at)}</td>
            <td>${log.user.username}</td>
            <td><span class="badge bg-primary">${log.action}</span></td>
            <td>${equipmentInfo}</td>
            <td>${log.description}</td>
            <td>-</td>
        `;
        tbody.appendChild(row);
    });
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';
    const date = new Date(dateTimeString);
    // 转换为中国时区 (UTC+8)
    const chinaTime = new Date(date.getTime() + (8 * 60 * 60 * 1000));
    return chinaTime.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function getAuditFilterValues() {
    const filters = {};
    
    const userId = document.getElementById('audit-filter-user').value;
    if (userId) filters.user_id = parseInt(userId);
    
    const action = document.getElementById('audit-filter-action').value;
    if (action) filters.action = action;
    
    const startDate = document.getElementById('audit-filter-start-date').value;
    if (startDate) filters.start_date = startDate;
    
    const endDate = document.getElementById('audit-filter-end-date').value;
    if (endDate) filters.end_date = endDate;
    
    return filters;
}
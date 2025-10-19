// 导入进度页面脚本
(function() {
    const jobIdEl = document.getElementById('job-id');
    const progressTextEl = document.getElementById('progress-text');
    const progressBarEl = document.getElementById('progress-bar');
    const statusEl = document.getElementById('status');
    const filenameEl = document.getElementById('filename');
    const processedEl = document.getElementById('processed');
    const totalEl = document.getElementById('total');
    const createdAtEl = document.getElementById('created-at');
    const errorSummaryEl = document.getElementById('error-summary');
    const errorLinkEl = document.getElementById('error-link');
    const cancelBtn = document.getElementById('cancel-btn');

    let pollTimer = null;

    function fmtDate(s) {
        if (!s) return '-';
        try {
            const d = new Date(s);
            if (isNaN(d.getTime())) return '-';
            return d.toLocaleString();
        } catch (e) {
            return s;
        }
    }

    async function fetchStatus() {
        try {
            const data = await window.sessionManager.apiRequest(`/api/imports/excel/${JOB_ID}/status`);
            updateStatus(data);
        } catch (e) {
            console.error('获取状态失败:', e);
            window.sessionManager.showNotification(`获取状态失败: ${e.message}`, 'error');
        }
    }

    function updateStatus(data) {
        statusEl.textContent = data.status;
        filenameEl.textContent = data.filename || '-';
        processedEl.textContent = data.processed_rows || 0;
        totalEl.textContent = data.total_rows || 0;
        createdAtEl.textContent = fmtDate(data.created_at);
        progressTextEl.textContent = `${data.progress || 0}%`;
        progressBarEl.style.width = `${data.progress || 0}%`;

        // 错误摘要
        if (data.error_summary) {
            errorSummaryEl.classList.remove('hidden');
            errorSummaryEl.textContent = data.error_summary;
        } else {
            errorSummaryEl.classList.add('hidden');
            errorSummaryEl.textContent = '';
        }

        // 错误下载链接
        if (data.error_report_url) {
            errorLinkEl.classList.remove('hidden');
            errorLinkEl.href = data.error_report_url;
        } else {
            errorLinkEl.classList.add('hidden');
            errorLinkEl.href = '#';
        }

        // 取消按钮
        if (data.can_cancel) {
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50');
        } else {
            cancelBtn.disabled = true;
            cancelBtn.classList.add('opacity-50');
        }

        // 完成或失败或取消后停止轮询
        if (['succeeded', 'failed', 'canceled'].includes(data.status)) {
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
            if (data.status === 'succeeded') {
                window.sessionManager.showNotification('导入完成', 'success');
            } else if (data.status === 'failed') {
                window.sessionManager.showNotification('导入失败', 'error');
            } else if (data.status === 'canceled') {
                window.sessionManager.showNotification('导入已取消', 'warning');
            }
        }
    }

    async function cancelJob() {
        if (!confirm('确定要取消该导入任务吗？')) return;
        try {
            await window.sessionManager.apiRequest(`/api/imports/excel/${JOB_ID}/cancel`, {
                method: 'POST'
            });
            window.sessionManager.showNotification('已请求取消', 'info');
            // 立即刷新状态
            fetchStatus();
        } catch (e) {
            window.sessionManager.showNotification(`取消失败: ${e.message}`, 'error');
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        // 初始加载状态
        fetchStatus();
        // 开始轮询
        pollTimer = setInterval(fetchStatus, 2000);
        // 绑定取消按钮
        cancelBtn.addEventListener('click', cancelJob);
    });
})();

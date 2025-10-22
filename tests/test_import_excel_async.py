import os
import io
import time
from fastapi.testclient import TestClient
import pandas as pd

# 确保数据库使用测试路径
os.makedirs('data', exist_ok=True)
os.environ.setdefault('DATABASE_URL', 'sqlite:///./data/test_inventory.db')

import main
from init_db import init_db

# 初始化数据库（创建管理员、部门、类别）
init_db()

client = TestClient(main.app)


def login_admin():
    resp = client.post('/api/auth/login/json', json={
        'username': 'admin',
        'password': 'admin123',
        'force': True
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data['access_token']


def build_excel_bytes(rows):
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()


def wait_for_status(job_id, token, timeout=20):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = client.get(f'/api/imports/excel/{job_id}/status', headers={'Authorization': f'Bearer {token}'})
        if r.status_code != 200:
            time.sleep(0.2)
            continue
        data = r.json()
        last = data
        if data['status'] in ['succeeded', 'failed', 'canceled']:
            return data
        time.sleep(0.2)
    return last


def test_start_and_complete_import():
    token = login_admin()

    rows = [
        {
            '使用部门': '树脂车间',
            '设备类别': '温度环境类',
            '计量器具名称': '铂热电阻',
            '型号/规格': 'PT100',
            '准确度等级': 'A级',
            '检定周期': '12个月',
            '检定(校准)日期': '2024-01-15',
            '检定方式': '内检',
            '检定结果': '合格',
            '出厂编号': 'UT-TEST-001'
        }
    ]

    content = build_excel_bytes(rows)
    files = {
        'file': ('import.xlsx', content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }

    r = client.post('/api/imports/excel/start', headers={'Authorization': f'Bearer {token}'}, files=files)
    assert r.status_code == 200, r.text
    job_id = r.json()['job_id']

    status = wait_for_status(job_id, token)
    assert status is not None
    assert status['status'] == 'succeeded'
    assert status['progress'] == 100
    assert status['processed_rows'] >= 1


def test_import_with_error_report():
    token = login_admin()

    rows = [
        {
            '使用部门': '树脂车间',
            '设备类别': '不存在的类别',  # 将触发错误
            '计量器具名称': '铂热电阻',
            '型号/规格': 'PT100',
            '准确度等级': 'A级',
            '检定周期': '12个月',
            '检定(校准)日期': '2024-01-15',
            '检定方式': '内检',
            '检定结果': '合格',
            '出厂编号': 'UT-TEST-ERR-001'
        }
    ]

    content = build_excel_bytes(rows)
    files = {
        'file': ('import.xlsx', content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }

    r = client.post('/api/imports/excel/start', headers={'Authorization': f'Bearer {token}'}, files=files)
    assert r.status_code == 200, r.text
    job_id = r.json()['job_id']

    status = wait_for_status(job_id, token)
    assert status is not None
    assert status['status'] == 'succeeded'  # 整体任务仍标记为完成
    assert status['progress'] == 100
    assert status['processed_rows'] >= 1
    # 应有错误摘要
    assert 'error_summary' in status
    # 错误明细可下载
    if status.get('error_report_url'):
        r2 = client.get(status['error_report_url'], headers={'Authorization': f'Bearer {token}'})
        assert r2.status_code == 200
        assert r2.text.find('manufacturer_id') != -1

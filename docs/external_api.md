# 外部系统API接口文档

## 概述

本系统提供了专门的外部API接口，供第三方系统获取设备台账信息。所有外部API都使用API Key进行身份验证，确保数据安全。

## 基础信息

- **基础URL**: `http://your-server:8000/api/external`
- **认证方式**: API Key（通过Header传递）
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

所有API请求都需要在HTTP Header中包含API Key：

```
X-API-Key: your_api_key_here
```

### 可用的API Keys（示例）
- `api_key_12345`
- `external_system_key_2024`

> **注意**: 生产环境中请使用更安全的API Key，并通过系统管理员获取。

## 接口列表

### 1. 健康检查

检查API服务状态（无需API Key）

**请求**
```
GET /api/external/health
```

**响应**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "Equipment Management External API",
  "version": "1.0"
}
```

### 2. 获取所有设备信息

获取系统中所有设备的信息，支持分页和筛选

**请求**
```
GET /api/external/equipment?skip=0&limit=100&department_id=1&status=在用
```

**参数说明**
- `skip` (可选): 跳过的记录数，默认0
- `limit` (可选): 返回的最大记录数，默认1000，最大1000
- `department_id` (可选): 部门ID筛选
- `category_id` (可选): 类别ID筛选
- `status` (可选): 设备状态筛选

**响应示例**
```json
[
  {
    "id": 1,
    "name": "电子天平",
    "model": "AL204",
    "internal_id": "TC-DZT-0001",
    "category": {
      "id": 1,
      "name": "质量称量类",
      "description": "用于质量测量的设备"
    },
    "department": {
      "id": 1,
      "name": "技术车间",
      "code": "TC",
      "description": "技术部门"
    },
    "accuracy_level": "0.1mg",
    "measurement_range": "0-210g",
    "calibration_cycle": "12个月",
    "calibration_date": "2024-01-15",
    "valid_until": "2025-01-14",
    "calibration_method": "外部检定",
    "manufacturer": "梅特勒-托利多",
    "manufacture_date": "2023-06-01",
    "manufacturer_id": "MT001234",
    "installation_location": "实验室A",
    "original_value": "15000.00",
    "scale_value": "0.1mg",
    "status": "在用",
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-15T14:30:00"
  }
]
```

### 3. 获取单个设备详情

根据设备ID获取详细信息

**请求**
```
GET /api/external/equipment/{equipment_id}
```

**响应**: 与上述设备信息格式相同的单个对象

### 4. 获取所有部门信息

获取系统中所有部门信息

**请求**
```
GET /api/external/departments
```

**响应示例**
```json
[
  {
    "id": 1,
    "name": "技术车间",
    "code": "TC",
    "description": "技术部门",
    "created_at": "2024-01-01T10:00:00"
  }
]
```

### 5. 获取所有设备类别

获取系统中所有设备类别信息

**请求**
```
GET /api/external/categories
```

**响应示例**
```json
[
  {
    "id": 1,
    "name": "质量称量类",
    "description": "用于质量测量的设备",
    "predefined_names": ["电子天平", "分析天平", "台秤"],
    "created_at": "2024-01-01T10:00:00"
  }
]
```

### 6. 获取指定部门的设备

根据部门ID获取该部门下的所有设备

**请求**
```
GET /api/external/equipment/by-department/{department_id}?skip=0&limit=100
```

**响应**: 设备信息数组

### 7. 获取系统统计信息

获取设备台账的基本统计信息

**请求**
```
GET /api/external/stats
```

**响应示例**
```json
{
  "total_equipment": 150,
  "active_equipment": 140,
  "total_departments": 5,
  "last_updated": "2024-01-01T12:00:00.000Z",
  "api_version": "1.0"
}
```

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 401 | API Key无效或缺失 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

**错误响应格式**
```json
{
  "detail": "Invalid API Key"
}
```

## 使用示例

### Python示例
```python
import requests

# API配置
BASE_URL = "http://your-server:8000/api/external"
API_KEY = "api_key_12345"
headers = {"X-API-Key": API_KEY}

# 获取所有设备
response = requests.get(f"{BASE_URL}/equipment", headers=headers)
if response.status_code == 200:
    equipment_list = response.json()
    print(f"获取到 {len(equipment_list)} 台设备")
else:
    print(f"请求失败: {response.status_code}")

# 获取指定部门的设备
dept_id = 1
response = requests.get(f"{BASE_URL}/equipment/by-department/{dept_id}", headers=headers)
equipment = response.json()
```

### JavaScript示例
```javascript
const BASE_URL = "http://your-server:8000/api/external";
const API_KEY = "api_key_12345";

const headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
};

// 获取所有设备
fetch(`${BASE_URL}/equipment`, { headers })
    .then(response => response.json())
    .then(data => {
        console.log(`获取到 ${data.length} 台设备`);
        console.log(data);
    })
    .catch(error => console.error("Error:", error));

// 获取系统统计信息
fetch(`${BASE_URL}/stats`, { headers })
    .then(response => response.json())
    .then(stats => {
        console.log("系统统计:", stats);
    });
```

### cURL示例
```bash
# 健康检查
curl -X GET "http://your-server:8000/api/external/health"

# 获取所有设备
curl -X GET "http://your-server:8000/api/external/equipment" \
  -H "X-API-Key: api_key_12345"

# 获取指定部门的设备
curl -X GET "http://your-server:8000/api/external/equipment/by-department/1" \
  -H "X-API-Key: api_key_12345"

# 获取系统统计
curl -X GET "http://your-server:8000/api/external/stats" \
  -H "X-API-Key: api_key_12345"
```

## 最佳实践

1. **缓存策略**: 建议在客户端实现适当的缓存机制，避免频繁请求
2. **分页查询**: 对于大量数据，使用分页参数避免单次请求过大
3. **错误处理**: 实现完善的错误处理和重试机制
4. **API Key安全**: 妥善保管API Key，不要在前端代码中暴露
5. **限流考虑**: 避免短时间内大量并发请求

## 技术支持

如需申请API Key或遇到技术问题，请联系系统管理员。

---

**文档版本**: 1.0  
**最后更新**: 2024年1月
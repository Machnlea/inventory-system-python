# JavaScript 错误修复验证

## 问题描述
用户报告在访问统计报表页面时出现JavaScript错误：
```
加载报表数据失败: TypeError: can't access property "map", data is undefined
createCalibrationTrendChart http://127.0.0.1:8000/reports:474
loadReportsData http://127.0.0.1:8000/reports:435
```

## 根本原因
在 `createCalibrationTrendChart` 函数中，代码尝试对 `data` 参数调用 `.map()` 方法，但 `data` 参数为 undefined。

## 修复方案
1. **添加数据验证**：在所有图表创建函数中添加对空数据的检查
2. **安全的函数调用**：在调用图表函数时添加安全检查
3. **优雅的降级处理**：当数据为空时显示"暂无数据"的图表

## 修复的函数
- `createCalibrationTrendChart()`
- `createEquipmentStatusChart()`
- `createDepartmentStatsChart()`
- `createCategoryStatsChart()`

## 修复内容
每个函数都添加了以下检查：
```javascript
if (!data || !Array.isArray(data) || data.length === 0) {
    // 创建空图表
    return;
}
```

## 测试建议
1. 清空浏览器缓存
2. 重新访问统计报表页面
3. 检查是否还会出现JavaScript错误
4. 验证图表是否正常显示（包括"暂无数据"状态）

## 预期结果
- 不再出现 JavaScript TypeError
- 当数据为空时，图表显示"暂无数据"状态
- 当数据正常时，图表正常显示
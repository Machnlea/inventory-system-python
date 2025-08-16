from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

from app.api.auth import get_current_user
from app.models.models import User

router = APIRouter()

# 系统设置文件路径
SETTINGS_FILE = Path(__file__).parent.parent.parent / "data" / "system_settings.json"

# 默认系统设置
DEFAULT_SETTINGS = {
    "systemName": "设备台账管理系统",
    "defaultLanguage": "zh-CN",
    "timezone": "Asia/Shanghai",
    "pageSize": 10,
    "sessionTimeout": 2,
    "minPasswordLength": 6,
    "enableTwoFactor": False,
    "enableLoginLog": True,
    "enableEmailNotification": True,
    "enableExpirationReminder": True,
    "enableCalibrationReminder": True,
    "reminderDays": 7,
    "smtpServer": "",
    "enableAutoBackup": True,
    "backupFrequency": "weekly",
    "backupRetention": 30,
    "backupPath": "./backups"
}

def load_settings() -> Dict[str, Any]:
    """加载系统设置"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"加载系统设置失败: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings_data: Dict[str, Any]) -> bool:
    """保存系统设置"""
    try:
        # 确保数据目录存在
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存系统设置失败: {e}")
        return False

@router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """获取系统设置"""
    try:
        settings_data = load_settings()
        return {"success": True, "data": settings_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统设置失败: {str(e)}")

@router.put("/settings")
async def update_settings(
    settings_data: Dict[str, Any], 
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """更新系统设置"""
    try:
        # 验证设置数据
        if not isinstance(settings_data, dict):
            raise HTTPException(status_code=400, detail="设置数据格式错误")
        
        # 验证必要字段
        required_fields = ["systemName", "defaultLanguage", "timezone", "pageSize"]
        for field in required_fields:
            if field not in settings_data:
                raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")
        
        # 验证数值范围
        if "pageSize" in settings_data:
            page_size = settings_data["pageSize"]
            if not isinstance(page_size, int) or page_size < 5 or page_size > 100:
                raise HTTPException(status_code=400, detail="每页显示条数必须在5-100之间")
        
        if "sessionTimeout" in settings_data:
            timeout = settings_data["sessionTimeout"]
            if not isinstance(timeout, int) or timeout < 1 or timeout > 24:
                raise HTTPException(status_code=400, detail="会话超时时间必须在1-24小时之间")
        
        if "minPasswordLength" in settings_data:
            min_length = settings_data["minPasswordLength"]
            if not isinstance(min_length, int) or min_length < 4 or min_length > 20:
                raise HTTPException(status_code=400, detail="密码最小长度必须在4-20之间")
        
        if "reminderDays" in settings_data:
            days = settings_data["reminderDays"]
            if not isinstance(days, int) or days < 1 or days > 30:
                raise HTTPException(status_code=400, detail="提醒提前天数必须在1-30之间")
        
        if "backupRetention" in settings_data:
            retention = settings_data["backupRetention"]
            if not isinstance(retention, int) or retention < 7 or retention > 365:
                raise HTTPException(status_code=400, detail="备份保留天数必须在7-365之间")
        
        # 保存设置
        success = save_settings(settings_data)
        if not success:
            raise HTTPException(status_code=500, detail="保存系统设置失败")
        
        return {"success": True, "data": settings_data, "message": "系统设置更新成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新系统设置失败: {str(e)}")

@router.post("/settings/reset")
async def reset_settings(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """重置系统设置为默认值"""
    try:
        default_settings = DEFAULT_SETTINGS.copy()
        success = save_settings(default_settings)
        
        if not success:
            raise HTTPException(status_code=500, detail="重置系统设置失败")
        
        return {"success": True, "data": default_settings, "message": "系统设置已重置为默认值"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置系统设置失败: {str(e)}")
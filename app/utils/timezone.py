from datetime import datetime, date
import pytz

# 中国时区
CHINA_TZ = pytz.timezone('Asia/Shanghai')

def get_china_now() -> datetime:
    """获取中国时区的当前时间"""
    return datetime.now(CHINA_TZ)

def get_china_today() -> date:
    """获取中国时区的今天日期"""
    return get_china_now().date()

def get_china_datetime_str() -> str:
    """获取格式化的中国时区时间字符串"""
    return get_china_now().strftime('%Y-%m-%d %H:%M:%S')

def utc_to_china(utc_dt: datetime) -> datetime:
    """将UTC时间转换为中国时区时间"""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(CHINA_TZ)

def china_to_utc(china_dt: datetime) -> datetime:
    """将中国时区时间转换为UTC时间"""
    if china_dt.tzinfo is None:
        china_dt = CHINA_TZ.localize(china_dt)
    return china_dt.astimezone(pytz.utc)
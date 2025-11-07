"""
缓存配置模块

定义缓存策略、TTL设置和缓存键命名规则。
"""

from typing import Dict, Any
from enum import Enum

class CacheStrategy(Enum):
    """缓存策略枚举"""
    VERY_SHORT = "very_short"    # 30秒 - 高频变化的数据
    SHORT = "short"              # 5分钟 - 一般性数据
    MEDIUM = "medium"            # 30分钟 - 相对稳定的数据
    LONG = "long"                # 2小时 - 稳定的配置数据
    VERY_LONG = "very_long"      # 24小时 - 基本不变的数据

class CacheKeyPrefix:
    """缓存键前缀常量"""
    DASHBOARD = "dashboard"
    EQUIPMENT = "equipment"
    DEPARTMENTS = "departments"
    CATEGORIES = "categories"
    USERS = "users"
    STATS = "stats"
    REPORTS = "reports"
    SYSTEM = "system"

class CacheConfig:
    """缓存配置类"""

    # TTL配置（秒）
    TTL_CONFIG: Dict[CacheStrategy, int] = {
        CacheStrategy.VERY_SHORT: 30,      # 30秒
        CacheStrategy.SHORT: 300,          # 5分钟
        CacheStrategy.MEDIUM: 1800,        # 30分钟
        CacheStrategy.LONG: 7200,          # 2小时
        CacheStrategy.VERY_LONG: 86400,    # 24小时
    }

    # 具体API端点的缓存配置
    API_CACHE_CONFIG: Dict[str, Dict[str, Any]] = {
        # 仪表盘相关
        "dashboard_stats": {
            "strategy": CacheStrategy.SHORT,
            "prefix": CacheKeyPrefix.DASHBOARD,
            "description": "仪表盘统计数据"
        },
        "dashboard_monthly_due": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.DASHBOARD,
            "description": "月度待检设备"
        },
        "dashboard_yearly_due": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.DASHBOARD,
            "description": "年度待检设备"
        },

        # 部门管理
        "departments_list": {
            "strategy": CacheStrategy.LONG,
            "prefix": CacheKeyPrefix.DEPARTMENTS,
            "description": "部门列表"
        },
        "departments_count": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.DEPARTMENTS,
            "description": "部门统计"
        },

        # 设备类别管理
        "categories_list": {
            "strategy": CacheStrategy.LONG,
            "prefix": CacheKeyPrefix.CATEGORIES,
            "description": "设备类别列表"
        },
        "categories_with_predefined": {
            "strategy": CacheStrategy.LONG,
            "prefix": CacheKeyPrefix.CATEGORIES,
            "description": "带预定义名称的类别列表"
        },

        # 设备管理
        "equipment_list": {
            "strategy": CacheStrategy.VERY_SHORT,
            "prefix": CacheKeyPrefix.EQUIPMENT,
            "description": "设备列表（短缓存）"
        },
        "equipment_count": {
            "strategy": CacheStrategy.SHORT,
            "prefix": CacheKeyPrefix.STATS,
            "description": "设备总数统计"
        },
        "equipment_search": {
            "strategy": CacheStrategy.SHORT,
            "prefix": CacheKeyPrefix.EQUIPMENT,
            "description": "设备搜索结果"
        },

        # 用户管理
        "users_list": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.USERS,
            "description": "用户列表"
        },
        "user_permissions": {
            "strategy": CacheStrategy.LONG,
            "prefix": CacheKeyPrefix.USERS,
            "description": "用户权限信息"
        },

        # 统计报表
        "reports_equipment_stats": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.REPORTS,
            "description": "设备统计报表"
        },
        "reports_calibration_stats": {
            "strategy": CacheStrategy.MEDIUM,
            "prefix": CacheKeyPrefix.REPORTS,
            "description": "检定统计报表"
        },

        # 系统信息
        "system_database_stats": {
            "strategy": CacheStrategy.SHORT,
            "prefix": CacheKeyPrefix.SYSTEM,
            "description": "数据库统计信息"
        },
        "system_status": {
            "strategy": CacheStrategy.VERY_SHORT,
            "prefix": CacheKeyPrefix.SYSTEM,
            "description": "系统状态信息"
        }
    }

    @classmethod
    def get_ttl(cls, strategy: CacheStrategy) -> int:
        """获取指定策略的TTL"""
        return cls.TTL_CONFIG.get(strategy, cls.TTL_CONFIG[CacheStrategy.SHORT])

    @classmethod
    def get_api_config(cls, api_name: str) -> Dict[str, Any]:
        """获取API的缓存配置"""
        return cls.API_CACHE_CONFIG.get(api_name, {
            "strategy": CacheStrategy.SHORT,
            "prefix": CacheKeyPrefix.SYSTEM,
            "description": "默认缓存配置"
        })

    @classmethod
    def get_cache_ttl_for_api(cls, api_name: str) -> int:
        """获取API的缓存TTL"""
        config = cls.get_api_config(api_name)
        return cls.get_ttl(config["strategy"])

    @classmethod
    def get_cache_prefix_for_api(cls, api_name: str) -> str:
        """获取API的缓存键前缀"""
        config = cls.get_api_config(api_name)
        return config["prefix"]

    @classmethod
    def all_cache_configs(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存配置"""
        return cls.API_CACHE_CONFIG.copy()

class CacheInvalidationRules:
    """缓存失效规则"""

    # 设备相关变更时需要失效的缓存模式
    EQUIPMENT_CHANGE_PATTERNS = [
        "dashboard:*",
        "equipment:*",
        "stats:*",
        "reports:*"
    ]

    # 部门相关变更时需要失效的缓存模式
    DEPARTMENT_CHANGE_PATTERNS = [
        "departments:*",
        "dashboard:*",
        "equipment:*",
        "stats:*"
    ]

    # 类别相关变更时需要失效的缓存模式
    CATEGORY_CHANGE_PATTERNS = [
        "categories:*",
        "dashboard:*",
        "equipment:*",
        "stats:*"
    ]

    # 用户相关变更时需要失效的缓存模式
    USER_CHANGE_PATTERNS = [
        "users:*",
        "dashboard:*",
        "stats:*"
    ]

    @classmethod
    def get_invalidation_patterns(cls, entity_type: str) -> list:
        """根据实体类型获取需要失效的缓存模式"""
        patterns_map = {
            "equipment": cls.EQUIPMENT_CHANGE_PATTERNS,
            "department": cls.DEPARTMENT_CHANGE_PATTERNS,
            "category": cls.CATEGORY_CHANGE_PATTERNS,
            "user": cls.USER_CHANGE_PATTERNS
        }
        return patterns_map.get(entity_type, [])

class CacheMetrics:
    """缓存指标统计"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0

    def record_hit(self):
        """记录缓存命中"""
        self.hits += 1

    def record_miss(self):
        """记录缓存未命中"""
        self.misses += 1

    def record_set(self):
        """记录缓存设置"""
        self.sets += 1

    def record_delete(self):
        """记录缓存删除"""
        self.deletes += 1

    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": f"{self.get_hit_rate():.2f}%",
            "total_requests": self.hits + self.misses
        }

    def reset(self):
        """重置统计"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0

# 全局缓存指标实例
cache_metrics = CacheMetrics()
"""
Redis缓存服务模块

提供高性能的API响应缓存功能，支持多种缓存策略和自动失效机制。
"""

import json
import pickle
from typing import Any, Optional, Union, Callable
from functools import wraps
import redis
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Redis缓存服务类"""

    def __init__(self, host: str = 'localhost', port: int = 6379,
                 db: int = 0, password: Optional[str] = None,
                 default_ttl: int = 300):
        """
        初始化Redis缓存服务

        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: Redis密码
            default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self.key_prefix = "inventory_system:"

        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # 使用bytes模式支持pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis缓存服务初始化成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用内存缓存: {e}")
            self.redis_client = None
            self._memory_cache = {}

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存的值，不存在返回None
        """
        cache_key = self._make_key(key)

        try:
            if self.redis_client:
                data = self.redis_client.get(cache_key)
                if data:
                    return pickle.loads(data)
            else:
                # 内存缓存降级
                return self._memory_cache.get(cache_key)
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {e}")

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用default_ttl

        Returns:
            是否设置成功
        """
        cache_key = self._make_key(key)
        ttl = ttl or self.default_ttl

        try:
            if self.redis_client:
                data = pickle.dumps(value)
                return self.redis_client.setex(cache_key, ttl, data)
            else:
                # 内存缓存降级
                self._memory_cache[cache_key] = value
                return True
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        cache_key = self._make_key(key)

        try:
            if self.redis_client:
                return bool(self.redis_client.delete(cache_key))
            else:
                # 内存缓存降级
                self._memory_cache.pop(cache_key, None)
                return True
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        批量删除匹配模式的缓存

        Args:
            pattern: 匹配模式

        Returns:
            删除的键数量
        """
        pattern = self._make_key(pattern)

        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # 内存缓存降级
                count = 0
                keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    self._memory_cache.pop(key, None)
                    count += 1
                return count
        except Exception as e:
            logger.error(f"批量缓存删除失败 {pattern}: {e}")

        return 0

    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            if self.redis_client:
                pattern = self._make_key("*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                self._memory_cache.clear()
            logger.info("所有缓存已清空")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        cache_key = self._make_key(key)

        try:
            if self.redis_client:
                return bool(self.redis_client.exists(cache_key))
            else:
                return cache_key in self._memory_cache
        except Exception as e:
            logger.error(f"缓存检查失败 {key}: {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """
        获取缓存剩余时间

        Args:
            key: 缓存键

        Returns:
            剩余时间（秒），-1表示永不过期，-2表示不存在
        """
        cache_key = self._make_key(key)

        try:
            if self.redis_client:
                return self.redis_client.ttl(cache_key)
            else:
                # 内存缓存无法获取TTL，返回默认值
                return -1 if cache_key in self._memory_cache else -2
        except Exception as e:
            logger.error(f"获取TTL失败 {key}: {e}")
            return -2

# 全局缓存服务实例
cache_service = CacheService()

def cache_key_generator(*args, **kwargs) -> str:
    """
    生成缓存键的辅助函数

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    # 过滤掉不需要的参数（如Session对象）
    filtered_kwargs = {k: v for k, v in kwargs.items()
                       if not hasattr(v, '__class__') or 'Session' not in str(type(v))}

    # 生成键的组成部分
    key_parts = []

    # 添加函数名
    if args and hasattr(args[0], '__name__'):
        key_parts.append(args[0].__name__)

    # 添加位置参数（过滤掉特殊对象）
    for arg in args[1:]:
        if not hasattr(arg, '__class__') or 'Session' not in str(type(arg)):
            key_parts.append(str(arg))

    # 添加关键字参数
    if filtered_kwargs:
        sorted_items = sorted(filtered_kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_items)

    return ":".join(key_parts)

def cached(ttl: int = 300, key_prefix: str = "",
          cache_key_func: Optional[Callable] = None):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        cache_key_func: 自定义缓存键生成函数

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = cache_key_generator(func, *args, **kwargs)

            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            # 执行原函数
            try:
                result = func(*args, **kwargs)

                # 存入缓存
                if result is not None:
                    cache_service.set(cache_key, result, ttl)
                    logger.debug(f"缓存设置: {cache_key}, TTL: {ttl}s")

                return result

            except Exception as e:
                logger.error(f"函数执行失败，跳过缓存: {func.__name__}: {e}")
                raise

        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> bool:
    """
    失效匹配模式的缓存

    Args:
        pattern: 缓存键模式

    Returns:
        是否成功
    """
    return cache_service.delete_pattern(pattern)

def get_cache_stats() -> dict:
    """
    获取缓存统计信息

    Returns:
        缓存统计字典
    """
    try:
        if cache_service.redis_client:
            info = cache_service.redis_client.info()
            return {
                "redis_connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", "N/A"),
                "total_commands_processed": info.get("total_commands_processed", "N/A"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        else:
            return {
                "redis_connected": False,
                "cache_type": "memory",
                "cached_keys": len(cache_service._memory_cache),
            }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return {"error": str(e)}
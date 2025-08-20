#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间管理工具模块
从原有utils/time_utils.py迁移而来，适配新轻量化架构
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

# 可选依赖 - pytz用于时区处理
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    pytz = None


class TimeManager:
    """时间管理器 - 处理静默时间和时间窗口"""
    
    def __init__(self, timezone: str = 'Asia/Shanghai'):
        """初始化时间管理器
        
        Args:
            timezone: 时区字符串，默认中国上海时区
        """
        if PYTZ_AVAILABLE and pytz:
            try:
                self.timezone = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                self.timezone = pytz.timezone('Asia/Shanghai')
        else:
            # 降级处理，使用系统时区
            self.timezone = None
            
        self.last_activity_time = None
        self.quiet_period_start = None
        self.quiet_period_duration = 300  # 默认5分钟
        
    def record_activity(self):
        """记录活动时间"""
        self.last_activity_time = time.time()
        self.quiet_period_start = None
        
    def start_quiet_period(self, duration_seconds: int = 300):
        """开始静默期（任务完成后的空闲时间）
        
        Args:
            duration_seconds: 静默期持续时间（秒），默认5分钟
        """
        self.quiet_period_start = time.time()
        self.quiet_period_duration = duration_seconds
        
    def is_in_quiet_period(self) -> bool:
        """检查是否在静默期内"""
        if self.quiet_period_start is None:
            return False
            
        elapsed = time.time() - self.quiet_period_start
        return elapsed < self.quiet_period_duration
        
    def get_quiet_time_remaining(self) -> Optional[int]:
        """获取静默期剩余时间（秒）"""
        if not self.is_in_quiet_period():
            return None
            
        elapsed = time.time() - self.quiet_period_start
        remaining = self.quiet_period_duration - elapsed
        return max(0, int(remaining))
        
    def get_idle_time(self) -> Optional[int]:
        """获取空闲时间（秒）"""
        if self.last_activity_time is None:
            return None
            
        return int(time.time() - self.last_activity_time)
        
    def should_send_idle_notification(self, idle_threshold: int = 1800) -> bool:
        """检查是否应该发送空闲通知（默认30分钟）
        
        Args:
            idle_threshold: 空闲时间阈值（秒），默认30分钟
        """
        idle_time = self.get_idle_time()
        if idle_time is None:
            return False
            
        # 只在刚好超过阈值时发送一次
        return idle_threshold <= idle_time < (idle_threshold + 60)
        
    def format_duration(self, seconds: int) -> str:
        """格式化持续时间为可读格式
        
        Args:
            seconds: 持续时间（秒）
            
        Returns:
            格式化的时间字符串
        """
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒" if secs > 0 else f"{minutes}分钟"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{hours}小时"
            
    def get_current_time_str(self) -> str:
        """获取当前时间字符串"""
        if self.timezone and PYTZ_AVAILABLE:
            now = datetime.now(self.timezone)
        else:
            now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')
        
    def parse_time_range(self, start_str: str, end_str: str) -> Tuple[datetime, datetime]:
        """解析时间范围字符串（HH:MM格式）
        
        Args:
            start_str: 开始时间字符串（HH:MM）
            end_str: 结束时间字符串（HH:MM）
            
        Returns:
            开始和结束datetime对象的元组
        """
        if self.timezone and PYTZ_AVAILABLE:
            today = datetime.now(self.timezone).date()
        else:
            today = datetime.now().date()
        
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        start_datetime = datetime.combine(today, start_time)
        end_datetime = datetime.combine(today, end_time)
        
        if self.timezone and PYTZ_AVAILABLE:
            start_datetime = self.timezone.localize(start_datetime)
            end_datetime = self.timezone.localize(end_datetime)
        
        # 处理跨天的情况
        if end_datetime <= start_datetime:
            end_datetime += timedelta(days=1)
            
        return start_datetime, end_datetime
        
    def is_in_time_window(self, start_str: str, end_str: str) -> bool:
        """检查当前时间是否在指定时间窗口内
        
        Args:
            start_str: 开始时间字符串（HH:MM）
            end_str: 结束时间字符串（HH:MM）
            
        Returns:
            是否在时间窗口内
        """
        if self.timezone and PYTZ_AVAILABLE:
            now = datetime.now(self.timezone)
        else:
            now = datetime.now()
            
        start_time, end_time = self.parse_time_range(start_str, end_str)
        
        # 处理跨天的情况
        if end_time.date() > start_time.date():
            # 时间窗口跨越午夜
            return now >= start_time or now <= end_time.replace(day=now.day)
        else:
            return start_time <= now <= end_time


class RateLimitTracker:
    """Claude使用限流追踪器 - 轻量级版本"""
    
    def __init__(self, custom_limits: Optional[dict] = None):
        """初始化限流追踪器
        
        Args:
            custom_limits: 自定义限流配置
        """
        self.usage_history = []  # [(timestamp, operation)]
        
        # 默认限流配置
        default_limits = {
            'minute': {'limit': 10, 'window': 60},
            'hour': {'limit': 100, 'window': 3600},
            'day': {'limit': 1000, 'window': 86400}
        }
        
        self.rate_limits = custom_limits if custom_limits else default_limits
        
    def record_usage(self, operation: str = 'api_call'):
        """记录一次使用
        
        Args:
            operation: 操作类型
        """
        self.usage_history.append((time.time(), operation))
        self._cleanup_old_records()
        
    def _cleanup_old_records(self):
        """清理过期记录"""
        current_time = time.time()
        # 只保留24小时内的记录
        self.usage_history = [
            (ts, op) for ts, op in self.usage_history 
            if current_time - ts < 86400
        ]
        
    def get_usage_count(self, window_seconds: int, operation_filter: Optional[str] = None) -> int:
        """获取指定时间窗口内的使用次数
        
        Args:
            window_seconds: 时间窗口（秒）
            operation_filter: 操作类型过滤器，None表示所有操作
            
        Returns:
            使用次数
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        if operation_filter:
            count = sum(1 for ts, op in self.usage_history 
                       if ts >= cutoff_time and op == operation_filter)
        else:
            count = sum(1 for ts, _ in self.usage_history if ts >= cutoff_time)
            
        return count
        
    def check_rate_limit(self, level: str = 'minute') -> dict:
        """检查限流状态
        
        Args:
            level: 限流级别（minute/hour/day）
            
        Returns:
            限流状态字典
        """
        if level not in self.rate_limits:
            level = 'minute'
            
        limit_config = self.rate_limits[level]
        usage_count = self.get_usage_count(limit_config['window'])
        limit = limit_config['limit']
        
        return {
            'level': level,
            'current': usage_count,
            'limit': limit,
            'remaining': max(0, limit - usage_count),
            'percentage': (usage_count / limit * 100) if limit > 0 else 0,
            'is_limited': usage_count >= limit,
            'reset_in': limit_config['window']
        }
        
    def get_all_limits_status(self) -> dict:
        """获取所有级别的限流状态
        
        Returns:
            所有限流级别的状态字典
        """
        status = {}
        for level in self.rate_limits:
            status[level] = self.check_rate_limit(level)
        return status
        
    def should_send_warning(self, warning_threshold: float = 90.0) -> Tuple[bool, Optional[str]]:
        """检查是否应该发送限流警告
        
        Args:
            warning_threshold: 警告阈值百分比，默认90%
            
        Returns:
            (是否应该警告, 警告信息)
        """
        for level in ['minute', 'hour', 'day']:
            if level not in self.rate_limits:
                continue
                
            status = self.check_rate_limit(level)
            
            # 达到阈值时警告
            if status['percentage'] >= warning_threshold and not status['is_limited']:
                return True, f"{level}级别使用率达到{status['percentage']:.1f}%"
                
            # 已限流时警告
            if status['is_limited']:
                return True, f"{level}级别已达到限制"
                
        return False, None
        
    def get_stats(self) -> dict:
        """获取使用统计信息
        
        Returns:
            统计信息字典
        """
        current_time = time.time()
        
        # 统计不同时间窗口的使用量
        windows = {
            '1分钟': 60,
            '5分钟': 300,
            '15分钟': 900,
            '1小时': 3600,
            '24小时': 86400
        }
        
        stats = {
            'total_records': len(self.usage_history),
            'usage_by_window': {},
            'limits_status': self.get_all_limits_status()
        }
        
        for window_name, window_seconds in windows.items():
            stats['usage_by_window'][window_name] = self.get_usage_count(window_seconds)
            
        return stats
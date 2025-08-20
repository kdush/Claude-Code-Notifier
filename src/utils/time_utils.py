#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz

class TimeManager:
    """时间管理器 - 处理静默时间和时间窗口"""
    
    def __init__(self, timezone: str = 'Asia/Shanghai'):
        self.timezone = pytz.timezone(timezone)
        self.last_activity_time = None
        self.quiet_period_start = None
        
    def record_activity(self):
        """记录活动时间"""
        self.last_activity_time = time.time()
        self.quiet_period_start = None
        
    def start_quiet_period(self, duration_seconds: int = 300):
        """开始静默期（任务完成后的空闲时间）"""
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
        """检查是否应该发送空闲通知（默认30分钟）"""
        idle_time = self.get_idle_time()
        if idle_time is None:
            return False
            
        # 只在刚好超过阈值时发送一次
        return idle_time >= idle_threshold and idle_time < (idle_threshold + 60)
        
    def format_duration(self, seconds: int) -> str:
        """格式化持续时间为可读格式"""
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
        now = datetime.now(self.timezone)
        return now.strftime('%Y-%m-%d %H:%M:%S')
        
    def parse_time_range(self, start_str: str, end_str: str) -> Tuple[datetime, datetime]:
        """解析时间范围字符串（HH:MM格式）"""
        today = datetime.now(self.timezone).date()
        
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        start_datetime = self.timezone.localize(datetime.combine(today, start_time))
        end_datetime = self.timezone.localize(datetime.combine(today, end_time))
        
        # 处理跨天的情况
        if end_datetime <= start_datetime:
            end_datetime += timedelta(days=1)
            
        return start_datetime, end_datetime
        
    def is_in_time_window(self, start_str: str, end_str: str) -> bool:
        """检查当前时间是否在指定时间窗口内"""
        now = datetime.now(self.timezone)
        start_time, end_time = self.parse_time_range(start_str, end_str)
        
        # 处理跨天的情况
        if end_time.date() > start_time.date():
            # 时间窗口跨越午夜
            return now >= start_time or now <= end_time.replace(day=now.day)
        else:
            return start_time <= now <= end_time


class RateLimitTracker:
    """Claude使用限流追踪器"""
    
    def __init__(self):
        self.usage_history = []  # [(timestamp, operation)]
        self.rate_limits = {
            'minute': {'limit': 10, 'window': 60},
            'hour': {'limit': 100, 'window': 3600},
            'day': {'limit': 1000, 'window': 86400}
        }
        
    def record_usage(self, operation: str = 'api_call'):
        """记录一次使用"""
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
        
    def get_usage_count(self, window_seconds: int) -> int:
        """获取指定时间窗口内的使用次数"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        count = sum(1 for ts, _ in self.usage_history if ts >= cutoff_time)
        return count
        
    def check_rate_limit(self, level: str = 'minute') -> dict:
        """检查限流状态"""
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
        """获取所有级别的限流状态"""
        status = {}
        for level in self.rate_limits:
            status[level] = self.check_rate_limit(level)
        return status
        
    def should_send_warning(self) -> Tuple[bool, Optional[str]]:
        """检查是否应该发送限流警告"""
        for level in ['minute', 'hour', 'day']:
            status = self.check_rate_limit(level)
            
            # 达到90%时警告
            if status['percentage'] >= 90 and not status['is_limited']:
                return True, f"{level}级别使用率达到{status['percentage']:.1f}%"
                
            # 已限流时警告
            if status['is_limited']:
                return True, f"{level}级别已达到限制"
                
        return False, None
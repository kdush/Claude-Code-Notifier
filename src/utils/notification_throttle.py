#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知频率控制系统 - Notification Throttle
防止通知轰炸，智能管理通知发送频率
"""

import time
import hashlib
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ThrottleAction(Enum):
    """节流动作枚举"""
    ALLOW = "allow"
    BLOCK = "block"
    DELAY = "delay"
    MERGE = "merge"


class NotificationPriority(Enum):
    """通知优先级"""
    CRITICAL = 4
    HIGH = 3
    NORMAL = 2
    LOW = 1


@dataclass
class NotificationRequest:
    """通知请求数据结构"""
    notification_id: str
    event_type: str
    channel: str
    priority: NotificationPriority
    content: Dict[str, Any]
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
            
    def get_content_hash(self) -> str:
        """获取内容哈希，用于检测重复通知"""
        content_str = f"{self.event_type}:{self.channel}:{str(self.content.get('project', ''))}:{str(self.content.get('operation', ''))}"
        return hashlib.md5(content_str.encode()).hexdigest()[:8]


class NotificationThrottle:
    """通知频率控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 频率限制配置
        self.rate_limits = self._load_rate_limits()
        
        # 通知历史记录
        self.notification_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 渠道特定历史
        self.channel_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        
        # 重复检测缓存
        self.duplicate_cache: Dict[str, Tuple[float, int]] = {}  # hash -> (last_time, count)
        
        # 延迟队列
        self.delayed_notifications: List[Tuple[float, NotificationRequest]] = []
        
        # 统计信息
        self.stats = {
            'allowed': 0,
            'blocked': 0,
            'delayed': 0,
            'merged': 0,
            'duplicates_filtered': 0
        }
        
    def _load_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """加载频率限制配置"""
        default_limits = {
            'global': {
                'max_per_minute': 20,
                'max_per_hour': 200,
                'burst_limit': 5,
                'burst_window': 10
            },
            'by_channel': {
                'dingtalk': {'max_per_minute': 10, 'max_per_hour': 100},
                'feishu': {'max_per_minute': 15, 'max_per_hour': 150},
                'email': {'max_per_minute': 5, 'max_per_hour': 50},
                'telegram': {'max_per_minute': 20, 'max_per_hour': 200},
                'serverchan': {'max_per_minute': 5, 'max_per_hour': 50}
            },
            'by_event': {
                'sensitive_operation': {'max_per_minute': 3, 'cooldown': 30},
                'task_completion': {'max_per_minute': 2, 'cooldown': 60},
                'rate_limit': {'max_per_minute': 1, 'cooldown': 300},
                'error_occurred': {'max_per_minute': 5, 'cooldown': 10}
            },
            'priority_weights': {
                'CRITICAL': 1.0,    # 不限制
                'HIGH': 0.8,        # 轻微限制
                'NORMAL': 0.6,      # 正常限制
                'LOW': 0.3          # 严格限制
            }
        }
        
        # 合并用户配置
        user_limits = self.config.get('notifications', {}).get('rate_limiting', {})
        if user_limits:
            # 深度合并配置
            for key, value in user_limits.items():
                if key in default_limits and isinstance(value, dict):
                    default_limits[key].update(value)
                else:
                    default_limits[key] = value
                    
        return default_limits
        
    def should_allow_notification(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查是否允许发送通知"""
        
        # 1. 检查重复通知
        duplicate_result = self._check_duplicate(request)
        if duplicate_result[0] != ThrottleAction.ALLOW:
            return duplicate_result
            
        # 2. 检查全局频率限制
        global_result = self._check_global_limits(request)
        if global_result[0] != ThrottleAction.ALLOW:
            return global_result
            
        # 3. 检查渠道特定限制
        channel_result = self._check_channel_limits(request)
        if channel_result[0] != ThrottleAction.ALLOW:
            return channel_result
            
        # 4. 检查事件特定限制
        event_result = self._check_event_limits(request)
        if event_result[0] != ThrottleAction.ALLOW:
            return event_result
            
        # 5. 检查优先级权重
        priority_result = self._check_priority_limits(request)
        if priority_result[0] != ThrottleAction.ALLOW:
            return priority_result
            
        # 6. 记录通知并允许
        self._record_notification(request)
        self.stats['allowed'] += 1
        return ThrottleAction.ALLOW, "通知已允许发送", None
        
    def _check_duplicate(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查重复通知"""
        content_hash = request.get_content_hash()
        current_time = time.time()
        
        # 配置重复检测窗口（默认5分钟）
        duplicate_window = self.config.get('notifications', {}).get('duplicate_window', 300)
        
        if content_hash in self.duplicate_cache:
            last_time, count = self.duplicate_cache[content_hash]
            
            # 在重复窗口内
            if current_time - last_time < duplicate_window:
                # 更新计数
                self.duplicate_cache[content_hash] = (current_time, count + 1)
                
                # 如果是关键通知，允许少量重复
                if request.priority == NotificationPriority.CRITICAL and count < 2:
                    return ThrottleAction.ALLOW, f"关键重复通知(#{count + 1})", None
                
                self.stats['duplicates_filtered'] += 1
                return ThrottleAction.BLOCK, f"重复通知已过滤(#{count + 1})", None
            else:
                # 超出重复窗口，重置计数
                self.duplicate_cache[content_hash] = (current_time, 1)
        else:
            # 首次出现
            self.duplicate_cache[content_hash] = (current_time, 1)
            
        return ThrottleAction.ALLOW, "", None
        
    def _check_global_limits(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查全局频率限制"""
        global_limits = self.rate_limits['global']
        current_time = time.time()
        
        # 检查每分钟限制
        minute_count = self._get_notification_count('global', 60)
        max_per_minute = global_limits['max_per_minute']
        
        if minute_count >= max_per_minute:
            # 检查是否是突发流量
            burst_count = self._get_notification_count('global', global_limits['burst_window'])
            if burst_count >= global_limits['burst_limit']:
                self.stats['blocked'] += 1
                return ThrottleAction.BLOCK, f"全局频率限制({minute_count}/{max_per_minute}/min)", None
            else:
                # 允许突发，但延迟发送
                delay = self._calculate_delay('global', 60)
                self.stats['delayed'] += 1
                return ThrottleAction.DELAY, f"全局频率接近限制，延迟{delay}秒", delay
                
        # 检查每小时限制
        hour_count = self._get_notification_count('global', 3600)
        max_per_hour = global_limits['max_per_hour']
        
        if hour_count >= max_per_hour:
            self.stats['blocked'] += 1
            return ThrottleAction.BLOCK, f"全局小时限制({hour_count}/{max_per_hour}/hour)", None
            
        return ThrottleAction.ALLOW, "", None
        
    def _check_channel_limits(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查渠道特定限制"""
        channel_limits = self.rate_limits['by_channel'].get(request.channel, {})
        if not channel_limits:
            return ThrottleAction.ALLOW, "", None
            
        # 检查渠道每分钟限制
        minute_count = self._get_notification_count(f"channel:{request.channel}", 60)
        max_per_minute = channel_limits.get('max_per_minute', 999)
        
        if minute_count >= max_per_minute:
            # 尝试延迟发送
            delay = self._calculate_delay(f"channel:{request.channel}", 60)
            if delay <= 30:  # 最多延迟30秒
                self.stats['delayed'] += 1
                return ThrottleAction.DELAY, f"渠道{request.channel}频率限制，延迟{delay}秒", delay
            else:
                self.stats['blocked'] += 1
                return ThrottleAction.BLOCK, f"渠道{request.channel}频率限制({minute_count}/{max_per_minute}/min)", None
                
        return ThrottleAction.ALLOW, "", None
        
    def _check_event_limits(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查事件特定限制"""
        event_limits = self.rate_limits['by_event'].get(request.event_type, {})
        if not event_limits:
            return ThrottleAction.ALLOW, "", None
            
        # 检查冷却时间
        cooldown = event_limits.get('cooldown', 0)
        if cooldown > 0:
            last_notification_time = self._get_last_notification_time(f"event:{request.event_type}")
            if last_notification_time and (time.time() - last_notification_time) < cooldown:
                remaining_cooldown = cooldown - (time.time() - last_notification_time)
                self.stats['blocked'] += 1
                return ThrottleAction.BLOCK, f"事件{request.event_type}冷却中，剩余{remaining_cooldown:.0f}秒", None
                
        # 检查事件频率限制
        minute_count = self._get_notification_count(f"event:{request.event_type}", 60)
        max_per_minute = event_limits.get('max_per_minute', 999)
        
        if minute_count >= max_per_minute:
            self.stats['blocked'] += 1
            return ThrottleAction.BLOCK, f"事件{request.event_type}频率限制({minute_count}/{max_per_minute}/min)", None
            
        return ThrottleAction.ALLOW, "", None
        
    def _check_priority_limits(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查优先级权重限制"""
        priority_weights = self.rate_limits['priority_weights']
        weight = priority_weights.get(request.priority.name, 0.5)
        
        # 关键优先级总是允许
        if request.priority == NotificationPriority.CRITICAL:
            return ThrottleAction.ALLOW, "", None
            
        # 根据权重调整限制
        current_load = self._calculate_current_load()
        if current_load > (1.0 - weight):
            # 当前负载过高，根据优先级决定处理方式
            if request.priority == NotificationPriority.HIGH:
                delay = min(5, current_load * 10)
                self.stats['delayed'] += 1
                return ThrottleAction.DELAY, f"系统负载高，优先级{request.priority.name}延迟{delay}秒", delay
            else:
                self.stats['blocked'] += 1
                return ThrottleAction.BLOCK, f"系统负载高，{request.priority.name}优先级通知被阻止", None
                
        return ThrottleAction.ALLOW, "", None
        
    def _get_notification_count(self, key: str, window_seconds: int) -> int:
        """获取指定时间窗口内的通知计数"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        history = self.notification_history[key]
        return sum(1 for timestamp in history if timestamp >= cutoff_time)
        
    def _get_last_notification_time(self, key: str) -> Optional[float]:
        """获取最后一次通知时间"""
        history = self.notification_history[key]
        return history[-1] if history else None
        
    def _calculate_delay(self, key: str, window_seconds: int) -> float:
        """计算合适的延迟时间"""
        current_count = self._get_notification_count(key, window_seconds)
        if current_count == 0:
            return 0
            
        # 基于当前频率计算延迟
        history = self.notification_history[key]
        if len(history) < 2:
            return 1
            
        recent_times = list(history)[-min(10, len(history)):]  # 最近10次
        if len(recent_times) < 2:
            return 1
            
        avg_interval = (recent_times[-1] - recent_times[0]) / (len(recent_times) - 1)
        suggested_delay = max(1, window_seconds / current_count - avg_interval)
        
        return min(suggested_delay, 60)  # 最多延迟60秒
        
    def _calculate_current_load(self) -> float:
        """计算当前系统负载"""
        current_time = time.time()
        
        # 计算最近1分钟的全局通知数
        minute_count = self._get_notification_count('global', 60)
        max_per_minute = self.rate_limits['global']['max_per_minute']
        
        return minute_count / max_per_minute if max_per_minute > 0 else 0
        
    def _record_notification(self, request: NotificationRequest):
        """记录通知发送"""
        current_time = time.time()
        
        # 记录到各种历史中
        self.notification_history['global'].append(current_time)
        self.notification_history[f'channel:{request.channel}'].append(current_time)
        self.notification_history[f'event:{request.event_type}'].append(current_time)
        
    def add_delayed_notification(self, request: NotificationRequest, delay_seconds: float):
        """添加延迟通知"""
        execute_at = time.time() + delay_seconds
        self.delayed_notifications.append((execute_at, request))
        
    def get_ready_notifications(self) -> List[NotificationRequest]:
        """获取准备发送的延迟通知"""
        current_time = time.time()
        ready_notifications = []
        
        # 分离准备好的和未准备好的通知
        remaining_notifications = []
        for execute_at, request in self.delayed_notifications:
            if execute_at <= current_time:
                ready_notifications.append(request)
            else:
                remaining_notifications.append((execute_at, request))
                
        self.delayed_notifications = remaining_notifications
        return ready_notifications
        
    def get_throttle_stats(self) -> Dict[str, Any]:
        """获取节流统计信息"""
        return {
            'stats': self.stats.copy(),
            'current_load': self._calculate_current_load(),
            'delayed_count': len(self.delayed_notifications),
            'duplicate_cache_size': len(self.duplicate_cache),
            'rate_limits': self.rate_limits,
            'recent_activity': {
                'global_1min': self._get_notification_count('global', 60),
                'global_1hour': self._get_notification_count('global', 3600)
            }
        }
        
    def cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 清理重复检测缓存（保留1小时）
        expired_hashes = [
            h for h, (last_time, _) in self.duplicate_cache.items()
            if current_time - last_time > 3600
        ]
        
        for h in expired_hashes:
            del self.duplicate_cache[h]
            
        # 清理通知历史（保留24小时）
        cutoff_time = current_time - 86400
        for key in self.notification_history:
            history = self.notification_history[key]
            while history and history[0] < cutoff_time:
                history.popleft()
                
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {key: 0 for key in self.stats}
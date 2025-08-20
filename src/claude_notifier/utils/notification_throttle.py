#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知频率控制系统 - Notification Throttle
智能管理通知发送频率，防止通知轰炸
从原有utils/notification_throttle.py迁移而来，适配新轻量化架构
"""

import time
import hashlib
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
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
    created_at: float = field(default_factory=time.time)
    
    def get_content_hash(self) -> str:
        """获取内容哈希，用于检测重复通知"""
        # 使用更稳定的内容来生成哈希
        key_content = {
            'event_type': self.event_type,
            'channel': self.channel,
            'project': self.content.get('project', ''),
            'operation': self.content.get('operation', ''),
            'error': self.content.get('error', ''),
            'title': self.content.get('title', ''),
        }
        content_str = '|'.join(f"{k}:{v}" for k, v in key_content.items())
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:8]


class NotificationThrottle:
    """通知频率控制器 - 轻量级智能版本"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化通知频率控制器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 频率限制配置
        self.rate_limits = self._load_rate_limits()
        
        # 通知历史记录 (使用deque自动限制大小)
        self.notification_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
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
        
        # 自动清理定时器
        self._last_cleanup = time.time()
        
    def _load_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """加载频率限制配置"""
        # 默认轻量级限制配置
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
                'serverchan': {'max_per_minute': 5, 'max_per_hour': 50},
                'wechat_work': {'max_per_minute': 10, 'max_per_hour': 100}
            },
            'by_event': {
                'sensitive_operation': {'max_per_minute': 3, 'cooldown': 30},
                'task_completion': {'max_per_minute': 2, 'cooldown': 60},
                'rate_limit': {'max_per_minute': 1, 'cooldown': 300},
                'error_occurred': {'max_per_minute': 5, 'cooldown': 10},
                'idle_detected': {'max_per_minute': 1, 'cooldown': 1800}
            },
            'priority_weights': {
                'CRITICAL': 1.0,    # 不限制
                'HIGH': 0.8,        # 轻微限制
                'NORMAL': 0.6,      # 正常限制
                'LOW': 0.3          # 严格限制
            }
        }
        
        # 合并用户配置
        throttle_config = self.config.get('intelligent_limiting', {}).get('notification_throttle', {})
        user_limits = throttle_config.get('rate_limits', {})
        
        if user_limits:
            # 深度合并配置
            for category, limits in user_limits.items():
                if category in default_limits and isinstance(limits, dict):
                    if isinstance(default_limits[category], dict):
                        default_limits[category].update(limits)
                    else:
                        default_limits[category] = limits
                else:
                    default_limits[category] = limits
                    
        return default_limits
        
    def should_allow_notification(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查是否允许发送通知
        
        Args:
            request: 通知请求
            
        Returns:
            (节流动作, 说明信息, 延迟时间)
        """
        # 定期清理缓存
        self._periodic_cleanup()
        
        try:
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
            
        except Exception as e:
            self.logger.error(f"节流检查异常: {e}")
            # 出错时默认允许，但记录错误
            return ThrottleAction.ALLOW, f"节流检查异常，默认允许: {str(e)}", None
        
    def _check_duplicate(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """检查重复通知"""
        content_hash = request.get_content_hash()
        current_time = time.time()
        
        # 配置重复检测窗口（默认5分钟）
        duplicate_window = self.config.get('intelligent_limiting', {}).get('notification_throttle', {}).get('duplicate_window', 300)
        
        if content_hash in self.duplicate_cache:
            last_time, count = self.duplicate_cache[content_hash]
            
            # 在重复窗口内
            if current_time - last_time < duplicate_window:
                # 更新计数
                self.duplicate_cache[content_hash] = (current_time, count + 1)
                
                # 关键通知允许少量重复
                if request.priority == NotificationPriority.CRITICAL and count < 3:
                    self._record_notification(request)
                    self.stats['allowed'] += 1
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
                return ThrottleAction.DELAY, f"全局频率接近限制，延迟{delay:.1f}秒", delay
                
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
                return ThrottleAction.DELAY, f"渠道{request.channel}频率限制，延迟{delay:.1f}秒", delay
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
                return ThrottleAction.DELAY, f"系统负载高，优先级{request.priority.name}延迟{delay:.1f}秒", delay
            else:
                self.stats['blocked'] += 1
                return ThrottleAction.BLOCK, f"系统负载高，{request.priority.name}优先级通知被阻止", None
                
        return ThrottleAction.ALLOW, "", None
        
    def _get_notification_count(self, key: str, window_seconds: int) -> int:
        """获取指定时间窗口内的通知计数"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        history = self.notification_history[key]
        count = sum(1 for timestamp in history if timestamp >= cutoff_time)
        return count
        
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
            return 1.0
            
        # 计算平均间隔
        recent_times = list(history)[-min(10, len(history)):]
        if len(recent_times) < 2:
            return 1.0
            
        time_span = recent_times[-1] - recent_times[0]
        if time_span <= 0:
            return 1.0
            
        avg_interval = time_span / (len(recent_times) - 1)
        
        # 建议的延迟时间
        suggested_delay = max(1.0, window_seconds / current_count - avg_interval)
        return min(suggested_delay, 60.0)  # 最多延迟60秒
        
    def _calculate_current_load(self) -> float:
        """计算当前系统负载"""
        # 计算最近1分钟的全局通知数
        minute_count = self._get_notification_count('global', 60)
        max_per_minute = self.rate_limits['global']['max_per_minute']
        
        return min(1.0, minute_count / max_per_minute) if max_per_minute > 0 else 0.0
        
    def _record_notification(self, request: NotificationRequest):
        """记录通知发送"""
        current_time = time.time()
        
        # 记录到各种历史中
        self.notification_history['global'].append(current_time)
        self.notification_history[f'channel:{request.channel}'].append(current_time)
        self.notification_history[f'event:{request.event_type}'].append(current_time)
        
    def add_delayed_notification(self, request: NotificationRequest, delay_seconds: float):
        """添加延迟通知
        
        Args:
            request: 通知请求
            delay_seconds: 延迟秒数
        """
        execute_at = time.time() + delay_seconds
        self.delayed_notifications.append((execute_at, request))
        self.logger.debug(f"添加延迟通知: {request.notification_id}，延迟{delay_seconds:.1f}秒")
        
    def get_ready_notifications(self) -> List[NotificationRequest]:
        """获取准备发送的延迟通知
        
        Returns:
            准备发送的通知请求列表
        """
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
        
        if ready_notifications:
            self.logger.debug(f"获取到{len(ready_notifications)}个延迟通知可以发送")
            
        return ready_notifications
        
    def get_throttle_stats(self) -> Dict[str, Any]:
        """获取节流统计信息
        
        Returns:
            统计信息字典
        """
        current_load = self._calculate_current_load()
        
        return {
            'enabled': True,
            'stats': self.stats.copy(),
            'current_load': current_load,
            'load_status': self._get_load_status(current_load),
            'delayed_count': len(self.delayed_notifications),
            'duplicate_cache_size': len(self.duplicate_cache),
            'active_channels': len([k for k in self.notification_history.keys() if k.startswith('channel:') and self.notification_history[k]]),
            'recent_activity': {
                'global_1min': self._get_notification_count('global', 60),
                'global_5min': self._get_notification_count('global', 300),
                'global_1hour': self._get_notification_count('global', 3600)
            }
        }
        
    def _get_load_status(self, load: float) -> str:
        """获取负载状态描述"""
        if load < 0.3:
            return "低"
        elif load < 0.6:
            return "正常"
        elif load < 0.8:
            return "中等"
        elif load < 0.95:
            return "高"
        else:
            return "过载"
        
    def _periodic_cleanup(self):
        """定期清理缓存"""
        current_time = time.time()
        
        # 每5分钟清理一次
        if current_time - self._last_cleanup > 300:
            self.cleanup_cache()
            self._last_cleanup = current_time
            
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
            
        self.logger.debug(f"清理了{len(expired_hashes)}个过期的重复检测缓存")
        
        # 清理过期的延迟通知（超过1小时的）
        original_delayed_count = len(self.delayed_notifications)
        self.delayed_notifications = [
            (execute_at, request) for execute_at, request in self.delayed_notifications
            if execute_at > current_time - 3600
        ]
        
        cleaned_delayed = original_delayed_count - len(self.delayed_notifications)
        if cleaned_delayed > 0:
            self.logger.debug(f"清理了{cleaned_delayed}个过期的延迟通知")
            
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {key: 0 for key in self.stats}
        self.logger.info("已重置节流统计信息")
        
    def configure_limits(self, **kwargs):
        """动态配置限流参数
        
        Args:
            **kwargs: 配置参数
        """
        for category, limits in kwargs.items():
            if category in self.rate_limits and isinstance(limits, dict):
                self.rate_limits[category].update(limits)
                self.logger.info(f"更新限流配置: {category}")
            else:
                self.logger.warning(f"未知限流配置类别: {category}")
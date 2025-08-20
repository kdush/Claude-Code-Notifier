#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
冷却机制管理器 - Cooldown Manager
智能冷却策略，防止过度通知和操作
"""

import time
import logging
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from .time_utils import TimeManager


class CooldownType(Enum):
    """冷却类型枚举"""
    STATIC = "static"          # 静态冷却（固定时间）
    EXPONENTIAL = "exponential"  # 指数退避冷却
    ADAPTIVE = "adaptive"      # 自适应冷却
    SLIDING = "sliding"        # 滑动窗口冷却


class CooldownScope(Enum):
    """冷却范围枚举"""
    EVENT_TYPE = "event_type"      # 按事件类型冷却
    CHANNEL = "channel"            # 按通知渠道冷却
    CONTENT_HASH = "content_hash"  # 按内容哈希冷却
    PROJECT = "project"            # 按项目冷却
    GLOBAL = "global"              # 全局冷却


@dataclass
class CooldownRule:
    """冷却规则定义"""
    scope: CooldownScope
    cooldown_type: CooldownType
    base_duration: float          # 基础冷却时间（秒）
    max_duration: float = 3600    # 最大冷却时间（秒）
    min_duration: float = 1       # 最小冷却时间（秒）
    multiplier: float = 2.0       # 指数退避倍数
    decay_factor: float = 0.5     # 衰减因子
    trigger_count: int = 1        # 触发阈值
    window_size: int = 300        # 时间窗口大小（秒）
    priority_bypass: Set[str] = field(default_factory=set)  # 可绕过优先级


@dataclass
class CooldownState:
    """冷却状态记录"""
    key: str
    rule: CooldownRule
    start_time: float
    end_time: float
    trigger_count: int = 0
    last_trigger: float = 0
    history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def is_active(self) -> bool:
        return time.time() < self.end_time
        
    @property
    def remaining_time(self) -> float:
        return max(0, self.end_time - time.time())
        
    def add_trigger(self, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()
        self.trigger_count += 1
        self.last_trigger = timestamp
        self.history.append(timestamp)


class CooldownManager:
    """冷却管理器 - 智能冷却策略核心"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.time_manager = TimeManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 冷却规则和状态
        self.cooldown_rules = self._load_cooldown_rules()
        self.cooldown_states: Dict[str, CooldownState] = {}
        self.state_lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'cooldowns_applied': 0,
            'cooldowns_bypassed': 0,
            'cooldowns_expired': 0,
            'cooldowns_reset': 0
        }
        
        # 启动清理线程
        self._start_cleanup_thread()
        
    def _load_cooldown_rules(self) -> List[CooldownRule]:
        """加载冷却规则配置"""
        default_rules = [
            # 事件类型冷却规则
            CooldownRule(
                scope=CooldownScope.EVENT_TYPE,
                cooldown_type=CooldownType.STATIC,
                base_duration=60,
                trigger_count=1
            ),
            
            # 敏感操作指数退避
            CooldownRule(
                scope=CooldownScope.CONTENT_HASH,
                cooldown_type=CooldownType.EXPONENTIAL,
                base_duration=30,
                max_duration=1800,
                multiplier=2.0,
                trigger_count=3,
                priority_bypass={'critical'}
            ),
            
            # 渠道自适应冷却
            CooldownRule(
                scope=CooldownScope.CHANNEL,
                cooldown_type=CooldownType.ADAPTIVE,
                base_duration=10,
                max_duration=300,
                window_size=60,
                trigger_count=5
            ),
            
            # 项目滑动窗口冷却
            CooldownRule(
                scope=CooldownScope.PROJECT,
                cooldown_type=CooldownType.SLIDING,
                base_duration=120,
                window_size=600,
                trigger_count=10
            ),
            
            # 全局冷却保护
            CooldownRule(
                scope=CooldownScope.GLOBAL,
                cooldown_type=CooldownType.EXPONENTIAL,
                base_duration=5,
                max_duration=60,
                trigger_count=20,
                window_size=60
            )
        ]
        
        # 从配置加载自定义规则
        custom_rules_config = self.config.get('cooldown', {}).get('rules', [])
        for rule_config in custom_rules_config:
            try:
                rule = self._parse_rule_config(rule_config)
                default_rules.append(rule)
            except Exception as e:
                self.logger.error(f"解析冷却规则失败: {e}")
                
        return default_rules
        
    def _parse_rule_config(self, rule_config: Dict[str, Any]) -> CooldownRule:
        """解析规则配置"""
        return CooldownRule(
            scope=CooldownScope(rule_config['scope']),
            cooldown_type=CooldownType(rule_config['type']),
            base_duration=rule_config['base_duration'],
            max_duration=rule_config.get('max_duration', 3600),
            min_duration=rule_config.get('min_duration', 1),
            multiplier=rule_config.get('multiplier', 2.0),
            decay_factor=rule_config.get('decay_factor', 0.5),
            trigger_count=rule_config.get('trigger_count', 1),
            window_size=rule_config.get('window_size', 300),
            priority_bypass=set(rule_config.get('priority_bypass', []))
        )
        
    def should_cooldown(self, event_context: Dict[str, Any], priority: str = 'normal') -> Tuple[bool, str, Optional[float]]:
        """检查是否应该进入冷却"""
        current_time = time.time()
        
        for rule in self.cooldown_rules:
            key = self._generate_key(rule.scope, event_context)
            
            with self.state_lock:
                # 检查优先级绕过
                if priority in rule.priority_bypass:
                    continue
                    
                # 获取或创建冷却状态
                state = self.cooldown_states.get(key)
                if state is None:
                    state = CooldownState(
                        key=key,
                        rule=rule,
                        start_time=current_time,
                        end_time=current_time
                    )
                    self.cooldown_states[key] = state
                    
                # 检查当前冷却是否激活
                if state.is_active:
                    return True, f"冷却中 ({rule.scope.value})", state.remaining_time
                    
                # 检查是否应该启动新的冷却
                if self._should_start_cooldown(state, current_time):
                    cooldown_duration = self._calculate_cooldown_duration(state, current_time)
                    state.start_time = current_time
                    state.end_time = current_time + cooldown_duration
                    state.add_trigger(current_time)
                    
                    self.stats['cooldowns_applied'] += 1
                    
                    return True, f"触发冷却 ({rule.scope.value})", cooldown_duration
                    
        return False, "", None
        
    def _generate_key(self, scope: CooldownScope, context: Dict[str, Any]) -> str:
        """生成冷却状态键"""
        if scope == CooldownScope.EVENT_TYPE:
            return f"event:{context.get('event_type', 'unknown')}"
        elif scope == CooldownScope.CHANNEL:
            return f"channel:{context.get('channel', 'unknown')}"
        elif scope == CooldownScope.CONTENT_HASH:
            content_str = f"{context.get('event_type', '')}:{context.get('content', {})}"
            import hashlib
            return f"content:{hashlib.md5(content_str.encode()).hexdigest()[:8]}"
        elif scope == CooldownScope.PROJECT:
            return f"project:{context.get('project', 'unknown')}"
        elif scope == CooldownScope.GLOBAL:
            return "global"
        else:
            return f"unknown:{scope.value}"
            
    def _should_start_cooldown(self, state: CooldownState, current_time: float) -> bool:
        """判断是否应该启动冷却"""
        rule = state.rule
        
        # 检查触发次数
        if rule.cooldown_type == CooldownType.SLIDING:
            # 滑动窗口：检查窗口内触发次数
            window_start = current_time - rule.window_size
            recent_triggers = sum(1 for ts in state.history if ts >= window_start)
            return recent_triggers >= rule.trigger_count
        else:
            # 其他类型：累积触发次数
            return state.trigger_count >= rule.trigger_count
            
    def _calculate_cooldown_duration(self, state: CooldownState, current_time: float) -> float:
        """计算冷却持续时间"""
        rule = state.rule
        
        if rule.cooldown_type == CooldownType.STATIC:
            return rule.base_duration
            
        elif rule.cooldown_type == CooldownType.EXPONENTIAL:
            # 指数退避：每次触发时间翻倍
            duration = rule.base_duration * (rule.multiplier ** (state.trigger_count - 1))
            return min(duration, rule.max_duration)
            
        elif rule.cooldown_type == CooldownType.ADAPTIVE:
            # 自适应：根据最近活动频率调整
            recent_frequency = self._calculate_recent_frequency(state, current_time)
            if recent_frequency > 0:
                # 频率越高，冷却时间越长
                adaptive_factor = min(recent_frequency / 10, 5.0)  # 最多5倍
                duration = rule.base_duration * adaptive_factor
                return min(duration, rule.max_duration)
            return rule.base_duration
            
        elif rule.cooldown_type == CooldownType.SLIDING:
            # 滑动窗口：基于窗口内触发密度
            window_start = current_time - rule.window_size
            recent_count = sum(1 for ts in state.history if ts >= window_start)
            density = recent_count / rule.window_size * 60  # 每分钟触发次数
            duration = rule.base_duration * max(1, density / 2)
            return min(duration, rule.max_duration)
            
        return rule.base_duration
        
    def _calculate_recent_frequency(self, state: CooldownState, current_time: float) -> float:
        """计算最近活动频率"""
        if len(state.history) < 2:
            return 0
            
        # 计算最近10次触发的平均间隔
        recent_triggers = list(state.history)[-10:]
        if len(recent_triggers) < 2:
            return 0
            
        time_span = recent_triggers[-1] - recent_triggers[0]
        if time_span <= 0:
            return 0
            
        return len(recent_triggers) / time_span * 60  # 每分钟频率
        
    def force_cooldown(self, scope: str, key: str, duration: float, reason: str = "手动冷却"):
        """强制启动冷却"""
        current_time = time.time()
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            # 创建虚拟规则用于强制冷却
            dummy_rule = CooldownRule(
                scope=CooldownScope.GLOBAL,  # 使用全局作为占位符
                cooldown_type=CooldownType.STATIC,
                base_duration=duration
            )
            
            state = CooldownState(
                key=cooldown_key,
                rule=dummy_rule,
                start_time=current_time,
                end_time=current_time + duration
            )
            state.add_trigger(current_time)
            
            self.cooldown_states[cooldown_key] = state
            self.stats['cooldowns_applied'] += 1
            
        self.logger.info(f"强制冷却已应用: {cooldown_key}, 时长: {duration}秒, 原因: {reason}")
        
    def cancel_cooldown(self, scope: str, key: str) -> bool:
        """取消冷却"""
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            if cooldown_key in self.cooldown_states:
                del self.cooldown_states[cooldown_key]
                self.stats['cooldowns_reset'] += 1
                self.logger.info(f"冷却已取消: {cooldown_key}")
                return True
                
        return False
        
    def reset_cooldown_counter(self, scope: str, key: str) -> bool:
        """重置冷却计数器"""
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            if cooldown_key in self.cooldown_states:
                state = self.cooldown_states[cooldown_key]
                state.trigger_count = 0
                state.history.clear()
                self.stats['cooldowns_reset'] += 1
                self.logger.info(f"冷却计数器已重置: {cooldown_key}")
                return True
                
        return False
        
    def get_cooldown_status(self, scope: str = None, key: str = None) -> Dict[str, Any]:
        """获取冷却状态"""
        current_time = time.time()
        
        with self.state_lock:
            if scope and key:
                # 获取特定冷却状态
                cooldown_key = f"{scope}:{key}"
                state = self.cooldown_states.get(cooldown_key)
                if state:
                    return {
                        'key': cooldown_key,
                        'active': state.is_active,
                        'remaining': state.remaining_time,
                        'trigger_count': state.trigger_count,
                        'rule_type': state.rule.cooldown_type.value,
                        'scope': state.rule.scope.value
                    }
                return {'key': cooldown_key, 'active': False}
            else:
                # 获取所有冷却状态摘要
                active_cooldowns = []
                total_cooldowns = len(self.cooldown_states)
                
                for state in self.cooldown_states.values():
                    if state.is_active:
                        active_cooldowns.append({
                            'key': state.key,
                            'remaining': state.remaining_time,
                            'rule_type': state.rule.cooldown_type.value,
                            'scope': state.rule.scope.value
                        })
                        
                return {
                    'total_cooldowns': total_cooldowns,
                    'active_cooldowns': len(active_cooldowns),
                    'active_details': active_cooldowns,
                    'statistics': self.stats.copy()
                }
                
    def cleanup_expired_cooldowns(self):
        """清理过期的冷却状态"""
        current_time = time.time()
        expired_keys = []
        
        with self.state_lock:
            for key, state in self.cooldown_states.items():
                if not state.is_active and (current_time - state.end_time) > 3600:  # 1小时后清理
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self.cooldown_states[key]
                self.stats['cooldowns_expired'] += 1
                
        if expired_keys:
            self.logger.debug(f"清理了{len(expired_keys)}个过期冷却状态")
            
    def export_cooldown_data(self) -> Dict[str, Any]:
        """导出冷却数据用于持久化"""
        with self.state_lock:
            export_data = {
                'version': '1.0',
                'timestamp': time.time(),
                'states': {}
            }
            
            for key, state in self.cooldown_states.items():
                export_data['states'][key] = {
                    'start_time': state.start_time,
                    'end_time': state.end_time,
                    'trigger_count': state.trigger_count,
                    'last_trigger': state.last_trigger,
                    'history': list(state.history)
                }
                
            return export_data
            
    def import_cooldown_data(self, data: Dict[str, Any]):
        """从持久化数据导入冷却状态"""
        if data.get('version') != '1.0':
            self.logger.warning("不兼容的冷却数据版本")
            return
            
        current_time = time.time()
        imported_count = 0
        
        with self.state_lock:
            for key, state_data in data.get('states', {}).items():
                # 只导入仍然活跃的冷却状态
                if state_data['end_time'] > current_time:
                    # 需要重新关联规则（简化版本，使用默认规则）
                    dummy_rule = self.cooldown_rules[0] if self.cooldown_rules else CooldownRule(
                        scope=CooldownScope.GLOBAL,
                        cooldown_type=CooldownType.STATIC,
                        base_duration=60
                    )
                    
                    state = CooldownState(
                        key=key,
                        rule=dummy_rule,
                        start_time=state_data['start_time'],
                        end_time=state_data['end_time'],
                        trigger_count=state_data.get('trigger_count', 0),
                        last_trigger=state_data.get('last_trigger', 0)
                    )
                    
                    # 恢复历史记录
                    for ts in state_data.get('history', []):
                        if current_time - ts < 3600:  # 只保留1小时内的历史
                            state.history.append(ts)
                            
                    self.cooldown_states[key] = state
                    imported_count += 1
                    
        self.logger.info(f"成功导入{imported_count}个冷却状态")
        
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_expired_cooldowns()
                    time.sleep(300)  # 每5分钟清理一次
                except Exception as e:
                    self.logger.error(f"冷却清理线程异常: {e}")
                    time.sleep(60)
                    
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        with self.state_lock:
            # 统计不同类型的冷却
            type_counts = defaultdict(int)
            scope_counts = defaultdict(int)
            active_count = 0
            
            for state in self.cooldown_states.values():
                type_counts[state.rule.cooldown_type.value] += 1
                scope_counts[state.rule.scope.value] += 1
                if state.is_active:
                    active_count += 1
                    
            return {
                'total_states': len(self.cooldown_states),
                'active_states': active_count,
                'type_distribution': dict(type_counts),
                'scope_distribution': dict(scope_counts),
                'lifetime_stats': self.stats.copy(),
                'rules_count': len(self.cooldown_rules)
            }
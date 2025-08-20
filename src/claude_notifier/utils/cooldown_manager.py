#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
冷却机制管理器 - Cooldown Manager
智能冷却策略，防止过度通知和操作
从原有utils/cooldown_manager.py迁移而来，适配新轻量化架构
"""

import time
import logging
import threading
import json
import hashlib
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
        """检查冷却是否激活"""
        return time.time() < self.end_time
        
    @property
    def remaining_time(self) -> float:
        """获取剩余冷却时间"""
        return max(0, self.end_time - time.time())
        
    def add_trigger(self, timestamp: float = None):
        """添加触发记录"""
        if timestamp is None:
            timestamp = time.time()
        self.trigger_count += 1
        self.last_trigger = timestamp
        self.history.append(timestamp)


class CooldownManager:
    """冷却管理器 - 智能冷却策略核心"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化冷却管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        try:
            self.time_manager = TimeManager()
        except Exception as e:
            # 如果TimeManager初始化失败，使用简化版本
            self.time_manager = None
            
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
        
        # 控制标志
        self._running = True
        
        # 启动清理线程
        self._start_cleanup_thread()
        
    def _load_cooldown_rules(self) -> List[CooldownRule]:
        """加载冷却规则配置"""
        default_rules = [
            # 敏感操作指数退避
            CooldownRule(
                scope=CooldownScope.EVENT_TYPE,
                cooldown_type=CooldownType.EXPONENTIAL,
                base_duration=30,
                max_duration=1800,
                multiplier=2.0,
                trigger_count=2,
                priority_bypass={'critical'}
            ),
            
            # 通知渠道自适应冷却
            CooldownRule(
                scope=CooldownScope.CHANNEL,
                cooldown_type=CooldownType.ADAPTIVE,
                base_duration=10,
                max_duration=300,
                window_size=60,
                trigger_count=5
            ),
            
            # 项目级别滑动窗口冷却
            CooldownRule(
                scope=CooldownScope.PROJECT,
                cooldown_type=CooldownType.SLIDING,
                base_duration=120,
                window_size=600,
                trigger_count=8
            ),
            
            # 内容哈希静态冷却
            CooldownRule(
                scope=CooldownScope.CONTENT_HASH,
                cooldown_type=CooldownType.STATIC,
                base_duration=300,  # 5分钟
                trigger_count=1,
                priority_bypass={'critical', 'high'}
            ),
            
            # 全局冷却保护
            CooldownRule(
                scope=CooldownScope.GLOBAL,
                cooldown_type=CooldownType.EXPONENTIAL,
                base_duration=5,
                max_duration=60,
                trigger_count=15,
                window_size=60
            )
        ]
        
        # 从配置加载自定义规则
        cooldown_config = self.config.get('intelligent_limiting', {}).get('cooldown_manager', {})
        custom_rules_config = cooldown_config.get('rules', [])
        
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
        """检查是否应该进入冷却
        
        Args:
            event_context: 事件上下文
            priority: 优先级
            
        Returns:
            (是否应该冷却, 原因, 剩余时间)
        """
        if not self._running:
            return False, "冷却管理器已停止", None
            
        current_time = time.time()
        
        try:
            for rule in self.cooldown_rules:
                key = self._generate_key(rule.scope, event_context)
                
                with self.state_lock:
                    # 检查优先级绕过
                    if priority.lower() in rule.priority_bypass:
                        self.stats['cooldowns_bypassed'] += 1
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
                        
        except Exception as e:
            self.logger.error(f"冷却检查异常: {e}")
            return False, f"冷却检查异常: {str(e)}", None
            
        return False, "", None
        
    def _generate_key(self, scope: CooldownScope, context: Dict[str, Any]) -> str:
        """生成冷却状态键"""
        if scope == CooldownScope.EVENT_TYPE:
            return f"event:{context.get('event_type', 'unknown')}"
        elif scope == CooldownScope.CHANNEL:
            return f"channel:{context.get('channel', 'unknown')}"
        elif scope == CooldownScope.CONTENT_HASH:
            # 生成内容哈希
            content_str = json.dumps({
                'event_type': context.get('event_type', ''),
                'title': context.get('title', ''),
                'content': str(context.get('content', '')),
                'operation': context.get('operation', '')
            }, sort_keys=True)
            content_hash = hashlib.md5(content_str.encode('utf-8')).hexdigest()[:8]
            return f"content:{content_hash}"
        elif scope == CooldownScope.PROJECT:
            return f"project:{context.get('project', 'unknown')}"
        elif scope == CooldownScope.GLOBAL:
            return "global"
        else:
            return f"unknown:{scope.value}"
            
    def _should_start_cooldown(self, state: CooldownState, current_time: float) -> bool:
        """判断是否应该启动冷却"""
        rule = state.rule
        
        try:
            if rule.cooldown_type == CooldownType.SLIDING:
                # 滑动窗口：检查窗口内触发次数
                window_start = current_time - rule.window_size
                recent_triggers = sum(1 for ts in state.history if ts >= window_start)
                return recent_triggers >= rule.trigger_count
            else:
                # 其他类型：累积触发次数（考虑时间衰减）
                if rule.window_size > 0:
                    # 在时间窗口内才计算触发
                    window_start = current_time - rule.window_size
                    recent_triggers = sum(1 for ts in state.history if ts >= window_start)
                    return recent_triggers >= rule.trigger_count
                else:
                    # 累积计数
                    return state.trigger_count >= rule.trigger_count
                    
        except Exception as e:
            self.logger.error(f"冷却触发检查异常: {e}")
            return False
            
    def _calculate_cooldown_duration(self, state: CooldownState, current_time: float) -> float:
        """计算冷却持续时间"""
        rule = state.rule
        
        try:
            if rule.cooldown_type == CooldownType.STATIC:
                return rule.base_duration
                
            elif rule.cooldown_type == CooldownType.EXPONENTIAL:
                # 指数退避：每次触发时间翻倍
                power = max(0, state.trigger_count - rule.trigger_count)
                duration = rule.base_duration * (rule.multiplier ** power)
                return min(max(duration, rule.min_duration), rule.max_duration)
                
            elif rule.cooldown_type == CooldownType.ADAPTIVE:
                # 自适应：根据最近活动频率调整
                recent_frequency = self._calculate_recent_frequency(state, current_time)
                if recent_frequency > 0:
                    # 频率越高，冷却时间越长
                    adaptive_factor = min(recent_frequency / 10, 5.0)  # 最多5倍
                    duration = rule.base_duration * adaptive_factor
                    return min(max(duration, rule.min_duration), rule.max_duration)
                return rule.base_duration
                
            elif rule.cooldown_type == CooldownType.SLIDING:
                # 滑动窗口：基于窗口内触发密度
                window_start = current_time - rule.window_size
                recent_count = sum(1 for ts in state.history if ts >= window_start)
                if rule.window_size > 0:
                    density = recent_count / (rule.window_size / 60)  # 每分钟触发次数
                    duration = rule.base_duration * max(1, density / 2)
                    return min(max(duration, rule.min_duration), rule.max_duration)
                return rule.base_duration
                
        except Exception as e:
            self.logger.error(f"冷却时间计算异常: {e}")
            
        return rule.base_duration
        
    def _calculate_recent_frequency(self, state: CooldownState, current_time: float) -> float:
        """计算最近活动频率"""
        if len(state.history) < 2:
            return 0
            
        try:
            # 计算最近10次触发的平均间隔
            recent_triggers = list(state.history)[-10:]
            if len(recent_triggers) < 2:
                return 0
                
            time_span = recent_triggers[-1] - recent_triggers[0]
            if time_span <= 0:
                return 0
                
            return len(recent_triggers) / time_span * 60  # 每分钟频率
            
        except Exception as e:
            self.logger.error(f"频率计算异常: {e}")
            return 0
        
    def force_cooldown(self, scope: str, key: str, duration: float, reason: str = "手动冷却"):
        """强制启动冷却
        
        Args:
            scope: 冷却范围
            key: 冷却键
            duration: 冷却时长（秒）
            reason: 冷却原因
        """
        current_time = time.time()
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            # 创建虚拟规则用于强制冷却
            dummy_rule = CooldownRule(
                scope=CooldownScope.GLOBAL,
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
        """取消冷却
        
        Args:
            scope: 冷却范围
            key: 冷却键
            
        Returns:
            是否成功取消
        """
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            if cooldown_key in self.cooldown_states:
                del self.cooldown_states[cooldown_key]
                self.stats['cooldowns_reset'] += 1
                self.logger.info(f"冷却已取消: {cooldown_key}")
                return True
                
        return False
        
    def reset_cooldown_counter(self, scope: str, key: str) -> bool:
        """重置冷却计数器
        
        Args:
            scope: 冷却范围
            key: 冷却键
            
        Returns:
            是否成功重置
        """
        cooldown_key = f"{scope}:{key}"
        
        with self.state_lock:
            if cooldown_key in self.cooldown_states:
                state = self.cooldown_states[cooldown_key]
                state.trigger_count = 0
                state.history.clear()
                state.end_time = time.time()  # 立即结束当前冷却
                self.stats['cooldowns_reset'] += 1
                self.logger.info(f"冷却计数器已重置: {cooldown_key}")
                return True
                
        return False
        
    def get_cooldown_status(self, scope: str = None, key: str = None) -> Dict[str, Any]:
        """获取冷却状态
        
        Args:
            scope: 冷却范围（可选）
            key: 冷却键（可选）
            
        Returns:
            冷却状态信息
        """
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
                        'scope': state.rule.scope.value,
                        'last_trigger': state.last_trigger
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
                    'enabled': self._running,
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
            for key, state in list(self.cooldown_states.items()):
                # 清理1小时后的非活跃状态
                if not state.is_active and (current_time - state.end_time) > 3600:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                if key in self.cooldown_states:
                    del self.cooldown_states[key]
                    self.stats['cooldowns_expired'] += 1
                
        if expired_keys:
            self.logger.debug(f"清理了{len(expired_keys)}个过期冷却状态")
            
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while self._running:
                try:
                    self.cleanup_expired_cooldowns()
                    time.sleep(300)  # 每5分钟清理一次
                except Exception as e:
                    self.logger.error(f"冷却清理线程异常: {e}")
                    time.sleep(60)
                    
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.debug("冷却管理器清理线程已启动")
        
    def stop(self):
        """停止冷却管理器"""
        self._running = False
        self.logger.info("冷却管理器已停止")
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取详细统计信息
        
        Returns:
            统计信息字典
        """
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
                'enabled': self._running,
                'total_states': len(self.cooldown_states),
                'active_states': active_count,
                'type_distribution': dict(type_counts),
                'scope_distribution': dict(scope_counts),
                'lifetime_stats': self.stats.copy(),
                'rules_count': len(self.cooldown_rules)
            }
            
    def configure_rule(self, rule_index: int, **kwargs):
        """动态配置冷却规则
        
        Args:
            rule_index: 规则索引
            **kwargs: 规则参数
        """
        if 0 <= rule_index < len(self.cooldown_rules):
            rule = self.cooldown_rules[rule_index]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
                    self.logger.info(f"更新冷却规则 {rule_index}: {key}={value}")
        else:
            self.logger.warning(f"无效的规则索引: {rule_index}")
            
    def export_cooldown_data(self) -> Dict[str, Any]:
        """导出冷却数据用于持久化
        
        Returns:
            导出的冷却数据
        """
        with self.state_lock:
            export_data = {
                'version': '1.1',
                'timestamp': time.time(),
                'states': {},
                'stats': self.stats.copy()
            }
            
            for key, state in self.cooldown_states.items():
                if state.is_active or state.trigger_count > 0:  # 只导出有意义的状态
                    export_data['states'][key] = {
                        'start_time': state.start_time,
                        'end_time': state.end_time,
                        'trigger_count': state.trigger_count,
                        'last_trigger': state.last_trigger,
                        'history': list(state.history)[-20:]  # 最多保存最近20条记录
                    }
                    
            return export_data
            
    def import_cooldown_data(self, data: Dict[str, Any]):
        """从持久化数据导入冷却状态
        
        Args:
            data: 导入的冷却数据
        """
        version = data.get('version', '1.0')
        if version not in ['1.0', '1.1']:
            self.logger.warning(f"不兼容的冷却数据版本: {version}")
            return
            
        current_time = time.time()
        imported_count = 0
        
        with self.state_lock:
            # 导入统计信息
            if 'stats' in data and version == '1.1':
                for key, value in data['stats'].items():
                    if key in self.stats:
                        self.stats[key] += value
            
            # 导入状态
            for key, state_data in data.get('states', {}).items():
                try:
                    # 只导入仍然活跃或最近的冷却状态
                    if (state_data['end_time'] > current_time or 
                        (current_time - state_data.get('last_trigger', 0)) < 3600):
                        
                        # 找到合适的规则（简化版本）
                        matching_rule = self._find_rule_for_key(key)
                        if not matching_rule:
                            matching_rule = self.cooldown_rules[0] if self.cooldown_rules else self._create_default_rule()
                        
                        state = CooldownState(
                            key=key,
                            rule=matching_rule,
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
                        
                except Exception as e:
                    self.logger.error(f"导入冷却状态失败 {key}: {e}")
                    
        self.logger.info(f"成功导入{imported_count}个冷却状态")
        
    def _find_rule_for_key(self, key: str) -> Optional[CooldownRule]:
        """为键找到合适的规则"""
        if ':' in key:
            scope_name = key.split(':', 1)[0]
            for rule in self.cooldown_rules:
                if rule.scope.value.replace('_', '') == scope_name.replace('_', ''):
                    return rule
        return None
        
    def _create_default_rule(self) -> CooldownRule:
        """创建默认规则"""
        return CooldownRule(
            scope=CooldownScope.GLOBAL,
            cooldown_type=CooldownType.STATIC,
            base_duration=60
        )
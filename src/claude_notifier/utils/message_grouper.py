#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
消息分组合并系统 - Message Grouper
智能合并相似通知，减少通知轰炸
从原有utils/message_grouper.py迁移而来，适配新轻量化架构
"""

import time
import json
import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class GroupingStrategy(Enum):
    """分组策略枚举"""
    BY_PROJECT = "by_project"
    BY_EVENT_TYPE = "by_event_type"
    BY_CHANNEL = "by_channel"
    BY_CONTENT = "by_content"
    BY_TIME_WINDOW = "by_time_window"
    BY_SIMILARITY = "by_similarity"


class MergeAction(Enum):
    """合并动作枚举"""
    MERGE = "merge"
    GROUP = "group"
    SUPPRESS = "suppress"
    ESCALATE = "escalate"


@dataclass
class MessageGroup:
    """消息组数据结构"""
    group_id: str
    strategy: GroupingStrategy
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    channel: str = ""
    event_type: str = ""
    project: str = ""
    merge_count: int = 0
    priority: int = 1
    
    def add_message(self, message: Dict[str, Any]):
        """添加消息到组"""
        self.messages.append(message)
        self.last_updated = time.time()
        self.merge_count += 1
        
        # 更新优先级（取最高优先级）
        msg_priority = message.get('priority', 1)
        if isinstance(msg_priority, str):
            # 转换字符串优先级到数字
            priority_map = {'low': 1, 'normal': 2, 'high': 3, 'critical': 4}
            msg_priority = priority_map.get(msg_priority.lower(), 2)
        
        self.priority = max(self.priority, msg_priority)
        
    def get_age(self) -> float:
        """获取组年龄（秒）"""
        return time.time() - self.created_at
        
    def get_idle_time(self) -> float:
        """获取闲置时间（秒）"""
        return time.time() - self.last_updated


class MessageGrouper:
    """消息分组合并器 - 轻量级智能版本"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化消息分组器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 分组配置
        self.grouping_config = self._load_grouping_config()
        
        # 活跃的消息组
        self.active_groups: Dict[str, MessageGroup] = {}
        
        # 分组规则
        self.grouping_rules = self._load_grouping_rules()
        
        # 相似度阈值
        self.similarity_threshold = self.grouping_config.get('similarity_threshold', 0.8)
        
        # 统计信息
        self.stats = {
            'groups_created': 0,
            'messages_grouped': 0,
            'messages_merged': 0,
            'groups_sent': 0
        }
        
        # 清理定时器
        self._last_cleanup = time.time()
        
    def _load_grouping_config(self) -> Dict[str, Any]:
        """加载分组配置"""
        default_config = {
            'enabled': True,
            'group_window': 300,          # 分组时间窗口（秒）
            'max_group_size': 10,         # 最大分组大小
            'max_groups': 50,             # 最大同时活跃分组数
            'send_threshold': 5,          # 发送阈值（消息数）
            'send_timeout': 60,           # 发送超时（秒）
            'similarity_threshold': 0.8,  # 相似度阈值
            'merge_strategies': [
                GroupingStrategy.BY_PROJECT,
                GroupingStrategy.BY_EVENT_TYPE,
                GroupingStrategy.BY_TIME_WINDOW
            ]
        }
        
        # 从配置中加载
        grouping_config = self.config.get('intelligent_limiting', {}).get('message_grouper', {})
        user_config = grouping_config.get('grouping', {})
        
        default_config.update(user_config)
        return default_config
        
    def _load_grouping_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载分组规则"""
        default_rules = {
            'sensitive_operation': {
                'strategy': GroupingStrategy.BY_PROJECT,
                'max_size': 3,
                'timeout': 30,
                'priority_boost': True
            },
            'task_completion': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 5,
                'timeout': 120,
                'summary_template': 'batch_completion'
            },
            'rate_limit': {
                'strategy': GroupingStrategy.BY_CONTENT,
                'max_size': 1,
                'timeout': 300,
                'suppress_duplicates': True
            },
            'error_occurred': {
                'strategy': GroupingStrategy.BY_SIMILARITY,
                'max_size': 5,
                'timeout': 60,
                'escalate_threshold': 3
            },
            'session_start': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 10,
                'timeout': 300,
                'summary_only': True
            },
            'idle_detected': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 3,
                'timeout': 1800,  # 30分钟
                'suppress_duplicates': True
            }
        }
        
        # 合并用户自定义规则
        grouping_config = self.config.get('intelligent_limiting', {}).get('message_grouper', {})
        user_rules = grouping_config.get('rules', {})
        
        if user_rules:
            for event_type, rule in user_rules.items():
                if event_type in default_rules:
                    default_rules[event_type].update(rule)
                else:
                    default_rules[event_type] = rule
                    
        return default_rules
        
    def should_group_message(self, message: Dict[str, Any]) -> Tuple[bool, Optional[str], MergeAction]:
        """检查消息是否应该分组
        
        Args:
            message: 消息数据
            
        Returns:
            (是否分组, 分组ID, 合并动作)
        """
        if not self.grouping_config.get('enabled', True):
            return False, None, MergeAction.MERGE
            
        # 定期清理过期组
        self._periodic_cleanup()
        
        try:
            event_type = message.get('event_type', 'unknown')
            channel = message.get('channel', 'unknown')
            project = message.get('project', 'unknown')
            
            # 1. 查找现有组
            existing_group_id = self._find_matching_group(message)
            if existing_group_id:
                group = self.active_groups[existing_group_id]
                
                # 检查组是否已满
                if len(group.messages) >= self._get_max_group_size(event_type):
                    # 立即发送当前组，创建新组
                    return False, existing_group_id, MergeAction.ESCALATE
                    
                # 检查组是否超时
                if group.get_age() > self._get_group_timeout(event_type):
                    return False, existing_group_id, MergeAction.ESCALATE
                    
                return True, existing_group_id, MergeAction.GROUP
                
            # 2. 检查是否应该创建新组
            if self._should_create_group(message):
                group_id = self._create_group(message)
                return True, group_id, MergeAction.GROUP
                
            # 3. 不分组，直接发送
            return False, None, MergeAction.MERGE
            
        except Exception as e:
            self.logger.error(f"分组检查异常: {e}")
            return False, None, MergeAction.MERGE
        
    def _find_matching_group(self, message: Dict[str, Any]) -> Optional[str]:
        """查找匹配的现有分组"""
        event_type = message.get('event_type', '')
        
        # 获取事件对应的分组策略
        rule = self.grouping_rules.get(event_type, {})
        strategy = rule.get('strategy', GroupingStrategy.BY_PROJECT)
        
        for group_id, group in self.active_groups.items():
            if self._messages_match(message, group, strategy):
                return group_id
                
        return None
        
    def _messages_match(self, message: Dict[str, Any], group: MessageGroup, strategy: GroupingStrategy) -> bool:
        """检查消息是否匹配分组"""
        try:
            if strategy == GroupingStrategy.BY_PROJECT:
                return (message.get('project') == group.project and 
                       message.get('channel') == group.channel)
                       
            elif strategy == GroupingStrategy.BY_EVENT_TYPE:
                return (message.get('event_type') == group.event_type and
                       message.get('channel') == group.channel)
                       
            elif strategy == GroupingStrategy.BY_CHANNEL:
                return message.get('channel') == group.channel
                
            elif strategy == GroupingStrategy.BY_TIME_WINDOW:
                window = self.grouping_config.get('group_window', 300)
                return (group.get_age() < window and
                       message.get('channel') == group.channel)
                       
            elif strategy == GroupingStrategy.BY_CONTENT:
                if group.messages:
                    return self._content_similar(message, group.messages[0])
                return False
                
            elif strategy == GroupingStrategy.BY_SIMILARITY:
                if group.messages:
                    # 检查最近3条消息
                    recent_messages = group.messages[-3:] if len(group.messages) > 3 else group.messages
                    return any(self._content_similar(message, msg) for msg in recent_messages)
                return False
                
        except Exception as e:
            self.logger.error(f"消息匹配检查异常: {e}")
            
        return False
        
    def _content_similar(self, msg1: Dict[str, Any], msg2: Dict[str, Any]) -> bool:
        """检查两条消息内容是否相似"""
        try:
            # 提取关键内容进行比较
            def get_content_tokens(msg):
                content_parts = [
                    str(msg.get('event_type', '')),
                    str(msg.get('project', '')),
                    str(msg.get('operation', '')),
                    str(msg.get('status', '')),
                    str(msg.get('title', '')),
                    str(msg.get('error_type', ''))
                ]
                content = ' '.join(filter(None, content_parts))
                return set(content.lower().split())
                
            tokens1 = get_content_tokens(msg1)
            tokens2 = get_content_tokens(msg2)
            
            if not tokens1 or not tokens2:
                return False
                
            intersection = tokens1 & tokens2
            union = tokens1 | tokens2
            
            jaccard_similarity = len(intersection) / len(union) if union else 0
            return jaccard_similarity >= self.similarity_threshold
            
        except Exception as e:
            self.logger.error(f"内容相似度计算异常: {e}")
            return False
        
    def _should_create_group(self, message: Dict[str, Any]) -> bool:
        """检查是否应该创建新分组"""
        # 检查是否达到最大分组数
        if len(self.active_groups) >= self.grouping_config.get('max_groups', 50):
            # 清理过期分组
            self._cleanup_expired_groups()
            
            if len(self.active_groups) >= self.grouping_config.get('max_groups', 50):
                return False
                
        event_type = message.get('event_type', '')
        
        # 检查事件是否支持分组
        if event_type in self.grouping_rules:
            return True
            
        # 默认策略
        return self.grouping_config.get('group_by_default', True)
        
    def _create_group(self, message: Dict[str, Any]) -> str:
        """创建新的消息分组"""
        event_type = message.get('event_type', 'unknown')
        channel = message.get('channel', 'unknown')
        project = message.get('project', 'unknown')
        
        # 生成分组ID
        timestamp = int(time.time())
        content_hash = hashlib.md5(f"{event_type}:{channel}:{project}".encode()).hexdigest()[:8]
        group_id = f"{event_type}_{content_hash}_{timestamp}"
        
        # 确定分组策略
        rule = self.grouping_rules.get(event_type, {})
        strategy = rule.get('strategy', GroupingStrategy.BY_PROJECT)
        
        # 创建分组
        group = MessageGroup(
            group_id=group_id,
            strategy=strategy,
            channel=channel,
            event_type=event_type,
            project=project
        )
        
        self.active_groups[group_id] = group
        self.stats['groups_created'] += 1
        
        self.logger.debug(f"创建新分组: {group_id} (策略: {strategy.value})")
        
        return group_id
        
    def add_message(self, message: Dict[str, Any]) -> bool:
        """添加消息（兼容旧接口）
        
        Args:
            message: 消息数据
            
        Returns:
            是否成功添加
        """
        should_group, group_id, action = self.should_group_message(message)
        
        if should_group and group_id:
            return self.add_message_to_group(group_id, message)
        
        return False
        
    def add_message_to_group(self, group_id: str, message: Dict[str, Any]) -> bool:
        """将消息添加到分组
        
        Args:
            group_id: 分组ID
            message: 消息数据
            
        Returns:
            是否成功添加
        """
        if group_id not in self.active_groups:
            return False
            
        try:
            group = self.active_groups[group_id]
            group.add_message(message)
            
            self.stats['messages_grouped'] += 1
            
            # 检查是否应该立即发送
            if self._should_send_group(group):
                self._mark_group_for_sending(group_id)
                
            return True
            
        except Exception as e:
            self.logger.error(f"添加消息到分组失败: {e}")
            return False
        
    def _should_send_group(self, group: MessageGroup) -> bool:
        """检查分组是否应该发送"""
        event_rule = self.grouping_rules.get(group.event_type, {})
        
        # 检查消息数量阈值
        send_threshold = event_rule.get('send_threshold', self.grouping_config.get('send_threshold', 5))
        if len(group.messages) >= send_threshold:
            return True
            
        # 检查超时
        timeout = event_rule.get('timeout', self.grouping_config.get('send_timeout', 60))
        if group.get_age() >= timeout:
            return True
            
        # 检查优先级升级
        if event_rule.get('priority_boost') and group.priority >= 3:  # HIGH 以上优先级
            if len(group.messages) >= 2:  # 至少2条消息
                return True
                
        # 检查升级阈值
        escalate_threshold = event_rule.get('escalate_threshold')
        if escalate_threshold and len(group.messages) >= escalate_threshold:
            return True
            
        return False
        
    def _mark_group_for_sending(self, group_id: str):
        """标记分组准备发送"""
        if group_id in self.active_groups:
            group = self.active_groups[group_id]
            # 添加标记属性
            setattr(group, 'ready_to_send', True)
            
    def get_ready_groups(self) -> List[MessageGroup]:
        """获取准备发送的分组
        
        Returns:
            准备发送的分组列表
        """
        ready_groups = []
        groups_to_remove = []
        
        for group_id, group in self.active_groups.items():
            if self._should_send_group(group):
                ready_groups.append(group)
                groups_to_remove.append(group_id)
                
        # 移除已发送的分组
        for group_id in groups_to_remove:
            if group_id in self.active_groups:
                del self.active_groups[group_id]
                self.stats['groups_sent'] += 1
                
        return ready_groups
        
    def merge_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并消息列表（兼容旧接口）
        
        Args:
            messages: 消息列表
            
        Returns:
            合并后的消息
        """
        if not messages:
            return {}
            
        # 创建临时组进行合并
        temp_group = MessageGroup(
            group_id="temp",
            strategy=GroupingStrategy.BY_CONTENT,
            event_type=messages[0].get('event_type', 'unknown'),
            channel=messages[0].get('channel', 'unknown'),
            project=messages[0].get('project', 'unknown')
        )
        
        for message in messages:
            temp_group.add_message(message)
            
        return self.merge_group_messages(temp_group)
        
    def merge_group_messages(self, group: MessageGroup) -> Dict[str, Any]:
        """合并分组中的消息
        
        Args:
            group: 消息分组
            
        Returns:
            合并后的消息
        """
        if not group.messages:
            return {}
            
        try:
            event_type = group.event_type
            rule = self.grouping_rules.get(event_type, {})
            
            # 基础合并信息
            merged_message = {
                'event_type': f"{event_type}_group",
                'event_id': f"group_{group.group_id}",
                'channel': group.channel,
                'project': group.project,
                'priority': group.priority,
                'group_info': {
                    'message_count': len(group.messages),
                    'time_span': group.get_age(),
                    'strategy': group.strategy.value,
                    'group_id': group.group_id
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 根据事件类型定制合并逻辑
            if event_type == 'sensitive_operation':
                merged_message.update(self._merge_sensitive_operations(group))
            elif event_type == 'task_completion':
                merged_message.update(self._merge_task_completions(group))
            elif event_type == 'error_occurred':
                merged_message.update(self._merge_errors(group))
            elif event_type == 'idle_detected':
                merged_message.update(self._merge_idle_notifications(group))
            else:
                merged_message.update(self._merge_generic(group))
                
            self.stats['messages_merged'] += len(group.messages)
            
            return merged_message
            
        except Exception as e:
            self.logger.error(f"消息合并异常: {e}")
            return self._merge_generic(group)
        
    def _merge_sensitive_operations(self, group: MessageGroup) -> Dict[str, Any]:
        """合并敏感操作消息"""
        operations = [msg.get('operation', '') for msg in group.messages if msg.get('operation')]
        projects = list(set(msg.get('project', '') for msg in group.messages if msg.get('project')))
        
        return {
            'title': f'🚨 检测到 {len(operations)} 个敏感操作',
            'content': f'在项目 {", ".join(projects)} 中检测到多个敏感操作',
            'operations': operations[:5],  # 最多显示5个
            'total_operations': len(operations),
            'projects': projects,
            'status': 'warning'
        }
        
    def _merge_task_completions(self, group: MessageGroup) -> Dict[str, Any]:
        """合并任务完成消息"""
        projects = list(set(msg.get('project', '') for msg in group.messages if msg.get('project')))
        tasks = [msg.get('task', msg.get('operation', '')) for msg in group.messages]
        
        return {
            'title': f'✅ {len(tasks)} 个任务已完成',
            'content': f'项目 {", ".join(projects)} 的多个任务已完成',
            'completed_tasks': len(tasks),
            'tasks': tasks[:5],  # 最多显示5个
            'projects': projects,
            'status': 'success'
        }
        
    def _merge_errors(self, group: MessageGroup) -> Dict[str, Any]:
        """合并错误消息"""
        error_types = list(set(msg.get('error_type', '') for msg in group.messages if msg.get('error_type')))
        error_messages = [msg.get('error_message', msg.get('content', '')) for msg in group.messages]
        
        return {
            'title': f'❌ 发现 {len(error_messages)} 个错误',
            'content': f'错误类型: {", ".join(error_types)}' if error_types else '发现多个错误',
            'error_count': len(error_messages),
            'error_types': error_types,
            'recent_errors': error_messages[-3:],  # 最近3个错误
            'status': 'error'
        }
        
    def _merge_idle_notifications(self, group: MessageGroup) -> Dict[str, Any]:
        """合并空闲通知消息"""
        idle_times = [msg.get('idle_time', 0) for msg in group.messages]
        max_idle_time = max(idle_times) if idle_times else 0
        
        return {
            'title': f'😴 检测到空闲状态',
            'content': f'已空闲 {max_idle_time//60} 分钟，建议休息或检查工作进度',
            'idle_time': max_idle_time,
            'notification_count': len(group.messages),
            'status': 'info'
        }
        
    def _merge_generic(self, group: MessageGroup) -> Dict[str, Any]:
        """通用消息合并"""
        return {
            'title': f'📋 {group.event_type} 事件汇总',
            'content': f'收到 {len(group.messages)} 条 {group.event_type} 事件',
            'message_count': len(group.messages),
            'event_type': group.event_type,
            'first_message': group.messages[0] if group.messages else {},
            'last_message': group.messages[-1] if group.messages else {},
            'status': 'info'
        }
        
    def _get_max_group_size(self, event_type: str) -> int:
        """获取事件类型的最大分组大小"""
        rule = self.grouping_rules.get(event_type, {})
        return rule.get('max_size', self.grouping_config.get('max_group_size', 10))
        
    def _get_group_timeout(self, event_type: str) -> int:
        """获取事件类型的分组超时时间"""
        rule = self.grouping_rules.get(event_type, {})
        return rule.get('timeout', self.grouping_config.get('send_timeout', 60))
        
    def _periodic_cleanup(self):
        """定期清理"""
        current_time = time.time()
        
        # 每5分钟清理一次
        if current_time - self._last_cleanup > 300:
            self._cleanup_expired_groups()
            self._last_cleanup = current_time
        
    def _cleanup_expired_groups(self):
        """清理过期的分组"""
        expired_groups = []
        
        for group_id, group in self.active_groups.items():
            max_age = self._get_group_timeout(group.event_type) * 3  # 超时时间的3倍
            if group.get_age() > max_age:
                expired_groups.append(group_id)
                
        for group_id in expired_groups:
            self.logger.debug(f"清理过期分组: {group_id}")
            if group_id in self.active_groups:
                del self.active_groups[group_id]
                
    def get_grouper_status(self) -> Dict[str, Any]:
        """获取分组器状态信息
        
        Returns:
            状态信息字典
        """
        return {
            'enabled': self.grouping_config.get('enabled', True),
            'stats': self.stats.copy(),
            'active_groups': len(self.active_groups),
            'group_details': [
                {
                    'group_id': group.group_id,
                    'event_type': group.event_type,
                    'message_count': len(group.messages),
                    'age': group.get_age(),
                    'idle_time': group.get_idle_time(),
                    'strategy': group.strategy.value,
                    'priority': group.priority
                }
                for group in self.active_groups.values()
            ],
            'config': self.grouping_config.copy()
        }
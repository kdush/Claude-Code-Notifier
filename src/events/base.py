#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import time
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

class EventType(Enum):
    """事件类型枚举"""
    PERMISSION_REQUEST = "permission_request"      # 权限请求
    SENSITIVE_OPERATION = "sensitive_operation"    # 敏感操作
    TASK_COMPLETION = "task_completion"            # 任务完成
    RATE_LIMIT = "rate_limit"                      # 限流冷却
    ERROR_OCCURRED = "error_occurred"              # 错误发生
    SESSION_START = "session_start"                # 会话开始
    SESSION_END = "session_end"                    # 会话结束
    CONFIRMATION_REQUIRED = "confirmation_required" # 待确认操作
    CUSTOM_EVENT = "custom_event"                  # 自定义事件

class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class BaseEvent(abc.ABC):
    """事件基础类"""
    
    def __init__(self, event_id: str, event_type: EventType, priority: EventPriority = EventPriority.NORMAL):
        self.event_id = event_id
        self.event_type = event_type
        self.priority = priority
        self.timestamp = time.time()
        self.data = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abc.abstractmethod
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """判断事件是否应该触发"""
        pass
        
    @abc.abstractmethod
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文中提取事件数据"""
        pass
        
    @abc.abstractmethod
    def get_default_message(self) -> Dict[str, Any]:
        """获取默认消息模板"""
        pass
        
    def trigger(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """触发事件"""
        if not self.should_trigger(context):
            return None
            
        self.data = self.extract_data(context)
        self.data['event_id'] = self.event_id
        self.data['event_type'] = self.event_type.value
        self.data['priority'] = self.priority.value
        self.data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))
        
        self.logger.info(f"事件触发: {self.event_id} ({self.event_type.value})")
        return self.data
        
    def get_channels(self, config: Dict[str, Any]) -> List[str]:
        """获取事件对应的通知渠道"""
        event_config = config.get('events', {}).get(self.event_id, {})
        channels = event_config.get('channels', [])
        
        # 如果没有配置特定渠道，使用默认渠道
        if not channels:
            channels = config.get('notifications', {}).get('default_channels', [])
            
        return channels
        
    def is_enabled(self, config: Dict[str, Any]) -> bool:
        """检查事件是否启用"""
        event_config = config.get('events', {}).get(self.event_id, {})
        return event_config.get('enabled', True)
        
    def get_template_name(self, config: Dict[str, Any]) -> str:
        """获取事件对应的模板名称"""
        event_config = config.get('events', {}).get(self.event_id, {})
        return event_config.get('template', f'{self.event_type.value}_default')

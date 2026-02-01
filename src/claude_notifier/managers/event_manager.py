#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, Any, List, Optional
from claude_notifier.events.base import BaseEvent
from claude_notifier.events.builtin import (
    SensitiveOperationEvent, TaskCompletionEvent, RateLimitEvent,
    ConfirmationRequiredEvent, SessionStartEvent, ErrorOccurredEvent
)
from claude_notifier.events.custom import CustomEventRegistry
from claude_notifier.templates.template_engine import TemplateEngine

# 配置基础日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class EventManager:
    """事件管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.events: List[BaseEvent] = []
        self.custom_registry = CustomEventRegistry()
        self.template_engine = TemplateEngine()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 注册内置事件
        self._register_builtin_events()
        
        # 加载自定义事件
        self._load_custom_events()
        
    def _register_builtin_events(self):
        """注册内置事件"""
        builtin_events = [
            SensitiveOperationEvent(),
            TaskCompletionEvent(),
            RateLimitEvent(),
            ConfirmationRequiredEvent(),
            SessionStartEvent(),
            ErrorOccurredEvent()
        ]
        
        # 根据配置过滤启用的事件
        for event in builtin_events:
            if self._is_event_enabled(event.event_id):
                self.events.append(event)
                self.logger.info(f"注册内置事件: {event.event_id}")
        
    def _load_custom_events(self):
        """加载自定义事件"""
        custom_count = self.custom_registry.load_from_config(self.config)
        self.logger.info(f"加载了 {custom_count} 个自定义事件")
        
    def _is_event_enabled(self, event_id: str) -> bool:
        """检查事件是否启用"""
        events_config = self.config.get('events', {})
        event_config = events_config.get(event_id, {})
        
        # 默认启用，除非明确禁用
        return event_config.get('enabled', True)
        
    def process_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理上下文，返回触发的事件数据"""
        triggered_events = []
        
        # 处理内置事件
        for event in self.events:
            if not self._is_event_enabled(event.event_id):
                continue
                
            event_data = event.trigger(context)
            if event_data:
                # 渲染模板
                template_name = self._get_event_template(event.event_id)
                rendered_data = self.template_engine.render_template(template_name, event_data)
                
                if rendered_data:
                    event_data['rendered'] = rendered_data
                    event_data['channels'] = self._get_event_channels(event.event_id)
                    triggered_events.append(event_data)
                
        # 处理自定义事件
        for event_id in self.custom_registry.list_events():
            if not self._is_event_enabled(event_id):
                continue
                
            custom_event = self.custom_registry.get_event(event_id)
            if custom_event:
                event_data = custom_event.trigger(context)
                if event_data:
                    # 渲染模板
                    template_name = self._get_event_template(event_id)
                    rendered_data = self.template_engine.render_template(template_name, event_data)
                    
                    if rendered_data:
                        event_data['rendered'] = rendered_data
                        event_data['channels'] = self._get_event_channels(event_id)
                        triggered_events.append(event_data)
                
        return triggered_events
        
    def _get_event_channels(self, event_id: str) -> List[str]:
        """获取事件对应的通知渠道"""
        events_config = self.config.get('events', {})
        event_config = events_config.get(event_id, {})
        
        # 获取事件特定渠道
        channels = event_config.get('channels', [])
        
        # 如果没有配置特定渠道，使用默认渠道
        if not channels:
            notifications_config = self.config.get('notifications', {})
            channels = notifications_config.get('default_channels', [])
            
        # 过滤启用的渠道
        enabled_channels = []
        channels_config = self.config.get('channels', {})
        for channel in channels:
            if channels_config.get(channel, {}).get('enabled', False):
                enabled_channels.append(channel)
                
        return enabled_channels
        
    def _get_event_template(self, event_id: str) -> str:
        """获取事件对应的模板名称"""
        events_config = self.config.get('events', {})
        event_config = events_config.get(event_id, {})
        
        # 获取自定义模板名称
        template_name = event_config.get('template')
        if template_name:
            return template_name
            
        # 使用默认模板
        return f'{event_id}_default'
        
    def add_custom_event(self, event_id: str, event_config: Dict[str, Any]) -> bool:
        """添加自定义事件"""
        # 验证配置
        validation_errors = self.custom_registry.validate_event_config(event_config)
        if validation_errors:
            self.logger.error(f"自定义事件配置无效 {event_id}: {validation_errors}")
            return False
            
        return self.custom_registry.register_event(event_id, event_config)
        
    def remove_custom_event(self, event_id: str) -> bool:
        """移除自定义事件"""
        return self.custom_registry.unregister_event(event_id)
        
    def list_all_events(self) -> Dict[str, List[str]]:
        """列出所有事件"""
        builtin_events = [event.event_id for event in self.events]
        custom_events = self.custom_registry.list_events()
        
        return {
            'builtin': builtin_events,
            'custom': custom_events
        }
        
    def get_event_config(self, event_id: str) -> Optional[Dict[str, Any]]:
        """获取事件配置"""
        events_config = self.config.get('events', {})
        return events_config.get(event_id)
        
    def update_event_config(self, event_id: str, config: Dict[str, Any]) -> bool:
        """更新事件配置"""
        try:
            if 'events' not in self.config:
                self.config['events'] = {}
                
            self.config['events'][event_id] = config
            self.logger.info(f"更新事件配置: {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"更新事件配置失败 {event_id}: {e}")
            return False
            
    def enable_event(self, event_id: str) -> bool:
        """启用事件"""
        return self.update_event_config(event_id, {'enabled': True})
        
    def disable_event(self, event_id: str) -> bool:
        """禁用事件"""
        return self.update_event_config(event_id, {'enabled': False})
        
    def set_event_channels(self, event_id: str, channels: List[str]) -> bool:
        """设置事件通知渠道"""
        current_config = self.get_event_config(event_id) or {}
        current_config['channels'] = channels
        return self.update_event_config(event_id, current_config)
        
    def set_event_template(self, event_id: str, template_name: str) -> bool:
        """设置事件模板"""
        current_config = self.get_event_config(event_id) or {}
        current_config['template'] = template_name
        return self.update_event_config(event_id, current_config)
        
    def get_event_statistics(self) -> Dict[str, Any]:
        """获取事件统计信息"""
        return {
            'total_events': len(self.events) + len(self.custom_registry.list_events()),
            'builtin_events': len(self.events),
            'custom_events': len(self.custom_registry.list_events()),
            'enabled_events': len([e for e in self.events if self._is_event_enabled(e.event_id)]),
            'available_templates': len(self.template_engine.list_templates())
        }
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
from typing import Dict, Any, Optional, List
import logging

class BaseChannel(abc.ABC):
    """通知渠道基础类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abc.abstractmethod
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通用通知"""
        pass
        
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        return self.send_notification(data, 'permission')
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知"""
        return self.send_notification(data, 'completion')
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        return self.send_notification(data, 'test')
        
    def send_custom_event_notification(self, data: Dict[str, Any]) -> bool:
        """发送自定义事件通知"""
        return self.send_notification(data, 'custom_event')
        
    def send_rate_limit_notification(self, data: Dict[str, Any]) -> bool:
        """发送限流通知"""
        return self.send_notification(data, 'rate_limit')
        
    def send_error_notification(self, data: Dict[str, Any]) -> bool:
        """发送错误通知"""
        return self.send_notification(data, 'error')
        
    def send_session_start_notification(self, data: Dict[str, Any]) -> bool:
        """发送会话开始通知"""
        return self.send_notification(data, 'session_start')
        
    @abc.abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        pass
        
    def is_enabled(self) -> bool:
        """检查渠道是否启用"""
        return self.config.get('enabled', False)
        
    def get_name(self) -> str:
        """获取渠道名称"""
        return self.__class__.__name__.lower().replace('channel', '')
        
    def format_message_for_channel(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """为特定渠道格式化消息"""
        # 默认实现，子类可以重写
        return template_data
        
    def supports_rich_content(self) -> bool:
        """检查渠道是否支持富文本内容"""
        return True
        
    def supports_actions(self) -> bool:
        """检查渠道是否支持交互按钮"""
        return False
        
    def get_max_content_length(self) -> int:
        """获取内容最大长度限制"""
        return 4000  # 默认限制
        
    def truncate_content(self, content: str, max_length: Optional[int] = None) -> str:
        """截断内容到指定长度"""
        if max_length is None:
            max_length = self.get_max_content_length()
            
        if len(content) <= max_length:
            return content
            
        return content[:max_length-3] + '...'

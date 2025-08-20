#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知渠道基础类
从原有channels/base.py迁移而来，适配新轻量化架构
"""

import abc
from typing import Dict, Any, Optional, List
import logging


class BaseChannel(abc.ABC):
    """通知渠道基础类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化通知渠道
        
        Args:
            config: 渠道配置字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abc.abstractmethod
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通用通知
        
        Args:
            template_data: 模板数据
            event_type: 事件类型
            
        Returns:
            发送是否成功
        """
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
        
    def send_idle_notification(self, data: Dict[str, Any]) -> bool:
        """发送空闲检测通知"""
        return self.send_notification(data, 'idle_detected')
        
    def send_sensitive_operation_notification(self, data: Dict[str, Any]) -> bool:
        """发送敏感操作通知"""
        return self.send_notification(data, 'sensitive_operation')
        
    @abc.abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否正确
        
        Returns:
            配置是否有效
        """
        pass
        
    def is_enabled(self) -> bool:
        """检查渠道是否启用
        
        Returns:
            渠道是否启用
        """
        return self.config.get('enabled', False)
        
    def get_name(self) -> str:
        """获取渠道名称
        
        Returns:
            渠道名称
        """
        return self.__class__.__name__.lower().replace('channel', '')
        
    def format_message_for_channel(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """为特定渠道格式化消息
        
        Args:
            template_data: 原始模板数据
            
        Returns:
            格式化后的消息数据
        """
        # 默认实现，子类可以重写
        return template_data
        
    def supports_rich_content(self) -> bool:
        """检查渠道是否支持富文本内容
        
        Returns:
            是否支持富文本
        """
        return True
        
    def supports_actions(self) -> bool:
        """检查渠道是否支持交互按钮
        
        Returns:
            是否支持交互按钮
        """
        return False
        
    def get_max_content_length(self) -> int:
        """获取内容最大长度限制
        
        Returns:
            最大内容长度
        """
        return 4000  # 默认限制
        
    def truncate_content(self, content: str, max_length: Optional[int] = None) -> str:
        """截断内容到指定长度
        
        Args:
            content: 原始内容
            max_length: 最大长度，None则使用默认值
            
        Returns:
            截断后的内容
        """
        if max_length is None:
            max_length = self.get_max_content_length()
            
        if len(content) <= max_length:
            return content
            
        return content[:max_length-3] + '...'
        
    def get_channel_info(self) -> Dict[str, Any]:
        """获取渠道信息
        
        Returns:
            渠道信息字典
        """
        return {
            'name': self.get_name(),
            'enabled': self.is_enabled(),
            'supports_rich_content': self.supports_rich_content(),
            'supports_actions': self.supports_actions(),
            'max_content_length': self.get_max_content_length(),
            'config_valid': self.validate_config() if self.is_enabled() else True
        }
        
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        try:
            if not self.is_enabled():
                return {'status': 'disabled', 'message': '渠道未启用'}
                
            if not self.validate_config():
                return {'status': 'error', 'message': '配置验证失败'}
                
            return {'status': 'ok', 'message': '渠道正常'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'健康检查失败: {str(e)}'}
            
    def format_error_message(self, error: Exception, context: str = '') -> str:
        """格式化错误消息
        
        Args:
            error: 异常对象
            context: 上下文信息
            
        Returns:
            格式化的错误消息
        """
        error_msg = f"渠道 {self.get_name()} 发送失败: {str(error)}"
        if context:
            error_msg = f"{error_msg} (上下文: {context})"
        return error_msg
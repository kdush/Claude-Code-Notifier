#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能协调器 - 统一管理所有智能限流功能
只有安装了 intelligence 模块才能使用
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from claude_notifier.core.notifier import Notifier
from claude_notifier.utils.helpers import merge_dict_recursive

# 智能模块导入 (延迟导入，避免依赖问题)
try:
    from claude_notifier.utils.operation_gate import OperationGate, OperationRequest, OperationResult
    from claude_notifier.utils.notification_throttle import NotificationThrottle, NotificationRequest, ThrottleAction
    from claude_notifier.utils.message_grouper import MessageGrouper, GroupingStrategy
    from claude_notifier.utils.cooldown_manager import CooldownManager
    INTELLIGENCE_AVAILABLE = True
except ImportError:
    INTELLIGENCE_AVAILABLE = False
    # 创建占位符类
    class OperationGate: pass
    class NotificationThrottle: pass 
    class MessageGrouper: pass
    class CooldownManager: pass


class IntelligentNotifier(Notifier):
    """智能通知器 - 集成所有智能功能的完整版本"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化智能通知器"""
        if not INTELLIGENCE_AVAILABLE:
            raise ImportError(
                "智能功能模块未安装。请运行: pip install claude-notifier[intelligence]"
            )
            
        super().__init__(config_path)
        
        # 智能功能开关
        self.intelligence_config = self.config.get('intelligent_limiting', {})
        self.intelligence_enabled = self.intelligence_config.get('enabled', False)
        
        if not self.intelligence_enabled:
            self.logger.info("智能功能已禁用，使用基础通知功能")
            return
            
        # 初始化智能组件
        self._init_intelligence_components()
        
    def _init_intelligence_components(self):
        """初始化智能功能组件"""
        try:
            # 操作门控制器
            if self.intelligence_config.get('operation_gate', {}).get('enabled', True):
                self.operation_gate = OperationGate(self.config)
                self.logger.info("✅ 操作阻止机制已启用")
            else:
                self.operation_gate = None
                
            # 通知频率控制器
            if self.intelligence_config.get('notification_throttle', {}).get('enabled', True):
                self.notification_throttle = NotificationThrottle(self.config)
                self.logger.info("✅ 通知频率控制已启用")
            else:
                self.notification_throttle = None
                
            # 消息分组器
            grouping_config = self.intelligence_config.get('message_grouper', {})
            if grouping_config.get('enabled', True):
                self.message_grouper = MessageGrouper(self.config)
                self.logger.info("✅ 消息分组功能已启用")
            else:
                self.message_grouper = None
                
            # 冷却管理器
            cooldown_config = self.intelligence_config.get('cooldown_manager', {})
            if cooldown_config.get('enabled', True):
                self.cooldown_manager = CooldownManager(self.config)
                self.logger.info("✅ 冷却管理功能已启用")
            else:
                self.cooldown_manager = None
                
        except Exception as e:
            self.logger.error(f"智能组件初始化失败: {e}")
            # 降级到基础功能
            self.intelligence_enabled = False
            
    def send(self, 
             message: Union[str, Dict[str, Any]], 
             channels: Optional[List[str]] = None,
             event_type: str = 'custom',
             operation_context: Optional[Dict[str, Any]] = None,
             **kwargs) -> bool:
        """智能发送通知 - 包含所有智能判断"""
        
        # 如果智能功能未启用，降级到基础功能
        if not self.intelligence_enabled:
            return super().send(message, channels, event_type, **kwargs)
            
        # 1. 操作检查 (如果提供了操作上下文)
        if operation_context and self.operation_gate:
            operation_result = self._check_operation_gate(operation_context)
            if operation_result[0] != OperationResult.ALLOWED:
                self.logger.warning(f"操作被阻止: {operation_result[1]}")
                return False
                
        # 2. 冷却检查
        if self.cooldown_manager:
            event_context = {
                'event_type': event_type,
                'channel': channels[0] if channels else 'default',
                'content': message,
                **kwargs
            }
            should_cooldown, reason, remaining = self.cooldown_manager.should_cooldown(
                event_context, kwargs.get('priority', 'normal')
            )
            if should_cooldown:
                self.logger.info(f"触发冷却机制: {reason}")
                if remaining:
                    self.logger.info(f"冷却剩余时间: {remaining:.1f}秒")
                return False
                
        # 3. 准备通知请求
        notification_request = self._prepare_notification_request(
            message, channels, event_type, **kwargs
        )
        
        # 4. 通知频率控制
        if self.notification_throttle:
            throttle_result = self.notification_throttle.should_allow_notification(
                notification_request
            )
            
            if throttle_result[0] == ThrottleAction.BLOCK:
                self.logger.info(f"通知被限流阻止: {throttle_result[1]}")
                return False
            elif throttle_result[0] == ThrottleAction.DELAY:
                self.logger.info(f"通知延迟发送: {throttle_result[1]}")
                self.notification_throttle.add_delayed_notification(
                    notification_request, throttle_result[2]
                )
                return True  # 延迟发送也算成功
            elif throttle_result[0] == ThrottleAction.MERGE:
                # 消息合并逻辑
                return self._handle_message_merge(notification_request)
                
        # 5. 消息分组 (如果启用)
        if self.message_grouper:
            group_result = self.message_grouper.should_group_message(notification_request)
            if group_result[0]:  # 需要分组
                self.logger.info(f"消息已分组: {group_result[1]}")
                return True  # 分组处理也算成功
                
        # 6. 正常发送
        return self._intelligent_send(notification_request)
        
    def _check_operation_gate(self, operation_context: Dict[str, Any]) -> Tuple[OperationResult, str]:
        """检查操作门控制"""
        operation_request = OperationRequest(
            operation_id=f"op_{int(time.time())}",
            operation_type=operation_context.get('type', 'unknown'),
            priority=operation_context.get('priority', 1),
            context=operation_context
        )
        
        return self.operation_gate.should_allow_operation(operation_request)
        
    def _prepare_notification_request(self, 
                                    message: Union[str, Dict[str, Any]], 
                                    channels: Optional[List[str]],
                                    event_type: str,
                                    **kwargs) -> 'NotificationRequest':
        """准备通知请求对象"""
        # 标准化消息内容
        if isinstance(message, str):
            content = {
                'title': '通知',
                'content': message,
                **kwargs
            }
        else:
            content = {**message, **kwargs}
            
        # 确定优先级
        priority_map = {
            'low': 1, 'normal': 2, 'high': 3, 'critical': 4
        }
        priority_name = kwargs.get('priority', 'normal')
        priority_value = priority_map.get(priority_name, 2)
        
        # 创建请求对象
        from ..utils.notification_throttle import NotificationRequest, NotificationPriority
        
        return NotificationRequest(
            notification_id=f"notif_{int(time.time())}_{hash(str(content)) % 10000}",
            event_type=event_type,
            channel=channels[0] if channels else 'default',
            priority=NotificationPriority(priority_value),
            content=content
        )
        
    def _handle_message_merge(self, notification_request: 'NotificationRequest') -> bool:
        """处理消息合并"""
        if not self.message_grouper:
            return False
            
        # 将消息添加到分组中
        self.message_grouper.add_message(notification_request)
        return True
        
    def _intelligent_send(self, notification_request: 'NotificationRequest') -> bool:
        """智能发送通知"""
        # 转换为标准格式发送
        template_data = notification_request.content
        channels = [notification_request.channel] if notification_request.channel != 'default' else None
        
        return super().send(
            template_data, 
            channels, 
            notification_request.event_type
        )
        
    def process_delayed_notifications(self):
        """处理延迟通知队列"""
        if not self.notification_throttle:
            return
            
        ready_notifications = self.notification_throttle.get_ready_notifications()
        for notification in ready_notifications:
            self._intelligent_send(notification)
            
    def process_grouped_messages(self):
        """处理分组消息"""
        if not self.message_grouper:
            return
            
        ready_groups = self.message_grouper.get_ready_groups()
        for group in ready_groups:
            # 发送合并后的消息
            merged_content = self.message_grouper.merge_messages(group['messages'])
            super().send(merged_content, event_type='grouped_notification')
            
    def get_intelligence_status(self) -> Dict[str, Any]:
        """获取智能功能状态"""
        if not self.intelligence_enabled:
            return {'enabled': False, 'reason': 'Intelligence features disabled'}
            
        status = {
            'enabled': True,
            'components': {}
        }
        
        # 操作门状态
        if self.operation_gate:
            status['components']['operation_gate'] = self.operation_gate.get_gate_status()
        else:
            status['components']['operation_gate'] = {'enabled': False}
            
        # 通知限流状态
        if self.notification_throttle:
            status['components']['notification_throttle'] = self.notification_throttle.get_throttle_stats()
        else:
            status['components']['notification_throttle'] = {'enabled': False}
            
        # 消息分组状态
        if self.message_grouper:
            status['components']['message_grouper'] = self.message_grouper.get_grouper_status()
        else:
            status['components']['message_grouper'] = {'enabled': False}
            
        # 冷却管理状态
        if self.cooldown_manager:
            status['components']['cooldown_manager'] = self.cooldown_manager.get_cooldown_status()
        else:
            status['components']['cooldown_manager'] = {'enabled': False}
            
        return status
        
    def configure_throttling(self, **kwargs):
        """动态配置限流参数"""
        if not self.notification_throttle:
            self.logger.warning("通知限流功能未启用")
            return False
            
        # 更新限流配置
        for key, value in kwargs.items():
            if hasattr(self.notification_throttle.rate_limits['global'], key):
                setattr(self.notification_throttle.rate_limits['global'], key, value)
                self.logger.info(f"限流参数已更新: {key}={value}")
                
        return True
        
    def emergency_disable_intelligence(self):
        """紧急禁用智能功能"""
        self.logger.warning("紧急禁用智能功能")
        self.intelligence_enabled = False
        
        # 清理资源
        if hasattr(self, 'operation_gate') and self.operation_gate:
            self.operation_gate.emergency_stop()
            
    def get_status(self) -> Dict[str, Any]:
        """获取完整状态 (继承并扩展基础状态)"""
        status = super().get_status()
        
        # 添加智能功能状态
        status['intelligence'] = self.get_intelligence_status()
        status['features'] = {
            'core': True,
            'intelligence': self.intelligence_enabled,
        }
        
        return status
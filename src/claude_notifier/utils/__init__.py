#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
提供通用的辅助函数和工具类，包括智能限流组件
"""

from .helpers import *
from .time_utils import TimeManager, RateLimitTracker

# 智能功能模块 (可选导入，允许优雅降级)
try:
    from .operation_gate import OperationGate, OperationRequest, OperationResult, BlockingStrategy
    from .notification_throttle import NotificationThrottle, NotificationRequest, ThrottleAction, NotificationPriority
    from .message_grouper import MessageGrouper, GroupingStrategy, MergeAction, MessageGroup
    from .cooldown_manager import CooldownManager, CooldownType, CooldownScope, CooldownRule
    
    INTELLIGENCE_AVAILABLE = True
    
    __all__ = [
        # 时间工具
        'TimeManager',
        'RateLimitTracker',
        
        # 智能功能组件
        'OperationGate', 'OperationRequest', 'OperationResult', 'BlockingStrategy',
        'NotificationThrottle', 'NotificationRequest', 'ThrottleAction', 'NotificationPriority',
        'MessageGrouper', 'GroupingStrategy', 'MergeAction', 'MessageGroup', 
        'CooldownManager', 'CooldownType', 'CooldownScope', 'CooldownRule',
        
        # 通用工具 (从helpers导入)
        'get_project_info',
        'is_sensitive_operation', 
        'validate_webhook_url',
        'sanitize_for_notification',
        'format_duration',
        'merge_dict_recursive',
        'format_timestamp',
        'truncate_text',
        'escape_markdown',
        'parse_command_output',
        'calculate_content_hash',
        'extract_error_summary',
        'safe_json_loads',
        'get_file_extension',
        'is_text_file',
        'create_backup_filename',
        'ensure_directory_exists',
        
        # 可用性标志
        'INTELLIGENCE_AVAILABLE',
    ]
    
except ImportError as e:
    INTELLIGENCE_AVAILABLE = False
    
    __all__ = [
        # 时间工具
        'TimeManager',
        'RateLimitTracker',
        
        # 通用工具 (从helpers导入)
        'get_project_info',
        'is_sensitive_operation', 
        'validate_webhook_url',
        'sanitize_for_notification',
        'format_duration',
        'merge_dict_recursive',
        'format_timestamp',
        'truncate_text',
        'escape_markdown',
        'parse_command_output',
        'calculate_content_hash',
        'extract_error_summary',
        'safe_json_loads',
        'get_file_extension',
        'is_text_file',
        'create_backup_filename',
        'ensure_directory_exists',
        
        # 可用性标志
        'INTELLIGENCE_AVAILABLE',
    ]
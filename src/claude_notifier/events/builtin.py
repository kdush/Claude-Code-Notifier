#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import time
from typing import Dict, Any, List
from .base import BaseEvent, EventType, EventPriority

class SensitiveOperationEvent(BaseEvent):
    def __init__(self):
        super().__init__('sensitive_operation', EventType.SENSITIVE_OPERATION, EventPriority.HIGH)
        self.patterns = [
            r'sudo\s+', r'rm\s+-[rf]*', r'chmod\s+', r'chown\s+',
            r'git\s+push', r'npm\s+publish', r'docker\s+', r'kubectl\s+'
        ]
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        tool_input = context.get('tool_input', '')
        tool_name = context.get('tool_name', '')
        
        if tool_name not in ['Bash', 'CreateFile', 'Write', 'DeleteFile']:
            return False
            
        command = self._extract_command(tool_input)
        if not command:
            return False
            
        for pattern in self.patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
        
    def _extract_command(self, tool_input: str) -> str:
        try:
            import json
            if tool_input.startswith('{'):
                data = json.loads(tool_input)
                return data.get('command', '') or data.get('content', '')
            return tool_input
        except:
            return tool_input
            
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        tool_input = context.get('tool_input', '')
        command = self._extract_command(tool_input)
        
        return {
            'project': self._get_project_name(),
            'operation': command[:200],
            'tool_name': context.get('tool_name', ''),
            'risk_level': 'medium'
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        current_dir = os.getcwd()
        if current_dir not in ['/', os.path.expanduser('~')]:
            return os.path.basename(current_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '🔐 敏感操作检测',
            'content': '检测到可能的敏感操作',
            'action': '请在终端中确认是否继续执行'
        }

class TaskCompletionEvent(BaseEvent):
    def __init__(self):
        super().__init__('task_completion', EventType.TASK_COMPLETION, EventPriority.NORMAL)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        return context.get('hook_event') == 'Stop'
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'status': f'{self._get_project_name()} 项目任务完成'
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '✅ 任务完成',
            'content': '🎉 工作完成，可以休息了！',
            'action': '建议您休息一下'
        }

class RateLimitEvent(BaseEvent):
    """Claude 额度限流冷却事件"""
    def __init__(self):
        super().__init__('rate_limit', EventType.RATE_LIMIT, EventPriority.HIGH)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        error_msg = context.get('error_message', '').lower()
        return any(keyword in error_msg for keyword in [
            'rate limit', 'quota exceeded', 'too many requests', 
            '限流', '额度', '请求过多'
        ])
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'error_type': 'rate_limit',
            'message': context.get('error_message', ''),
            'cooldown_time': context.get('cooldown_time', '未知')
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '⏰ Claude 额度限流',
            'content': '检测到 Claude 额度限制，请稍后再试',
            'action': '建议等待冷却时间后继续'
        }

class ConfirmationRequiredEvent(BaseEvent):
    """待确认操作事件"""
    def __init__(self):
        super().__init__('confirmation_required', EventType.PERMISSION_REQUEST, EventPriority.CRITICAL)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        return context.get('requires_confirmation', False) or \
               context.get('user_input_required', False)
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'operation': context.get('operation', '未知操作'),
            'reason': context.get('confirmation_reason', '需要用户确认'),
            'risk_level': context.get('risk_level', 'medium')
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '⚠️ 需要确认',
            'content': '检测到需要用户确认的操作',
            'action': '请在终端中确认是否继续'
        }

class SessionStartEvent(BaseEvent):
    """会话开始事件"""
    def __init__(self):
        super().__init__('session_start', EventType.SESSION_START, EventPriority.LOW)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        return context.get('hook_event') == 'Start'
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'session_id': context.get('session_id', 'unknown'),
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '🚀 会话开始',
            'content': 'Claude Code 会话已启动',
            'action': '开始编程之旅'
        }

class ConfirmationRequiredEvent(BaseEvent):
    """待确认操作事件"""
    def __init__(self):
        super().__init__('confirmation_required', EventType.CONFIRMATION_REQUIRED, EventPriority.HIGH)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        return context.get('requires_confirmation', False) or \
               context.get('confirmation_needed', False)
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'operation': context.get('operation', '未知操作'),
            'confirmation_message': context.get('confirmation_message', ''),
            'timeout': context.get('confirmation_timeout', 30)
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '⚠️ 需要确认',
            'content': '检测到需要用户确认的操作',
            'action': '请在终端中确认是否继续'
        }

class ErrorOccurredEvent(BaseEvent):
    """错误发生事件"""
    def __init__(self):
        super().__init__('error_occurred', EventType.ERROR_OCCURRED, EventPriority.HIGH)
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        return context.get('has_error', False) or \
               context.get('error_message') is not None
        
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'project': self._get_project_name(),
            'error_type': context.get('error_type', 'unknown'),
            'error_message': context.get('error_message', ''),
            'stack_trace': context.get('stack_trace', '')[:500]  # 限制长度
        }
        
    def _get_project_name(self) -> str:
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        return {
            'title': '❌ 错误发生',
            'content': '检测到执行错误',
            'action': '请检查错误信息并修复'
        }

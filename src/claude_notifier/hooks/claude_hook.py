#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Hook Integration
与Claude Code的钩子集成，监控命令执行和状态变化
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 导入 Notifier（优先绝对导入，失败则尝试相对导入；不再回退到 src.*）
try:
    from claude_notifier.core.notifier import Notifier
    PYPI_MODE = True
except Exception:
    try:
        from ..core.notifier import Notifier  # 可能在直接脚本执行时失败
        PYPI_MODE = True
    except Exception:
        Notifier = None  # 简化模式，不发送通知
        PYPI_MODE = True

class ClaudeHook:
    """Claude Code钩子处理器"""
    
    def __init__(self):
        """初始化钩子处理器，仅支持PyPI模式（完整或简化）。"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # PyPI模式：优先使用 Notifier，不可用则降级为简化模式
        try:
            if Notifier is not None:
                self.notifier = Notifier()
                self.config = getattr(self.notifier, 'config', {})
                self.mode = 'pypi_full'
            else:
                self.notifier = None
                self.config = {}
                self.mode = 'pypi_simple'
        except Exception as e:
            self.logger.warning(f"PyPI完整模式初始化失败: {e}，切换到简化模式")
            self.notifier = None
            self.config = {}
            self.mode = 'pypi_simple'
        
        # 设置钩子状态文件
        self.state_file = os.path.expanduser('~/.claude-notifier/hook_state.json')
        self.load_state()
        
    def load_state(self):
        """加载钩子状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            else:
                self.state = {
                    'session_id': None,
                    'session_start': None,
                    'last_activity': None,
                    'command_count': 0,
                    'task_status': 'idle'
                }
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            self.state = {}
            
    def save_state(self):
        """保存钩子状态"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            
    def on_session_start(self, context: Dict[str, Any]):
        """会话开始钩子"""
        self.logger.info("Claude Code 会话开始")
        
        # 更新状态
        self.state['session_id'] = context.get('session_id', str(time.time()))
        self.state['session_start'] = time.time()
        self.state['last_activity'] = time.time()
        self.state['command_count'] = 0
        self.state['task_status'] = 'active'
        self.save_state()
        
        if self.mode == 'pypi_full':
            try:
                # PyPI完整模式：发送简单通知
                self.notifier.send(
                    "🚀 Claude Code 会话已开始", 
                    event_type='session_start'
                )
            except Exception as e:
                self.logger.warning(f"通知发送失败: {e}")
        
        # 简化模式：只记录日志
        self.logger.info(f"会话开始 - 模式: {self.mode}")
        
    def on_command_execute(self, context: Dict[str, Any]):
        """命令执行钩子"""
        command = context.get('command', '')
        tool = context.get('tool', '')
        
        self.logger.info(f"检测到命令执行: {tool} - {command[:100]}")
        
        # 更新状态
        self.state['last_activity'] = time.time()
        self.state['command_count'] += 1
        self.save_state()
        
        # 简化模式：基本记录
        self.logger.debug(f"命令执行记录 - 模式: {self.mode}, 工具: {tool}")
            
    def on_task_complete(self, context: Dict[str, Any]):
        """任务完成钩子"""
        self.logger.info("Claude Code 任务完成")
        
        # 更新状态
        self.state['task_status'] = 'completed'
        self.save_state()
        
        if self.mode == 'pypi_full':
            try:
                # PyPI完整模式：发送完成通知
                duration = int(time.time() - self.state.get('session_start', time.time()))
                message = f"✅ 任务已完成 ({self.state.get('command_count', 0)} 个命令, {duration//60}分钟)"
                self.notifier.send(message, event_type='task_completion')
            except Exception as e:
                self.logger.warning(f"通知发送失败: {e}")
        
        # 简化模式：基本记录
        self.logger.info(f"任务完成 - 模式: {self.mode}")
        
    def on_error(self, context: Dict[str, Any]):
        """错误发生钩子"""
        error_type = context.get('error_type', 'unknown')
        error_message = context.get('error_message', '')
        
        self.logger.error(f"Claude Code 错误: {error_type} - {error_message}")
        
        if self.mode == 'pypi_full':
            try:
                # PyPI完整模式：发送错误通知
                message = f"❌ {error_type}: {error_message[:100]}"
                self.notifier.send(message, event_type='error_occurred', priority='high')
            except Exception as e:
                self.logger.warning(f"错误通知发送失败: {e}")
        
        # 简化模式：基本记录
        self.logger.error(f"错误记录 - 模式: {self.mode}")
        
    def on_confirmation_required(self, context: Dict[str, Any]):
        """需要确认钩子"""
        message = context.get('message', '')
        
        self.logger.info(f"需要用户确认: {message}")
        
        if self.mode == 'pypi_full':
            try:
                # PyPI完整模式：发送确认通知
                notify_message = f"⚠️ 需要确认: {message[:100]}"
                self.notifier.send(notify_message, event_type='confirmation_required', priority='high')
            except Exception as e:
                self.logger.warning(f"确认通知发送失败: {e}")
        
        # 简化模式：基本记录
        self.logger.info(f"确认请求 - 模式: {self.mode}")
        
    def pause_for_confirmation(self, command: str):
        """暂停执行等待确认"""
        print("\n" + "="*50)
        print("⚠️  检测到敏感操作，需要确认")
        print(f"命令: {command}")
        print("="*50)
        
        response = input("是否继续执行？(y/n): ").lower().strip()
        
        if response != 'y':
            print("操作已取消")
            sys.exit(1)
        else:
            print("继续执行...")
            
    def check_idle_notification(self):
        """检查是否需要发送空闲通知"""
        # 简化：PyPI版本暂不支持空闲通知检测
        self.logger.debug(f"空闲检查 - 模式: {self.mode} 暂未实现空闲通知")

    # ==================== 新版 Claude Code CLI Hooks API ====================
    
    def on_pre_tool_use(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PreToolUse 钩子 - 工具使用前触发
        
        用于敏感操作检测和权限控制
        返回 {"continue": True/False} 控制是否继续执行
        """
        tool_name = context.get('tool_name', '')
        tool_input = context.get('tool_input', {})
        
        self.logger.info(f"PreToolUse: {tool_name}")
        
        # 更新状态（如果 session_start 未设置，初始化它）
        current_time = time.time()
        if not self.state.get('session_start'):
            self.state['session_start'] = current_time
            self.state['task_status'] = 'active'
        self.state['last_activity'] = current_time
        self.state['command_count'] = self.state.get('command_count', 0) + 1
        self.save_state()
        
        # 敏感操作检测
        sensitive_tools = ['Bash', 'Edit', 'Write', 'MultiEdit', 'DeleteFile']
        if tool_name in sensitive_tools:
            self.logger.info(f"检测到敏感操作: {tool_name}")
            
            if self.mode == 'pypi_full':
                try:
                    # 确保 tool_input 是字典类型
                    if not isinstance(tool_input, dict):
                        tool_input = {}
                    
                    # 提取操作详情
                    if tool_name == 'Bash':
                        command = str(tool_input.get('command', ''))[:100]
                        message = f"⚠️ 即将执行命令: {command}"
                    elif tool_name in ['Edit', 'Write', 'MultiEdit']:
                        file_path = tool_input.get('file_path', tool_input.get('path', ''))
                        message = f"⚠️ 即将修改文件: {file_path}"
                    elif tool_name == 'DeleteFile':
                        file_path = tool_input.get('file_path', '')
                        message = f"⚠️ 即将删除文件: {file_path}"
                    else:
                        message = f"⚠️ 敏感操作: {tool_name}"
                    
                    self.notifier.send(message, event_type='sensitive_operation', priority='high')
                except Exception as e:
                    self.logger.warning(f"敏感操作通知发送失败: {e}")
        
        # 返回继续执行
        return {"continue": True}
    
    def on_post_tool_use(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PostToolUse 钩子 - 工具使用后触发
        
        用于错误检测和结果记录
        """
        tool_name = context.get('tool_name', '')
        tool_result = context.get('tool_result', {})
        
        self.logger.info(f"PostToolUse: {tool_name}")
        
        # 检测错误
        is_error = tool_result.get('is_error', False)
        if is_error:
            error_content = str(tool_result.get('content', ''))[:200]
            self.logger.error(f"工具执行错误: {tool_name} - {error_content}")
            
            if self.mode == 'pypi_full':
                try:
                    message = f"❌ {tool_name} 执行失败: {error_content[:100]}"
                    self.notifier.send(message, event_type='error_occurred', priority='high')
                except Exception as e:
                    self.logger.warning(f"错误通知发送失败: {e}")
        
        return {"continue": True}
    
    def on_stop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stop 钩子 - Claude 停止工作时触发
        
        用于任务完成通知
        """
        stop_hook_name = context.get('stop_hook_name', 'Stop')
        reason = context.get('reason', '')
        
        self.logger.info(f"Stop: {stop_hook_name}, reason: {reason}")
        
        # 更新状态
        self.state['task_status'] = 'completed'
        self.save_state()
        
        if self.mode == 'pypi_full':
            try:
                duration = int(time.time() - self.state.get('session_start', time.time()))
                cmd_count = self.state.get('command_count', 0)
                message = f"✅ 任务已完成 ({cmd_count} 个操作, {duration//60}分钟)"
                self.notifier.send(message, event_type='task_completion')
            except Exception as e:
                self.logger.warning(f"完成通知发送失败: {e}")
        
        self.logger.info(f"任务完成 - 模式: {self.mode}")
        return {"continue": True}
    
    def on_notification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notification 钩子 - 通知事件
        
        处理 permission_prompt（权限请求）和 idle_prompt（空闲提示）
        """
        notification_type = context.get('type', '')
        message = str(context.get('message', '') or '')
        
        self.logger.info(f"Notification: {notification_type} - {message[:50]}")
        
        if notification_type == 'permission_prompt':
            # 权限请求通知
            if self.mode == 'pypi_full':
                try:
                    notify_message = f"⚠️ 需要权限确认: {message[:100]}"
                    self.notifier.send(notify_message, event_type='confirmation_required', priority='high')
                except Exception as e:
                    self.logger.warning(f"权限通知发送失败: {e}")
                    
        elif notification_type == 'idle_prompt':
            # 空闲提示
            if self.mode == 'pypi_full':
                try:
                    notify_message = f"💤 Claude 等待输入中..."
                    self.notifier.send(notify_message, event_type='idle_prompt')
                except Exception as e:
                    self.logger.warning(f"空闲通知发送失败: {e}")
        
        return {"continue": True}


def main():
    """
    主函数 - 处理钩子调用
    
    支持两种调用方式：
    1. 新版 API：通过环境变量 CLAUDE_HOOK_EVENT 获取事件类型，stdin 读取 JSON 数据
    2. 旧版 API：通过命令行参数传递事件类型和数据（向后兼容）
    """
    hook = ClaudeHook()
    
    # 检查是否使用新版 API（通过环境变量）
    hook_event = os.environ.get('CLAUDE_HOOK_EVENT', '')
    
    if hook_event:
        # 新版 API：从 stdin 读取 JSON 数据
        try:
            input_data = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            input_data = {}
        
        # 路由到对应的钩子处理器
        result = {"continue": True}
        
        if hook_event == 'PreToolUse':
            result = hook.on_pre_tool_use(input_data)
        elif hook_event == 'PostToolUse':
            result = hook.on_post_tool_use(input_data)
        elif hook_event == 'Stop':
            result = hook.on_stop(input_data)
        elif hook_event == 'SubagentStop':
            result = hook.on_stop(input_data)  # 复用 Stop 处理器
        elif hook_event == 'Notification':
            result = hook.on_notification(input_data)
        else:
            hook.logger.warning(f"未知的钩子事件: {hook_event}")
        
        # 输出 JSON 响应到 stdout
        print(json.dumps(result))
        
    else:
        # 旧版 API：通过命令行参数（向后兼容）
        if len(sys.argv) < 2:
            print("Usage: claude_hook.py <hook_type> [context_json]")
            print("Or set CLAUDE_HOOK_EVENT environment variable for new API")
            sys.exit(1)
            
        hook_type = sys.argv[1]
        context = {}
        
        if len(sys.argv) > 2:
            try:
                context = json.loads(sys.argv[2])
            except (json.JSONDecodeError, ValueError):
                context = {'data': sys.argv[2]}
        
        # 路由到对应的钩子处理器
        if hook_type == 'session_start':
            hook.on_session_start(context)
        elif hook_type == 'command_execute':
            hook.on_command_execute(context)
        elif hook_type == 'task_complete':
            hook.on_task_complete(context)
        elif hook_type == 'error':
            hook.on_error(context)
        elif hook_type == 'confirmation_required':
            hook.on_confirmation_required(context)
        elif hook_type == 'check_idle':
            hook.check_idle_notification()
        else:
            print(f"Unknown hook type: {hook_type}")
            sys.exit(1)


if __name__ == '__main__':
    main()
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

# 智能导入模式检测和设置
PYPI_MODE = False

try:
    # 方法1: 尝试相对导入（PyPI包内调用）
    from ..core.notifier import Notifier
    from ..core.events.base import BaseEvent
    from ..config import Config
    PYPI_MODE = True
except ImportError:
    try:
        # 方法2: 尝试绝对导入（PyPI安装后独立执行）
        from claude_notifier.core.notifier import Notifier
        from claude_notifier.core.events.base import BaseEvent
        from claude_notifier.config import Config
        PYPI_MODE = True
    except ImportError:
        try:
            # 方法3: 尝试添加路径后导入（开发环境）
            project_root = Path(__file__).parent.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from src.claude_notifier.core.notifier import Notifier
            from src.claude_notifier.config import Config
            PYPI_MODE = True
        except ImportError:
            # 方法4: Git安装模式回退导入
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from src.managers.event_manager import EventManager
            from src.config_manager import ConfigManager
            from src.utils.helpers import is_sensitive_operation, parse_command_output, get_project_info
            from src.utils.time_utils import TimeManager, RateLimitTracker
            PYPI_MODE = False

class ClaudeHook:
    """Claude Code钩子处理器"""
    
    def __init__(self):
        """初始化钩子处理器，支持PyPI和Git两种模式"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if PYPI_MODE:
            # PyPI模式：使用统一的Notifier
            try:
                self.notifier = Notifier()
                self.config = self.notifier.config
                self.mode = 'pypi_full'
            except Exception as e:
                self.logger.warning(f"PyPI完整模式初始化失败: {e}，切换到简化模式")
                self.mode = 'pypi_simple'
        else:
            # Git模式：使用原有的管理器
            try:
                self.config_manager = ConfigManager()
                self.config = self.config_manager.get_config()
                self.event_manager = EventManager(self.config)
                self.time_manager = TimeManager()
                self.rate_tracker = RateLimitTracker()
                self.mode = 'git'
            except Exception as e:
                self.logger.error(f"Git模式初始化失败: {e}")
                self.mode = 'error'
        
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
                
        elif self.mode == 'git':
            # Git模式：完整处理
            self.time_manager.record_activity()
            
            event_context = {
                'event_type': 'session_start',
                'project': get_project_info(os.getcwd())['name'],
                'user': os.environ.get('USER', 'unknown'),
                'timestamp': self.time_manager.get_current_time_str()
            }
            
            self.event_manager.process_context(event_context)
        
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
        
        if self.mode == 'git':
            # Git模式：完整处理
            self.time_manager.record_activity()
            self.rate_tracker.record_usage(f"{tool}:{command[:50]}")
            
            # 检查是否为敏感操作
            if is_sensitive_operation(command):
                self.logger.warning(f"检测到敏感操作: {command}")
                
                event_context = {
                    'event_type': 'sensitive_operation',
                    'tool_input': command,
                    'tool_name': tool,
                    'project': get_project_info(os.getcwd())['name'],
                    'operation': command,
                    'timestamp': self.time_manager.get_current_time_str()
                }
                
                events = self.event_manager.process_context(event_context)
                
                if events and self.config.get('detection', {}).get('pause_on_sensitive', True):
                    self.pause_for_confirmation(command)
                    
            # 检查限流状态
            should_warn, message = self.rate_tracker.should_send_warning()
            if should_warn:
                self.logger.warning(f"Claude使用限流警告: {message}")
                
                event_context = {
                    'event_type': 'rate_limit',
                    'message': message,
                    'limits': self.rate_tracker.get_all_limits_status(),
                    'project': get_project_info(os.getcwd())['name'],
                    'timestamp': self.time_manager.get_current_time_str()
                }
                
                self.event_manager.process_context(event_context)
        
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
                
        elif self.mode == 'git':
            # Git模式：完整处理
            quiet_duration = self.config.get('notifications', {}).get('quiet_duration', 300)
            self.time_manager.start_quiet_period(quiet_duration)
            
            event_context = {
                'event_type': 'task_completion',
                'project': get_project_info(os.getcwd())['name'],
                'status': context.get('status', '任务已完成'),
                'command_count': self.state.get('command_count', 0),
                'duration': self.time_manager.format_duration(
                    int(time.time() - self.state.get('session_start', time.time()))
                ),
                'timestamp': self.time_manager.get_current_time_str()
            }
            
            self.event_manager.process_context(event_context)
        
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
                
        elif self.mode == 'git':
            # Git模式：完整处理
            event_context = {
                'event_type': 'error_occurred',
                'error_type': error_type,
                'error_message': error_message,
                'traceback': context.get('traceback', ''),
                'project': get_project_info(os.getcwd())['name'],
                'timestamp': self.time_manager.get_current_time_str()
            }
            
            self.event_manager.process_context(event_context)
        
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
                
        elif self.mode == 'git':
            # Git模式：完整处理
            event_context = {
                'event_type': 'confirmation_required',
                'confirmation_message': message,
                'project': get_project_info(os.getcwd())['name'],
                'timestamp': self.time_manager.get_current_time_str()
            }
            
            self.event_manager.process_context(event_context)
        
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
        if self.mode == 'git' and hasattr(self, 'time_manager'):
            if self.time_manager.should_send_idle_notification():
                idle_time = self.time_manager.get_idle_time()
                
                event_context = {
                    'event_type': 'idle_detected',
                    'idle_duration': self.time_manager.format_duration(idle_time),
                    'project': get_project_info(os.getcwd())['name'],
                    'timestamp': self.time_manager.get_current_time_str()
                }
                
                self.event_manager.process_context(event_context)
        else:
            self.logger.debug(f"空闲检查 - 模式: {self.mode} 不支持此功能")


def main():
    """主函数 - 处理钩子调用"""
    if len(sys.argv) < 2:
        print("Usage: claude_hook.py <hook_type> [context_json]")
        sys.exit(1)
        
    hook_type = sys.argv[1]
    context = {}
    
    if len(sys.argv) > 2:
        try:
            context = json.loads(sys.argv[2])
        except:
            context = {'data': sys.argv[2]}
            
    hook = ClaudeHook()
    
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
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
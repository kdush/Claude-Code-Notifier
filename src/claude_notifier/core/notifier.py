#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心通知器 - 轻量级实现
保持简单，专注核心功能
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .config import ConfigManager
from .channels import get_channel_class, get_available_channels


class Notifier:
    """轻量级通知器 - 核心功能实现"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化通知器
        
        Args:
            config_path: 配置文件路径，默认使用 ~/.claude-notifier/config.yaml
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.logger = self._setup_logging()
        self.channels = self._init_channels()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger('claude_notifier')
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 设置日志级别
            log_level = self.config.get('advanced', {}).get('logging', {}).get('level', 'info')
            logger.setLevel(getattr(logging, log_level.upper()))
            
        return logger
        
    def _init_channels(self) -> Dict[str, Any]:
        """初始化通知渠道"""
        channels = {}
        channels_config = self.config.get('channels', {})
        
        for channel_name, channel_config in channels_config.items():
            if channel_config.get('enabled', False):
                try:
                    channel_class = get_channel_class(channel_name)
                    if channel_class:
                        channels[channel_name] = channel_class(channel_config)
                        self.logger.debug(f"初始化渠道: {channel_name}")
                except Exception as e:
                    self.logger.error(f"初始化渠道失败 {channel_name}: {e}")
                    
        self.logger.info(f"已启用 {len(channels)} 个通知渠道")
        return channels
        
    def send(self, 
             message: Union[str, Dict[str, Any]], 
             channels: Optional[List[str]] = None,
             event_type: str = 'custom',
             **kwargs) -> bool:
        """发送通知 - 简化接口
        
        Args:
            message: 通知消息 (字符串或字典)
            channels: 指定渠道列表，None则使用默认渠道
            event_type: 事件类型
            **kwargs: 额外参数
            
        Returns:
            bool: 发送成功返回True
            
        Examples:
            # 简单使用
            notifier.send("Hello World!")
            
            # 指定渠道
            notifier.send("重要通知", channels=['dingtalk', 'email'])
            
            # 复杂消息
            notifier.send({
                'title': '任务完成',
                'content': '代码分析已完成',
                'project': 'my-project'
            })
        """
        # 标准化消息格式
        if isinstance(message, str):
            template_data = {
                'title': '通知',
                'content': message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **kwargs
            }
        else:
            template_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **message,
                **kwargs
            }
            
        # 确定发送渠道
        if channels is None:
            channels = self._get_default_channels(event_type)
            
        if not channels:
            self.logger.warning("没有可用的通知渠道")
            return True  # 不算失败
            
        # 发送通知
        return self._send_to_channels(template_data, channels, event_type)
        
    def _get_default_channels(self, event_type: str) -> List[str]:
        """获取默认通知渠道"""
        # 事件特定渠道
        event_config = self.config.get('events', {}).get(event_type, {})
        if event_config.get('channels'):
            return event_config['channels']
            
        # 全局默认渠道
        default_channels = self.config.get('notifications', {}).get('default_channels', [])
        if default_channels:
            return default_channels
            
        # 返回所有启用的渠道
        return list(self.channels.keys())
        
    def _send_to_channels(self, 
                         template_data: Dict[str, Any], 
                         channels: List[str],
                         event_type: str) -> bool:
        """发送到指定渠道"""
        if not channels:
            return True
            
        success_count = 0
        total_count = len(channels)
        
        for channel_name in channels:
            if channel_name not in self.channels:
                self.logger.warning(f"渠道未配置或未启用: {channel_name}")
                continue
                
            try:
                result = self.channels[channel_name].send_notification(template_data, event_type)
                if result:
                    success_count += 1
                    self.logger.debug(f"发送成功: {channel_name}")
                else:
                    self.logger.error(f"发送失败: {channel_name}")
                    
            except Exception as e:
                self.logger.error(f"发送异常 {channel_name}: {e}")
                
        # 只要有一个成功就算成功
        success = success_count > 0
        self.logger.info(f"通知发送结果: {success_count}/{total_count} 成功")
        return success
        
    def test_channels(self, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """测试通知渠道
        
        Args:
            channels: 要测试的渠道列表，None则测试所有渠道
            
        Returns:
            Dict[str, bool]: 渠道名称 -> 测试结果
        """
        if channels is None:
            channels = list(self.channels.keys())
            
        results = {}
        test_message = {
            'title': '🔔 Claude Notifier 测试',
            'content': f'测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            'project': 'claude-notifier-test'
        }
        
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    result = self.channels[channel_name].send_notification(
                        test_message, 'test'
                    )
                    results[channel_name] = result
                except Exception as e:
                    self.logger.error(f"测试渠道异常 {channel_name}: {e}")
                    results[channel_name] = False
            else:
                results[channel_name] = False
                
        return results
        
    def get_status(self) -> Dict[str, Any]:
        """获取通知器状态信息"""
        return {
            'version': self._get_version(),
            'channels': {
                'available': get_available_channels(),
                'enabled': list(self.channels.keys()),
                'total_enabled': len(self.channels)
            },
            'config': {
                'file': self.config_manager.config_path,
                'valid': self.config_manager.is_valid(),
                'last_modified': self._get_config_mtime()
            }
        }
        
    def _get_version(self) -> str:
        """获取版本信息"""
        try:
            from ..__version__ import __version__
            return __version__
        except ImportError:
            return "unknown"
            
    def _get_config_mtime(self) -> Optional[str]:
        """获取配置文件修改时间"""
        try:
            if os.path.exists(self.config_manager.config_path):
                mtime = os.path.getmtime(self.config_manager.config_path)
                return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        except Exception:
            pass
        return None
        
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            old_channels = set(self.channels.keys())
            self.config = self.config_manager.reload()
            self.channels = self._init_channels()
            new_channels = set(self.channels.keys())
            
            if old_channels != new_channels:
                self.logger.info(f"渠道配置已更新: {old_channels} -> {new_channels}")
                
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
            
    # 便捷方法 - 保持向后兼容
    def send_permission_notification(self, operation: str) -> bool:
        """发送权限确认通知"""
        return self.send({
            'title': '🔒 权限确认',
            'content': f'检测到敏感操作: {operation}',
            'operation': operation,
            'project': self._get_current_project()
        }, event_type='sensitive_operation')
        
    def send_completion_notification(self, status: str) -> bool:
        """发送任务完成通知"""
        return self.send({
            'title': '✅ 任务完成',
            'content': status,
            'project': self._get_current_project()
        }, event_type='task_completion')
        
    def _get_current_project(self) -> str:
        """获取当前项目名称"""
        try:
            cwd = os.getcwd()
            return os.path.basename(cwd) if cwd != os.path.expanduser('~') else 'claude-code'
        except Exception:
            return 'unknown'
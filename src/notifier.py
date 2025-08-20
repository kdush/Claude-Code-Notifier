#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# 导入所有通知渠道
from .channels.base import BaseChannel
from .channels.dingtalk import DingtalkChannel
from .channels.feishu import FeishuChannel
from .channels.wechat_work import WechatWorkChannel
from .channels.telegram import TelegramChannel
from .channels.email import EmailChannel
from .channels.serverchan import ServerChanChannel

class ClaudeCodeNotifier:
    """Claude Code 通知管理器"""
    
    # 渠道映射
    CHANNEL_CLASSES = {
        'dingtalk': DingtalkChannel,
        'feishu': FeishuChannel,
        'wechat_work': WechatWorkChannel,
        'telegram': TelegramChannel,
        'email': EmailChannel,
        'serverchan': ServerChanChannel,
        # 可以继续添加其他渠道
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser('~/.claude-notifier/config.yaml')
        self.config = self._load_config()
        self.channels: Dict[str, BaseChannel] = {}
        self.logger = self._setup_logging()
        
        # 初始化启用的渠道
        self._init_channels()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('ClaudeCodeNotifier')
        
        # 避免重复设置
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件日志
        log_file = os.path.expanduser('~/.claude-notifier/logs/notifier.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"配置文件不存在: {self.config_path}")
            print("请先运行 ./scripts/configure.sh 进行配置")
            sys.exit(1)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            sys.exit(1)
            
    def _init_channels(self):
        """初始化通知渠道"""
        channels_config = self.config.get('channels', {})
        
        for channel_name, channel_config in channels_config.items():
            if not channel_config.get('enabled', False):
                continue
                
            if channel_name not in self.CHANNEL_CLASSES:
                self.logger.warning(f"不支持的通知渠道: {channel_name}")
                continue
                
            try:
                channel_class = self.CHANNEL_CLASSES[channel_name]
                channel = channel_class(channel_config)
                
                if channel.validate_config():
                    self.channels[channel_name] = channel
                    self.logger.info(f"通知渠道初始化成功: {channel_name}")
                else:
                    self.logger.error(f"通知渠道配置验证失败: {channel_name}")
                    
            except Exception as e:
                self.logger.error(f"通知渠道初始化失败 {channel_name}: {e}")
                
    def _get_project_name(self) -> str:
        """获取项目名称"""
        # 优先使用环境变量
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
            
        # 使用当前目录
        current_dir = os.getcwd()
        if current_dir != '/' and current_dir != os.path.expanduser('~'):
            return os.path.basename(current_dir)
            
        return 'claude-code'
        
    def _get_enabled_channels(self, notification_type: str) -> List[str]:
        """获取指定通知类型的启用渠道"""
        notifications_config = self.config.get('notifications', {})
        type_config = notifications_config.get(notification_type, {})
        
        if not type_config.get('enabled', True):
            return []
            
        # 如果配置了特定渠道，使用配置的渠道
        configured_channels = type_config.get('channels', [])
        if configured_channels:
            return [ch for ch in configured_channels if ch in self.channels]
            
        # 否则使用所有启用的渠道
        return list(self.channels.keys())
        
    def send_permission_notification(self, operation: str) -> bool:
        """发送权限确认通知"""
        if not self.channels:
            self.logger.warning("没有可用的通知渠道")
            return False
            
        enabled_channels = self._get_enabled_channels('permission')
        if not enabled_channels:
            self.logger.info("权限通知已禁用")
            return True
            
        data = {
            'project': self._get_project_name(),
            'operation': operation,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        success = True
        for channel_name in enabled_channels:
            if channel_name in self.channels:
                try:
                    result = self.channels[channel_name].send_permission_notification(data)
                    if not result:
                        success = False
                        self.logger.error(f"权限通知发送失败: {channel_name}")
                except Exception as e:
                    success = False
                    self.logger.error(f"权限通知发送异常 {channel_name}: {e}")
                    
        return success
        
    def send_completion_notification(self, status: str) -> bool:
        """发送任务完成通知"""
        if not self.channels:
            self.logger.warning("没有可用的通知渠道")
            return False
            
        enabled_channels = self._get_enabled_channels('completion')
        if not enabled_channels:
            self.logger.info("完成通知已禁用")
            return True
            
        data = {
            'project': self._get_project_name(),
            'status': status,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        success = True
        for channel_name in enabled_channels:
            if channel_name in self.channels:
                try:
                    result = self.channels[channel_name].send_completion_notification(data)
                    if not result:
                        success = False
                        self.logger.error(f"完成通知发送失败: {channel_name}")
                except Exception as e:
                    success = False
                    self.logger.error(f"完成通知发送异常 {channel_name}: {e}")
                    
        return success
        
    def send_test_notification(self, channel: Optional[str] = None) -> bool:
        """发送测试通知"""
        if not self.channels:
            self.logger.warning("没有可用的通知渠道")
            return False
            
        # 如果指定了渠道，只测试该渠道
        if channel:
            if channel not in self.channels:
                self.logger.error(f"通知渠道不存在或未启用: {channel}")
                return False
            test_channels = [channel]
        else:
            test_channels = self._get_enabled_channels('test')
            
        if not test_channels:
            self.logger.info("测试通知已禁用")
            return True
            
        data = {
            'project': self._get_project_name(),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        success = True
        for channel_name in test_channels:
            if channel_name in self.channels:
                try:
                    result = self.channels[channel_name].send_test_notification(data)
                    if result:
                        print(f"✅ {channel_name} 测试通知发送成功")
                    else:
                        success = False
                        print(f"❌ {channel_name} 测试通知发送失败")
                except Exception as e:
                    success = False
                    print(f"❌ {channel_name} 测试通知发送异常: {e}")
                    
        return success

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python notifier.py <notification_type> [message]")
        print("通知类型: permission, completion, test")
        sys.exit(1)
        
    notification_type = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    
    notifier = ClaudeCodeNotifier()
    
    if notification_type == 'permission':
        success = notifier.send_permission_notification(message)
    elif notification_type == 'completion':
        success = notifier.send_completion_notification(message)
    elif notification_type == 'test':
        channel = sys.argv[2] if len(sys.argv) > 2 else None
        success = notifier.send_test_notification(channel)
    else:
        print(f"不支持的通知类型: {notification_type}")
        sys.exit(1)
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

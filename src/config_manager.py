#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser('~/.claude-notifier/config.yaml')
        self.config_dir = os.path.dirname(self.config_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            self.logger.info("配置文件不存在，创建默认配置")
            return self._create_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"加载配置文件: {self.config_path}")
                return config or {}
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self._create_default_config()
            
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        default_config = {
            'channels': {},
            'events': {
                'sensitive_operation': {'enabled': True},
                'task_completion': {'enabled': True},
                'rate_limit': {'enabled': True},
                'error_occurred': {'enabled': True},
                'session_start': {'enabled': False}
            },
            'custom_events': {},
            'notifications': {
                'default_channels': [],
                'rate_limiting': {'enabled': True, 'max_per_minute': 10}
            },
            'templates': {
                'custom_dir': '~/.claude-notifier/templates'
            },
            'advanced': {
                'logging': {'enabled': True, 'level': 'info'}
            }
        }
        
        self.save_config(default_config)
        return default_config
        
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置文件"""
        try:
            config_to_save = config or self.config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            self.logger.info(f"保存配置文件: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
            
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        return self.config.get(section, {})
        
    def set_section(self, section: str, data: Dict[str, Any]) -> bool:
        """设置配置节"""
        self.config[section] = data
        return self.save_config()
        
    def update_section(self, section: str, data: Dict[str, Any]) -> bool:
        """更新配置节"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section].update(data)
        return self.save_config()
        
    # 渠道管理
    def enable_channel(self, channel_name: str, channel_config: Dict[str, Any]) -> bool:
        """启用通知渠道"""
        if 'channels' not in self.config:
            self.config['channels'] = {}
            
        channel_config['enabled'] = True
        self.config['channels'][channel_name] = channel_config
        return self.save_config()
        
    def disable_channel(self, channel_name: str) -> bool:
        """禁用通知渠道"""
        if channel_name in self.config.get('channels', {}):
            self.config['channels'][channel_name]['enabled'] = False
            return self.save_config()
        return False
        
    def get_enabled_channels(self) -> List[str]:
        """获取启用的渠道列表"""
        channels = self.config.get('channels', {})
        return [name for name, config in channels.items() 
                if config.get('enabled', False)]
                
    # 事件管理
    def enable_event(self, event_id: str) -> bool:
        """启用事件"""
        if 'events' not in self.config:
            self.config['events'] = {}
        if event_id not in self.config['events']:
            self.config['events'][event_id] = {}
            
        self.config['events'][event_id]['enabled'] = True
        return self.save_config()
        
    def disable_event(self, event_id: str) -> bool:
        """禁用事件"""
        if event_id in self.config.get('events', {}):
            self.config['events'][event_id]['enabled'] = False
            return self.save_config()
        return False
        
    def set_event_channels(self, event_id: str, channels: List[str]) -> bool:
        """设置事件通知渠道"""
        if 'events' not in self.config:
            self.config['events'] = {}
        if event_id not in self.config['events']:
            self.config['events'][event_id] = {}
            
        self.config['events'][event_id]['channels'] = channels
        return self.save_config()
        
    def set_event_template(self, event_id: str, template_name: str) -> bool:
        """设置事件模板"""
        if 'events' not in self.config:
            self.config['events'] = {}
        if event_id not in self.config['events']:
            self.config['events'][event_id] = {}
            
        self.config['events'][event_id]['template'] = template_name
        return self.save_config()
        
    def get_enabled_events(self) -> List[str]:
        """获取启用的事件列表"""
        events = self.config.get('events', {})
        return [event_id for event_id, config in events.items() 
                if config.get('enabled', True)]
                
    # 自定义事件管理
    def add_custom_event(self, event_id: str, event_config: Dict[str, Any]) -> bool:
        """添加自定义事件"""
        if 'custom_events' not in self.config:
            self.config['custom_events'] = {}
            
        self.config['custom_events'][event_id] = event_config
        return self.save_config()
        
    def remove_custom_event(self, event_id: str) -> bool:
        """移除自定义事件"""
        if event_id in self.config.get('custom_events', {}):
            del self.config['custom_events'][event_id]
            return self.save_config()
        return False
        
    def list_custom_events(self) -> List[str]:
        """列出自定义事件"""
        return list(self.config.get('custom_events', {}).keys())
        
    # 默认渠道管理
    def set_default_channels(self, channels: List[str]) -> bool:
        """设置默认通知渠道"""
        if 'notifications' not in self.config:
            self.config['notifications'] = {}
            
        self.config['notifications']['default_channels'] = channels
        return self.save_config()
        
    def get_default_channels(self) -> List[str]:
        """获取默认通知渠道"""
        return self.config.get('notifications', {}).get('default_channels', [])
        
    # 配置验证
    def validate_config(self) -> List[str]:
        """验证配置文件"""
        errors = []
        
        # 验证渠道配置
        channels = self.config.get('channels', {})
        for channel_name, channel_config in channels.items():
            if not isinstance(channel_config, dict):
                errors.append(f"渠道 {channel_name} 配置格式错误")
                continue
                
            if channel_config.get('enabled', False):
                # 验证必需字段
                if channel_name == 'dingtalk':
                    if not channel_config.get('webhook'):
                        errors.append(f"钉钉渠道缺少 webhook 配置")
                elif channel_name == 'telegram':
                    if not channel_config.get('bot_token') or not channel_config.get('chat_id'):
                        errors.append(f"Telegram 渠道缺少 bot_token 或 chat_id")
                        
        # 验证事件配置
        events = self.config.get('events', {})
        for event_id, event_config in events.items():
            if not isinstance(event_config, dict):
                errors.append(f"事件 {event_id} 配置格式错误")
                continue
                
            channels = event_config.get('channels', [])
            if channels:
                for channel in channels:
                    if channel not in self.config.get('channels', {}):
                        errors.append(f"事件 {event_id} 引用了不存在的渠道: {channel}")
                        
        return errors
        
    # 配置导入导出
    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
            
    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = yaml.safe_load(f)
                
            if not isinstance(imported_config, dict):
                self.logger.error("导入的配置格式错误")
                return False
                
            if merge:
                # 合并配置
                self._deep_merge(self.config, imported_config)
            else:
                # 替换配置
                self.config = imported_config
                
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
            
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
                
    # 配置统计
    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        channels = self.config.get('channels', {})
        events = self.config.get('events', {})
        custom_events = self.config.get('custom_events', {})
        
        return {
            'total_channels': len(channels),
            'enabled_channels': len([c for c in channels.values() if c.get('enabled', False)]),
            'total_events': len(events),
            'enabled_events': len([e for e in events.values() if e.get('enabled', True)]),
            'custom_events': len(custom_events),
            'default_channels': len(self.get_default_channels()),
            'config_file_size': os.path.getsize(self.config_path) if os.path.exists(self.config_path) else 0
        }
        
    # 配置备份
    def backup_config(self, backup_dir: Optional[str] = None) -> str:
        """备份配置文件"""
        import time
        
        backup_dir = backup_dir or os.path.join(self.config_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'config_backup_{timestamp}.yaml')
        
        if self.export_config(backup_file):
            self.logger.info(f"配置已备份到: {backup_file}")
            return backup_file
        else:
            raise Exception("配置备份失败")
            
    def restore_config(self, backup_file: str) -> bool:
        """从备份恢复配置"""
        if not os.path.exists(backup_file):
            self.logger.error(f"备份文件不存在: {backup_file}")
            return False
            
        # 先备份当前配置
        try:
            self.backup_config()
        except:
            pass
            
        # 恢复配置
        return self.import_config(backup_file, merge=False)

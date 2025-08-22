#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理 - 从 config_manager.py 迁移而来
轻量化实现，保持核心功能
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """轻量化配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认 ~/.claude-notifier/config.yaml
        """
        if config_path is None:
            config_path = os.path.expanduser('~/.claude-notifier/config.yaml')
            
        self.config_path = config_path
        # 先初始化 logger，避免 _load_config 调用时访问未定义的 self.logger
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            self.logger.warning(f"配置文件不存在: {self.config_path}")
            return self._get_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                
            # 合并默认配置
            default_config = self._get_default_config()
            return self._merge_configs(default_config, config)
            
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'channels': {},
            'events': {},
            'notifications': {
                'default_channels': [],
                'rate_limiting': {
                    'enabled': False,
                    'max_per_minute': 10
                }
            },
            'intelligent_limiting': {
                'enabled': False
            },
            'advanced': {
                'logging': {
                    'level': 'info'
                }
            }
        }
        
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置 (深度合并)"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
        
    def reload(self) -> Dict[str, Any]:
        """重新加载配置"""
        self.config = self._load_config()
        return self.config
        
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        try:
            # 首先检查配置文件是否存在
            if not os.path.exists(self.config_path):
                return False
                
            # 基本验证
            if not isinstance(self.config, dict):
                return False
                
            # 检查必需的顶级键
            required_keys = ['channels', 'notifications']
            for key in required_keys:
                if key not in self.config:
                    return False
                    
            return True
        except Exception:
            return False
            
    def get_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """获取渠道配置"""
        return self.config.get('channels', {}).get(channel_name, {})
        
    def is_channel_enabled(self, channel_name: str) -> bool:
        """检查渠道是否启用"""
        channel_config = self.get_channel_config(channel_name)
        return channel_config.get('enabled', False)
        
    def get_enabled_channels(self) -> list:
        """获取启用的渠道列表"""
        enabled = []
        channels = self.config.get('channels', {})
        
        for channel_name, channel_config in channels.items():
            if channel_config.get('enabled', False):
                enabled.append(channel_name)
                
        return enabled
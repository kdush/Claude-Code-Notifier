#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知渠道模块
集中管理所有通知渠道
"""

from typing import Dict, Type, List, Optional

# 导入基础类
from .base import BaseChannel

# 导入所有渠道实现
from .dingtalk import DingtalkChannel
from .feishu import FeishuChannel
from .telegram import TelegramChannel
from .email import EmailChannel
from .serverchan import ServerChanChannel

# 尝试导入企业微信 (可选)
try:
    from .wechat_work import WechatWorkChannel
    _WECHAT_WORK_AVAILABLE = True
except ImportError:
    _WECHAT_WORK_AVAILABLE = False
    WechatWorkChannel = None


# 渠道注册表
CHANNEL_REGISTRY: Dict[str, Type[BaseChannel]] = {
    'dingtalk': DingtalkChannel,
    'feishu': FeishuChannel,
    'telegram': TelegramChannel,
    'email': EmailChannel,
    'serverchan': ServerChanChannel,
}

# 添加可选渠道
if _WECHAT_WORK_AVAILABLE and WechatWorkChannel:
    CHANNEL_REGISTRY['wechat_work'] = WechatWorkChannel


def get_available_channels() -> List[str]:
    """获取所有可用的渠道名称"""
    return list(CHANNEL_REGISTRY.keys())


def get_channel_class(channel_name: str) -> Optional[Type[BaseChannel]]:
    """根据渠道名称获取渠道类
    
    Args:
        channel_name: 渠道名称
        
    Returns:
        渠道类，如果不存在则返回None
    """
    return CHANNEL_REGISTRY.get(channel_name)


def register_channel(name: str, channel_class: Type[BaseChannel]) -> bool:
    """注册自定义渠道
    
    Args:
        name: 渠道名称
        channel_class: 渠道类 (必须继承自BaseChannel)
        
    Returns:
        注册成功返回True
    """
    if not issubclass(channel_class, BaseChannel):
        return False
        
    CHANNEL_REGISTRY[name] = channel_class
    return True


def is_channel_available(channel_name: str) -> bool:
    """检查渠道是否可用"""
    return channel_name in CHANNEL_REGISTRY


def get_channel_info() -> Dict[str, Dict[str, str]]:
    """获取所有渠道的信息"""
    info = {}
    
    for name, channel_class in CHANNEL_REGISTRY.items():
        info[name] = {
            'name': name,
            'display_name': getattr(channel_class, 'DISPLAY_NAME', name.title()),
            'description': getattr(channel_class, 'DESCRIPTION', ''),
            'required_config': getattr(channel_class, 'REQUIRED_CONFIG', []),
        }
        
    return info


# 向后兼容的别名
CHANNEL_CLASSES = CHANNEL_REGISTRY

__all__ = [
    'BaseChannel',
    'DingtalkChannel',
    'FeishuChannel', 
    'TelegramChannel',
    'EmailChannel',
    'ServerChanChannel',
    'WechatWorkChannel',
    'CHANNEL_REGISTRY',
    'get_available_channels',
    'get_channel_class',
    'register_channel',
    'is_channel_available',
    'get_channel_info',
    # 向后兼容
    'CHANNEL_CLASSES',
]
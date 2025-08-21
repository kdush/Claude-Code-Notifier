#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知渠道模块
集中管理所有通知渠道，支持动态扩展
"""

from typing import Dict, Type, List, Optional
import logging

# 导入基础类
from .base import BaseChannel

# 导入可用的渠道实现
logger = logging.getLogger(__name__)

# 先只导入已实现的渠道
_available_channels = {}

# 导入钉钉渠道
try:
    from .dingtalk import DingtalkChannel
    _available_channels['dingtalk'] = DingtalkChannel
except ImportError as e:
    logger.debug(f"钉钉渠道导入失败: {e}")

# 导入 Webhook 渠道
try:
    from .webhook import WebhookChannel
    _available_channels['webhook'] = WebhookChannel
except ImportError as e:
    logger.debug(f"Webhook 渠道导入失败: {e}")

# 后续可以逐步添加更多渠道
# try:
#     from .feishu import FeishuChannel
#     _available_channels['feishu'] = FeishuChannel
# except ImportError:
#     pass

# try:
#     from .telegram import TelegramChannel
#     _available_channels['telegram'] = TelegramChannel
# except ImportError:
#     pass

# try:
#     from .email import EmailChannel
#     _available_channels['email'] = EmailChannel
# except ImportError:
#     pass

# try:
#     from .serverchan import ServerChanChannel
#     _available_channels['serverchan'] = ServerChanChannel
# except ImportError:
#     pass

# try:
#     from .wechat_work import WechatWorkChannel
#     _available_channels['wechat_work'] = WechatWorkChannel
# except ImportError:
#     pass

# 渠道注册表
CHANNEL_REGISTRY: Dict[str, Type[BaseChannel]] = _available_channels.copy()


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

# 构建导出列表
_exports = [
    'BaseChannel',
    'CHANNEL_REGISTRY',
    'get_available_channels',
    'get_channel_class',
    'register_channel',
    'is_channel_available',
    'get_channel_info',
    # 向后兼容
    'CHANNEL_CLASSES',
]

# 动态添加可用的渠道类到导出列表
for channel_name, channel_class in _available_channels.items():
    _exports.append(channel_class.__name__)

__all__ = _exports
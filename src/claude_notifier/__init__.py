#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Notifier - Claude Code智能通知系统

轻量级、模块化的通知管理系统，支持多渠道通知、智能限流、监控统计等功能。

基础使用:
    from claude_notifier import Notifier
    
    notifier = Notifier()
    notifier.send("Hello from Claude!")

高级使用:
    from claude_notifier import IntelligentNotifier
    
    # 需要先安装: pip install claude-code-notifier[intelligence]
    notifier = IntelligentNotifier()
    notifier.configure_throttling(max_per_minute=10)
    notifier.send("智能通知消息")
"""

import os
from .__version__ import __version__, __version_info__

# 核心模块 - 始终可用
from .core.notifier import Notifier
from .core.config import ConfigManager
from .core.channels import get_available_channels

# 可选模块 - 按需导入
def _import_optional_modules():
    """动态导入可选功能模块"""
    optional_modules = {}
    
    # 智能功能模块
    try:
        from .intelligence.coordinator import IntelligentNotifier
        optional_modules['IntelligentNotifier'] = IntelligentNotifier
    except ImportError:
        pass
        
    # 监控功能模块
    try:
        from .monitoring.stats import StatsManager
        optional_modules['StatsManager'] = StatsManager
    except ImportError:
        pass
        
    # 集成功能模块  
    try:
        from .integration.claude_hooks import HookManager
        optional_modules['HookManager'] = HookManager
    except ImportError:
        pass
        
    return optional_modules

# 动态添加可选模块到命名空间（可通过环境变量跳过以加速导入/避免CI阻塞）
if os.getenv('CLAUDE_NOTIFIER_SKIP_OPTIONAL_IMPORTS') == '1':
    _optional = {}
else:
    _optional = _import_optional_modules()
locals().update(_optional)

# 公开API
__all__ = [
    # 版本信息
    '__version__',
    '__version_info__',
    
    # 核心功能
    'Notifier',
    'ConfigManager', 
    'get_available_channels',
    
    # 可选功能 (如果可用)
    *_optional.keys()
]

# 功能检查函数
def has_intelligence() -> bool:
    """检查是否安装了智能功能模块"""
    return 'IntelligentNotifier' in _optional

def has_monitoring() -> bool:
    """检查是否安装了监控功能模块"""
    return 'StatsManager' in _optional

def has_integration() -> bool:
    """检查是否安装了集成功能模块"""
    return 'HookManager' in _optional

def get_feature_status():
    """获取功能模块安装状态"""
    return {
        'core': True,
        'intelligence': has_intelligence(),
        'monitoring': has_monitoring(),
        'integration': has_integration(),
        'version': __version__
    }

def print_feature_status():
    """打印功能状态信息"""
    status = get_feature_status()
    print(f"Claude Notifier v{status['version']}")
    print("功能模块状态:")
    print(f"  ✅ 核心功能: {'已安装' if status['core'] else '未安装'}")
    print(f"  {'✅' if status['intelligence'] else '❌'} 智能功能: {'已安装' if status['intelligence'] else '未安装 (pip install claude-code-notifier[intelligence])'}")
    print(f"  {'✅' if status['monitoring'] else '❌'} 监控功能: {'已安装' if status['monitoring'] else '未安装 (pip install claude-code-notifier[monitoring])'}")
    print(f"  {'✅' if status['integration'] else '❌'} 集成功能: {'已安装' if status['integration'] else '未安装 (pip install claude-code-notifier[integration])'}")

# 兼容性别名 (保持向后兼容)
ClaudeCodeNotifier = Notifier  # 兼容旧版本
EnhancedNotifier = _optional.get('IntelligentNotifier', Notifier)  # 智能版本别名
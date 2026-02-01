#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI 命令模块

拆分自 main.py，按功能组织命令：
- core: 核心命令 (setup, send, test, status, monitor)
- config: 配置管理命令组
- hooks: Claude Code 钩子命令组
- debug: 调试工具命令组
"""

from .core import register_core_commands
from .config import config
from .hooks import hooks
from .debug import debug

__all__ = [
    'register_core_commands',
    'config',
    'hooks', 
    'debug',
]

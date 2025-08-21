#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version information for Claude Code Notifier
"""

__version__ = "0.0.2"
__version_info__ = (0, 0, 2)

# 版本历史
VERSION_HISTORY = {
    "0.0.2": "修复版本：解决配置备份/恢复、模板引擎API、相对导入等集成问题",
    "0.0.1": "首个版本，包含多渠道通知、智能限流、监控统计等完整功能"
}

def print_version_info():
    """打印版本信息"""
    print(f"Claude Code Notifier v{__version__}")
    print(f"版本描述: {VERSION_HISTORY.get(__version__, '未知版本')}")
    print("项目地址: https://github.com/kdush/Claude-Code-Notifier")
    print("许可证: Apache-2.0")
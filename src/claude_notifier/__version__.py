#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version information for Claude Code Notifier
"""

__version__ = "0.0.3b4"
__version_info__ = (0, 0, 3)

# 版本历史
VERSION_HISTORY = {
    "0.0.3b4": "预发行：CLI命令优化、卸载功能修复、跨平台兼容性完善、CI/CD流程增强",
    "0.0.3b2": "预发行：PyPI版本Claude Code钩子自动配置系统、智能CLI管理、统一用户体验、跨平台兼容性增强",
    "0.0.3b1": "预发行：PyPI版本Claude Code钩子自动配置系统、智能CLI管理、统一用户体验",
    "0.0.2": "修复版本：解决配置备份/恢复、模板引擎API、相对导入等集成问题",
    "0.0.1": "首个版本，包含多渠道通知、智能限流、监控统计等完整功能"
}

def print_version_info():
    """打印版本信息"""
    print(f"Claude Code Notifier v{__version__}")
    # 预发行检测（按照 PEP 440 a/b/rc）
    pre_label = None
    if "rc" in __version__:
        pre_label = "RC"
    elif "a" in __version__:
        pre_label = "Alpha"
    elif "b" in __version__:
        pre_label = "Beta"

    if pre_label:
        print(f"版本类型: {pre_label}")
        print("这是预发行版本，可能包含变更")

    print(f"版本描述: {VERSION_HISTORY.get(__version__, '未知版本')}")
    print("项目地址: https://github.com/kdush/Claude-Code-Notifier")
    print("许可证: Apache-2.0")
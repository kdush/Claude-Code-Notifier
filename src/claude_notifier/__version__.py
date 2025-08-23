#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version information for Claude Code Notifier
"""

__version__ = "0.0.7b1"
__version_info__ = (0, 0, 7, 'beta', 1)

# 版本历史
VERSION_HISTORY = {
    "0.0.7b1": "PyPI兼容性修复（Beta版）：解决相对导入错误（attempted relative import with no known parent package）；将所有相对导入改为绝对导入；重新组织包结构确保PyPI安装正常工作",
    "0.0.6": "发布流程稳定性：TestPyPI 版本存在检查并在已存在时跳过上传以规避 400 错误；发布作业步骤顺序与 YAML 修复（移除 heredoc，改用 python -c，统一校验步骤命令）；安装测试加入重试与 Python 3.8 下 pip 限制；文档同步到 0.0.6",
    "0.0.5": "稳定版：跨平台 CI 修复（移除 heredoc 与多进程导入测试，改为同步导入并打印版本）、包内容清理（prune src/hooks）、文档同步，发布首个稳定版本",
    "0.0.4b2": "预发行：修复 GA test-install 多进程错误，清理打包内容并修复换行问题，提升发布稳定性",
    "0.0.4b1": "预发行：CLI系统稳定性与用户体验优化，调试诊断修复，包名引用标准化，日志系统智能化",
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
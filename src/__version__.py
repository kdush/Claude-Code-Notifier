#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 版本信息
"""

# 统一版本来源：委托到包内版本实现，避免多处维护
from claude_notifier.__version__ import (
    __version__ as _pkg_version,
    __version_info__ as _pkg_version_info,
    VERSION_HISTORY as _PKG_VERSION_HISTORY,
    print_version_info as _pkg_print_version_info,
)

# 对外保持与旧接口一致
__version__ = _pkg_version
__version_info__ = _pkg_version_info

# 版本历史
# 版本历史与包内保持一致
VERSION_HISTORY = _PKG_VERSION_HISTORY

# 构建信息
BUILD_INFO = {
    "name": "Claude Code Notifier",
    "codename": "Intelligent Griffin",
    "author": "kdush", 
    "license": "Apache-2.0",
    "python_requires": ">=3.8",
    "homepage": "https://github.com/kdush/Claude-Code-Notifier"
}

def get_version_string(include_build=False):
    """获取版本字符串"""
    version = f"v{__version__}"
    if include_build:
        version += f" ({BUILD_INFO['codename']})"
    return version

def print_version_info():
    """打印详细版本信息（委托包内实现，确保与 CLI 一致）"""
    _pkg_print_version_info()

if __name__ == "__main__":
    print_version_info()
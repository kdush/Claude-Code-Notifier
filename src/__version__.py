#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 版本信息
"""

__version__ = "0.0.2"
__version_info__ = (0, 0, 2)

# 版本历史
VERSION_HISTORY = {
    "0.0.2": {
        "date": "2025-08-20",
        "fixes": [
            "🔧 修复配置备份/恢复功能bug",
            "🎯 修复模板引擎API不一致问题", 
            "📦 修复模块相对导入问题"
        ],
        "status": "集成问题修复版本"
    },
    "0.0.1": {
        "date": "2025-08-20",
        "features": [
            "🔔 多渠道通知系统 (钉钉、飞书、企业微信、Telegram、邮箱、Server酱)",
            "🧠 智能操作门控和限流保护",
            "📊 实时监控和性能统计",
            "⚙️ 灵活的配置管理系统",
            "🧪 完整的测试框架",
            "📖 全面的文档和使用指南"
        ],
        "status": "首个版本"
    }
}

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
    """打印详细版本信息"""
    print(f"{BUILD_INFO['name']} {get_version_string(True)}")
    print(f"作者: {BUILD_INFO['author']}")
    print(f"许可: {BUILD_INFO['license']}")
    print(f"主页: {BUILD_INFO['homepage']}")
    
    current_version = VERSION_HISTORY.get(__version__)
    if current_version:
        print(f"\n📅 发布日期: {current_version['date']}")
        if current_version.get('features'):
            print("\n✨ 新功能:")
            for feature in current_version['features']:
                print(f"  {feature}")
        
        if current_version.get('improvements'):
            print("\n🔧 改进:")
            for improvement in current_version['improvements']:
                print(f"  • {improvement}")

if __name__ == "__main__":
    print_version_info()
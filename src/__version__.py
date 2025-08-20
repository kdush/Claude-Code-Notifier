#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 版本信息
"""

__version__ = "1.2.0"
__version_info__ = (1, 2, 0)

# 版本历史
VERSION_HISTORY = {
    "1.2.0": {
        "date": "2024-01-20",
        "features": [
            "🧠 智能操作阻止机制",
            "📊 通知频率自动控制", 
            "🔄 消息智能分组合并",
            "❄️ 多层级冷却管理",
            "📈 实时监控和统计",
            "🎯 自适应限流策略"
        ],
        "improvements": [
            "重构架构支持模块化扩展",
            "优化性能和内存使用",
            "增强配置管理和验证",
            "完善错误处理和恢复"
        ],
        "breaking_changes": [
            "配置文件格式升级到enhanced_config.yaml",
            "钩子系统API变更",
            "部分函数签名调整"
        ]
    },
    "1.1.0": {
        "date": "2024-01-15", 
        "features": [
            "多渠道通知支持",
            "Claude Code钩子集成",
            "基础限流机制",
            "配置文件支持"
        ]
    },
    "1.0.0": {
        "date": "2024-01-10",
        "features": [
            "初始版本发布",
            "基础通知功能"
        ]
    }
}

# 构建信息
BUILD_INFO = {
    "name": "Claude Code Notifier",
    "codename": "Intelligent Griffin",
    "author": "kdush", 
    "license": "MIT",
    "python_requires": ">=3.6",
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
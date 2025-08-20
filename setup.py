#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier - 智能通知系统
Setup script for Python package installation
"""

import os
import sys
from setuptools import setup, find_packages

# 确保 Python 版本
if sys.version_info < (3, 6):
    print("错误: Claude Code Notifier 需要 Python 3.6 或更高版本")
    sys.exit(1)

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__version__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            exec(f.read())
            return locals().get('__version__', '1.0.0')
    return '1.0.0'

# 读取 README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "Claude Code Notifier - 智能通知系统"

# 读取依赖
def get_requirements():
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return ['requests>=2.25.0', 'PyYAML>=5.4.0', 'pytz>=2021.1']

# 开发依赖
dev_requirements = [
    'pytest>=6.0.0',
    'pytest-cov>=2.10.0',
    'pytest-asyncio>=0.14.0',
    'black>=21.0.0',
    'flake8>=3.8.0',
    'mypy>=0.800',
]

# 可选依赖
optional_requirements = {
    'monitoring': ['psutil>=5.8.0'],
    'encryption': ['cryptography>=3.4.0'],
    'dev': dev_requirements,
    'all': ['psutil>=5.8.0', 'cryptography>=3.4.0'] + dev_requirements
}

setup(
    name="claude-code-notifier",
    version=get_version(),
    author="kdush",
    author_email="your-email@example.com",
    description="Claude Code 智能通知系统 - 具备操作阻止、频率控制、消息分组的高级通知管理",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/kdush/Claude-Code-Notifier",
    project_urls={
        "Bug Reports": "https://github.com/kdush/Claude-Code-Notifier/issues",
        "Source": "https://github.com/kdush/Claude-Code-Notifier",
        "Documentation": "https://github.com/kdush/Claude-Code-Notifier/blob/main/docs/README.md"
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "": [
            "templates/*.md",
            "templates/*.html", 
            "config/*.yaml",
            "config/*.template",
            "hooks/*.sh"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Monitoring",
        "Topic :: Communications",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.6",
    install_requires=get_requirements(),
    extras_require=optional_requirements,
    entry_points={
        "console_scripts": [
            "claude-notifier=notifier:main",
            "claude-notify=notifier:main",
        ],
    },
    keywords=[
        "claude-code", "notification", "webhook", "dingtalk", "feishu", 
        "telegram", "email", "serverchan", "rate-limiting", "intelligent",
        "monitoring", "automation", "development-tools"
    ],
    zip_safe=False,
    platforms=["any"],
    license="MIT",
)
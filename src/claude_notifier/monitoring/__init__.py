#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控系统模块
提供统计、健康检查、性能监控等功能
"""

from .statistics import StatisticsManager
from .health_check import HealthChecker

# 可选导入
try:
    from .performance import PerformanceMonitor
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PerformanceMonitor = None
    PERFORMANCE_AVAILABLE = False

try:
    from .dashboard import MonitoringDashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    MonitoringDashboard = None
    DASHBOARD_AVAILABLE = False

# 监控功能可用性标志
MONITORING_AVAILABLE = True

__all__ = [
    'StatisticsManager',
    'HealthChecker',
    'MONITORING_AVAILABLE',
    'PERFORMANCE_AVAILABLE', 
    'DASHBOARD_AVAILABLE'
]

# 添加可选模块到导出列表
if PERFORMANCE_AVAILABLE:
    __all__.append('PerformanceMonitor')
if DASHBOARD_AVAILABLE:
    __all__.append('MonitoringDashboard')
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控仪表板
统一的监控数据展示和管理界面
"""

import time
import threading
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .statistics import StatisticsManager
from .health_check import HealthChecker, HealthStatus
from .performance import PerformanceMonitor, PerformanceLevel


class DashboardMode(Enum):
    """仪表板模式"""
    OVERVIEW = "overview"
    DETAILED = "detailed"
    ALERTS = "alerts"
    HISTORICAL = "historical"


@dataclass
class SystemStatus:
    """系统状态汇总"""
    overall_status: str
    health_status: str
    performance_status: str
    statistics_available: bool
    last_update: float
    components: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class MonitoringDashboard:
    """监控仪表板 - 统一监控数据管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化监控仪表板
        
        Args:
            config: 仪表板配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化各监控组件
        self.statistics_manager = self._init_statistics_manager()
        self.health_checker = self._init_health_checker()
        self.performance_monitor = self._init_performance_monitor()
        
        # 仪表板状态
        self._last_update = 0
        self._update_interval = self.config.get('update_interval', 30)
        self._auto_refresh = self.config.get('auto_refresh', True)
        
        # 缓存的状态数据
        self._cached_status: Optional[SystemStatus] = None
        self._cache_duration = self.config.get('cache_duration', 10)  # 缓存10秒
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 后台更新线程
        self._running = False
        self._update_thread: Optional[threading.Thread] = None
        
        # 报警配置
        self.alert_config = {
            'max_alerts': self.config.get('max_alerts', 50),
            'alert_history_hours': self.config.get('alert_history_hours', 24),
            'critical_alert_threshold': self.config.get('critical_alert_threshold', 3)
        }
        
    def _init_statistics_manager(self) -> Optional[StatisticsManager]:
        """初始化统计管理器"""
        try:
            stats_config = self.config.get('statistics', {})
            return StatisticsManager(
                stats_file=stats_config.get('file_path'),
                auto_save=stats_config.get('auto_save', True)
            )
        except Exception as e:
            self.logger.error(f"初始化统计管理器失败: {e}")
            return None
            
    def _init_health_checker(self) -> Optional[HealthChecker]:
        """初始化健康检查器"""
        try:
            health_config = self.config.get('health_check', {})
            return HealthChecker(config=health_config)
        except Exception as e:
            self.logger.error(f"初始化健康检查器失败: {e}")
            return None
            
    def _init_performance_monitor(self) -> Optional[PerformanceMonitor]:
        """初始化性能监控器"""
        try:
            perf_config = self.config.get('performance', {})
            return PerformanceMonitor(config=perf_config)
        except Exception as e:
            self.logger.error(f"初始化性能监控器失败: {e}")
            return None
            
    def start(self):
        """启动监控仪表板"""
        if self._running:
            self.logger.warning("监控仪表板已在运行")
            return
            
        self._running = True
        
        # 启动各监控组件
        if self.health_checker:
            self.health_checker.start_background_checks()
            
        if self.performance_monitor:
            self.performance_monitor.start_monitoring()
            
        # 启动仪表板后台更新
        if self._auto_refresh:
            self._update_thread = threading.Thread(target=self._update_worker, daemon=True)
            self._update_thread.start()
            
        self.logger.info("监控仪表板已启动")
        
    def stop(self):
        """停止监控仪表板"""
        self._running = False
        
        # 停止各监控组件
        if self.health_checker:
            self.health_checker.stop_background_checks()
            
        if self.performance_monitor:
            self.performance_monitor.stop_monitoring()
            
        # 等待后台线程结束
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=5)
            
        self.logger.info("监控仪表板已停止")
        
    def _update_worker(self):
        """后台更新工作线程"""
        while self._running:
            try:
                # 强制刷新缓存
                self._update_cached_status()
                time.sleep(self._update_interval)
            except Exception as e:
                self.logger.error(f"仪表板后台更新异常: {e}")
                time.sleep(10)
                
    def _update_cached_status(self):
        """更新缓存的状态数据"""
        with self._lock:
            self._cached_status = self._collect_system_status()
            self._last_update = time.time()
            
    def get_system_status(self, force_refresh: bool = False) -> SystemStatus:
        """获取系统状态
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            系统状态汇总
        """
        with self._lock:
            # 检查缓存是否有效
            cache_age = time.time() - self._last_update
            if (not force_refresh and 
                self._cached_status and 
                cache_age < self._cache_duration):
                return self._cached_status
                
            # 刷新状态
            self._update_cached_status()
            return self._cached_status
            
    def _collect_system_status(self) -> SystemStatus:
        """收集系统状态数据"""
        # 收集健康检查数据
        health_status = "unknown"
        health_data = {}
        if self.health_checker:
            try:
                health_summary = self.health_checker.get_system_health()
                health_status = health_summary['overall_status']
                health_data = health_summary
            except Exception as e:
                self.logger.error(f"获取健康状态失败: {e}")
                
        # 收集性能监控数据
        performance_status = "unknown"
        performance_data = {}
        performance_alerts = []
        if self.performance_monitor:
            try:
                perf_summary = self.performance_monitor.get_performance_summary()
                performance_status = perf_summary['overall_performance']
                performance_data = perf_summary
                performance_alerts = self.performance_monitor.get_alerts()
            except Exception as e:
                self.logger.error(f"获取性能状态失败: {e}")
                
        # 收集统计数据
        statistics_available = self.statistics_manager is not None
        statistics_data = {}
        if self.statistics_manager:
            try:
                statistics_data = self.statistics_manager.get_realtime_stats()
            except Exception as e:
                self.logger.error(f"获取统计数据失败: {e}")
                
        # 确定整体状态
        overall_status = self._determine_overall_status(health_status, performance_status)
        
        # 收集所有报警
        all_alerts = []
        
        # 健康检查报警
        if health_data.get('critical_issues'):
            for issue in health_data['critical_issues']:
                all_alerts.append({
                    'type': 'health',
                    'level': 'critical',
                    'message': issue,
                    'timestamp': time.time(),
                    'component': 'health_check'
                })
                
        if health_data.get('warning_issues'):
            for issue in health_data['warning_issues']:
                all_alerts.append({
                    'type': 'health',
                    'level': 'warning',
                    'message': issue,
                    'timestamp': time.time(),
                    'component': 'health_check'
                })
                
        # 性能监控报警
        all_alerts.extend([{
            **alert,
            'type': 'performance',
            'component': 'performance_monitor'
        } for alert in performance_alerts])
        
        # 按时间排序并限制数量
        all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        all_alerts = all_alerts[:self.alert_config['max_alerts']]
        
        return SystemStatus(
            overall_status=overall_status,
            health_status=health_status,
            performance_status=performance_status,
            statistics_available=statistics_available,
            last_update=time.time(),
            components={
                'health': health_data,
                'performance': performance_data,
                'statistics': statistics_data
            },
            alerts=all_alerts,
            metrics=self._collect_key_metrics()
        )
        
    def _determine_overall_status(self, health_status: str, performance_status: str) -> str:
        """确定整体系统状态"""
        # 状态优先级: critical > warning > unknown > good > excellent
        status_priority = {
            'critical': 0,
            'warning': 1,
            'unknown': 2,
            'good': 3,
            'excellent': 4,
            'healthy': 3  # 健康检查中的healthy等同于good
        }
        
        statuses = [health_status, performance_status]
        min_priority = min(status_priority.get(status, 2) for status in statuses)
        
        # 找到对应的状态
        for status, priority in status_priority.items():
            if priority == min_priority:
                return status
                
        return 'unknown'
        
    def _collect_key_metrics(self) -> Dict[str, Any]:
        """收集关键指标"""
        metrics = {}
        
        # 统计指标
        if self.statistics_manager:
            try:
                realtime = self.statistics_manager.get_realtime_stats()
                metrics.update({
                    'session_duration': realtime['current_session']['duration'],
                    'events_count': realtime['current_session']['events_count'],
                    'notifications_sent': realtime['current_session']['notifications_sent'],
                    'errors_count': realtime['current_session']['errors_count']
                })
            except Exception:
                pass
                
        # 性能指标
        if self.performance_monitor:
            try:
                current_metrics = self.performance_monitor.get_current_metrics()
                for name, metric in current_metrics.items():
                    if name in ['cpu_usage', 'memory_usage', 'response_time']:
                        metrics[name] = {
                            'value': metric.value,
                            'unit': metric.unit,
                            'level': metric.level.value
                        }
            except Exception:
                pass
                
        # 健康指标
        if self.health_checker:
            try:
                health_summary = self.health_checker.get_system_health()
                summary = health_summary.get('summary', {})
                metrics.update({
                    'healthy_components': summary.get('healthy_components', 0),
                    'total_components': summary.get('total_components', 0)
                })
            except Exception:
                pass
                
        return metrics
        
    def get_dashboard_view(self, mode: Union[str, DashboardMode] = DashboardMode.OVERVIEW) -> str:
        """获取仪表板视图
        
        Args:
            mode: 显示模式
            
        Returns:
            格式化的仪表板文本
        """
        if isinstance(mode, str):
            try:
                mode = DashboardMode(mode)
            except ValueError:
                mode = DashboardMode.OVERVIEW
                
        status = self.get_system_status()
        
        if mode == DashboardMode.OVERVIEW:
            return self._generate_overview_view(status)
        elif mode == DashboardMode.DETAILED:
            return self._generate_detailed_view(status)
        elif mode == DashboardMode.ALERTS:
            return self._generate_alerts_view(status)
        elif mode == DashboardMode.HISTORICAL:
            return self._generate_historical_view(status)
        else:
            return self._generate_overview_view(status)
            
    def _generate_overview_view(self, status: SystemStatus) -> str:
        """生成概览视图"""
        lines = []
        
        # 标题
        lines.append("=" * 60)
        lines.append("📊 Claude Code Notifier 监控仪表板")
        lines.append("=" * 60)
        lines.append("")
        
        # 系统状态
        status_icon = {
            'critical': '🔴',
            'warning': '🟡',
            'good': '🟢',
            'excellent': '💚',
            'healthy': '🟢',
            'unknown': '⚪'
        }.get(status.overall_status, '⚪')
        
        lines.append(f"{status_icon} 系统整体状态: {status.overall_status.upper()}")
        lines.append(f"🏥 健康状态: {status.health_status}")
        lines.append(f"⚡ 性能状态: {status.performance_status}")
        lines.append(f"📈 统计功能: {'可用' if status.statistics_available else '不可用'}")
        
        last_update = datetime.fromtimestamp(status.last_update)
        lines.append(f"🕐 最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 关键指标
        if status.metrics:
            lines.append("📋 关键指标:")
            for name, value in status.metrics.items():
                if isinstance(value, dict):
                    level_icon = {
                        'excellent': '💚',
                        'good': '🟢',
                        'warning': '🟡',
                        'critical': '🔴'
                    }.get(value.get('level'), '')
                    lines.append(f"  {level_icon} {name}: {value['value']}{value.get('unit', '')}")
                else:
                    lines.append(f"  • {name}: {value}")
            lines.append("")
        
        # 当前报警
        if status.alerts:
            lines.append("⚠️  当前报警:")
            for alert in status.alerts[:5]:  # 显示前5个
                icon = '🔴' if alert['level'] == 'critical' else '🟡'
                lines.append(f"  {icon} {alert['message']}")
            
            if len(status.alerts) > 5:
                lines.append(f"  ... 还有 {len(status.alerts) - 5} 个报警")
            lines.append("")
            
        lines.append("=" * 60)
        return '\n'.join(lines)
        
    def _generate_detailed_view(self, status: SystemStatus) -> str:
        """生成详细视图"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("📊 Claude Code Notifier 详细监控报告")
        lines.append("=" * 80)
        lines.append("")
        
        # 健康检查详情
        if status.components.get('health'):
            health_data = status.components['health']
            lines.append("🏥 健康检查详情:")
            lines.append(f"  整体状态: {health_data.get('overall_status', 'unknown')}")
            
            components = health_data.get('components', {})
            for comp_name, comp_data in components.items():
                icon = {
                    'healthy': '🟢',
                    'warning': '🟡',
                    'critical': '🔴',
                    'unknown': '⚪',
                    'disabled': '⚫'
                }.get(comp_data.get('status'), '⚪')
                
                response_time = comp_data.get('response_time', 0)
                lines.append(f"    {icon} {comp_name}: {comp_data.get('message')} ({response_time:.3f}s)")
            lines.append("")
            
        # 性能监控详情
        if status.components.get('performance'):
            perf_data = status.components['performance']
            lines.append("⚡ 性能监控详情:")
            lines.append(f"  整体性能: {perf_data.get('overall_performance', 'unknown')}")
            
            metrics = perf_data.get('metrics', {})
            for metric_name, metric_data in metrics.items():
                level_icon = {
                    'excellent': '💚',
                    'good': '🟢',
                    'warning': '🟡',
                    'critical': '🔴',
                    'unknown': '⚪'
                }.get(metric_data.get('level'), '⚪')
                
                lines.append(f"    {level_icon} {metric_name}: {metric_data['value']}{metric_data['unit']}")
            lines.append("")
            
        # 统计数据详情
        if status.components.get('statistics'):
            stats_data = status.components['statistics']
            lines.append("📈 统计数据详情:")
            
            current_session = stats_data.get('current_session', {})
            if current_session:
                lines.append(f"  当前会话:")
                lines.append(f"    持续时间: {current_session.get('duration', 0)}秒")
                lines.append(f"    事件数量: {current_session.get('events_count', 0)}")
                lines.append(f"    通知发送: {current_session.get('notifications_sent', 0)}")
                lines.append(f"    错误次数: {current_session.get('errors_count', 0)}")
            lines.append("")
            
        lines.append("=" * 80)
        return '\n'.join(lines)
        
    def _generate_alerts_view(self, status: SystemStatus) -> str:
        """生成报警视图"""
        lines = []
        
        lines.append("=" * 60)
        lines.append("⚠️  Claude Code Notifier 报警中心")
        lines.append("=" * 60)
        lines.append("")
        
        if not status.alerts:
            lines.append("✅ 当前无报警")
        else:
            lines.append(f"📊 报警总数: {len(status.alerts)}")
            critical_count = sum(1 for alert in status.alerts if alert['level'] == 'critical')
            warning_count = sum(1 for alert in status.alerts if alert['level'] == 'warning')
            lines.append(f"🔴 严重报警: {critical_count}")
            lines.append(f"🟡 警告报警: {warning_count}")
            lines.append("")
            
            lines.append("📋 报警列表:")
            for i, alert in enumerate(status.alerts, 1):
                icon = '🔴' if alert['level'] == 'critical' else '🟡'
                timestamp = datetime.fromtimestamp(alert['timestamp'])
                time_str = timestamp.strftime('%H:%M:%S')
                
                lines.append(f"  {i:2}. {icon} [{time_str}] {alert['message']}")
                lines.append(f"      类型: {alert['type']} | 组件: {alert['component']}")
                
                if i >= 20:  # 限制显示数量
                    remaining = len(status.alerts) - 20
                    lines.append(f"  ... 还有 {remaining} 个报警")
                    break
                    
        lines.append("")
        lines.append("=" * 60)
        return '\n'.join(lines)
        
    def _generate_historical_view(self, status: SystemStatus) -> str:
        """生成历史视图"""
        lines = []
        
        lines.append("=" * 60)
        lines.append("📈 Claude Code Notifier 历史数据")
        lines.append("=" * 60)
        lines.append("")
        
        # 获取统计摘要
        if self.statistics_manager:
            try:
                summary = self.statistics_manager.get_summary(period_days=7)
                
                lines.append("📊 最近7天统计:")
                lines.append(f"  事件总数: {summary['total_events']}")
                lines.append(f"  最近事件: {summary['recent_events']}")
                lines.append(f"  通知发送: {summary['total_notifications']}")
                lines.append(f"  成功率: {summary['success_rate']}")
                lines.append(f"  会话总数: {summary['total_sessions']}")
                lines.append(f"  平均时长: {summary['average_session_duration']}")
                lines.append(f"  最活跃时段: {summary['most_active_hour']}")
                lines.append(f"  最常用渠道: {summary['most_used_channel']}")
                lines.append("")
                
            except Exception as e:
                lines.append(f"❌ 获取历史统计数据失败: {e}")
                lines.append("")
                
        # 性能历史趋势（简化显示）
        if self.performance_monitor:
            try:
                lines.append("⚡ 性能趋势 (最近1小时):")
                
                # 获取CPU使用率历史
                cpu_history = self.performance_monitor.get_metric_history('cpu_usage', 60)
                if cpu_history:
                    recent_cpu = [record['value'] for record in cpu_history[-10:]]
                    avg_cpu = sum(recent_cpu) / len(recent_cpu) if recent_cpu else 0
                    lines.append(f"  CPU平均使用率: {avg_cpu:.1f}%")
                    
                # 获取内存使用率历史
                memory_history = self.performance_monitor.get_metric_history('memory_usage', 60)
                if memory_history:
                    recent_memory = [record['value'] for record in memory_history[-10:]]
                    avg_memory = sum(recent_memory) / len(recent_memory) if recent_memory else 0
                    lines.append(f"  内存平均使用率: {avg_memory:.1f}%")
                    
            except Exception as e:
                lines.append(f"❌ 获取性能历史数据失败: {e}")
                
        lines.append("")
        lines.append("=" * 60)
        return '\n'.join(lines)
        
    def export_dashboard_data(self, include_history: bool = False) -> Dict[str, Any]:
        """导出仪表板数据
        
        Args:
            include_history: 是否包含历史数据
            
        Returns:
            导出的数据
        """
        status = self.get_system_status(force_refresh=True)
        
        export_data = {
            'dashboard_info': {
                'export_time': time.time(),
                'version': '1.2.0',
                'mode': 'dashboard_export'
            },
            'system_status': {
                'overall_status': status.overall_status,
                'health_status': status.health_status,
                'performance_status': status.performance_status,
                'last_update': status.last_update
            },
            'current_metrics': status.metrics,
            'alerts': status.alerts,
            'components': status.components
        }
        
        if include_history:
            history_data = {}
            
            # 导出统计历史
            if self.statistics_manager:
                try:
                    history_data['statistics'] = self.statistics_manager.export_data(include_raw=True)
                except Exception as e:
                    history_data['statistics'] = {'error': str(e)}
                    
            # 导出性能历史
            if self.performance_monitor:
                try:
                    history_data['performance'] = {}
                    for metric_name in ['cpu_usage', 'memory_usage', 'response_time']:
                        history_data['performance'][metric_name] = \
                            self.performance_monitor.get_metric_history(metric_name, 24*60)  # 24小时
                except Exception as e:
                    history_data['performance'] = {'error': str(e)}
                    
            export_data['history'] = history_data
            
        return export_data
        
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要（轻量级）"""
        status = self.get_system_status()
        
        return {
            'overall_status': status.overall_status,
            'health_status': status.health_status,
            'performance_status': status.performance_status,
            'alert_count': len(status.alerts),
            'critical_alerts': len([a for a in status.alerts if a['level'] == 'critical']),
            'last_update': status.last_update,
            'components_available': {
                'statistics': status.statistics_available,
                'health_check': self.health_checker is not None,
                'performance': self.performance_monitor is not None
            }
        }
        
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        if self.performance_monitor:
            self.performance_monitor.cleanup()
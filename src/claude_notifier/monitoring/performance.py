#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能监控器
监控系统性能指标，包括CPU、内存、响应时间等
"""

import time
import threading
import logging
import os
import gc
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import deque, defaultdict

# 可选依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


class PerformanceLevel(Enum):
    """性能等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    level: PerformanceLevel = PerformanceLevel.UNKNOWN
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'level': self.level.value,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'details': self.details
        }


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""
    excellent_threshold: float
    good_threshold: float
    warning_threshold: float
    critical_threshold: float
    
    def get_level(self, value: float, reverse: bool = False) -> PerformanceLevel:
        """根据值获取性能等级
        
        Args:
            value: 指标值
            reverse: 是否反向比较（值越小越好，如响应时间）
        """
        if reverse:
            if value <= self.excellent_threshold:
                return PerformanceLevel.EXCELLENT
            elif value <= self.good_threshold:
                return PerformanceLevel.GOOD
            elif value <= self.warning_threshold:
                return PerformanceLevel.WARNING
            else:
                return PerformanceLevel.CRITICAL
        else:
            if value >= self.excellent_threshold:
                return PerformanceLevel.EXCELLENT
            elif value >= self.good_threshold:
                return PerformanceLevel.GOOD
            elif value >= self.warning_threshold:
                return PerformanceLevel.WARNING
            else:
                return PerformanceLevel.CRITICAL


class PerformanceMonitor:
    """系统性能监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化性能监控器
        
        Args:
            config: 性能监控配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 性能指标历史数据（使用deque限制大小）
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 当前性能指标
        self.current_metrics: Dict[str, PerformanceMetric] = {}
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 后台监控线程控制
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = self.config.get('monitor_interval', 30)  # 默认30秒
        
        # 性能阈值配置
        self.thresholds = self._init_thresholds()
        
        # 监控统计
        self.stats = {
            'total_samples': 0,
            'alerts_triggered': 0,
            'performance_degradation_count': 0,
            'last_monitor_time': None,
            'monitoring_overhead': 0.0
        }
        
        # 注册性能监控器
        self._register_monitors()
        
    def _init_thresholds(self) -> Dict[str, PerformanceThresholds]:
        """初始化性能阈值"""
        default_thresholds = {
            'cpu_usage': PerformanceThresholds(80, 60, 40, 20),  # CPU使用率 (%)
            'memory_usage': PerformanceThresholds(80, 60, 40, 20),  # 内存使用率 (%)
            'disk_usage': PerformanceThresholds(90, 80, 70, 50),  # 磁盘使用率 (%)
            'response_time': PerformanceThresholds(100, 500, 1000, 2000),  # 响应时间 (ms) - 反向
            'throughput': PerformanceThresholds(100, 80, 50, 20),  # 吞吐量 (req/s)
            'error_rate': PerformanceThresholds(1, 5, 10, 20),  # 错误率 (%) - 反向
            'queue_size': PerformanceThresholds(10, 50, 100, 500)  # 队列大小 - 反向
        }
        
        # 允许通过配置覆盖阈值
        user_thresholds = self.config.get('thresholds', {})
        for name, user_config in user_thresholds.items():
            if name in default_thresholds and isinstance(user_config, dict):
                default_thresholds[name] = PerformanceThresholds(**user_config)
                
        return default_thresholds
        
    def _register_monitors(self):
        """注册性能监控器"""
        self.monitors: Dict[str, Callable[[], Tuple[float, Dict[str, Any]]]] = {
            'cpu_usage': self._monitor_cpu_usage,
            'memory_usage': self._monitor_memory_usage,
            'disk_usage': self._monitor_disk_usage,
            'process_info': self._monitor_process_info,
            'gc_stats': self._monitor_gc_stats
        }
        
    def start_monitoring(self):
        """启动后台性能监控"""
        if self._running:
            self.logger.warning("性能监控已在运行")
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self._monitor_thread.start()
        self.logger.info("后台性能监控已启动")
        
    def stop_monitoring(self):
        """停止后台性能监控"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        self.logger.info("后台性能监控已停止")
        
    def _monitoring_worker(self):
        """后台监控工作线程"""
        while self._running:
            try:
                start_time = time.time()
                
                # 收集所有性能指标
                self.collect_all_metrics()
                
                # 记录监控开销
                overhead = time.time() - start_time
                with self._lock:
                    self.stats['monitoring_overhead'] = overhead
                    self.stats['last_monitor_time'] = time.time()
                
                # 休眠到下一个监控周期
                time.sleep(self._monitor_interval)
                
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                time.sleep(10)  # 异常时短暂休眠
                
    def collect_all_metrics(self) -> Dict[str, PerformanceMetric]:
        """收集所有性能指标"""
        metrics = {}
        
        with self._lock:
            for name, monitor_func in self.monitors.items():
                try:
                    value, details = monitor_func()
                    
                    # 确定性能等级
                    level = PerformanceLevel.UNKNOWN
                    if name in self.thresholds:
                        reverse = name in ['response_time', 'error_rate', 'queue_size']
                        level = self.thresholds[name].get_level(value, reverse)
                    
                    # 创建性能指标
                    metric = PerformanceMetric(
                        name=name,
                        value=value,
                        unit=details.get('unit', ''),
                        level=level,
                        details=details
                    )
                    
                    metrics[name] = metric
                    self.current_metrics[name] = metric
                    
                    # 添加到历史数据
                    self.metrics_history[name].append({
                        'timestamp': metric.timestamp,
                        'value': metric.value,
                        'level': metric.level.value
                    })
                    
                    # 检查是否需要报警
                    if level in [PerformanceLevel.WARNING, PerformanceLevel.CRITICAL]:
                        self.stats['alerts_triggered'] += 1
                        if level == PerformanceLevel.CRITICAL:
                            self.stats['performance_degradation_count'] += 1
                            
                except Exception as e:
                    self.logger.error(f"收集 {name} 指标失败: {e}")
                    
            self.stats['total_samples'] += 1
            
        return metrics
        
    def get_current_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取当前性能指标"""
        with self._lock:
            return self.current_metrics.copy()
            
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取指标历史数据
        
        Args:
            metric_name: 指标名称
            minutes: 获取最近多少分钟的数据
        """
        cutoff_time = time.time() - (minutes * 60)
        
        with self._lock:
            if metric_name not in self.metrics_history:
                return []
                
            history = self.metrics_history[metric_name]
            return [
                record for record in history 
                if record['timestamp'] >= cutoff_time
            ]
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        with self._lock:
            metrics = self.current_metrics
            
            # 统计各等级指标数量
            level_counts = defaultdict(int)
            for metric in metrics.values():
                level_counts[metric.level.value] += 1
                
            # 计算整体性能等级
            overall_level = PerformanceLevel.EXCELLENT
            if level_counts.get('critical', 0) > 0:
                overall_level = PerformanceLevel.CRITICAL
            elif level_counts.get('warning', 0) > 0:
                overall_level = PerformanceLevel.WARNING
            elif level_counts.get('good', 0) > 0:
                overall_level = PerformanceLevel.GOOD
                
            # 生成摘要
            summary = {
                'overall_performance': overall_level.value,
                'total_metrics': len(metrics),
                'level_distribution': dict(level_counts),
                'metrics': {name: metric.to_dict() for name, metric in metrics.items()},
                'stats': self.stats.copy(),
                'monitoring_active': self._running,
                'last_update': max(
                    (m.timestamp for m in metrics.values()), default=None
                )
            }
            
            return summary
            
    def _monitor_cpu_usage(self) -> Tuple[float, Dict[str, Any]]:
        """监控CPU使用率"""
        if not PSUTIL_AVAILABLE:
            return 0.0, {'unit': '%', 'error': 'psutil not available'}
            
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            details = {
                'unit': '%',
                'cpu_count': cpu_count,
                'per_cpu': psutil.cpu_percent(interval=None, percpu=True)[:4]  # 只显示前4个核心
            }
            
            return cpu_percent, details
            
        except Exception as e:
            return 0.0, {'unit': '%', 'error': str(e)}
            
    def _monitor_memory_usage(self) -> Tuple[float, Dict[str, Any]]:
        """监控内存使用率"""
        if not PSUTIL_AVAILABLE:
            return 0.0, {'unit': '%', 'error': 'psutil not available'}
            
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            details = {
                'unit': '%',
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'process_memory_mb': round(process_memory.rss / (1024**2), 2),
                'swap_percent': psutil.swap_memory().percent
            }
            
            return memory.percent, details
            
        except Exception as e:
            return 0.0, {'unit': '%', 'error': str(e)}
            
    def _monitor_disk_usage(self) -> Tuple[float, Dict[str, Any]]:
        """监控磁盘使用率"""
        if not PSUTIL_AVAILABLE:
            return 0.0, {'unit': '%', 'error': 'psutil not available'}
            
        try:
            # 监控根目录磁盘使用率
            disk_usage = psutil.disk_usage('/')
            
            details = {
                'unit': '%',
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2)
            }
            
            return (disk_usage.used / disk_usage.total) * 100, details
            
        except Exception as e:
            return 0.0, {'unit': '%', 'error': str(e)}
            
    def _monitor_process_info(self) -> Tuple[float, Dict[str, Any]]:
        """监控进程信息"""
        if not PSUTIL_AVAILABLE:
            return 0.0, {'unit': 'count', 'error': 'psutil not available'}
            
        try:
            process = psutil.Process()
            
            details = {
                'unit': 'count',
                'pid': process.pid,
                'ppid': process.ppid(),
                'threads': process.num_threads(),
                'fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                'status': process.status(),
                'create_time': process.create_time(),
                'uptime': time.time() - process.create_time()
            }
            
            return float(process.num_threads()), details
            
        except Exception as e:
            return 0.0, {'unit': 'count', 'error': str(e)}
            
    def _monitor_gc_stats(self) -> Tuple[float, Dict[str, Any]]:
        """监控垃圾回收统计"""
        try:
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()
            
            details = {
                'unit': 'count',
                'generation_0': gc_counts[0],
                'generation_1': gc_counts[1],
                'generation_2': gc_counts[2],
                'total_collections': sum(stat['collections'] for stat in gc_stats),
                'total_collected': sum(stat['collected'] for stat in gc_stats),
                'total_uncollectable': sum(stat['uncollectable'] for stat in gc_stats)
            }
            
            # 返回generation 0的对象数量作为主要指标
            return float(gc_counts[0]), details
            
        except Exception as e:
            return 0.0, {'unit': 'count', 'error': str(e)}
            
    def record_custom_metric(self, name: str, value: float, unit: str = '', 
                           details: Optional[Dict[str, Any]] = None):
        """记录自定义性能指标
        
        Args:
            name: 指标名称
            value: 指标值
            unit: 单位
            details: 详细信息
        """
        with self._lock:
            # 确定性能等级
            level = PerformanceLevel.UNKNOWN
            if name in self.thresholds:
                reverse = name in ['response_time', 'error_rate', 'queue_size']
                level = self.thresholds[name].get_level(value, reverse)
            
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                level=level,
                details=details or {}
            )
            
            self.current_metrics[name] = metric
            self.metrics_history[name].append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'level': metric.level.value
            })
            
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取性能报警
        
        Args:
            severity: 报警严重程度过滤 ('warning', 'critical')
        """
        alerts = []
        
        with self._lock:
            for name, metric in self.current_metrics.items():
                if metric.level in [PerformanceLevel.WARNING, PerformanceLevel.CRITICAL]:
                    if severity is None or metric.level.value == severity:
                        alerts.append({
                            'metric_name': name,
                            'current_value': metric.value,
                            'unit': metric.unit,
                            'level': metric.level.value,
                            'timestamp': metric.timestamp,
                            'message': f"{name} 性能 {metric.level.value}: {metric.value}{metric.unit}",
                            'details': metric.details
                        })
                        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
        
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        summary = self.get_performance_summary()
        
        report = []
        report.append("=" * 60)
        report.append("⚡ Claude Code Notifier 性能监控报告")
        report.append("=" * 60)
        report.append("")
        
        report.append(f"📊 整体性能状态: {summary['overall_performance'].upper()}")
        report.append(f"🔍 监控指标数量: {summary['total_metrics']}")
        report.append(f"📈 监控状态: {'运行中' if summary['monitoring_active'] else '已停止'}")
        
        if summary['last_update']:
            last_update = datetime.fromtimestamp(summary['last_update'])
            report.append(f"🕐 最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 性能等级分布
        distribution = summary['level_distribution']
        if distribution:
            report.append("📈 性能等级分布:")
            for level, count in distribution.items():
                report.append(f"  • {level.capitalize()}: {count}")
            report.append("")
        
        # 详细指标
        report.append("📋 详细性能指标:")
        for name, metric in summary['metrics'].items():
            level_icon = {
                'excellent': '🟢',
                'good': '🔵', 
                'warning': '🟡',
                'critical': '🔴',
                'unknown': '⚪'
            }.get(metric['level'], '⚪')
            
            report.append(f"  {level_icon} {name}: {metric['value']}{metric['unit']} ({metric['level']})")
            
        report.append("")
        
        # 统计信息
        stats = summary['stats']
        report.append("📊 监控统计:")
        report.append(f"  • 采样总数: {stats['total_samples']}")
        report.append(f"  • 触发报警: {stats['alerts_triggered']}")
        report.append(f"  • 性能降级次数: {stats['performance_degradation_count']}")
        report.append(f"  • 监控开销: {stats['monitoring_overhead']:.3f}s")
        report.append("")
        
        # 当前报警
        alerts = self.get_alerts()
        if alerts:
            report.append("⚠️  当前性能报警:")
            for alert in alerts[:5]:  # 只显示最近5个
                icon = '🔴' if alert['level'] == 'critical' else '🟡'
                report.append(f"  {icon} {alert['message']}")
            
            if len(alerts) > 5:
                report.append(f"  ... 还有 {len(alerts) - 5} 个报警")
                
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)
        
    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        
        with self._lock:
            self.metrics_history.clear()
            self.current_metrics.clear()
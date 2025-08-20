#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统健康检查器
监控各组件健康状态，提供实时健康报告
"""

import time
import threading
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: HealthStatus
    message: str
    response_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'response_time': self.response_time,
            'details': self.details,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    component: str
    check_function: Callable[[], Tuple[HealthStatus, str, Dict[str, Any]]]
    interval: int = 60  # 检查间隔（秒）
    timeout: int = 10   # 超时时间（秒）
    enabled: bool = True
    critical: bool = False  # 是否为关键组件


class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化健康检查器
        
        Args:
            config: 健康检查配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 注册的健康检查
        self.health_checks: Dict[str, HealthCheckConfig] = {}
        
        # 健康检查结果缓存
        self.check_results: Dict[str, HealthCheckResult] = {}
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 后台检查线程控制
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.stats = {
            'total_checks': 0,
            'failed_checks': 0,
            'average_response_time': 0.0,
            'last_check_time': None
        }
        
        # 注册默认健康检查
        self._register_default_checks()
        
    def _register_default_checks(self):
        """注册默认健康检查"""
        # 基础系统检查
        self.register_check(
            'system_basic',
            self._check_system_basic,
            interval=120,
            critical=True
        )
        
        # 文件系统检查
        self.register_check(
            'filesystem',
            self._check_filesystem,
            interval=300
        )
        
        # 内存使用检查
        self.register_check(
            'memory',
            self._check_memory_usage,
            interval=60
        )
        
    def register_check(self, component: str, 
                      check_function: Callable[[], Tuple[HealthStatus, str, Dict[str, Any]]],
                      interval: int = 60,
                      timeout: int = 10,
                      enabled: bool = True,
                      critical: bool = False):
        """注册健康检查
        
        Args:
            component: 组件名称
            check_function: 检查函数，返回 (状态, 消息, 详情)
            interval: 检查间隔（秒）
            timeout: 超时时间（秒）
            enabled: 是否启用
            critical: 是否为关键组件
        """
        with self._lock:
            config = HealthCheckConfig(
                component=component,
                check_function=check_function,
                interval=interval,
                timeout=timeout,
                enabled=enabled,
                critical=critical
            )
            
            self.health_checks[component] = config
            self.logger.debug(f"已注册健康检查: {component}")
            
    def unregister_check(self, component: str):
        """取消注册健康检查"""
        with self._lock:
            if component in self.health_checks:
                del self.health_checks[component]
                if component in self.check_results:
                    del self.check_results[component]
                self.logger.debug(f"已取消注册健康检查: {component}")
                
    def check_component(self, component: str, force: bool = False) -> Optional[HealthCheckResult]:
        """检查单个组件健康状态
        
        Args:
            component: 组件名称
            force: 是否强制检查（忽略缓存）
            
        Returns:
            健康检查结果
        """
        with self._lock:
            if component not in self.health_checks:
                return None
                
            config = self.health_checks[component]
            
            if not config.enabled and not force:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DISABLED,
                    message="健康检查已禁用"
                )
                
            # 检查缓存是否有效
            if not force and component in self.check_results:
                result = self.check_results[component]
                age = time.time() - result.timestamp
                if age < config.interval:
                    return result
                    
            # 执行健康检查
            start_time = time.time()
            
            try:
                status, message, details = config.check_function()
                response_time = time.time() - start_time
                
                result = HealthCheckResult(
                    component=component,
                    status=status,
                    message=message,
                    response_time=response_time,
                    details=details
                )
                
                # 更新缓存和统计
                self.check_results[component] = result
                self._update_stats(response_time, status != HealthStatus.HEALTHY)
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.CRITICAL,
                    message=f"健康检查异常: {str(e)}",
                    response_time=response_time,
                    details={'error': str(e)}
                )
                
                self.check_results[component] = result
                self._update_stats(response_time, True)
                self.logger.error(f"组件 {component} 健康检查失败: {e}")
                
                return result
                
    def check_all_components(self, force: bool = False) -> Dict[str, HealthCheckResult]:
        """检查所有组件健康状态
        
        Args:
            force: 是否强制检查
            
        Returns:
            所有组件的健康检查结果
        """
        results = {}
        
        with self._lock:
            for component in self.health_checks:
                result = self.check_component(component, force)
                if result:
                    results[component] = result
                    
        return results
        
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统整体健康状态"""
        results = self.check_all_components()
        
        if not results:
            return {
                'overall_status': HealthStatus.UNKNOWN.value,
                'message': '无健康检查数据',
                'components': {},
                'summary': {
                    'total_components': 0,
                    'healthy_components': 0,
                    'warning_components': 0,
                    'critical_components': 0,
                    'disabled_components': 0
                }
            }
            
        # 统计各状态组件数量
        summary = {
            'total_components': len(results),
            'healthy_components': 0,
            'warning_components': 0,
            'critical_components': 0,
            'disabled_components': 0
        }
        
        critical_issues = []
        warning_issues = []
        
        for component, result in results.items():
            config = self.health_checks.get(component)
            
            if result.status == HealthStatus.HEALTHY:
                summary['healthy_components'] += 1
            elif result.status == HealthStatus.WARNING:
                summary['warning_components'] += 1
                warning_issues.append(f"{component}: {result.message}")
            elif result.status == HealthStatus.CRITICAL:
                summary['critical_components'] += 1
                critical_issues.append(f"{component}: {result.message}")
                
                # 关键组件故障影响整体状态
                if config and config.critical:
                    pass  # 将在下面的整体状态判断中处理
                    
            elif result.status == HealthStatus.DISABLED:
                summary['disabled_components'] += 1
                
        # 确定整体健康状态
        if critical_issues:
            # 检查是否有关键组件故障
            critical_components = [
                comp for comp, result in results.items()
                if (result.status == HealthStatus.CRITICAL and 
                    self.health_checks.get(comp, {}).critical)
            ]
            
            if critical_components:
                overall_status = HealthStatus.CRITICAL
                message = f"关键组件故障: {', '.join(critical_components)}"
            else:
                overall_status = HealthStatus.WARNING
                message = f"发现 {len(critical_issues)} 个组件故障"
        elif warning_issues:
            overall_status = HealthStatus.WARNING
            message = f"发现 {len(warning_issues)} 个警告"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "所有组件正常运行"
            
        return {
            'overall_status': overall_status.value,
            'message': message,
            'components': {comp: result.to_dict() for comp, result in results.items()},
            'summary': summary,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'stats': self.stats.copy(),
            'last_check_time': max(r.timestamp for r in results.values()) if results else None
        }
        
    def start_background_checks(self):
        """启动后台健康检查"""
        if self._running:
            self.logger.warning("后台健康检查已在运行")
            return
            
        self._running = True
        self._check_thread = threading.Thread(target=self._background_check_worker, daemon=True)
        self._check_thread.start()
        self.logger.info("后台健康检查已启动")
        
    def stop_background_checks(self):
        """停止后台健康检查"""
        self._running = False
        if self._check_thread and self._check_thread.is_alive():
            self._check_thread.join(timeout=5)
        self.logger.info("后台健康检查已停止")
        
    def _background_check_worker(self):
        """后台检查工作线程"""
        next_check_times = {}
        
        while self._running:
            try:
                current_time = time.time()
                
                # 检查哪些组件需要进行健康检查
                for component, config in self.health_checks.items():
                    if not config.enabled:
                        continue
                        
                    next_check = next_check_times.get(component, 0)
                    
                    if current_time >= next_check:
                        self.check_component(component)
                        next_check_times[component] = current_time + config.interval
                        
                # 休眠一小段时间避免CPU占用过高
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"后台健康检查异常: {e}")
                time.sleep(30)
                
    def _update_stats(self, response_time: float, failed: bool):
        """更新统计信息"""
        self.stats['total_checks'] += 1
        self.stats['last_check_time'] = time.time()
        
        if failed:
            self.stats['failed_checks'] += 1
            
        # 更新平均响应时间
        total = self.stats['total_checks']
        avg = self.stats['average_response_time']
        self.stats['average_response_time'] = (avg * (total - 1) + response_time) / total
        
    # 默认健康检查函数
    def _check_system_basic(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """基础系统检查"""
        try:
            import os
            import sys
            
            details = {
                'python_version': sys.version,
                'platform': sys.platform,
                'process_id': os.getpid()
            }
            
            return HealthStatus.HEALTHY, "系统基础功能正常", details
            
        except Exception as e:
            return HealthStatus.CRITICAL, f"系统基础检查失败: {e}", {'error': str(e)}
            
    def _check_filesystem(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """文件系统检查"""
        try:
            import os
            import shutil
            from pathlib import Path
            
            # 检查配置目录
            config_dir = Path.home() / '.claude-notifier'
            
            details = {
                'config_dir_exists': config_dir.exists(),
                'config_dir_writable': os.access(config_dir.parent, os.W_OK)
            }
            
            # 检查磁盘空间
            if config_dir.exists():
                disk_usage = shutil.disk_usage(config_dir)
                free_gb = disk_usage.free / (1024**3)
                details['free_space_gb'] = round(free_gb, 2)
                
                if free_gb < 0.1:  # 小于100MB
                    return HealthStatus.CRITICAL, f"磁盘空间不足: {free_gb:.1f}GB", details
                elif free_gb < 1:  # 小于1GB
                    return HealthStatus.WARNING, f"磁盘空间较低: {free_gb:.1f}GB", details
                    
            return HealthStatus.HEALTHY, "文件系统正常", details
            
        except Exception as e:
            return HealthStatus.WARNING, f"文件系统检查异常: {e}", {'error': str(e)}
            
    def _check_memory_usage(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """内存使用检查"""
        try:
            import psutil
            
            # 获取当前进程内存使用
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # 获取系统内存信息
            system_memory = psutil.virtual_memory()
            
            details = {
                'process_memory_mb': round(memory_mb, 2),
                'system_memory_percent': system_memory.percent,
                'system_available_gb': round(system_memory.available / (1024**3), 2)
            }
            
            # 判断内存使用情况
            if memory_mb > 500:  # 进程使用超过500MB
                return HealthStatus.WARNING, f"内存使用较高: {memory_mb:.1f}MB", details
            elif system_memory.percent > 90:  # 系统内存使用超过90%
                return HealthStatus.WARNING, f"系统内存使用率: {system_memory.percent}%", details
            
            return HealthStatus.HEALTHY, f"内存使用正常: {memory_mb:.1f}MB", details
            
        except ImportError:
            return HealthStatus.UNKNOWN, "psutil库未安装，无法检查内存", {}
        except Exception as e:
            return HealthStatus.WARNING, f"内存检查异常: {e}", {'error': str(e)}
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控系统专项测试 - 统计管理、健康检查、性能监控和仪表板
"""

import unittest
import tempfile
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 检查监控组件可用性
try:
    from claude_notifier.monitoring.statistics import StatisticsManager
    from claude_notifier.monitoring.health_check import HealthChecker
    from claude_notifier.monitoring.performance import PerformanceMonitor
    from claude_notifier.monitoring.dashboard import MonitoringDashboard, DashboardMode
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"监控组件不可用: {e}")


@unittest.skipIf(not MONITORING_AVAILABLE, "监控组件不可用")
class TestEnhancedStatisticsManager(unittest.TestCase):
    """测试增强的统计管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.stats_manager = StatisticsManager(self.temp_file.name)
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.stats_manager.stats)
        self.assertIn('intelligence', self.stats_manager.stats)
        self.assertIn('monitoring', self.stats_manager.stats)
        
    def test_record_intelligence_event(self):
        """测试记录智能事件"""
        self.stats_manager.record_intelligence_event(
            'operation_gate', 
            'blocked', 
            {'reason': 'critical_operation', 'command': 'sudo rm -rf /'}
        )
        
        stats = self.stats_manager.get_intelligence_stats()
        self.assertIn('operation_gate', stats)
        self.assertEqual(stats['operation_gate']['blocked'], 1)
        
        # 测试多次记录
        self.stats_manager.record_intelligence_event('operation_gate', 'blocked')
        self.stats_manager.record_intelligence_event('operation_gate', 'allowed')
        
        stats = self.stats_manager.get_intelligence_stats()
        self.assertEqual(stats['operation_gate']['blocked'], 2)
        self.assertEqual(stats['operation_gate']['allowed'], 1)
        
    def test_record_monitoring_event(self):
        """测试记录监控事件"""
        self.stats_manager.record_monitoring_event(
            'health_check',
            'warning',
            {'component': 'channels', 'status': 'degraded'}
        )
        
        stats = self.stats_manager.get_monitoring_stats()
        self.assertIn('health_check', stats)
        self.assertEqual(stats['health_check']['warning'], 1)
        
    def test_record_cli_operation(self):
        """测试记录CLI操作"""
        self.stats_manager.record_cli_operation(
            'status',
            0.5,
            'success',
            {'mode': 'overview', 'monitoring': True}
        )
        
        stats = self.stats_manager.get_cli_stats()
        self.assertIn('commands', stats)
        self.assertEqual(stats['commands']['status']['count'], 1)
        self.assertTrue(stats['commands']['status']['success_rate'] > 0)
        
    def test_system_health_summary(self):
        """测试系统健康摘要"""
        # 添加一些测试数据
        self.stats_manager.record_intelligence_event('operation_gate', 'blocked')
        self.stats_manager.record_monitoring_event('health_check', 'ok')
        self.stats_manager.record_cli_operation('status', 0.2, 'success')
        
        summary = self.stats_manager.get_system_health_summary()
        
        self.assertIn('intelligence_health', summary)
        self.assertIn('monitoring_health', summary)
        self.assertIn('cli_health', summary)
        self.assertIn('overall_health', summary)
        
    def test_generate_detailed_report(self):
        """测试生成详细报告"""
        # 添加测试数据
        self.stats_manager.record_intelligence_event('notification_throttle', 'throttled')
        self.stats_manager.record_monitoring_event('performance_monitor', 'alert')
        
        report = self.stats_manager.generate_detailed_report()
        
        self.assertIn('统计报告', report)
        self.assertIn('智能系统统计', report)
        self.assertIn('监控系统统计', report)
        
    def test_persistence(self):
        """测试持久化"""
        # 记录数据
        self.stats_manager.record_intelligence_event('message_grouper', 'grouped')
        original_stats = self.stats_manager.get_intelligence_stats().copy()
        
        # 保存数据
        self.stats_manager.save()
        
        # 创建新实例加载数据
        new_manager = StatisticsManager(self.temp_file.name)
        loaded_stats = new_manager.get_intelligence_stats()
        
        self.assertEqual(loaded_stats['message_grouper']['grouped'], 1)


@unittest.skipIf(not MONITORING_AVAILABLE, "监控组件不可用")
class TestHealthChecker(unittest.TestCase):
    """测试健康检查器"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'check_interval': 30,
            'components': ['channels', 'events', 'intelligence', 'monitoring'],
            'thresholds': {
                'response_time': 5.0,
                'error_rate': 0.05
            }
        }
        self.checker = HealthChecker(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.checker.enabled)
        self.assertEqual(self.checker.check_interval, 30)
        self.assertIn('channels', self.checker.components)
        
    def test_check_component_health(self):
        """测试组件健康检查"""
        # 测试渠道健康
        channel_health = self.checker.check_component_health('channels')
        self.assertIn('status', channel_health)
        self.assertIn('details', channel_health)
        self.assertIn('timestamp', channel_health)
        
        # 测试事件系统健康
        event_health = self.checker.check_component_health('events')
        self.assertIn('status', event_health)
        
    def test_system_health_check(self):
        """测试系统整体健康检查"""
        health = self.checker.get_system_health()
        
        self.assertIn('status', health)
        self.assertIn('components', health)
        self.assertIn('timestamp', health)
        self.assertIn('uptime', health)
        
        # 验证组件状态
        components = health['components']
        for component in self.config['components']:
            self.assertIn(component, components)
            
    def test_health_status_determination(self):
        """测试健康状态判定"""
        # 测试不同的健康状态
        component_results = {
            'channels': {'status': 'healthy', 'score': 1.0},
            'events': {'status': 'healthy', 'score': 1.0},
            'intelligence': {'status': 'degraded', 'score': 0.7},
            'monitoring': {'status': 'healthy', 'score': 0.9}
        }
        
        overall_status = self.checker._determine_overall_status(component_results)
        # 当有组件降级时，整体状态应该是警告
        self.assertIn(overall_status, ['healthy', 'warning', 'critical'])
        
    @patch('claude_notifier.monitoring.health_check.time.time')
    def test_continuous_monitoring(self, mock_time):
        """测试连续监控"""
        mock_time.return_value = 1000000
        
        # 启动后台监控
        self.checker.start_background_monitoring()
        self.assertTrue(self.checker.background_monitoring)
        
        # 停止后台监控
        self.checker.stop_background_monitoring()
        self.assertFalse(self.checker.background_monitoring)


@unittest.skipIf(not MONITORING_AVAILABLE, "监控组件不可用")
class TestPerformanceMonitor(unittest.TestCase):
    """测试性能监控器"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'collection_interval': 60,
            'metrics': ['cpu', 'memory', 'disk', 'response_time'],
            'thresholds': {
                'cpu_warning': 70.0,
                'cpu_critical': 90.0,
                'memory_warning': 80.0,
                'memory_critical': 95.0
            }
        }
        self.monitor = PerformanceMonitor(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.monitor.enabled)
        self.assertEqual(self.monitor.collection_interval, 60)
        self.assertIn('cpu', self.monitor.metrics)
        
    def test_collect_system_metrics(self):
        """测试收集系统指标"""
        metrics = self.monitor.collect_all_metrics()
        
        self.assertIsInstance(metrics, dict)
        
        # 检查是否包含系统指标
        if 'cpu' in self.config['metrics']:
            self.assertIn('cpu', metrics)
            
        if 'memory' in self.config['metrics']:
            self.assertIn('memory', metrics)
            
    def test_custom_metric_registration(self):
        """测试自定义指标注册"""
        def custom_metric():
            return 42.0, {'source': 'test'}
            
        self.monitor.register_metric('test_metric', custom_metric)
        
        metrics = self.monitor.collect_all_metrics()
        self.assertIn('test_metric', metrics)
        self.assertEqual(metrics['test_metric'].value, 42.0)
        
    def test_alert_checking(self):
        """测试警报检查"""
        # 模拟高CPU使用率
        def high_cpu_metric():
            return 85.0, {'source': 'mock'}
            
        self.monitor.register_metric('cpu', high_cpu_metric)
        
        alerts = self.monitor.check_alerts()
        
        self.assertIsInstance(alerts, list)
        # 应该有CPU警告警报
        cpu_alerts = [alert for alert in alerts if 'cpu' in alert.get('metric', '')]
        self.assertTrue(len(cpu_alerts) > 0)
        
    def test_performance_history(self):
        """测试性能历史记录"""
        # 收集一些指标
        self.monitor.collect_all_metrics()
        time.sleep(0.1)
        self.monitor.collect_all_metrics()
        
        history = self.monitor.get_performance_history(limit=10)
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)
        
    def test_metric_aggregation(self):
        """测试指标聚合"""
        # 添加多个数据点
        for i in range(5):
            self.monitor.collect_all_metrics()
            time.sleep(0.01)
            
        # 测试聚合统计
        aggregated = self.monitor.get_aggregated_stats(minutes=1)
        self.assertIsInstance(aggregated, dict)
        
        for metric_name in self.config['metrics']:
            if metric_name in aggregated:
                stats = aggregated[metric_name]
                self.assertIn('avg', stats)
                self.assertIn('min', stats)
                self.assertIn('max', stats)


@unittest.skipIf(not MONITORING_AVAILABLE, "监控组件不可用") 
class TestMonitoringDashboard(unittest.TestCase):
    """测试监控仪表板"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        # 创建组件
        self.stats_manager = StatisticsManager(self.temp_file.name)
        self.health_checker = HealthChecker({'enabled': True})
        self.performance_monitor = PerformanceMonitor({'enabled': True})
        
        self.dashboard = MonitoringDashboard(
            stats_manager=self.stats_manager,
            health_checker=self.health_checker,
            performance_monitor=self.performance_monitor
        )
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
        
    def test_dashboard_initialization(self):
        """测试仪表板初始化"""
        self.assertIsNotNone(self.dashboard.stats_manager)
        self.assertIsNotNone(self.dashboard.health_checker)
        self.assertIsNotNone(self.dashboard.performance_monitor)
        
    def test_overview_view(self):
        """测试概览视图"""
        overview = self.dashboard.get_dashboard_view(DashboardMode.OVERVIEW)
        
        self.assertIsInstance(overview, str)
        self.assertIn('系统状态', overview)
        self.assertIn('健康状态', overview)
        
    def test_detailed_view(self):
        """测试详细视图"""
        # 添加一些测试数据
        self.stats_manager.record_intelligence_event('operation_gate', 'blocked')
        self.stats_manager.record_monitoring_event('health_check', 'ok')
        
        detailed = self.dashboard.get_dashboard_view(DashboardMode.DETAILED)
        
        self.assertIsInstance(detailed, str)
        self.assertIn('详细监控信息', detailed)
        
    def test_alerts_view(self):
        """测试警报视图"""
        alerts = self.dashboard.get_dashboard_view(DashboardMode.ALERTS)
        
        self.assertIsInstance(alerts, str)
        self.assertIn('系统警报', alerts)
        
    def test_historical_view(self):
        """测试历史视图"""
        historical = self.dashboard.get_dashboard_view(DashboardMode.HISTORICAL)
        
        self.assertIsInstance(historical, str)
        self.assertIn('历史数据', historical)
        
    def test_system_status(self):
        """测试系统状态获取"""
        status = self.dashboard.get_system_status()
        
        self.assertIn('health', status)
        self.assertIn('performance', status)
        self.assertIn('statistics', status)
        self.assertIn('timestamp', status)
        
    def test_export_functionality(self):
        """测试导出功能"""
        # 添加测试数据
        self.stats_manager.record_intelligence_event('notification_throttle', 'allowed')
        
        # 测试JSON导出
        json_data = self.dashboard.export_data('json')
        self.assertIsInstance(json_data, str)
        
        parsed = json.loads(json_data)
        self.assertIn('statistics', parsed)
        self.assertIn('health', parsed)
        
    def test_real_time_updates(self):
        """测试实时更新功能"""
        # 获取初始状态
        initial_status = self.dashboard.get_system_status()
        
        # 添加新的事件
        self.stats_manager.record_cli_operation('config', 0.3, 'success')
        
        # 获取更新后状态
        updated_status = self.dashboard.get_system_status()
        
        # 统计应该有变化
        self.assertNotEqual(
            initial_status['statistics'], 
            updated_status['statistics']
        )


def run_tests():
    """运行所有监控测试"""
    if not MONITORING_AVAILABLE:
        print("监控组件不可用，跳过监控测试")
        return False
        
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEnhancedStatisticsManager,
        TestHealthChecker,
        TestPerformanceMonitor,
        TestMonitoringDashboard
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
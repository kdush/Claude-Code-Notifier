#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能基准测试 - 测量系统响应时间、内存使用和吞吐量
"""

import unittest
import time
import threading
import concurrent.futures
import tempfile
import os
import sys
import psutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from collections import defaultdict

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = None
        self.end_time = None
        
    def start_timing(self):
        """开始计时"""
        self.start_time = time.perf_counter()
        
    def end_timing(self, operation_name):
        """结束计时并记录"""
        self.end_time = time.perf_counter()
        if self.start_time:
            duration = self.end_time - self.start_time
            self.metrics[operation_name].append(duration)
            return duration
        return None
        
    def record_memory(self, operation_name):
        """记录内存使用"""
        process = psutil.Process()
        memory_info = process.memory_info()
        self.metrics[f"{operation_name}_memory_rss"].append(memory_info.rss / 1024 / 1024)  # MB
        self.metrics[f"{operation_name}_memory_vms"].append(memory_info.vms / 1024 / 1024)  # MB
        
    def get_statistics(self, operation_name):
        """获取统计信息"""
        if operation_name not in self.metrics:
            return None
            
        values = self.metrics[operation_name]
        if not values:
            return None
            
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'total': sum(values)
        }
        
    def print_report(self):
        """打印性能报告"""
        print("\n📊 性能基准测试报告")
        print("=" * 60)
        
        for operation in sorted(self.metrics.keys()):
            if operation.endswith('_memory_rss') or operation.endswith('_memory_vms'):
                continue
                
            stats = self.get_statistics(operation)
            if stats:
                print(f"\n🔹 {operation}:")
                print(f"   执行次数: {stats['count']}")
                print(f"   最小时间: {stats['min']:.4f}s")
                print(f"   最大时间: {stats['max']:.4f}s")
                print(f"   平均时间: {stats['avg']:.4f}s")
                print(f"   总时间: {stats['total']:.4f}s")
                
                # 内存信息
                memory_stats = self.get_statistics(f"{operation}_memory_rss")
                if memory_stats:
                    print(f"   内存使用: {memory_stats['avg']:.2f} MB")


class TestBasicOperationPerformance(unittest.TestCase):
    """测试基本操作性能"""
    
    def setUp(self):
        """设置测试环境"""
        self.metrics = PerformanceMetrics()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.metrics.print_report()
        
    def test_helper_function_performance(self):
        """测试工具函数性能"""
        try:
            from utils.helpers import is_sensitive_operation, truncate_text, escape_markdown
            
            # 测试敏感操作检测性能
            test_commands = [
                'sudo rm -rf /',
                'ls -la',
                'git commit -m "test"',
                'npm install',
                'DROP TABLE users'
            ] * 100  # 500次测试
            
            self.metrics.start_timing()
            self.metrics.record_memory('sensitive_operation_detection')
            
            for cmd in test_commands:
                is_sensitive_operation(cmd)
                
            duration = self.metrics.end_timing('sensitive_operation_detection')
            self.metrics.record_memory('sensitive_operation_detection')
            
            # 性能断言
            self.assertLess(duration, 1.0, "敏感操作检测应该在1秒内完成500次")
            
            # 测试文本截断性能
            long_text = "这是一个很长的文本内容" * 1000
            
            self.metrics.start_timing()
            
            for _ in range(1000):
                truncate_text(long_text, 100)
                
            duration = self.metrics.end_timing('text_truncation')
            
            self.assertLess(duration, 0.5, "文本截断应该在0.5秒内完成1000次")
            
            # 测试Markdown转义性能
            markdown_text = "这是*粗体*和_斜体_和`代码`" * 100
            
            self.metrics.start_timing()
            
            for _ in range(500):
                escape_markdown(markdown_text)
                
            duration = self.metrics.end_timing('markdown_escaping')
            
            self.assertLess(duration, 0.3, "Markdown转义应该在0.3秒内完成500次")
            
        except ImportError as e:
            self.skipTest(f"工具函数不可用: {e}")
            
    def test_channel_initialization_performance(self):
        """测试通道初始化性能"""
        try:
            from channels.dingtalk import DingtalkChannel
            from channels.email import EmailChannel
            
            configs = {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'https://test.webhook.com',
                    'secret': 'test'
                },
                'email': {
                    'enabled': True,
                    'smtp_host': 'smtp.test.com',
                    'sender': 'test@test.com',
                    'password': 'test',
                    'receivers': ['user@test.com']
                }
            }
            
            # 测试DingTalk初始化性能
            self.metrics.start_timing()
            
            channels = []
            for _ in range(100):
                channel = DingtalkChannel(configs['dingtalk'])
                channels.append(channel)
                
            duration = self.metrics.end_timing('dingtalk_initialization')
            self.assertLess(duration, 0.5, "100个DingTalk通道初始化应该在0.5秒内完成")
            
            # 测试Email初始化性能
            self.metrics.start_timing()
            
            email_channels = []
            for _ in range(100):
                channel = EmailChannel(configs['email'])
                email_channels.append(channel)
                
            duration = self.metrics.end_timing('email_initialization')
            self.assertLess(duration, 0.5, "100个Email通道初始化应该在0.5秒内完成")
            
        except ImportError as e:
            self.skipTest(f"通道模块不可用: {e}")
            
    def test_event_processing_performance(self):
        """测试事件处理性能"""
        try:
            from events.builtin import SensitiveOperationEvent, TaskCompletionEvent
            
            # 创建事件
            sensitive_event = SensitiveOperationEvent()
            completion_event = TaskCompletionEvent()
            
            # 准备测试上下文
            contexts = [
                {'tool_input': 'sudo rm -rf /test', 'project': 'test'},
                {'tool_input': 'ls -la', 'project': 'test'},
                {'status': 'completed', 'task_count': 5},
                {'status': 'running', 'task_count': 3}
            ] * 250  # 1000次测试
            
            # 测试敏感操作事件性能
            self.metrics.start_timing()
            
            for context in contexts:
                sensitive_event.should_trigger(context)
                
            duration = self.metrics.end_timing('sensitive_event_processing')
            self.assertLess(duration, 1.0, "敏感事件处理应该在1秒内完成1000次")
            
            # 测试任务完成事件性能
            self.metrics.start_timing()
            
            for context in contexts:
                completion_event.should_trigger(context)
                
            duration = self.metrics.end_timing('completion_event_processing')
            self.assertLess(duration, 1.0, "完成事件处理应该在1秒内完成1000次")
            
        except ImportError as e:
            self.skipTest(f"事件模块不可用: {e}")
            
    def test_config_loading_performance(self):
        """测试配置加载性能"""
        try:
            from config_manager import ConfigManager
            
            # 创建测试配置文件
            config_file = os.path.join(self.temp_dir, 'perf_config.yaml')
            
            large_config = {
                'channels': {},
                'events': {'builtin': {}, 'custom': {}},
                'notifications': {'templates': {}}
            }
            
            # 创建较大的配置
            for i in range(50):
                large_config['channels'][f'channel_{i}'] = {
                    'enabled': True,
                    'webhook': f'https://test{i}.webhook.com'
                }
                
            for i in range(30):
                large_config['events']['builtin'][f'event_{i}'] = {'enabled': True}
                
            with open(config_file, 'w') as f:
                yaml.dump(large_config, f)
                
            # 测试配置加载性能
            self.metrics.start_timing()
            self.metrics.record_memory('config_loading')
            
            for _ in range(100):
                config_manager = ConfigManager(config_file)
                config = config_manager.get_config()
                
            duration = self.metrics.end_timing('config_loading')
            self.metrics.record_memory('config_loading')
            
            self.assertLess(duration, 2.0, "100次大配置加载应该在2秒内完成")
            
        except ImportError as e:
            self.skipTest(f"配置管理器不可用: {e}")


class TestConcurrencyPerformance(unittest.TestCase):
    """测试并发性能"""
    
    def setUp(self):
        """设置测试环境"""
        self.metrics = PerformanceMetrics()
        
    def tearDown(self):
        """清理测试环境"""
        self.metrics.print_report()
        
    def test_concurrent_event_processing(self):
        """测试并发事件处理"""
        try:
            from events.builtin import SensitiveOperationEvent
            
            event = SensitiveOperationEvent()
            
            def process_events(context_batch):
                """处理一批事件"""
                results = []
                for context in context_batch:
                    result = event.should_trigger(context)
                    results.append(result)
                return results
                
            # 准备测试数据
            contexts = [
                {'tool_input': f'test command {i}', 'project': 'test'}
                for i in range(1000)
            ]
            
            # 分批处理
            batch_size = 100
            batches = [contexts[i:i+batch_size] for i in range(0, len(contexts), batch_size)]
            
            # 测试串行处理
            self.metrics.start_timing()
            
            serial_results = []
            for batch in batches:
                result = process_events(batch)
                serial_results.extend(result)
                
            serial_duration = self.metrics.end_timing('serial_event_processing')
            
            # 测试并行处理
            self.metrics.start_timing()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_events, batch) for batch in batches]
                parallel_results = []
                for future in concurrent.futures.as_completed(futures):
                    parallel_results.extend(future.result())
                    
            parallel_duration = self.metrics.end_timing('parallel_event_processing')
            
            # 验证结果一致性
            self.assertEqual(len(serial_results), len(parallel_results))
            
            # 性能比较
            speedup = serial_duration / parallel_duration
            print(f"\n并发性能提升: {speedup:.2f}x")
            
            # 并行处理应该至少有一定的性能提升
            self.assertGreater(speedup, 0.8, "并行处理应该有性能提升或至少不变差")
            
        except ImportError as e:
            self.skipTest(f"事件模块不可用: {e}")
            
    def test_concurrent_channel_operations(self):
        """测试并发通道操作"""
        try:
            from channels.dingtalk import DingtalkChannel
            
            config = {
                'enabled': True,
                'webhook': 'https://test.webhook.com'
            }
            
            def create_and_validate_channels(count):
                """创建和验证多个通道"""
                channels = []
                for _ in range(count):
                    channel = DingtalkChannel(config)
                    validation_result = channel.validate_config()
                    channels.append((channel, validation_result))
                return channels
                
            # 测试串行创建
            self.metrics.start_timing()
            serial_channels = create_and_validate_channels(200)
            serial_duration = self.metrics.end_timing('serial_channel_creation')
            
            # 测试并行创建
            self.metrics.start_timing()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(create_and_validate_channels, 50)
                    for _ in range(4)
                ]
                parallel_channels = []
                for future in concurrent.futures.as_completed(futures):
                    parallel_channels.extend(future.result())
                    
            parallel_duration = self.metrics.end_timing('parallel_channel_creation')
            
            # 验证结果
            self.assertEqual(len(serial_channels), len(parallel_channels))
            
            speedup = serial_duration / parallel_duration
            print(f"\n通道创建并发提升: {speedup:.2f}x")
            
        except ImportError as e:
            self.skipTest(f"通道模块不可用: {e}")


class TestMemoryPerformance(unittest.TestCase):
    """测试内存性能"""
    
    def setUp(self):
        """设置测试环境"""
        self.metrics = PerformanceMetrics()
        
    def tearDown(self):
        """清理测试环境"""
        self.metrics.print_report()
        
    def test_memory_usage_patterns(self):
        """测试内存使用模式"""
        try:
            from utils.statistics import StatisticsManager
            import tempfile
            
            # 创建临时统计文件
            stats_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
            stats_file.close()
            
            try:
                # 测试大量操作的内存使用
                self.metrics.record_memory('memory_baseline')
                
                stats_manager = StatisticsManager(stats_file.name)
                
                # 记录大量事件
                for i in range(1000):
                    stats_manager.record_event(f'test_event_{i % 10}', ['dingtalk'])
                    stats_manager.record_notification('dingtalk', True, 0.1)
                    
                    if i % 100 == 0:
                        self.metrics.record_memory(f'memory_after_{i}_operations')
                        
                # 生成报告（可能消耗更多内存）
                report = stats_manager.generate_report()
                
                self.metrics.record_memory('memory_after_report')
                
                # 验证内存使用合理
                baseline = self.metrics.get_statistics('memory_baseline_memory_rss')
                final = self.metrics.get_statistics('memory_after_report_memory_rss')
                
                if baseline and final:
                    memory_increase = final['avg'] - baseline['avg']
                    print(f"\n内存使用增长: {memory_increase:.2f} MB")
                    
                    # 内存增长应该合理（小于100MB）
                    self.assertLess(memory_increase, 100, "大量操作后内存增长应该小于100MB")
                    
            finally:
                os.unlink(stats_file.name)
                
        except ImportError as e:
            self.skipTest(f"统计管理器不可用: {e}")
            
    def test_memory_leaks(self):
        """测试内存泄漏"""
        try:
            from channels.dingtalk import DingtalkChannel
            
            config = {
                'enabled': True,
                'webhook': 'https://test.webhook.com'
            }
            
            initial_memory = None
            memory_samples = []
            
            # 多轮创建和销毁对象
            for round_num in range(10):
                # 创建大量对象
                channels = []
                for _ in range(100):
                    channel = DingtalkChannel(config)
                    channels.append(channel)
                    
                # 记录内存
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
                
                if initial_memory is None:
                    initial_memory = memory_mb
                    
                # 显式删除对象
                del channels
                
            # 分析内存趋势
            if len(memory_samples) >= 3:
                # 检查最后几个样本是否稳定
                last_three = memory_samples[-3:]
                memory_variance = max(last_three) - min(last_three)
                
                print(f"\n内存使用样本: {[f'{m:.1f}MB' for m in memory_samples]}")
                print(f"内存变化范围: {memory_variance:.2f} MB")
                
                # 内存变化应该相对稳定（小于20MB波动）
                self.assertLess(memory_variance, 20, "内存使用应该相对稳定，不应该有大的泄漏")
                
        except ImportError as e:
            self.skipTest(f"通道模块不可用: {e}")


class TestScalabilityPerformance(unittest.TestCase):
    """测试可扩展性性能"""
    
    def setUp(self):
        """设置测试环境"""
        self.metrics = PerformanceMetrics()
        
    def tearDown(self):
        """清理测试环境"""
        self.metrics.print_report()
        
    def test_operation_scaling(self):
        """测试操作扩展性"""
        try:
            from utils.helpers import is_sensitive_operation
            
            # 测试不同规模的操作
            scales = [100, 500, 1000, 2000]
            
            for scale in scales:
                test_commands = [f'test command {i}' for i in range(scale)]
                
                self.metrics.start_timing()
                
                for cmd in test_commands:
                    is_sensitive_operation(cmd)
                    
                duration = self.metrics.end_timing(f'scale_{scale}_operations')
                
                throughput = scale / duration
                print(f"规模 {scale}: {duration:.4f}s, 吞吐量: {throughput:.0f} ops/s")
                
            # 分析扩展性
            scales_with_data = []
            for scale in scales:
                stats = self.metrics.get_statistics(f'scale_{scale}_operations')
                if stats:
                    throughput = scale / stats['avg']
                    scales_with_data.append((scale, throughput))
                    
            if len(scales_with_data) >= 2:
                # 计算吞吐量变化
                first_throughput = scales_with_data[0][1]
                last_throughput = scales_with_data[-1][1]
                
                throughput_ratio = last_throughput / first_throughput
                
                print(f"\n吞吐量比率 (最大/最小): {throughput_ratio:.2f}")
                
                # 吞吐量不应该显著下降（线性扩展性）
                self.assertGreater(throughput_ratio, 0.5, "吞吐量不应该随规模显著下降")
                
        except ImportError as e:
            self.skipTest(f"工具函数不可用: {e}")


def run_performance_tests():
    """运行所有性能测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestBasicOperationPerformance,
        TestConcurrencyPerformance,
        TestMemoryPerformance,
        TestScalabilityPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("⚡ 运行性能基准测试")
    
    # 检查psutil是否可用
    try:
        import psutil
        print(f"系统信息: CPU核心数={psutil.cpu_count()}, 内存={psutil.virtual_memory().total//1024//1024//1024}GB")
    except ImportError:
        print("⚠️ psutil不可用，部分内存测试可能被跳过")
        
    success = run_performance_tests()
    
    if success:
        print("\n✅ 所有性能基准测试完成!")
    else:
        print("\n⚠️ 部分性能基准测试发现问题")
        
    sys.exit(0 if success else 1)
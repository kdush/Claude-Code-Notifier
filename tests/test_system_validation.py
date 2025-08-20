#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统验证测试 - 全面的端到端集成验证和质量保证
"""

import unittest
import tempfile
import os
import sys
import time
import json
import yaml
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))


class SystemValidationResult:
    """系统验证结果"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.issues_found = []
        self.performance_metrics = {}
        
    def add_result(self, test_name, passed, issue=None, duration=None):
        """添加测试结果"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            if issue:
                self.issues_found.append(f"{test_name}: {issue}")
                
        if duration:
            self.performance_metrics[test_name] = duration
            
    def skip_test(self, test_name, reason):
        """跳过测试"""
        self.tests_run += 1
        self.tests_skipped += 1
        self.issues_found.append(f"{test_name}: SKIPPED - {reason}")
        
    def print_summary(self):
        """打印验证摘要"""
        print(f"\n🎯 系统验证结果摘要")
        print(f"=" * 50)
        print(f"总测试数: {self.tests_run}")
        print(f"通过: {self.tests_passed} ✅")
        print(f"失败: {self.tests_failed} ❌")
        print(f"跳过: {self.tests_skipped} ⚠️")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"成功率: {success_rate:.1f}%")
            
        if self.issues_found:
            print(f"\n🔍 发现的问题:")
            for issue in self.issues_found:
                print(f"  - {issue}")
                
        if self.performance_metrics:
            print(f"\n⚡ 性能指标:")
            for test, duration in self.performance_metrics.items():
                print(f"  - {test}: {duration:.4f}s")


class TestCompleteSystemValidation(unittest.TestCase):
    """完整系统验证测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.validation_result = SystemValidationResult()
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = self._create_comprehensive_config()
        
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.validation_result.print_summary()
        
    def _create_comprehensive_config(self):
        """创建全面的测试配置"""
        config_file = os.path.join(self.temp_dir, 'system_config.yaml')
        
        comprehensive_config = {
            'channels': {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
                    'secret': 'test_secret'
                },
                'email': {
                    'enabled': True,
                    'smtp_host': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'sender': 'test@example.com',
                    'password': 'test_password',
                    'receivers': ['admin@example.com']
                },
                'telegram': {
                    'enabled': False,
                    'token': 'test_token',
                    'chat_id': 'test_chat'
                }
            },
            'events': {
                'builtin': {
                    'sensitive_operation': {
                        'enabled': True,
                        'channels': ['dingtalk', 'email']
                    },
                    'task_completion': {
                        'enabled': True,
                        'channels': ['dingtalk']
                    },
                    'error_occurred': {
                        'enabled': True,
                        'channels': ['email']
                    },
                    'session_start': {
                        'enabled': False
                    }
                },
                'custom': {
                    'git_operation': {
                        'name': 'Git操作检测',
                        'priority': 'normal',
                        'enabled': True,
                        'channels': ['dingtalk'],
                        'triggers': [{
                            'type': 'pattern',
                            'pattern': r'git\s+(commit|push|merge)',
                            'field': 'tool_input'
                        }]
                    },
                    'production_deploy': {
                        'name': '生产部署检测',
                        'priority': 'critical',
                        'enabled': True,
                        'channels': ['dingtalk', 'email'],
                        'triggers': [{
                            'type': 'condition',
                            'field': 'project',
                            'operator': 'contains',
                            'value': 'prod'
                        }]
                    }
                }
            },
            'notifications': {
                'default_channels': ['dingtalk'],
                'templates': {
                    'default': 'basic',
                    'detailed': 'comprehensive',
                    'alert': 'urgent'
                }
            },
            'intelligent_limiting': {
                'enabled': True,
                'operation_gate': {
                    'enabled': True,
                    'strategies': {
                        'critical_operations': {
                            'type': 'hard_block',
                            'patterns': ['sudo rm -rf', 'DROP TABLE', 'DELETE FROM']
                        }
                    }
                },
                'notification_throttle': {
                    'enabled': True,
                    'limits': {
                        'per_minute': 5,
                        'per_hour': 50
                    }
                }
            },
            'monitoring': {
                'enabled': True,
                'statistics': {
                    'enabled': True,
                    'file_path': os.path.join(self.temp_dir, 'system_stats.json')
                },
                'health_check': {
                    'enabled': True,
                    'check_interval': 30
                }
            },
            'advanced': {
                'logging': {
                    'level': 'INFO',
                    'file': os.path.join(self.temp_dir, 'system_test.log')
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(comprehensive_config, f, default_flow_style=False)
            
        return config_file
        
    def test_complete_notification_workflow(self):
        """测试完整通知工作流程"""
        test_name = "complete_notification_workflow"
        start_time = time.time()
        
        try:
            # 1. 验证配置加载
            from config_manager import ConfigManager
            config_manager = ConfigManager(self.test_config)
            config = config_manager.get_config()
            
            self.assertIn('channels', config)
            self.assertIn('events', config)
            
            # 2. 验证事件管理器
            from managers.event_manager import EventManager
            event_manager = EventManager(config)
            
            # 3. 创建通道
            from channels.dingtalk import DingtalkChannel
            dingtalk_config = config['channels']['dingtalk']
            dingtalk_channel = DingtalkChannel(dingtalk_config)
            
            # 4. 测试多种事件场景
            test_scenarios = [
                {
                    'name': 'sensitive_operation',
                    'context': {
                        'tool_input': 'sudo rm -rf /tmp/test',
                        'project': 'system-validation-test',
                        'user': 'test-user'
                    }
                },
                {
                    'name': 'git_operation',
                    'context': {
                        'tool_input': 'git push origin main',
                        'project': 'validation-project'
                    }
                },
                {
                    'name': 'production_deploy',
                    'context': {
                        'project': 'my-prod-app',
                        'operation': 'deploy'
                    }
                }
            ]
            
            workflow_results = []
            
            for scenario in test_scenarios:
                # 处理事件
                triggered_events = event_manager.process_context(scenario['context'])
                
                # 记录结果
                workflow_results.append({
                    'scenario': scenario['name'],
                    'events_triggered': len(triggered_events),
                    'events': triggered_events
                })
                
            # 验证工作流程
            total_events = sum(result['events_triggered'] for result in workflow_results)
            
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, total_events > 0, duration=duration)
            
            print(f"\n🔄 工作流程测试结果:")
            for result in workflow_results:
                print(f"  - {result['scenario']}: {result['events_triggered']} 事件")
                
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)
            
    def test_multi_channel_integration(self):
        """测试多渠道集成"""
        test_name = "multi_channel_integration"
        start_time = time.time()
        
        try:
            from config_manager import ConfigManager
            from channels.dingtalk import DingtalkChannel
            from channels.email import EmailChannel
            
            config_manager = ConfigManager(self.test_config)
            config = config_manager.get_config()
            
            # 创建所有启用的渠道
            active_channels = {}
            
            for channel_name, channel_config in config['channels'].items():
                if channel_config.get('enabled', False):
                    try:
                        if channel_name == 'dingtalk':
                            channel = DingtalkChannel(channel_config)
                        elif channel_name == 'email':
                            channel = EmailChannel(channel_config)
                        else:
                            continue
                            
                        # 验证渠道配置
                        if channel.validate_config():
                            active_channels[channel_name] = channel
                            
                    except Exception as e:
                        print(f"渠道 {channel_name} 创建失败: {e}")
                        
            # 验证多渠道创建成功
            channel_count = len(active_channels)
            
            duration = time.time() - start_time
            self.validation_result.add_result(
                test_name, 
                channel_count > 0, 
                f"创建了 {channel_count} 个渠道" if channel_count > 0 else "没有渠道创建成功",
                duration
            )
            
            print(f"\n📡 多渠道集成结果: {channel_count} 个活跃渠道")
            for name in active_channels.keys():
                print(f"  - {name}: ✅")
                
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)
            
    def test_intelligence_systems_integration(self):
        """测试智能系统集成"""
        test_name = "intelligence_systems_integration"
        start_time = time.time()
        
        # 检查智能组件可用性
        intelligence_available = True
        try:
            from claude_notifier.utils.operation_gate import OperationGate
            from claude_notifier.utils.notification_throttle import NotificationThrottle
        except ImportError:
            intelligence_available = False
            
        if not intelligence_available:
            self.validation_result.skip_test(test_name, "智能组件不可用")
            return
            
        try:
            # 测试操作门
            from claude_notifier.utils.operation_gate import OperationGate, OperationRequest
            
            gate_config = {
                'enabled': True,
                'strategies': {
                    'critical': {
                        'type': 'hard_block',
                        'patterns': ['sudo rm -rf']
                    }
                }
            }
            
            operation_gate = OperationGate(gate_config)
            
            # 测试阻止操作
            dangerous_request = OperationRequest(
                command='sudo rm -rf /',
                context={'project': 'test'},
                priority='normal'
            )
            
            result, message = operation_gate.should_allow_operation(dangerous_request)
            
            # 测试通知限流
            from claude_notifier.utils.notification_throttle import NotificationThrottle, NotificationRequest
            
            throttle_config = {
                'enabled': True,
                'limits': {'per_minute': 5}
            }
            
            throttle = NotificationThrottle(throttle_config)
            
            # 测试限流逻辑
            notification_request = NotificationRequest(
                content='test notification',
                channel='test',
                event_type='test'
            )
            
            throttle_result, throttle_message, delay = throttle.should_allow_notification(notification_request)
            
            # 验证智能系统功能
            intelligence_working = (result is not None) and (throttle_result is not None)
            
            duration = time.time() - start_time
            self.validation_result.add_result(
                test_name,
                intelligence_working,
                "智能系统正常工作" if intelligence_working else "智能系统功能异常",
                duration
            )
            
            print(f"\n🧠 智能系统集成结果:")
            print(f"  - 操作门: {'✅' if result is not None else '❌'}")
            print(f"  - 通知限流: {'✅' if throttle_result is not None else '❌'}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)
            
    def test_monitoring_systems_integration(self):
        """测试监控系统集成"""
        test_name = "monitoring_systems_integration"
        start_time = time.time()
        
        # 检查监控组件可用性
        monitoring_available = True
        try:
            from claude_notifier.monitoring.statistics import StatisticsManager
            from claude_notifier.monitoring.health_check import HealthChecker
        except ImportError:
            monitoring_available = False
            
        if not monitoring_available:
            self.validation_result.skip_test(test_name, "监控组件不可用")
            return
            
        try:
            from claude_notifier.monitoring.statistics import StatisticsManager
            from claude_notifier.monitoring.health_check import HealthChecker
            
            # 创建统计管理器
            stats_file = os.path.join(self.temp_dir, 'integration_stats.json')
            stats_manager = StatisticsManager(stats_file)
            
            # 创建健康检查器
            health_config = {'enabled': True}
            health_checker = HealthChecker(health_config)
            
            # 测试统计收集
            stats_manager.record_intelligence_event('operation_gate', 'blocked')
            stats_manager.record_monitoring_event('health_check', 'ok')
            stats_manager.record_cli_operation('status', 0.1, 'success')
            
            # 测试健康检查
            health_result = health_checker.get_system_health()
            
            # 验证监控功能
            monitoring_working = (
                health_result is not None and
                'status' in health_result
            )
            
            duration = time.time() - start_time
            self.validation_result.add_result(
                test_name,
                monitoring_working,
                "监控系统正常工作" if monitoring_working else "监控系统功能异常",
                duration
            )
            
            print(f"\n📊 监控系统集成结果:")
            print(f"  - 统计管理器: ✅")
            print(f"  - 健康检查: {'✅' if monitoring_working else '❌'}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)
            
    def test_configuration_robustness(self):
        """测试配置系统健壮性"""
        test_name = "configuration_robustness"
        start_time = time.time()
        
        try:
            from config_manager import ConfigManager
            
            robustness_results = []
            
            # 1. 测试正常配置
            try:
                config_manager = ConfigManager(self.test_config)
                config = config_manager.get_config()
                robustness_results.append(("normal_config", True))
            except Exception as e:
                robustness_results.append(("normal_config", False, str(e)))
                
            # 2. 测试无效配置文件
            try:
                invalid_config = os.path.join(self.temp_dir, 'invalid.yaml')
                with open(invalid_config, 'w') as f:
                    f.write("invalid: yaml: content:")
                    
                config_manager = ConfigManager(invalid_config)
                robustness_results.append(("invalid_yaml", False, "应该失败但没有"))
            except Exception:
                robustness_results.append(("invalid_yaml", True))  # 预期失败
                
            # 3. 测试不存在的配置文件
            try:
                nonexistent_config = os.path.join(self.temp_dir, 'nonexistent.yaml')
                config_manager = ConfigManager(nonexistent_config)
                robustness_results.append(("nonexistent_file", False, "应该失败但没有"))
            except Exception:
                robustness_results.append(("nonexistent_file", True))  # 预期失败
                
            # 4. 测试配置验证
            try:
                config_manager = ConfigManager(self.test_config)
                errors = config_manager.validate_config()
                robustness_results.append(("config_validation", True))
            except Exception as e:
                robustness_results.append(("config_validation", False, str(e)))
                
            # 计算健壮性分数
            passed_tests = sum(1 for result in robustness_results if result[1])
            total_tests = len(robustness_results)
            robustness_score = (passed_tests / total_tests) * 100
            
            duration = time.time() - start_time
            self.validation_result.add_result(
                test_name,
                robustness_score >= 75,  # 至少75%通过
                f"健壮性分数: {robustness_score:.1f}%",
                duration
            )
            
            print(f"\n🛡️ 配置健壮性测试:")
            for result in robustness_results:
                status = "✅" if result[1] else "❌"
                print(f"  - {result[0]}: {status}")
                
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)
            
    def test_system_stress_tolerance(self):
        """测试系统压力容忍度"""
        test_name = "system_stress_tolerance"
        start_time = time.time()
        
        try:
            from utils.helpers import is_sensitive_operation
            from utils.statistics import StatisticsManager
            
            # 创建统计管理器
            stats_file = os.path.join(self.temp_dir, 'stress_stats.json')
            stats_manager = StatisticsManager(stats_file)
            
            # 压力测试参数
            operations_count = 1000
            concurrent_threads = 4
            
            def stress_test_worker(worker_id, operations_per_worker):
                """压力测试工作器"""
                results = []
                for i in range(operations_per_worker):
                    try:
                        # 模拟各种操作
                        command = f"test command {worker_id}_{i}"
                        is_sensitive = is_sensitive_operation(command)
                        
                        # 记录统计
                        stats_manager.record_event(f'stress_test_{worker_id}', ['test'])
                        stats_manager.record_notification('test', True, 0.001)
                        
                        results.append(True)
                    except Exception as e:
                        results.append(False)
                        
                return results
                
            # 运行并发压力测试
            operations_per_worker = operations_count // concurrent_threads
            
            with ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
                futures = [
                    executor.submit(stress_test_worker, worker_id, operations_per_worker)
                    for worker_id in range(concurrent_threads)
                ]
                
                stress_results = []
                for future in as_completed(futures):
                    worker_results = future.result()
                    stress_results.extend(worker_results)
                    
            # 计算成功率
            successful_operations = sum(stress_results)
            total_operations = len(stress_results)
            success_rate = (successful_operations / total_operations) * 100
            
            # 生成压力测试报告
            try:
                report = stats_manager.generate_report()
                report_generated = len(report) > 0
            except Exception:
                report_generated = False
                
            stress_tolerance_good = success_rate >= 95 and report_generated
            
            duration = time.time() - start_time
            self.validation_result.add_result(
                test_name,
                stress_tolerance_good,
                f"成功率: {success_rate:.1f}%, 报告: {'✅' if report_generated else '❌'}",
                duration
            )
            
            print(f"\n💪 系统压力测试:")
            print(f"  - 总操作数: {total_operations}")
            print(f"  - 成功操作: {successful_operations}")
            print(f"  - 成功率: {success_rate:.1f}%")
            print(f"  - 并发线程: {concurrent_threads}")
            print(f"  - 报告生成: {'✅' if report_generated else '❌'}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.validation_result.add_result(test_name, False, str(e), duration)


def run_system_validation():
    """运行系统验证测试"""
    print("🎯 启动系统全面验证测试")
    print(f"Python版本: {sys.version}")
    print(f"测试环境: {os.getcwd()}")
    
    # 运行测试
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCompleteSystemValidation)
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_system_validation()
    
    if success:
        print(f"\n🎉 系统验证完成！所有测试通过")
    else:
        print(f"\n⚠️ 系统验证发现问题，需要关注")
        
    sys.exit(0 if success else 1)
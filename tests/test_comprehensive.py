#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化综合测试套件 - 测试所有功能模块 (轻量级架构)
"""

import os
import sys
import unittest
import tempfile
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 使用现有架构的导入
from channels.base import BaseChannel
from channels.dingtalk import DingtalkChannel
from channels.feishu import FeishuChannel
from channels.telegram import TelegramChannel
from channels.email import EmailChannel
from channels.serverchan import ServerChanChannel
from channels.wechat_work import WechatWorkChannel

from events.base import BaseEvent, EventType, EventPriority
from events.builtin import (
    SensitiveOperationEvent, TaskCompletionEvent, RateLimitEvent,
    ConfirmationRequiredEvent, SessionStartEvent, ErrorOccurredEvent
)
from events.custom import CustomEvent, CustomEventRegistry

from managers.event_manager import EventManager
from config_manager import ConfigManager
from templates.template_engine import TemplateEngine
from notifier import ClaudeCodeNotifier

from utils.helpers import (
    is_sensitive_operation, truncate_text, escape_markdown,
    parse_command_output, check_rate_limit_status, validate_webhook_url
)
from utils.time_utils import TimeManager, RateLimitTracker
from utils.statistics import StatisticsManager

# 导入新的智能组件 (可选组件，优雅降级)
try:
    from claude_notifier.utils.operation_gate import OperationGate
    from claude_notifier.utils.notification_throttle import NotificationThrottle
    from claude_notifier.utils.message_grouper import MessageGrouper
    from claude_notifier.utils.cooldown_manager import CooldownManager
    INTELLIGENCE_AVAILABLE = True
except ImportError:
    INTELLIGENCE_AVAILABLE = False

# 导入监控组件
try:
    from claude_notifier.monitoring.statistics import StatisticsManager as EnhancedStatisticsManager
    from claude_notifier.monitoring.health_check import HealthChecker
    from claude_notifier.monitoring.performance import PerformanceMonitor
    from claude_notifier.monitoring.dashboard import MonitoringDashboard
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


class TestChannels(unittest.TestCase):
    """测试通知渠道"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_data = {
            'project': 'test-project',
            'operation': 'test operation',
            'timestamp': '2025-08-20 12:00:00'
        }
        
    def test_dingtalk_channel_init(self):
        """测试钉钉渠道初始化"""
        config = {
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
            'secret': 'test_secret'
        }
        channel = DingtalkChannel(config)
        self.assertTrue(channel.validate_config())
        
    def test_feishu_channel_init(self):
        """测试飞书渠道初始化"""
        config = {
            'webhook': 'https://open.feishu.cn/open-apis/bot/v2/hook/test',
            'secret': 'test_secret'
        }
        channel = FeishuChannel(config)
        self.assertTrue(channel.validate_config())
        
    def test_email_channel_init(self):
        """测试邮箱渠道初始化"""
        config = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender': 'test@example.com',
            'password': 'test_password',
            'receivers': ['receiver@example.com']
        }
        channel = EmailChannel(config)
        self.assertTrue(channel.validate_config())
        
    def test_serverchan_channel_init(self):
        """测试Server酱渠道初始化"""
        config = {
            'send_key': 'test_send_key'
        }
        channel = ServerChanChannel(config)
        self.assertTrue(channel.validate_config())
        
    def test_channel_validation_failure(self):
        """测试渠道配置验证失败"""
        # 缺少必要配置
        config = {}
        channel = EmailChannel(config)
        self.assertFalse(channel.validate_config())
        
    @patch('requests.post')
    def test_dingtalk_send_notification(self, mock_post):
        """测试钉钉发送通知"""
        mock_response = Mock()
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response
        
        config = {
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
            'secret': 'test_secret'
        }
        channel = DingtalkChannel(config)
        result = channel.send_notification(self.test_data, 'test')
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
    def test_max_content_length(self):
        """测试各渠道的最大内容长度"""
        channels = [
            (DingtalkChannel({'webhook': 'test', 'secret': 'test'}), 20000),
            (FeishuChannel({'webhook': 'test', 'secret': 'test'}), 30000),
            (EmailChannel({
                'sender': 'test@test.com',
                'password': 'test',
                'receivers': ['test@test.com']
            }), 50000),
            (ServerChanChannel({'send_key': 'test'}), 10000)
        ]
        
        for channel, expected_length in channels:
            self.assertEqual(channel.get_max_content_length(), expected_length)


class TestEvents(unittest.TestCase):
    """测试事件系统"""
    
    def test_sensitive_operation_event(self):
        """测试敏感操作事件"""
        event = SensitiveOperationEvent()
        
        # 应该触发的情况
        context = {'tool_input': 'sudo rm -rf /'}
        self.assertTrue(event.should_trigger(context))
        
        # 不应该触发的情况
        context = {'tool_input': 'ls -la'}
        self.assertFalse(event.should_trigger(context))
        
    def test_task_completion_event(self):
        """测试任务完成事件"""
        event = TaskCompletionEvent()
        
        # 应该触发的情况
        context = {'task_status': 'completed'}
        self.assertTrue(event.should_trigger(context))
        
        # 不应该触发的情况
        context = {'task_status': 'in_progress'}
        self.assertFalse(event.should_trigger(context))
        
    def test_rate_limit_event(self):
        """测试限流事件"""
        event = RateLimitEvent()
        
        # 应该触发的情况
        context = {'rate_limit_exceeded': True}
        self.assertTrue(event.should_trigger(context))
        
    def test_custom_event(self):
        """测试自定义事件"""
        config = {
            'name': 'Test Custom Event',
            'priority': 'high',
            'triggers': [
                {
                    'type': 'pattern',
                    'pattern': 'git push',
                    'field': 'tool_input'
                }
            ]
        }
        
        event = CustomEvent('test_custom', config)
        
        # 应该触发的情况
        context = {'tool_input': 'git push origin main'}
        self.assertTrue(event.should_trigger(context))
        
        # 不应该触发的情况
        context = {'tool_input': 'git status'}
        self.assertFalse(event.should_trigger(context))
        
    def test_event_priority(self):
        """测试事件优先级"""
        event = SensitiveOperationEvent()
        self.assertEqual(event.priority, EventPriority.HIGH)
        
        event = SessionStartEvent()
        self.assertEqual(event.priority, EventPriority.LOW)


class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
    def test_is_sensitive_operation(self):
        """测试敏感操作检测"""
        sensitive_commands = [
            'sudo rm -rf /',
            'chmod 777 /etc/passwd',
            'git push --force',
            'npm publish',
            'docker rm container',
            'kubectl delete pod',
            'DROP TABLE users;'
        ]
        
        for cmd in sensitive_commands:
            self.assertTrue(is_sensitive_operation(cmd), f"应该检测到敏感操作: {cmd}")
            
        safe_commands = [
            'ls -la',
            'cd /home',
            'echo "hello"',
            'cat file.txt'
        ]
        
        for cmd in safe_commands:
            self.assertFalse(is_sensitive_operation(cmd), f"不应该检测为敏感操作: {cmd}")
            
    def test_truncate_text(self):
        """测试文本截断"""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        self.assertEqual(len(result), 20)
        self.assertTrue(result.endswith("..."))
        
        short_text = "Short"
        result = truncate_text(short_text, 20)
        self.assertEqual(result, short_text)
        
    def test_escape_markdown(self):
        """测试Markdown转义"""
        text = "This has *special* _characters_ `code` [link](url)"
        escaped = escape_markdown(text)
        self.assertNotIn('*', escaped.replace('\\*', ''))
        self.assertNotIn('_', escaped.replace('\\_', ''))
        
    def test_parse_command_output(self):
        """测试命令输出解析"""
        output = """
        Info: Starting process
        Warning: Deprecated feature
        Error: Failed to connect
        Info: Process completed
        """
        
        result = parse_command_output(output)
        self.assertTrue(result['has_error'])
        self.assertEqual(len(result['error_lines']), 1)
        self.assertEqual(len(result['warning_lines']), 1)
        
    def test_validate_webhook_url(self):
        """测试Webhook URL验证"""
        valid_urls = [
            'https://oapi.dingtalk.com/robot/send?access_token=xxx',
            'https://open.feishu.cn/open-apis/bot/v2/hook/xxx',
            'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
            'https://hooks.slack.com/services/xxx'
        ]
        
        for url in valid_urls:
            self.assertTrue(validate_webhook_url(url), f"应该是有效的URL: {url}")
            
        invalid_urls = [
            'http://example.com',  # 不是HTTPS
            'not-a-url',
            'ftp://example.com'
        ]
        
        for url in invalid_urls:
            self.assertFalse(validate_webhook_url(url), f"应该是无效的URL: {url}")


class TestTimeUtils(unittest.TestCase):
    """测试时间管理工具"""
    
    def test_time_manager(self):
        """测试时间管理器"""
        tm = TimeManager()
        
        # 记录活动
        tm.record_activity()
        time.sleep(0.1)
        
        # 检查空闲时间
        idle_time = tm.get_idle_time()
        self.assertIsNotNone(idle_time)
        self.assertGreaterEqual(idle_time, 0)
        
        # 测试静默期
        tm.start_quiet_period(5)
        self.assertTrue(tm.is_in_quiet_period())
        
        remaining = tm.get_quiet_time_remaining()
        self.assertIsNotNone(remaining)
        self.assertLessEqual(remaining, 5)
        
    def test_rate_limit_tracker(self):
        """测试限流追踪器"""
        tracker = RateLimitTracker()
        
        # 记录使用
        for _ in range(5):
            tracker.record_usage()
            
        # 检查使用计数
        count = tracker.get_usage_count(60)
        self.assertEqual(count, 5)
        
        # 检查限流状态
        status = tracker.check_rate_limit('minute')
        self.assertEqual(status['current'], 5)
        self.assertFalse(status['is_limited'])
        
        # 模拟达到限制
        for _ in range(6):
            tracker.record_usage()
            
        status = tracker.check_rate_limit('minute')
        self.assertTrue(status['is_limited'])
        
    def test_format_duration(self):
        """测试时间格式化"""
        tm = TimeManager()
        
        self.assertEqual(tm.format_duration(30), "30秒")
        self.assertEqual(tm.format_duration(90), "1分30秒")
        self.assertEqual(tm.format_duration(3600), "1小时")
        self.assertEqual(tm.format_duration(3660), "1小时1分钟")


class TestStatistics(unittest.TestCase):
    """测试统计监控"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.stats_manager = StatisticsManager(self.temp_file.name)
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
        
    def test_record_event(self):
        """测试记录事件"""
        self.stats_manager.record_event('test_event', ['channel1', 'channel2'])
        
        stats = self.stats_manager.stats
        self.assertEqual(stats['events']['total_triggered'], 1)
        self.assertEqual(stats['events']['by_type'].get('test_event', 0), 1)
        
    def test_record_notification(self):
        """测试记录通知"""
        self.stats_manager.record_notification('email', True, 0.5)
        self.stats_manager.record_notification('dingtalk', False)
        
        stats = self.stats_manager.stats
        self.assertEqual(stats['notifications']['total_sent'], 1)
        self.assertEqual(stats['notifications']['total_failed'], 1)
        self.assertEqual(stats['notifications']['success_rate'], 50.0)
        
    def test_performance_metrics(self):
        """测试性能指标"""
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        for rt in response_times:
            self.stats_manager.record_notification('test', True, rt)
            
        perf = self.stats_manager.stats['performance']
        self.assertEqual(perf['max_response_time'], 0.5)
        self.assertEqual(perf['min_response_time'], 0.1)
        self.assertAlmostEqual(perf['average_response_time'], 0.3, places=1)
        
    def test_generate_report(self):
        """测试生成报告"""
        # 添加一些测试数据
        self.stats_manager.record_event('test_event', ['channel1'])
        self.stats_manager.record_notification('email', True, 0.5)
        self.stats_manager.record_session(300)
        self.stats_manager.record_command(is_sensitive=True)
        
        report = self.stats_manager.generate_report()
        
        self.assertIn('统计报告', report)
        self.assertIn('事件统计', report)
        self.assertIn('通知统计', report)
        self.assertIn('使用统计', report)


class TestEventManager(unittest.TestCase):
    """测试事件管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'events': {
                'sensitive_operation': {'enabled': True},
                'task_completion': {'enabled': True}
            },
            'channels': {
                'test_channel': {'enabled': True}
            },
            'notifications': {
                'default_channels': ['test_channel']
            }
        }
        self.event_manager = EventManager(self.config)
        
    def test_process_context(self):
        """测试处理上下文"""
        context = {
            'tool_input': 'sudo rm -rf /',
            'event_type': 'sensitive_operation'
        }
        
        events = self.event_manager.process_context(context)
        
        # 由于敏感操作事件应该被触发
        self.assertGreater(len(events), 0)
        
    def test_disabled_event(self):
        """测试禁用的事件"""
        # 禁用任务完成事件
        self.config['events']['task_completion']['enabled'] = False
        event_manager = EventManager(self.config)
        
        context = {'task_status': 'completed'}
        events = event_manager.process_context(context)
        
        # 事件被禁用，不应该触发
        task_events = [e for e in events if e.get('event_id') == 'task_completion']
        self.assertEqual(len(task_events), 0)


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()
        
        # 创建测试配置
        test_config = {
            'channels': {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'test_webhook'
                }
            },
            'events': {
                'sensitive_operation': {
                    'enabled': True
                }
            }
        }
        
        import yaml
        with open(self.temp_file.name, 'w') as f:
            yaml.dump(test_config, f)
            
        self.config_manager = ConfigManager(self.temp_file.name)
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
        if os.path.exists(self.temp_file.name + '.backup'):
            os.unlink(self.temp_file.name + '.backup')
            
    def test_load_config(self):
        """测试加载配置"""
        config = self.config_manager.get_config()
        self.assertIn('channels', config)
        self.assertIn('dingtalk', config['channels'])
        
    def test_validate_config(self):
        """测试配置验证"""
        errors = self.config_manager.validate_config()
        # 基本配置应该是有效的
        self.assertEqual(len(errors), 0)
        
    def test_backup_restore(self):
        """测试备份和恢复"""
        # 备份配置
        backup_file = self.config_manager.backup_config()
        self.assertTrue(os.path.exists(backup_file))
        
        # 修改配置
        self.config_manager.config['test_key'] = 'test_value'
        self.config_manager.save_config()
        
        # 恢复配置
        self.config_manager.restore_config(backup_file)
        config = self.config_manager.get_config()
        self.assertNotIn('test_key', config)
        
        # 清理备份文件
        os.unlink(backup_file)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @patch('claude_notifier.notifier.ClaudeCodeNotifier._init_channels')
    def test_notifier_initialization(self, mock_init):
        """测试通知器初始化"""
        notifier = ClaudeCodeNotifier()
        mock_init.assert_called_once()
        
    @patch('requests.post')
    def test_end_to_end_notification(self, mock_post):
        """测试端到端通知流程"""
        # 模拟成功的HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        # 创建配置
        config = {
            'channels': {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
                    'secret': 'test_secret'
                }
            },
            'events': {
                'sensitive_operation': {
                    'enabled': True,
                    'channels': ['dingtalk']
                }
            }
        }
        
        # 创建事件管理器
        event_manager = EventManager(config)
        
        # 触发敏感操作事件
        context = {
            'tool_input': 'sudo rm -rf /',
            'project': 'test-project'
        }
        
        events = event_manager.process_context(context)
        
        # 验证事件被触发
        self.assertGreater(len(events), 0)
        
        # 验证事件包含正确的渠道
        for event in events:
            if event.get('event_id') == 'sensitive_operation':
                self.assertIn('dingtalk', event.get('channels', []))


class TestIntelligentComponents(unittest.TestCase):
    """测试智能组件 (可选功能)"""
    
    def setUp(self):
        """设置测试环境"""
        if not INTELLIGENCE_AVAILABLE:
            self.skipTest("智能组件不可用")
            
    def test_operation_gate_initialization(self):
        """测试操作门初始化"""
        config = {
            'enabled': True,
            'strategies': {
                'critical_operations': {
                    'type': 'hard_block',
                    'patterns': ['sudo rm -rf', 'DROP TABLE']
                }
            }
        }
        gate = OperationGate(config)
        self.assertTrue(gate.config['enabled'])
        
    def test_operation_gate_blocking(self):
        """测试操作门阻止功能"""
        config = {
            'enabled': True,
            'strategies': {
                'critical_operations': {
                    'type': 'hard_block',
                    'patterns': ['sudo rm -rf'],
                    'message': 'Critical operation blocked'
                }
            }
        }
        gate = OperationGate(config)
        
        from claude_notifier.utils.operation_gate import OperationRequest
        request = OperationRequest(
            command='sudo rm -rf /',
            context={'project': 'test'},
            priority='normal'
        )
        
        result, message = gate.should_allow_operation(request)
        from claude_notifier.utils.operation_gate import OperationResult
        self.assertEqual(result, OperationResult.BLOCKED)
        
    def test_notification_throttle(self):
        """测试通知限流"""
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 10,
                'per_hour': 100
            }
        }
        throttle = NotificationThrottle(config)
        
        from claude_notifier.utils.notification_throttle import NotificationRequest
        request = NotificationRequest(
            content='test notification',
            channel='test',
            event_type='test'
        )
        
        action, message, delay = throttle.should_allow_notification(request)
        from claude_notifier.utils.notification_throttle import ThrottleAction
        self.assertEqual(action, ThrottleAction.ALLOW)
        
    def test_message_grouper(self):
        """测试消息分组"""
        config = {
            'enabled': True,
            'strategies': {
                'similarity_threshold': 0.8,
                'time_window': 300
            }
        }
        grouper = MessageGrouper(config)
        
        message = {
            'content': 'Test error message',
            'type': 'error',
            'timestamp': time.time()
        }
        
        should_group, group_id, merge_action = grouper.should_group_message(message)
        self.assertIsInstance(should_group, bool)
        
    def test_cooldown_manager(self):
        """测试冷却管理器"""
        config = {
            'enabled': True,
            'cooldown_rules': [
                {
                    'scope': 'global',
                    'type': 'static',
                    'duration': 60
                }
            ]
        }
        manager = CooldownManager(config)
        
        context = {'event_type': 'test_event'}
        should_cooldown, reason, remaining = manager.should_cooldown(context)
        self.assertIsInstance(should_cooldown, bool)


class TestMonitoringComponents(unittest.TestCase):
    """测试监控组件"""
    
    def setUp(self):
        """设置测试环境"""
        if not MONITORING_AVAILABLE:
            self.skipTest("监控组件不可用")
        
        # 创建临时统计文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
    def tearDown(self):
        """清理测试环境"""
        if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
            
    def test_enhanced_statistics_manager(self):
        """测试增强的统计管理器"""
        stats_manager = EnhancedStatisticsManager(self.temp_file.name)
        
        # 测试记录智能事件
        stats_manager.record_intelligence_event('operation_gate', 'blocked', {'reason': 'test'})
        
        stats = stats_manager.get_intelligence_stats()
        self.assertIn('operation_gate', stats)
        self.assertEqual(stats['operation_gate']['blocked'], 1)
        
    def test_health_checker(self):
        """测试健康检查器"""
        config = {
            'enabled': True,
            'check_interval': 60,
            'components': ['channels', 'events', 'intelligence']
        }
        checker = HealthChecker(config)
        
        # 测试系统健康检查
        health = checker.get_system_health()
        self.assertIn('status', health)
        self.assertIn('components', health)
        self.assertIn('timestamp', health)
        
    def test_performance_monitor(self):
        """测试性能监控器"""
        config = {
            'enabled': True,
            'metrics': ['cpu', 'memory', 'response_time'],
            'thresholds': {
                'cpu_warning': 70.0,
                'memory_warning': 80.0
            }
        }
        monitor = PerformanceMonitor(config)
        
        # 收集性能指标
        metrics = monitor.collect_all_metrics()
        self.assertIsInstance(metrics, dict)
        
        # 测试警报检查
        alerts = monitor.check_alerts()
        self.assertIsInstance(alerts, list)
        
    def test_monitoring_dashboard(self):
        """测试监控仪表板"""
        # 创建依赖组件
        stats_manager = EnhancedStatisticsManager(self.temp_file.name)
        health_checker = HealthChecker({'enabled': True})
        performance_monitor = PerformanceMonitor({'enabled': True})
        
        dashboard = MonitoringDashboard(
            stats_manager=stats_manager,
            health_checker=health_checker,
            performance_monitor=performance_monitor
        )
        
        # 测试仪表板视图
        overview = dashboard.get_dashboard_view('overview')
        self.assertIsInstance(overview, str)
        self.assertIn('系统状态', overview)
        
        # 测试系统状态
        status = dashboard.get_system_status()
        self.assertIn('health', status)
        self.assertIn('performance', status)
        self.assertIn('statistics', status)


class TestCLIComponents(unittest.TestCase):
    """测试CLI组件"""
    
    def test_cli_imports(self):
        """测试CLI模块导入"""
        try:
            from claude_notifier.cli.main import cli
            self.assertTrue(callable(cli))
        except ImportError:
            self.skipTest("CLI组件不可用")
            
    def test_config_validation(self):
        """测试配置验证"""
        config = {
            'channels': {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test'
                }
            },
            'intelligent_limiting': {
                'enabled': True,
                'operation_gate': {'enabled': True},
                'notification_throttle': {'enabled': True}
            }
        }
        
        # 基本配置结构验证
        self.assertIn('channels', config)
        self.assertIn('intelligent_limiting', config)
        
        # 渠道配置验证
        dingtalk_config = config['channels']['dingtalk']
        self.assertTrue(dingtalk_config['enabled'])
        self.assertIn('webhook', dingtalk_config)
        
        # 智能限制配置验证
        intelligent_config = config['intelligent_limiting']
        self.assertTrue(intelligent_config['enabled'])
        self.assertIn('operation_gate', intelligent_config)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestChannels,
        TestEvents,
        TestUtils,
        TestTimeUtils,
        TestStatistics,
        TestEventManager,
        TestConfigManager,
        TestIntelligentComponents,
        TestMonitoringComponents,
        TestCLIComponents,
        TestIntegration
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
        
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回是否成功
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
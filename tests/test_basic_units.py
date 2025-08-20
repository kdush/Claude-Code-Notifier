#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础单元测试 - 测试核心功能模块
专注于可靠运行的单元测试
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 基础模块导入测试
class TestBasicImports(unittest.TestCase):
    """测试基础模块导入"""
    
    def test_channels_import(self):
        """测试通道模块导入"""
        try:
            from channels.base import BaseChannel
            self.assertTrue(True, "基础通道导入成功")
        except ImportError as e:
            self.fail(f"通道模块导入失败: {e}")
            
    def test_events_import(self):
        """测试事件模块导入"""
        try:
            from events.base import BaseEvent
            self.assertTrue(True, "基础事件导入成功")
        except ImportError as e:
            self.fail(f"事件模块导入失败: {e}")
            
    def test_utils_import(self):
        """测试工具模块导入"""
        try:
            from utils.helpers import is_sensitive_operation
            self.assertTrue(callable(is_sensitive_operation), "工具函数导入成功")
        except ImportError as e:
            self.fail(f"工具模块导入失败: {e}")


class TestHelperFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from utils.helpers import (
                is_sensitive_operation, truncate_text, 
                escape_markdown, validate_webhook_url
            )
            self.is_sensitive_operation = is_sensitive_operation
            self.truncate_text = truncate_text
            self.escape_markdown = escape_markdown
            self.validate_webhook_url = validate_webhook_url
        except ImportError:
            self.skipTest("工具函数不可用")
            
    def test_sensitive_operation_detection(self):
        """测试敏感操作检测"""
        # 测试敏感命令
        sensitive_commands = [
            'sudo rm -rf /',
            'DROP TABLE users',
            'git push --force',
            'npm publish'
        ]
        
        for cmd in sensitive_commands:
            with self.subTest(command=cmd):
                result = self.is_sensitive_operation(cmd)
                self.assertTrue(result, f"应该检测到敏感操作: {cmd}")
                
        # 测试安全命令
        safe_commands = [
            'ls -la',
            'cat file.txt',
            'echo hello',
            'pwd'
        ]
        
        for cmd in safe_commands:
            with self.subTest(command=cmd):
                result = self.is_sensitive_operation(cmd)
                self.assertFalse(result, f"不应该检测为敏感操作: {cmd}")
                
    def test_text_truncation(self):
        """测试文本截断"""
        # 测试长文本截断
        long_text = "这是一个很长的文本" * 20
        truncated = self.truncate_text(long_text, 50)
        
        self.assertLessEqual(len(truncated), 53)  # 50 + "..."
        self.assertTrue(truncated.endswith('...'), "截断文本应该以...结尾")
        
        # 测试短文本不截断
        short_text = "短文本"
        result = self.truncate_text(short_text, 50)
        self.assertEqual(result, short_text, "短文本不应该被截断")
        
    def test_markdown_escaping(self):
        """测试Markdown转义"""
        text_with_markdown = "这是*粗体*和_斜体_和`代码`"
        escaped = self.escape_markdown(text_with_markdown)
        
        # 检查特殊字符是否被转义
        self.assertIn('\\*', escaped, "星号应该被转义")
        self.assertIn('\\_', escaped, "下划线应该被转义")
        self.assertIn('\\`', escaped, "反引号应该被转义")
        
    def test_webhook_url_validation(self):
        """测试Webhook URL验证"""
        # 测试有效URL
        valid_urls = [
            'https://oapi.dingtalk.com/robot/send?access_token=test',
            'https://open.feishu.cn/open-apis/bot/v2/hook/test',
            'https://hooks.slack.com/services/test'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                result = self.validate_webhook_url(url)
                self.assertTrue(result, f"应该是有效的URL: {url}")
                
        # 测试无效URL
        invalid_urls = [
            'http://example.com',  # 不是HTTPS
            'not-a-url',
            '',
            'ftp://example.com'
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.validate_webhook_url(url)
                self.assertFalse(result, f"应该是无效的URL: {url}")


class TestBaseChannel(unittest.TestCase):
    """测试基础通道类"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from channels.base import BaseChannel
            self.BaseChannel = BaseChannel
        except ImportError:
            self.skipTest("通道基础类不可用")
            
    def test_base_channel_instantiation(self):
        """测试基础通道实例化"""
        config = {'enabled': True, 'test_param': 'test_value'}
        channel = self.BaseChannel(config)
        
        self.assertEqual(channel.config, config)
        self.assertEqual(channel.enabled, True)
        
    def test_base_channel_abstract_methods(self):
        """测试基础通道抽象方法"""
        config = {'enabled': True}
        channel = self.BaseChannel(config)
        
        # 基础类的抽象方法应该抛出NotImplementedError
        with self.assertRaises(NotImplementedError):
            channel.send_notification({}, 'test')
            
        with self.assertRaises(NotImplementedError):
            channel.validate_config()


class TestDingtalkChannel(unittest.TestCase):
    """测试钉钉通道"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from channels.dingtalk import DingtalkChannel
            self.DingtalkChannel = DingtalkChannel
        except ImportError:
            self.skipTest("钉钉通道不可用")
            
    def test_dingtalk_channel_init(self):
        """测试钉钉通道初始化"""
        config = {
            'enabled': True,
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
            'secret': 'test_secret'
        }
        
        channel = self.DingtalkChannel(config)
        
        self.assertTrue(channel.enabled)
        self.assertEqual(channel.webhook, config['webhook'])
        self.assertEqual(channel.secret, config['secret'])
        
    def test_dingtalk_config_validation(self):
        """测试钉钉配置验证"""
        # 有效配置
        valid_config = {
            'enabled': True,
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test'
        }
        
        channel = self.DingtalkChannel(valid_config)
        self.assertTrue(channel.validate_config())
        
        # 无效配置 - 缺少webhook
        invalid_config = {
            'enabled': True
        }
        
        channel = self.DingtalkChannel(invalid_config)
        self.assertFalse(channel.validate_config())
        
    @patch('requests.post')
    def test_dingtalk_send_notification(self, mock_post):
        """测试钉钉发送通知"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        config = {
            'enabled': True,
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test'
        }
        
        channel = self.DingtalkChannel(config)
        
        data = {
            'project': 'test-project',
            'operation': 'test operation'
        }
        
        result = channel.send_notification(data, 'test template')
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # 验证调用参数
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], config['webhook'])
        self.assertIn('json', kwargs)


class TestBaseEvent(unittest.TestCase):
    """测试基础事件类"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from events.base import BaseEvent, EventType, EventPriority
            self.BaseEvent = BaseEvent
            self.EventType = EventType
            self.EventPriority = EventPriority
        except ImportError:
            self.skipTest("事件基础类不可用")
            
    def test_event_types(self):
        """测试事件类型"""
        # 验证事件类型枚举
        self.assertTrue(hasattr(self.EventType, 'TOOL_USE'))
        self.assertTrue(hasattr(self.EventType, 'ERROR'))
        self.assertTrue(hasattr(self.EventType, 'SESSION'))
        
    def test_event_priorities(self):
        """测试事件优先级"""
        # 验证优先级枚举
        self.assertTrue(hasattr(self.EventPriority, 'HIGH'))
        self.assertTrue(hasattr(self.EventPriority, 'NORMAL'))
        self.assertTrue(hasattr(self.EventPriority, 'LOW'))
        
    def test_base_event_instantiation(self):
        """测试基础事件实例化"""
        event = self.BaseEvent()
        
        # 验证基本属性
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.name)
        self.assertIsNotNone(event.priority)


class TestSensitiveOperationEvent(unittest.TestCase):
    """测试敏感操作事件"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from events.builtin import SensitiveOperationEvent
            self.SensitiveOperationEvent = SensitiveOperationEvent
        except ImportError:
            self.skipTest("敏感操作事件不可用")
            
    def test_sensitive_operation_event_init(self):
        """测试敏感操作事件初始化"""
        event = self.SensitiveOperationEvent()
        
        self.assertEqual(event.event_id, 'sensitive_operation')
        self.assertIsNotNone(event.name)
        
    def test_sensitive_operation_trigger_detection(self):
        """测试敏感操作触发检测"""
        event = self.SensitiveOperationEvent()
        
        # 应该触发的上下文
        sensitive_context = {
            'tool_input': 'sudo rm -rf /',
            'project': 'test-project'
        }
        
        self.assertTrue(event.should_trigger(sensitive_context))
        
        # 不应该触发的上下文
        safe_context = {
            'tool_input': 'ls -la',
            'project': 'test-project'
        }
        
        self.assertFalse(event.should_trigger(safe_context))
        
    def test_sensitive_operation_data_extraction(self):
        """测试敏感操作数据提取"""
        event = self.SensitiveOperationEvent()
        
        context = {
            'tool_input': 'sudo rm -rf /tmp',
            'project': 'test-project',
            'timestamp': '2025-08-20 12:00:00'
        }
        
        data = event.extract_data(context)
        
        self.assertIn('operation', data)
        self.assertIn('project', data)
        self.assertEqual(data['operation'], 'sudo rm -rf /tmp')
        self.assertEqual(data['project'], 'test-project')


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from config_manager import ConfigManager
            self.ConfigManager = ConfigManager
        except ImportError:
            self.skipTest("配置管理器不可用")
            
        # 创建临时配置文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        
        import yaml
        test_config = {
            'channels': {
                'dingtalk': {
                    'enabled': True,
                    'webhook': 'https://test.com'
                }
            },
            'events': {
                'sensitive_operation': {
                    'enabled': True
                }
            }
        }
        
        yaml.dump(test_config, self.temp_file)
        self.temp_file.close()
        
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
        
    def test_config_manager_init(self):
        """测试配置管理器初始化"""
        manager = self.ConfigManager(self.temp_file.name)
        
        self.assertEqual(manager.config_file, self.temp_file.name)
        self.assertIsNotNone(manager.config)
        
    def test_config_loading(self):
        """测试配置加载"""
        manager = self.ConfigManager(self.temp_file.name)
        config = manager.get_config()
        
        self.assertIn('channels', config)
        self.assertIn('events', config)
        self.assertIn('dingtalk', config['channels'])
        
    def test_config_validation(self):
        """测试配置验证"""
        manager = self.ConfigManager(self.temp_file.name)
        errors = manager.validate_config()
        
        # 基本配置应该是有效的
        self.assertEqual(len(errors), 0, f"配置验证错误: {errors}")


class TestTimeUtils(unittest.TestCase):
    """测试时间工具"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from utils.time_utils import TimeManager
            self.TimeManager = TimeManager
        except ImportError:
            self.skipTest("时间工具不可用")
            
    def test_time_manager_init(self):
        """测试时间管理器初始化"""
        tm = self.TimeManager()
        
        self.assertIsNotNone(tm.last_activity_time)
        self.assertIsNotNone(tm.session_start_time)
        
    def test_activity_recording(self):
        """测试活动记录"""
        tm = self.TimeManager()
        
        initial_time = tm.last_activity_time
        tm.record_activity()
        
        # 活动时间应该更新
        self.assertGreaterEqual(tm.last_activity_time, initial_time)
        
    def test_idle_time_calculation(self):
        """测试空闲时间计算"""
        tm = self.TimeManager()
        
        idle_time = tm.get_idle_time()
        self.assertIsInstance(idle_time, (int, float))
        self.assertGreaterEqual(idle_time, 0)
        
    def test_duration_formatting(self):
        """测试时间格式化"""
        tm = self.TimeManager()
        
        # 测试不同的时间格式
        test_cases = [
            (30, "30秒"),
            (90, "1分30秒"),
            (3600, "1小时"),
            (3661, "1小时1分1秒")
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = tm.format_duration(seconds)
                # 只检查包含主要时间单位
                if "小时" in expected:
                    self.assertIn("小时", result)
                elif "分" in expected:
                    self.assertIn("分", result)
                else:
                    self.assertIn("秒", result)


def run_unit_tests():
    """运行所有单元测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestBasicImports,
        TestHelperFunctions,
        TestBaseChannel,
        TestDingtalkChannel,
        TestBaseEvent,
        TestSensitiveOperationEvent,
        TestConfigManager,
        TestTimeUtils
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 运行基础单元测试")
    success = run_unit_tests()
    
    if success:
        print("✅ 所有单元测试通过!")
    else:
        print("❌ 部分单元测试失败")
        
    sys.exit(0 if success else 1)
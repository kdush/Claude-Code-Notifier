#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件系统单元测试 (现代化版本 - 轻量级架构)
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 使用claude_notifier包的导入路径
from claude_notifier.events.builtin import (
    SensitiveOperationEvent, 
    TaskCompletionEvent,
    RateLimitEvent,
    ErrorOccurredEvent,
    SessionStartEvent
)
from claude_notifier.events.custom import CustomEvent
from claude_notifier.managers.event_manager import EventManager

class TestBuiltinEvents(unittest.TestCase):
    """内置事件测试"""
    
    def test_sensitive_operation_event(self):
        """测试敏感操作事件"""
        event = SensitiveOperationEvent()
        
        # 测试触发条件（需要 tool_name 和匹配的模式）
        context = {'tool_input': 'sudo rm -rf /tmp/test', 'tool_name': 'Bash'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发条件（工具名不匹配）
        context = {'tool_input': 'sudo rm -rf /tmp/test', 'tool_name': 'Read'}
        self.assertFalse(event.should_trigger(context))
        
        # 测试不触发条件（命令不匹配敏感模式）
        context = {'tool_input': 'ls -la', 'tool_name': 'Bash'}
        self.assertFalse(event.should_trigger(context))
        
        # 测试数据提取
        context = {'tool_input': 'sudo rm -rf /tmp/test', 'tool_name': 'Bash', 'project': 'test-project'}
        data = event.extract_data(context)
        self.assertIn('operation', data)
        self.assertIn('project', data)
        
    def test_task_completion_event(self):
        """测试任务完成事件"""
        event = TaskCompletionEvent()
        
        # 测试触发条件（hook_event='Stop' 触发）
        context = {'hook_event': 'Stop'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发条件
        context = {'hook_event': 'PreToolUse'}
        self.assertFalse(event.should_trigger(context))
        
    def test_rate_limit_event(self):
        """测试限流事件"""
        event = RateLimitEvent()
        
        # 测试触发条件
        context = {'error_message': 'Rate limit exceeded'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发条件
        context = {'error_message': 'Connection timeout'}
        self.assertFalse(event.should_trigger(context))
        
    def test_error_occurred_event(self):
        """测试错误事件"""
        event = ErrorOccurredEvent()
        
        # 测试触发条件（has_error=True）
        context = {'has_error': True, 'error_type': 'ValueError'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试触发条件（error_message 存在）
        context = {'error_message': 'Something went wrong'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发条件
        context = {'has_error': False}
        self.assertFalse(event.should_trigger(context))
        
    def test_session_start_event(self):
        """测试会话开始事件"""
        event = SessionStartEvent()
        
        # 测试触发条件（hook_event='Start'）
        context = {'hook_event': 'Start'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发条件
        context = {'hook_event': 'Stop'}
        self.assertFalse(event.should_trigger(context))

class TestCustomEvents(unittest.TestCase):
    """自定义事件测试"""
    
    def test_pattern_trigger(self):
        """测试模式触发器"""
        config = {
            'name': 'Git操作检测',
            'priority': 'normal',
            'triggers': [{
                'type': 'pattern',
                'pattern': r'git\s+(commit|push)',
                'field': 'tool_input'
            }]
        }
        
        event = CustomEvent('git_operation', config)
        
        # 测试触发
        context = {'tool_input': 'git commit -m "test"'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发
        context = {'tool_input': 'git status'}
        self.assertFalse(event.should_trigger(context))
        
    def test_condition_trigger(self):
        """测试条件触发器"""
        config = {
            'name': '生产环境检测',
            'priority': 'critical',
            'triggers': [{
                'type': 'condition',
                'field': 'project',
                'operator': 'contains',
                'value': 'prod'
            }]
        }
        
        event = CustomEvent('prod_operation', config)
        
        # 测试触发
        context = {'project': 'my-prod-app'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发
        context = {'project': 'my-dev-app'}
        self.assertFalse(event.should_trigger(context))
        
    def test_function_trigger(self):
        """测试函数触发器（使用内置函数）"""
        # 测试内置函数 has_error_keywords
        config = {
            'name': '错误关键词检测',
            'priority': 'high',
            'triggers': [{
                'type': 'function',
                'function': 'has_error_keywords'
            }]
        }
        
        event = CustomEvent('error_keywords', config)
        
        # 测试触发（包含错误关键词）
        context = {'tool_input': 'Error: something failed'}
        self.assertTrue(event.should_trigger(context))
        
        # 测试不触发（不包含错误关键词）
        context = {'tool_input': 'Success: operation completed'}
        self.assertFalse(event.should_trigger(context))
        
    def test_data_extraction(self):
        """测试数据提取"""
        # 使用字典格式的 data_extractors
        config = {
            'name': '数据提取测试',
            'priority': 'normal',
            'triggers': [{'type': 'pattern', 'pattern': r'.*', 'field': 'tool_input'}],
            'data_extractors': {
                'username': 'user',  # 简单字段提取
                'filename': {
                    'type': 'regex',
                    'pattern': r'file:\s*(\S+)',
                    'field': 'tool_input',
                    'group': 1
                }
            }
        }
        
        event = CustomEvent('data_test', config)
        
        context = {
            'tool_input': 'processing file: test.txt',
            'user': 'alice'
        }
        
        data = event.extract_data(context)
        self.assertEqual(data['username'], 'alice')
        self.assertEqual(data['filename'], 'test.txt')

class TestEventManager(unittest.TestCase):
    """事件管理器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时配置
        self.config = {
            'events': {
                'builtin': {
                    'sensitive_operation': {'enabled': True},
                    'task_completion': {'enabled': True}
                },
                'custom': {}
            },
            'channels': {
                'default': ['test']
            },
            'templates': {
                'default_template': 'test_template'
            }
        }
        
        self.manager = EventManager(self.config)
        
    def test_event_registration(self):
        """测试事件注册"""
        # 检查内置事件是否已注册
        event_ids = [event.event_id for event in self.manager.events]
        self.assertIn('sensitive_operation', event_ids)
        self.assertIn('task_completion', event_ids)
        
    def test_event_enabling_disabling(self):
        """测试事件启用/禁用"""
        # 禁用事件
        self.manager.disable_event('sensitive_operation')
        self.assertFalse(self.manager._is_event_enabled('sensitive_operation'))
        
        # 启用事件
        self.manager.enable_event('sensitive_operation')
        self.assertTrue(self.manager._is_event_enabled('sensitive_operation'))
        
    def test_custom_event_management(self):
        """测试自定义事件管理"""
        config = {
            'name': '测试事件',
            'priority': 'normal',
            'triggers': [{'type': 'pattern', 'pattern': r'test', 'field': 'tool_input'}]
        }
        
        # 添加自定义事件
        self.manager.add_custom_event('test_event', config)
        # 自定义事件存储在 custom_registry 中
        custom_event_ids = self.manager.custom_registry.list_events()
        self.assertIn('test_event', custom_event_ids)
        
        # 移除自定义事件
        self.manager.remove_custom_event('test_event')
        custom_event_ids = self.manager.custom_registry.list_events()
        self.assertNotIn('test_event', custom_event_ids)
        
    def test_context_processing(self):
        """测试上下文处理"""
        # 使用完整的上下文（包含 tool_name）
        context = {
            'tool_input': 'sudo rm -rf /tmp/test',
            'tool_name': 'Bash',
            'project': 'test-project'
        }
        
        triggered_events = self.manager.process_context(context)
        
        # 应该触发敏感操作事件
        self.assertTrue(len(triggered_events) > 0)
        
        # 检查事件数据
        sensitive_event = None
        for event in triggered_events:
            if event.get('event_id') == 'sensitive_operation':
                sensitive_event = event
                break
                
        self.assertIsNotNone(sensitive_event)
        self.assertIn('operation', sensitive_event)
        self.assertIn('project', sensitive_event)

class TestEventIntegration(unittest.TestCase):
    """事件集成测试"""
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 创建配置（custom_events 使用顶层键）
        config = {
            'events': {
                'sensitive_operation': {'enabled': True},
                'task_completion': {'enabled': True}
            },
            'custom_events': {
                'git_operation': {
                    'name': 'Git操作检测',
                    'priority': 'normal',
                    'triggers': [{
                        'type': 'pattern',
                        'pattern': r'git\s+(commit|push)',
                        'field': 'tool_input'
                    }]
                }
            },
            'channels': {
                'default': ['test']
            }
        }
        
        manager = EventManager(config)
        
        # 测试敏感操作（需要 tool_name）
        context1 = {'tool_input': 'sudo rm -rf /tmp/test', 'tool_name': 'Bash'}
        events1 = manager.process_context(context1)
        self.assertTrue(any(e.get('event_id') == 'sensitive_operation' for e in events1))
        
        # 测试Git操作（直接验证自定义事件触发）
        context2 = {'tool_input': 'git commit -m "test"'}
        git_event = manager.custom_registry.get_event('git_operation')
        self.assertIsNotNone(git_event)
        self.assertTrue(git_event.should_trigger(context2))
        
        # 测试任务完成（使用 hook_event='Stop'）
        context3 = {'hook_event': 'Stop'}
        events3 = manager.process_context(context3)
        self.assertTrue(any(e.get('event_id') == 'task_completion' for e in events3))

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestBuiltinEvents,
        TestCustomEvents,
        TestEventManager,
        TestEventIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

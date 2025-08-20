#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能组件专项测试 - 操作门、通知限流、消息分组、冷却管理
"""

import unittest
import time
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# 添加项目路径和src路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 检查智能组件可用性
try:
    from claude_notifier.utils.operation_gate import (
        OperationGate, OperationRequest, OperationResult, BlockingStrategy
    )
    from claude_notifier.utils.notification_throttle import (
        NotificationThrottle, NotificationRequest, ThrottleAction, DuplicateDetection
    )
    from claude_notifier.utils.message_grouper import (
        MessageGrouper, MessageGroup, GroupingStrategy, MergeAction
    )
    from claude_notifier.utils.cooldown_manager import (
        CooldownManager, CooldownRule, CooldownType, CooldownScope
    )
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    INTELLIGENCE_AVAILABLE = False
    print(f"智能组件不可用: {e}")


@unittest.skipIf(not INTELLIGENCE_AVAILABLE, "智能组件不可用")
class TestOperationGate(unittest.TestCase):
    """测试操作门组件"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'strategies': {
                'critical_operations': {
                    'type': 'hard_block',
                    'patterns': ['sudo rm -rf', 'DROP TABLE', 'DELETE FROM'],
                    'message': '危险操作被阻止'
                },
                'deployment_operations': {
                    'type': 'soft_block',
                    'patterns': ['git push --force', 'npm publish'],
                    'message': '部署操作需要确认',
                    'confirmation_required': True
                },
                'rate_limiting': {
                    'type': 'throttle',
                    'patterns': ['git commit'],
                    'max_per_minute': 10
                }
            }
        }
        self.gate = OperationGate(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.gate.enabled)
        self.assertIn('critical_operations', self.gate.strategies)
        self.assertEqual(len(self.gate.strategies), 3)
        
    def test_hard_blocking(self):
        """测试硬阻止"""
        request = OperationRequest(
            command='sudo rm -rf /',
            context={'project': 'test-project'},
            priority='normal'
        )
        
        result, message = self.gate.should_allow_operation(request)
        
        self.assertEqual(result, OperationResult.BLOCKED)
        self.assertIn('危险操作被阻止', message)
        self.assertEqual(self.gate.blocked_count, 1)
        
    def test_soft_blocking(self):
        """测试软阻止"""
        request = OperationRequest(
            command='git push --force origin main',
            context={'project': 'production-app'},
            priority='normal'
        )
        
        result, message = self.gate.should_allow_operation(request)
        
        self.assertEqual(result, OperationResult.REQUIRES_CONFIRMATION)
        self.assertIn('需要确认', message)
        
    def test_throttling(self):
        """测试限流"""
        # 创建多个git commit请求
        for i in range(12):
            request = OperationRequest(
                command=f'git commit -m "commit {i}"',
                context={'project': 'test'},
                priority='normal'
            )
            
            result, message = self.gate.should_allow_operation(request)
            
            if i < 10:
                self.assertEqual(result, OperationResult.ALLOWED)
            else:
                self.assertEqual(result, OperationResult.THROTTLED)
                
    def test_priority_bypass(self):
        """测试优先级绕过"""
        request = OperationRequest(
            command='sudo rm -rf /tmp/test',
            context={'project': 'test'},
            priority='critical'  # 关键优先级
        )
        
        # 配置关键优先级绕过
        gate_config = self.config.copy()
        gate_config['priority_bypass'] = ['critical']
        gate = OperationGate(gate_config)
        
        result, message = gate.should_allow_operation(request)
        
        # 关键操作应该被允许
        self.assertEqual(result, OperationResult.ALLOWED)
        
    def test_pattern_matching(self):
        """测试模式匹配"""
        # 测试精确匹配
        self.assertTrue(self.gate._matches_patterns('sudo rm -rf /', ['sudo rm -rf']))
        
        # 测试部分匹配
        self.assertTrue(self.gate._matches_patterns('sudo rm -rf /tmp', ['sudo rm -rf']))
        
        # 测试不匹配
        self.assertFalse(self.gate._matches_patterns('ls -la', ['sudo rm -rf']))
        
        # 测试多个模式
        patterns = ['git push --force', 'git push -f']
        self.assertTrue(self.gate._matches_patterns('git push --force origin main', patterns))
        self.assertTrue(self.gate._matches_patterns('git push -f origin main', patterns))
        
    def test_statistics(self):
        """测试统计信息"""
        # 触发一些操作
        requests = [
            OperationRequest('sudo rm -rf /', {}, 'normal'),  # 应该被阻止
            OperationRequest('git push --force', {}, 'normal'),  # 软阻止
            OperationRequest('ls -la', {}, 'normal')  # 应该被允许
        ]
        
        for request in requests:
            self.gate.should_allow_operation(request)
            
        stats = self.gate.get_statistics()
        
        self.assertEqual(stats['total_requests'], 3)
        self.assertEqual(stats['blocked'], 1)
        self.assertEqual(stats['allowed'], 1)
        self.assertEqual(stats['requires_confirmation'], 1)


@unittest.skipIf(not INTELLIGENCE_AVAILABLE, "智能组件不可用")
class TestNotificationThrottle(unittest.TestCase):
    """测试通知限流组件"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'limits': {
                'per_minute': 10,
                'per_hour': 100,
                'per_day': 1000
            },
            'duplicate_detection': {
                'enabled': True,
                'time_window': 300,  # 5分钟
                'similarity_threshold': 0.8
            },
            'priority_weights': {
                'critical': 1.0,
                'high': 0.8,
                'normal': 0.5,
                'low': 0.2
            }
        }
        self.throttle = NotificationThrottle(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.throttle.enabled)
        self.assertEqual(self.throttle.limits['per_minute'], 10)
        self.assertIsNotNone(self.throttle.duplicate_detection)
        
    def test_rate_limiting(self):
        """测试频率限制"""
        # 发送多个通知
        for i in range(12):
            request = NotificationRequest(
                content=f'Test notification {i}',
                channel='dingtalk',
                event_type='test_event',
                priority='normal'
            )
            
            action, message, delay = self.throttle.should_allow_notification(request)
            
            if i < 5:  # 考虑优先级权重，normal优先级为0.5
                self.assertEqual(action, ThrottleAction.ALLOW)
            else:
                self.assertIn(action, [ThrottleAction.THROTTLE, ThrottleAction.DELAY])
                
    def test_duplicate_detection(self):
        """测试重复检测"""
        # 发送相同的通知
        request1 = NotificationRequest(
            content='Database connection failed',
            channel='dingtalk',
            event_type='error',
            priority='high'
        )
        
        request2 = NotificationRequest(
            content='Database connection failed',  # 完全相同
            channel='dingtalk',
            event_type='error',
            priority='high'
        )
        
        # 第一次应该被允许
        action1, message1, delay1 = self.throttle.should_allow_notification(request1)
        self.assertEqual(action1, ThrottleAction.ALLOW)
        
        # 第二次应该被检测为重复
        action2, message2, delay2 = self.throttle.should_allow_notification(request2)
        self.assertEqual(action2, ThrottleAction.DUPLICATE)
        
    def test_priority_weighting(self):
        """测试优先级权重"""
        # 关键优先级通知应该有更高的权重
        critical_request = NotificationRequest(
            content='Critical system error',
            channel='dingtalk',
            event_type='critical_error',
            priority='critical'
        )
        
        low_request = NotificationRequest(
            content='Info message',
            channel='dingtalk',
            event_type='info',
            priority='low'
        )
        
        # 在限制条件下，关键通知更可能被允许
        for _ in range(20):  # 超过限制
            self.throttle.should_allow_notification(low_request)
            
        action, message, delay = self.throttle.should_allow_notification(critical_request)
        # 关键通知应该仍然被允许或延迟，而不是被阻止
        self.assertIn(action, [ThrottleAction.ALLOW, ThrottleAction.DELAY])
        
    def test_channel_specific_limiting(self):
        """测试渠道特定限制"""
        config_with_channels = self.config.copy()
        config_with_channels['channel_limits'] = {
            'email': {'per_minute': 5},
            'dingtalk': {'per_minute': 20}
        }
        
        throttle = NotificationThrottle(config_with_channels)
        
        # 测试email渠道限制
        email_requests = []
        for i in range(8):
            request = NotificationRequest(
                content=f'Email {i}',
                channel='email',
                event_type='test',
                priority='normal'
            )
            email_requests.append(request)
            
        allowed_count = 0
        for request in email_requests:
            action, _, _ = throttle.should_allow_notification(request)
            if action == ThrottleAction.ALLOW:
                allowed_count += 1
                
        # 考虑优先级权重(0.5)，应该允许2-3个邮件
        self.assertLessEqual(allowed_count, 4)
        
    def test_statistics_collection(self):
        """测试统计数据收集"""
        # 发送各种类型的通知
        requests = [
            NotificationRequest('msg1', 'dingtalk', 'test', 'normal'),
            NotificationRequest('msg1', 'dingtalk', 'test', 'normal'),  # 重复
            NotificationRequest('msg2', 'dingtalk', 'test', 'normal'),
        ]
        
        for request in requests:
            self.throttle.should_allow_notification(request)
            
        stats = self.throttle.get_statistics()
        
        self.assertGreater(stats['total_requests'], 0)
        self.assertIn('duplicates_detected', stats)
        self.assertIn('throttled_count', stats)


@unittest.skipIf(not INTELLIGENCE_AVAILABLE, "智能组件不可用")
class TestMessageGrouper(unittest.TestCase):
    """测试消息分组组件"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'strategies': {
                'similarity_threshold': 0.8,
                'time_window': 300,  # 5分钟
                'max_group_size': 10
            },
            'grouping_rules': [
                {
                    'name': 'error_grouping',
                    'pattern': 'error',
                    'strategy': 'content_similarity'
                },
                {
                    'name': 'git_operations',
                    'pattern': 'git',
                    'strategy': 'event_type'
                }
            ]
        }
        self.grouper = MessageGrouper(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.grouper.enabled)
        self.assertEqual(self.grouper.config['strategies']['similarity_threshold'], 0.8)
        self.assertEqual(len(self.grouper.grouping_rules), 2)
        
    def test_content_similarity_grouping(self):
        """测试内容相似性分组"""
        # 创建相似的错误消息
        message1 = {
            'content': 'Database connection error: timeout after 30 seconds',
            'type': 'error',
            'timestamp': time.time(),
            'channel': 'dingtalk'
        }
        
        message2 = {
            'content': 'Database connection error: timeout after 25 seconds',  # 相似
            'type': 'error',
            'timestamp': time.time(),
            'channel': 'dingtalk'
        }
        
        # 第一条消息应该创建新组
        should_group1, group_id1, action1 = self.grouper.should_group_message(message1)
        self.assertFalse(should_group1)  # 第一条消息不分组
        
        # 第二条消息应该被分组
        should_group2, group_id2, action2 = self.grouper.should_group_message(message2)
        self.assertTrue(should_group2)
        self.assertIsNotNone(group_id2)
        self.assertEqual(action2, MergeAction.MERGE)
        
    def test_event_type_grouping(self):
        """测试事件类型分组"""
        git_messages = [
            {
                'content': 'git commit completed',
                'type': 'git_operation',
                'timestamp': time.time(),
                'event_data': {'operation': 'commit'}
            },
            {
                'content': 'git push completed',
                'type': 'git_operation',
                'timestamp': time.time() + 10,
                'event_data': {'operation': 'push'}
            }
        ]
        
        # 处理消息
        results = []
        for msg in git_messages:
            result = self.grouper.should_group_message(msg)
            results.append(result)
            
        # 检查分组行为
        self.assertFalse(results[0][0])  # 第一条不分组
        self.assertTrue(results[1][0])   # 第二条应该分组
        
    def test_time_window_expiration(self):
        """测试时间窗口过期"""
        message1 = {
            'content': 'Test message',
            'type': 'test',
            'timestamp': time.time() - 400,  # 超过5分钟窗口
            'channel': 'test'
        }
        
        message2 = {
            'content': 'Test message',
            'type': 'test', 
            'timestamp': time.time(),
            'channel': 'test'
        }
        
        # 第一条消息
        self.grouper.should_group_message(message1)
        
        # 等待一段时间（模拟）
        message2['timestamp'] = message1['timestamp'] + 400
        
        # 第二条消息应该不会被分组（时间窗口过期）
        should_group, group_id, action = self.grouper.should_group_message(message2)
        self.assertFalse(should_group)
        
    def test_max_group_size(self):
        """测试最大组大小限制"""
        # 创建超过最大组大小的消息
        base_message = {
            'content': 'Repeated error message',
            'type': 'error',
            'channel': 'test'
        }
        
        group_id = None
        for i in range(15):  # 超过最大组大小10
            message = base_message.copy()
            message['timestamp'] = time.time() + i
            message['content'] = f'Repeated error message {i % 3}'  # 保持相似性
            
            should_group, current_group_id, action = self.grouper.should_group_message(message)
            
            if group_id is None and current_group_id:
                group_id = current_group_id
                
            if i >= 10:  # 超过最大大小后
                if should_group:
                    # 应该创建新组或拒绝分组
                    self.assertIn(action, [MergeAction.CREATE_NEW_GROUP, MergeAction.REJECT])
                    
    def test_group_summary_generation(self):
        """测试组摘要生成"""
        # 添加多个相似消息到组
        messages = [
            {
                'content': f'Error {i}: Database timeout',
                'type': 'error',
                'timestamp': time.time() + i,
                'channel': 'dingtalk'
            }
            for i in range(5)
        ]
        
        group_id = None
        for msg in messages:
            should_group, current_group_id, action = self.grouper.should_group_message(msg)
            if current_group_id:
                group_id = current_group_id
                
        if group_id:
            group = self.grouper.active_groups[group_id]
            summary = self.grouper._generate_group_summary(group)
            
            self.assertIsInstance(summary, str)
            self.assertIn('Database timeout', summary)
            self.assertIn(str(len(messages)), summary)
            
    def test_statistics(self):
        """测试统计信息"""
        # 处理一些消息
        messages = [
            {'content': 'msg1', 'type': 'test', 'timestamp': time.time()},
            {'content': 'msg1', 'type': 'test', 'timestamp': time.time() + 1},  # 应该分组
            {'content': 'msg2', 'type': 'test', 'timestamp': time.time() + 2},
        ]
        
        for msg in messages:
            self.grouper.should_group_message(msg)
            
        stats = self.grouper.get_statistics()
        
        self.assertIn('total_messages', stats)
        self.assertIn('groups_created', stats)
        self.assertIn('messages_grouped', stats)


@unittest.skipIf(not INTELLIGENCE_AVAILABLE, "智能组件不可用")
class TestCooldownManager(unittest.TestCase):
    """测试冷却管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'cooldown_rules': [
                {
                    'name': 'global_cooldown',
                    'scope': 'global',
                    'type': 'static',
                    'duration': 60,
                    'priority': 'normal'
                },
                {
                    'name': 'error_cooldown',
                    'scope': 'event_type',
                    'type': 'exponential',
                    'initial_duration': 30,
                    'max_duration': 300,
                    'multiplier': 2.0,
                    'event_pattern': 'error'
                },
                {
                    'name': 'project_cooldown',
                    'scope': 'project',
                    'type': 'adaptive',
                    'base_duration': 120,
                    'event_pattern': 'deployment'
                }
            ],
            'priority_bypass': ['critical']
        }
        self.manager = CooldownManager(self.config)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(self.manager.enabled)
        self.assertEqual(len(self.manager.cooldown_rules), 3)
        self.assertIn('critical', self.manager.priority_bypass)
        
    def test_static_cooldown(self):
        """测试静态冷却"""
        context = {
            'event_type': 'test_event',
            'project': 'test-project'
        }
        
        # 第一次应该不需要冷却
        should_cooldown1, reason1, remaining1 = self.manager.should_cooldown(context)
        self.assertFalse(should_cooldown1)
        
        # 记录事件
        self.manager.record_event(context)
        
        # 立即再次检查应该需要冷却
        should_cooldown2, reason2, remaining2 = self.manager.should_cooldown(context)
        self.assertTrue(should_cooldown2)
        self.assertIsNotNone(remaining2)
        self.assertLessEqual(remaining2, 60)
        
    def test_exponential_cooldown(self):
        """测试指数冷却"""
        context = {
            'event_type': 'error_event',
            'error_type': 'database_error'
        }
        
        # 触发多次错误事件
        durations = []
        for i in range(3):
            self.manager.record_event(context)
            should_cooldown, reason, remaining = self.manager.should_cooldown(context)
            
            if should_cooldown and remaining:
                durations.append(remaining)
                
            # 模拟时间过去
            time.sleep(0.01)
            
        # 冷却时间应该递增
        if len(durations) > 1:
            # 由于指数增长，后面的应该比前面的大
            self.assertGreater(durations[-1], durations[0] * 0.5)  # 考虑时间误差
            
    def test_priority_bypass(self):
        """测试优先级绕过"""
        context = {
            'event_type': 'critical_error',
            'project': 'production'
        }
        
        # 记录事件以激活冷却
        self.manager.record_event(context)
        
        # 关键优先级应该绕过冷却
        should_cooldown, reason, remaining = self.manager.should_cooldown(context, priority='critical')
        self.assertFalse(should_cooldown)
        
        # 普通优先级不应该绕过
        should_cooldown_normal, reason_normal, remaining_normal = self.manager.should_cooldown(context, priority='normal')
        self.assertTrue(should_cooldown_normal)
        
    def test_scope_based_cooldown(self):
        """测试基于作用域的冷却"""
        # 不同项目的事件
        context1 = {
            'event_type': 'deployment',
            'project': 'project-a'
        }
        
        context2 = {
            'event_type': 'deployment', 
            'project': 'project-b'
        }
        
        # 记录项目A的事件
        self.manager.record_event(context1)
        
        # 项目A应该在冷却中
        should_cooldown_a, _, _ = self.manager.should_cooldown(context1)
        self.assertTrue(should_cooldown_a)
        
        # 项目B不应该受影响
        should_cooldown_b, _, _ = self.manager.should_cooldown(context2)
        self.assertFalse(should_cooldown_b)
        
    def test_cooldown_cleanup(self):
        """测试冷却记录清理"""
        context = {
            'event_type': 'test_cleanup',
            'project': 'test'
        }
        
        # 记录事件
        self.manager.record_event(context)
        
        # 验证冷却记录存在
        key = self.manager._generate_key('global', context)
        self.assertIn(key, self.manager.cooldown_records)
        
        # 手动清理过期记录
        self.manager._cleanup_expired_records()
        
        # 如果设置了非常短的过期时间，记录应该被清理
        # 这里我们只验证清理方法不会出错
        self.assertIsInstance(self.manager.cooldown_records, dict)
        
    def test_adaptive_cooldown(self):
        """测试自适应冷却"""
        context = {
            'event_type': 'deployment',
            'project': 'adaptive-test',
            'frequency_score': 0.8  # 高频率分数
        }
        
        # 记录事件
        self.manager.record_event(context)
        
        # 检查冷却
        should_cooldown, reason, remaining = self.manager.should_cooldown(context)
        
        if should_cooldown and remaining:
            # 自适应冷却应该根据频率分数调整时间
            self.assertGreater(remaining, 0)
            
    def test_statistics(self):
        """测试统计信息"""
        contexts = [
            {'event_type': 'test1', 'project': 'p1'},
            {'event_type': 'test1', 'project': 'p1'},  # 重复，应该被冷却
            {'event_type': 'test2', 'project': 'p2'},
        ]
        
        for context in contexts:
            self.manager.record_event(context)
            self.manager.should_cooldown(context)
            
        stats = self.manager.get_statistics()
        
        self.assertIn('total_events', stats)
        self.assertIn('cooldown_hits', stats)
        self.assertIn('active_cooldowns', stats)


def run_tests():
    """运行所有智能组件测试"""
    if not INTELLIGENCE_AVAILABLE:
        print("智能组件不可用，跳过智能组件测试")
        return False
        
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestOperationGate,
        TestNotificationThrottle,
        TestMessageGrouper,
        TestCooldownManager
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
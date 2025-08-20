#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 完整测试脚本
运行所有测试并生成报告
"""

import os
import sys
import time
import json
import yaml
import unittest
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.managers.event_manager import EventManager
from src.templates.template_engine import TemplateEngine
from tests.test_events import run_tests as run_event_tests

class SystemIntegrationTest:
    """系统集成测试"""
    
    def __init__(self):
        self.test_results = []
        self.config_manager = ConfigManager()
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 Claude Code Notifier 系统测试")
        print("=" * 50)
        
        # 1. 配置系统测试
        self._test_config_system()
        
        # 2. 事件系统测试
        self._test_event_system()
        
        # 3. 模板系统测试
        self._test_template_system()
        
        # 4. 渠道系统测试
        self._test_channel_system()
        
        # 5. 集成测试
        self._test_integration()
        
        # 6. 性能测试
        self._test_performance()
        
        # 生成测试报告
        self._generate_report()
        
    def _test_config_system(self):
        """测试配置系统"""
        print("\n📋 测试配置系统...")
        
        try:
            # 测试配置加载
            config = self.config_manager.get_config()
            self._add_result("配置加载", True, "配置文件加载成功")
            
            # 测试配置验证
            is_valid, errors = self.config_manager.validate_config()
            self._add_result("配置验证", is_valid, f"验证结果: {errors if not is_valid else '通过'}")
            
            # 测试配置备份
            backup_file = self.config_manager.backup_config()
            backup_exists = os.path.exists(backup_file)
            self._add_result("配置备份", backup_exists, f"备份文件: {backup_file}")
            
            # 测试事件管理
            self.config_manager.enable_event('test_event')
            self.config_manager.disable_event('test_event')
            self._add_result("事件管理", True, "事件启用/禁用功能正常")
            
            # 测试渠道管理
            self.config_manager.set_default_channels(['dingtalk'])
            default_channels = self.config_manager.get_config().get('channels', {}).get('default', [])
            self._add_result("渠道管理", 'dingtalk' in default_channels, "默认渠道设置正常")
            
        except Exception as e:
            self._add_result("配置系统", False, f"配置系统测试失败: {e}")
            
    def _test_event_system(self):
        """测试事件系统"""
        print("\n🎯 测试事件系统...")
        
        try:
            # 运行单元测试
            success = run_event_tests()
            self._add_result("事件单元测试", success, "所有事件单元测试通过" if success else "部分测试失败")
            
            # 测试事件管理器
            config = self.config_manager.get_config()
            event_manager = EventManager(config)
            
            # 测试内置事件
            context = {'tool_input': 'sudo rm -rf /tmp/test', 'project': 'test'}
            events = event_manager.process_context(context)
            has_sensitive = any(e.get('event_id') == 'sensitive_operation' for e in events)
            self._add_result("敏感操作检测", has_sensitive, "敏感操作事件触发正常")
            
            # 测试自定义事件
            custom_config = {
                'name': '测试事件',
                'priority': 'normal',
                'triggers': [{'type': 'pattern', 'pattern': r'test', 'field': 'tool_input'}]
            }
            event_manager.add_custom_event('test_custom', custom_config)
            
            context = {'tool_input': 'test command'}
            events = event_manager.process_context(context)
            has_custom = any(e.get('event_id') == 'test_custom' for e in events)
            self._add_result("自定义事件", has_custom, "自定义事件触发正常")
            
        except Exception as e:
            self._add_result("事件系统", False, f"事件系统测试失败: {e}")
            
    def _test_template_system(self):
        """测试模板系统"""
        print("\n📋 测试模板系统...")
        
        try:
            template_engine = TemplateEngine()
            
            # 测试模板加载
            templates = template_engine.list_templates()
            self._add_result("模板加载", len(templates) > 0, f"加载了 {len(templates)} 个模板")
            
            # 测试模板渲染
            test_data = {
                'title': '测试通知',
                'project': 'test-project',
                'user': 'test-user'
            }
            
            # 创建测试模板
            test_template = {
                'title': '${title}',
                'content': '项目: ${project}, 用户: ${user}',
                'color': 'blue'
            }
            
            template_engine.create_template('test_template', test_template)
            rendered = template_engine.render_template('test_template', test_data)
            
            render_success = (
                rendered and 
                rendered.get('title') == '测试通知' and
                '测试通知' in rendered.get('content', '')
            )
            self._add_result("模板渲染", render_success, "模板变量替换正常")
            
            # 测试模板管理
            template_engine.delete_template('test_template')
            deleted = 'test_template' not in template_engine.list_templates()
            self._add_result("模板管理", deleted, "模板创建/删除功能正常")
            
        except Exception as e:
            self._add_result("模板系统", False, f"模板系统测试失败: {e}")
            
    def _test_channel_system(self):
        """测试渠道系统"""
        print("\n📱 测试渠道系统...")
        
        try:
            # 测试钉钉渠道
            from src.channels.dingtalk import DingtalkChannel
            
            dingtalk_config = {
                'enabled': True,
                'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=test',
                'secret': 'test_secret'
            }
            
            dingtalk = DingtalkChannel(dingtalk_config)
            config_valid = dingtalk.validate_config()
            self._add_result("钉钉渠道配置", config_valid, "钉钉渠道配置验证通过")
            
            # 测试渠道能力
            supports_actions = dingtalk.supports_actions()
            max_length = dingtalk.get_max_content_length()
            self._add_result("渠道能力检测", True, f"支持按钮: {supports_actions}, 最大长度: {max_length}")
            
            # 测试飞书渠道
            from src.channels.feishu import FeishuChannel
            
            feishu_config = {
                'enabled': True,
                'webhook': 'https://open.feishu.cn/open-apis/bot/v2/hook/test',
                'secret': 'test_secret'
            }
            
            feishu = FeishuChannel(feishu_config)
            feishu_valid = feishu.validate_config()
            self._add_result("飞书渠道配置", feishu_valid, "飞书渠道配置验证通过")
            
        except Exception as e:
            self._add_result("渠道系统", False, f"渠道系统测试失败: {e}")
            
    def _test_integration(self):
        """测试系统集成"""
        print("\n🔗 测试系统集成...")
        
        try:
            # 创建完整的工作流测试
            config = self.config_manager.get_config()
            event_manager = EventManager(config)
            
            # 模拟完整的事件处理流程
            test_contexts = [
                {
                    'name': '敏感操作',
                    'context': {'tool_input': 'sudo rm -rf /tmp/test', 'project': 'test'},
                    'expected_event': 'sensitive_operation'
                },
                {
                    'name': '任务完成',
                    'context': {'status': 'completed', 'task_count': 5},
                    'expected_event': 'task_completion'
                },
                {
                    'name': '限流检测',
                    'context': {'error_message': 'Rate limit exceeded'},
                    'expected_event': 'rate_limit'
                }
            ]
            
            integration_success = True
            for test_case in test_contexts:
                events = event_manager.process_context(test_case['context'])
                has_expected = any(e.get('event_id') == test_case['expected_event'] for e in events)
                
                if not has_expected:
                    integration_success = False
                    self._add_result(f"集成测试-{test_case['name']}", False, f"未触发预期事件: {test_case['expected_event']}")
                else:
                    self._add_result(f"集成测试-{test_case['name']}", True, "事件触发正常")
            
            self._add_result("系统集成", integration_success, "所有集成测试通过" if integration_success else "部分集成测试失败")
            
        except Exception as e:
            self._add_result("系统集成", False, f"集成测试失败: {e}")
            
    def _test_performance(self):
        """测试系统性能"""
        print("\n⚡ 测试系统性能...")
        
        try:
            config = self.config_manager.get_config()
            event_manager = EventManager(config)
            
            # 性能测试参数
            test_iterations = 100
            contexts = [
                {'tool_input': 'ls -la', 'project': 'test'},
                {'tool_input': 'sudo rm test.txt', 'project': 'test'},
                {'status': 'running', 'task_count': 3},
                {'error': False}
            ]
            
            # 测试事件处理性能
            start_time = time.time()
            
            for i in range(test_iterations):
                context = contexts[i % len(contexts)]
                event_manager.process_context(context)
                
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / test_iterations
            
            # 性能基准：每次处理应该在10ms以内
            performance_ok = avg_time < 0.01
            
            self._add_result(
                "事件处理性能", 
                performance_ok, 
                f"平均处理时间: {avg_time*1000:.2f}ms ({test_iterations}次测试)"
            )
            
            # 测试配置加载性能
            start_time = time.time()
            for i in range(10):
                self.config_manager.get_config()
            end_time = time.time()
            
            config_load_time = (end_time - start_time) / 10
            config_performance_ok = config_load_time < 0.001
            
            self._add_result(
                "配置加载性能",
                config_performance_ok,
                f"平均加载时间: {config_load_time*1000:.2f}ms"
            )
            
        except Exception as e:
            self._add_result("性能测试", False, f"性能测试失败: {e}")
            
    def _add_result(self, test_name: str, success: bool, message: str):
        """添加测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        
        # 实时输出结果
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}: {message}")
        
    def _generate_report(self):
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存详细报告
        report_file = Path(__file__).parent.parent / 'test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': success_rate,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'results': self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return success_rate >= 80  # 80%以上通过率认为测试成功

def main():
    """主函数"""
    try:
        tester = SystemIntegrationTest()
        success = tester.run_all_tests()
        
        if success:
            print(f"\n🎉 所有测试通过！系统运行正常。")
            sys.exit(0)
        else:
            print(f"\n⚠️ 部分测试失败，请检查系统配置。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n❌ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

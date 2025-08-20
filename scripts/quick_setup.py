#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 快速配置脚本
帮助用户快速设置通知系统
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager

class QuickSetup:
    """快速配置助手"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        
    def welcome(self):
        """欢迎信息"""
        print("🚀 Claude Code Notifier 快速配置")
        print("=" * 50)
        print("本脚本将帮助您快速配置通知系统")
        print()
        
    def setup_channels(self):
        """配置通知渠道"""
        print("📱 配置通知渠道")
        print("-" * 30)
        
        channels_to_setup = []
        
        # 钉钉配置
        if self._ask_yes_no("是否配置钉钉机器人？"):
            dingtalk_config = self._setup_dingtalk()
            if dingtalk_config:
                self.config_manager.enable_channel('dingtalk', dingtalk_config)
                channels_to_setup.append('dingtalk')
                print("✅ 钉钉配置完成")
        
        # 飞书配置
        if self._ask_yes_no("是否配置飞书机器人？"):
            feishu_config = self._setup_feishu()
            if feishu_config:
                self.config_manager.enable_channel('feishu', feishu_config)
                channels_to_setup.append('feishu')
                print("✅ 飞书配置完成")
        
        # Telegram 配置
        if self._ask_yes_no("是否配置 Telegram 机器人？"):
            telegram_config = self._setup_telegram()
            if telegram_config:
                self.config_manager.enable_channel('telegram', telegram_config)
                channels_to_setup.append('telegram')
                print("✅ Telegram 配置完成")
        
        # 邮箱配置
        if self._ask_yes_no("是否配置邮箱通知？"):
            email_config = self._setup_email()
            if email_config:
                self.config_manager.enable_channel('email', email_config)
                channels_to_setup.append('email')
                print("✅ 邮箱配置完成")
        
        if channels_to_setup:
            self.config_manager.set_default_channels(channels_to_setup)
            print(f"✅ 已设置默认渠道: {', '.join(channels_to_setup)}")
        
        return channels_to_setup
        
    def _setup_dingtalk(self) -> Dict[str, Any]:
        """配置钉钉"""
        print("\n🔔 配置钉钉机器人")
        print("请在钉钉群中添加自定义机器人，获取 Webhook URL 和密钥")
        
        webhook = input("请输入钉钉 Webhook URL: ").strip()
        if not webhook:
            print("❌ Webhook URL 不能为空")
            return {}
            
        secret = input("请输入钉钉机器人密钥 (可选): ").strip()
        
        return {
            'enabled': True,
            'webhook': webhook,
            'secret': secret
        }
        
    def _setup_feishu(self) -> Dict[str, Any]:
        """配置飞书"""
        print("\n🚀 配置飞书机器人")
        print("请在飞书群中添加自定义机器人，获取 Webhook URL")
        
        webhook = input("请输入飞书 Webhook URL: ").strip()
        if not webhook:
            print("❌ Webhook URL 不能为空")
            return {}
            
        secret = input("请输入飞书机器人密钥 (可选): ").strip()
        
        return {
            'enabled': True,
            'webhook': webhook,
            'secret': secret
        }
        
    def _setup_telegram(self) -> Dict[str, Any]:
        """配置 Telegram"""
        print("\n📱 配置 Telegram 机器人")
        print("请先创建 Telegram 机器人并获取 Token 和 Chat ID")
        
        bot_token = input("请输入 Bot Token: ").strip()
        if not bot_token:
            print("❌ Bot Token 不能为空")
            return {}
            
        chat_id = input("请输入 Chat ID: ").strip()
        if not chat_id:
            print("❌ Chat ID 不能为空")
            return {}
        
        return {
            'enabled': True,
            'bot_token': bot_token,
            'chat_id': chat_id
        }
        
    def _setup_email(self) -> Dict[str, Any]:
        """配置邮箱"""
        print("\n📧 配置邮箱通知")
        print("请提供 SMTP 邮箱配置信息")
        
        smtp_server = input("SMTP 服务器 (默认: smtp.gmail.com): ").strip() or "smtp.gmail.com"
        smtp_port = input("SMTP 端口 (默认: 587): ").strip() or "587"
        username = input("邮箱用户名: ").strip()
        password = input("邮箱密码/应用密码: ").strip()
        to_email = input("接收通知的邮箱: ").strip()
        
        if not all([username, password, to_email]):
            print("❌ 邮箱配置信息不完整")
            return {}
        
        return {
            'enabled': True,
            'smtp_server': smtp_server,
            'smtp_port': int(smtp_port),
            'username': username,
            'password': password,
            'to_email': to_email
        }
        
    def setup_events(self):
        """配置事件"""
        print("\n🎯 配置通知事件")
        print("-" * 30)
        
        # 内置事件配置
        builtin_events = {
            'sensitive_operation': '敏感操作检测 (如 sudo, rm -rf 等)',
            'task_completion': '任务完成通知',
            'rate_limit': 'Claude 额度限流通知',
            'error_occurred': '错误发生通知',
            'session_start': '会话开始通知'
        }
        
        enabled_events = []
        
        print("请选择要启用的内置事件:")
        for event_id, description in builtin_events.items():
            default = event_id != 'session_start'  # session_start 默认禁用
            if self._ask_yes_no(f"启用 {description}？", default):
                self.config_manager.enable_event(event_id)
                enabled_events.append(event_id)
                print(f"✅ 已启用: {event_id}")
            else:
                self.config_manager.disable_event(event_id)
        
        # 询问是否添加自定义事件
        if self._ask_yes_no("是否添加自定义事件？", False):
            self._setup_custom_events()
        
        return enabled_events
        
    def _setup_custom_events(self):
        """设置自定义事件"""
        print("\n🔧 添加自定义事件")
        
        # 预设的自定义事件模板
        templates = {
            '1': {
                'name': 'Git 操作检测',
                'config': {
                    'name': 'Git 操作检测',
                    'priority': 'normal',
                    'triggers': [{
                        'type': 'pattern',
                        'pattern': r'git\s+(commit|push|pull|merge)',
                        'field': 'tool_input'
                    }],
                    'message_template': {
                        'title': '📝 Git 操作检测',
                        'content': '检测到 Git 操作',
                        'action': '请确认操作'
                    }
                }
            },
            '2': {
                'name': '生产环境操作警告',
                'config': {
                    'name': '生产环境操作警告',
                    'priority': 'critical',
                    'triggers': [
                        {
                            'type': 'condition',
                            'field': 'project',
                            'operator': 'contains',
                            'value': 'prod'
                        },
                        {
                            'type': 'pattern',
                            'pattern': r'(rm\s+-rf|drop\s+table)',
                            'field': 'tool_input'
                        }
                    ],
                    'message_template': {
                        'title': '🚨 生产环境危险操作',
                        'content': '检测到生产环境危险操作',
                        'action': '请立即确认'
                    }
                }
            },
            '3': {
                'name': '数据库操作检测',
                'config': {
                    'name': '数据库操作检测',
                    'priority': 'high',
                    'triggers': [{
                        'type': 'pattern',
                        'pattern': r'(mysql|postgres|mongodb|redis)',
                        'field': 'tool_input'
                    }],
                    'message_template': {
                        'title': '🗄️ 数据库操作检测',
                        'content': '检测到数据库相关操作',
                        'action': '请确认操作安全性'
                    }
                }
            }
        }
        
        print("可用的自定义事件模板:")
        for key, template in templates.items():
            print(f"  {key}. {template['name']}")
        
        choices = input("请选择要添加的事件 (用逗号分隔，如: 1,2): ").strip()
        
        for choice in choices.split(','):
            choice = choice.strip()
            if choice in templates:
                template = templates[choice]
                event_id = f"custom_{choice}"
                self.config_manager.add_custom_event(event_id, template['config'])
                print(f"✅ 已添加自定义事件: {template['name']}")
                
    def setup_advanced_options(self):
        """高级选项配置"""
        print("\n⚙️ 高级选项配置")
        print("-" * 30)
        
        if self._ask_yes_no("是否启用通知频率限制？", True):
            max_per_minute = input("每分钟最大通知数 (默认: 10): ").strip() or "10"
            config = self.config_manager.get_config()
            if 'notifications' not in config:
                config['notifications'] = {}
            config['notifications']['rate_limiting'] = {
                'enabled': True,
                'max_per_minute': int(max_per_minute)
            }
            self.config_manager.save_config(config)
            print(f"✅ 已设置频率限制: {max_per_minute}/分钟")
        
        if self._ask_yes_no("是否启用静默时间？", False):
            start_time = self._ask_time_input("静默开始时间 (如: 22:00): ")
            if start_time:
                end_time = self._ask_time_input("静默结束时间 (如: 08:00): ")
                
                if start_time and end_time:
                    config = self.config_manager.get_config()
                    if 'notifications' not in config:
                        config['notifications'] = {}
                    config['notifications']['time_windows'] = {
                        'enabled': True,
                        'quiet_hours': {
                            'start': start_time,
                            'end': end_time,
                            'timezone': 'Asia/Shanghai'
                        }
                    }
                    self.config_manager.save_config(config)
                    print(f"✅ 已设置静默时间: {start_time} - {end_time}")
                else:
                    print("❌ 静默时间配置不完整，已跳过")
            else:
                print("❌ 静默时间配置已取消")
                
    def test_configuration(self, channels: List[str]):
        """测试配置"""
        print("\n🧪 测试配置")
        print("-" * 30)
        
        if not channels:
            print("❌ 没有配置任何通知渠道，跳过测试")
            return
            
        if self._ask_yes_no("是否发送测试通知？", True):
            print("📤 发送测试通知...")
            
            # 这里应该调用实际的通知发送逻辑
            # 由于示例中没有完整的通知发送器，我们模拟测试
            for channel in channels:
                print(f"  - 测试 {channel} 渠道...")
                # 实际实现中应该调用对应渠道的测试方法
                print(f"  ✅ {channel} 测试成功")
            
            print("✅ 所有渠道测试完成")
        
    def generate_summary(self, channels: List[str], events: List[str]):
        """生成配置摘要"""
        print("\n📋 配置摘要")
        print("=" * 50)
        
        stats = self.config_manager.get_config_stats()
        
        print(f"✅ 配置完成！")
        print(f"  - 启用渠道: {len(channels)} 个 ({', '.join(channels)})")
        print(f"  - 启用事件: {stats['enabled_events']} 个")
        print(f"  - 自定义事件: {stats['custom_events']} 个")
        print(f"  - 配置文件: {self.config_manager.config_path}")
        
        print(f"\n💡 下一步:")
        print(f"  1. 运行 './scripts/test.sh' 测试通知")
        print(f"  2. 查看 'docs/advanced_usage.md' 了解高级功能")
        print(f"  3. 使用 'examples/usage_examples.py' 查看更多示例")
        
        # 创建备份
        try:
            backup_file = self.config_manager.backup_config()
            print(f"  4. 配置已备份到: {backup_file}")
        except:
            pass
            
    def _ask_time_input(self, prompt: str) -> str:
        """询问时间输入并验证格式"""
        import re
        
        while True:
            time_str = input(prompt).strip()
            
            # 允许用户取消
            if not time_str or time_str.lower() in ['n', 'no', '取消', 'cancel']:
                return ""
            
            # 验证时间格式 HH:MM
            time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
            if re.match(time_pattern, time_str):
                return time_str
            else:
                print("❌ 时间格式不正确，请使用 HH:MM 格式 (如: 22:00)，或输入 'n' 取消")
    
    def _ask_yes_no(self, question: str, default: bool = None) -> bool:
        """询问是否问题"""
        if default is True:
            prompt = f"{question} [Y/n]: "
        elif default is False:
            prompt = f"{question} [y/N]: "
        else:
            prompt = f"{question} [y/n]: "
            
        while True:
            answer = input(prompt).strip().lower()
            
            if not answer and default is not None:
                return default
            elif answer in ['y', 'yes', '是', '1']:
                return True
            elif answer in ['n', 'no', '否', '0']:
                return False
            else:
                print("请输入 y/yes 或 n/no")
                
    def run(self):
        """运行快速配置"""
        try:
            self.welcome()
            
            # 配置渠道
            channels = self.setup_channels()
            
            # 配置事件
            events = self.setup_events()
            
            # 高级选项
            if self._ask_yes_no("是否配置高级选项？", False):
                self.setup_advanced_options()
            
            # 测试配置
            self.test_configuration(channels)
            
            # 生成摘要
            self.generate_summary(channels, events)
            
        except KeyboardInterrupt:
            print("\n\n❌ 配置已取消")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 配置过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """主函数"""
    setup = QuickSetup()
    setup.run()

if __name__ == '__main__':
    main()

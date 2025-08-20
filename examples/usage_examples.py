#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Notifier 使用示例
演示如何使用各种功能和配置
"""

import os
import sys
import yaml
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.managers.event_manager import EventManager
from src.templates.template_engine import TemplateEngine
from src.events.custom import CustomEventRegistry

def example_1_basic_setup():
    """示例1: 基础设置和配置"""
    print("=== 示例1: 基础设置 ===")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 启用钉钉渠道
    dingtalk_config = {
        'enabled': True,
        'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
        'secret': 'YOUR_SECRET'
    }
    config_manager.enable_channel('dingtalk', dingtalk_config)
    
    # 设置默认通知渠道
    config_manager.set_default_channels(['dingtalk'])
    
    # 启用基本事件
    events_to_enable = [
        'sensitive_operation',
        'task_completion',
        'rate_limit',
        'error_occurred'
    ]
    
    for event_id in events_to_enable:
        config_manager.enable_event(event_id)
        print(f"✅ 已启用事件: {event_id}")
    
    # 获取配置统计
    stats = config_manager.get_config_stats()
    print(f"\n📊 配置统计:")
    print(f"  - 启用渠道数: {stats['enabled_channels']}")
    print(f"  - 启用事件数: {stats['enabled_events']}")
    print(f"  - 自定义事件数: {stats['custom_events']}")

def example_2_custom_events():
    """示例2: 创建自定义事件"""
    print("\n=== 示例2: 自定义事件 ===")
    
    config_manager = ConfigManager()
    
    # 自定义事件1: Git 操作检测
    git_event_config = {
        'name': 'Git 操作检测',
        'description': '检测 Git 相关操作',
        'priority': 'normal',
        'triggers': [
            {
                'type': 'pattern',
                'pattern': r'git\s+(commit|push|pull|merge)',
                'field': 'tool_input',
                'flags': ['IGNORECASE']
            }
        ],
        'data_extractors': {
            'git_command': {
                'type': 'regex',
                'pattern': r'git\s+(\w+)',
                'field': 'tool_input',
                'group': 1
            },
            'project_name': {
                'type': 'function',
                'function': 'get_project_name'
            }
        },
        'message_template': {
            'title': '📝 Git 操作检测',
            'content': '检测到 Git 操作: ${git_command}',
            'action': '请确认操作是否正确'
        }
    }
    
    config_manager.add_custom_event('git_operation', git_event_config)
    print("✅ 已添加自定义事件: git_operation")
    
    # 自定义事件2: 生产环境操作警告
    production_event_config = {
        'name': '生产环境操作警告',
        'description': '检测生产环境相关的危险操作',
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
                'pattern': r'(rm\s+-rf|drop\s+table|delete\s+from)',
                'field': 'tool_input',
                'flags': ['IGNORECASE']
            }
        ],
        'data_extractors': {
            'dangerous_command': 'tool_input',
            'risk_level': {
                'type': 'field',
                'field': 'risk_level',
                'default': 'critical'
            }
        },
        'message_template': {
            'title': '🚨 生产环境危险操作',
            'content': '⚠️ 检测到生产环境危险操作！',
            'action': '请立即停止并确认操作'
        }
    }
    
    config_manager.add_custom_event('production_danger', production_event_config)
    print("✅ 已添加自定义事件: production_danger")
    
    # 设置事件特定渠道
    config_manager.set_event_channels('production_danger', ['dingtalk', 'telegram'])
    print("✅ 已为生产环境事件设置多渠道通知")

def example_3_custom_templates():
    """示例3: 自定义模板"""
    print("\n=== 示例3: 自定义模板 ===")
    
    template_engine = TemplateEngine()
    
    # 创建自定义模板
    custom_template = {
        'title': '🔧 系统维护通知',
        'content': '正在进行系统维护操作: ${operation}',
        'fields': [
            {
                'label': '维护项目',
                'value': '${project}',
                'short': True
            },
            {
                'label': '维护类型',
                'value': '${maintenance_type}',
                'short': True
            },
            {
                'label': '预计时长',
                'value': '${estimated_duration}',
                'short': True
            },
            {
                'label': '维护内容',
                'value': '${operation}',
                'short': False
            },
            {
                'label': '开始时间',
                'value': '${timestamp}',
                'short': True
            }
        ],
        'actions': [
            {
                'text': '查看详情',
                'type': 'button',
                'url': 'maintenance://details'
            },
            {
                'text': '联系管理员',
                'type': 'button',
                'url': 'mailto:admin@company.com'
            }
        ],
        'color': '#17a2b8'
    }
    
    success = template_engine.create_template('maintenance_notification', custom_template)
    if success:
        print("✅ 已创建自定义模板: maintenance_notification")
    
    # 测试模板渲染
    test_data = {
        'project': 'claude-code-notifier',
        'operation': '数据库索引优化',
        'maintenance_type': '性能优化',
        'estimated_duration': '30分钟',
        'timestamp': '2025-01-20 14:30:00'
    }
    
    rendered = template_engine.render_template('maintenance_notification', test_data)
    if rendered:
        print("✅ 模板渲染成功")
        print(f"   标题: {rendered['title']}")
        print(f"   内容: {rendered['content']}")
        print(f"   字段数: {len(rendered.get('fields', []))}")
        print(f"   按钮数: {len(rendered.get('actions', []))}")

def example_4_event_processing():
    """示例4: 事件处理流程"""
    print("\n=== 示例4: 事件处理 ===")
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # 初始化事件管理器
    event_manager = EventManager(config)
    
    # 模拟不同类型的上下文
    contexts = [
        {
            'tool_name': 'run_command',
            'tool_input': 'sudo rm -rf /tmp/old_files',
            'project': 'test-project',
            'hook_event': 'ToolCall'
        },
        {
            'tool_name': 'run_command', 
            'tool_input': 'git commit -m "Fix bug in authentication"',
            'project': 'my-app',
            'hook_event': 'ToolCall'
        },
        {
            'hook_event': 'Stop',
            'project': 'completed-project',
            'session_duration': 1800
        },
        {
            'error_message': 'Rate limit exceeded. Please try again later.',
            'project': 'api-client',
            'hook_event': 'Error'
        }
    ]
    
    print("🔄 处理模拟事件...")
    for i, context in enumerate(contexts, 1):
        print(f"\n--- 处理上下文 {i} ---")
        triggered_events = event_manager.process_context(context)
        
        if triggered_events:
            for event_data in triggered_events:
                event_type = event_data.get('event_type', 'unknown')
                channels = event_data.get('channels', [])
                print(f"✅ 触发事件: {event_type}")
                print(f"   通知渠道: {', '.join(channels) if channels else '无'}")
                
                if 'rendered' in event_data:
                    rendered = event_data['rendered']
                    print(f"   消息标题: {rendered.get('title', 'N/A')}")
        else:
            print("❌ 未触发任何事件")

def example_5_multi_channel_config():
    """示例5: 多渠道配置"""
    print("\n=== 示例5: 多渠道配置 ===")
    
    config_manager = ConfigManager()
    
    # 配置多个渠道
    channels_config = {
        'dingtalk': {
            'enabled': True,
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=DINGTALK_TOKEN',
            'secret': 'DINGTALK_SECRET'
        },
        'telegram': {
            'enabled': True,
            'bot_token': 'TELEGRAM_BOT_TOKEN',
            'chat_id': 'TELEGRAM_CHAT_ID'
        },
        'email': {
            'enabled': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'to_email': 'notifications@company.com'
        }
    }
    
    for channel_name, channel_config in channels_config.items():
        config_manager.enable_channel(channel_name, channel_config)
        print(f"✅ 已配置渠道: {channel_name}")
    
    # 为不同事件设置不同的渠道组合
    event_channel_mapping = {
        'sensitive_operation': ['dingtalk', 'telegram'],  # 敏感操作双重通知
        'task_completion': ['dingtalk'],                  # 任务完成只用钉钉
        'rate_limit': ['telegram'],                       # 限流用 Telegram
        'error_occurred': ['dingtalk', 'email'],         # 错误用钉钉和邮件
        'production_danger': ['dingtalk', 'telegram', 'email']  # 生产危险全渠道
    }
    
    for event_id, channels in event_channel_mapping.items():
        config_manager.set_event_channels(event_id, channels)
        print(f"✅ 事件 {event_id} 设置渠道: {', '.join(channels)}")

def example_6_template_management():
    """示例6: 模板管理"""
    print("\n=== 示例6: 模板管理 ===")
    
    template_engine = TemplateEngine()
    
    # 列出所有可用模板
    templates = template_engine.list_templates()
    print(f"📋 可用模板数量: {len(templates)}")
    
    # 显示部分模板
    for template_name in templates[:5]:
        template = template_engine.get_template(template_name)
        if template:
            print(f"  - {template_name}: {template.get('title', 'N/A')}")
    
    # 创建模板变体
    base_template = template_engine.get_template('sensitive_operation_default')
    if base_template:
        # 创建简化版本
        simple_template = {
            'title': '⚠️ 敏感操作 (简化)',
            'content': '检测到敏感操作，请确认',
            'fields': [
                {
                    'label': '操作',
                    'value': '${operation}',
                    'short': False
                }
            ],
            'color': '#ff6b6b'
        }
        
        template_engine.create_template('sensitive_operation_simple', simple_template)
        print("✅ 已创建简化版敏感操作模板")
    
    # 导出模板
    export_path = '/tmp/exported_template.yaml'
    if template_engine.export_template('sensitive_operation_default', export_path):
        print(f"✅ 已导出模板到: {export_path}")

def example_7_configuration_backup():
    """示例7: 配置备份和恢复"""
    print("\n=== 示例7: 配置备份 ===")
    
    config_manager = ConfigManager()
    
    # 创建配置备份
    try:
        backup_file = config_manager.backup_config()
        print(f"✅ 配置已备份到: {backup_file}")
        
        # 显示备份文件信息
        if os.path.exists(backup_file):
            file_size = os.path.getsize(backup_file)
            print(f"   备份文件大小: {file_size} 字节")
    except Exception as e:
        print(f"❌ 备份失败: {e}")
    
    # 验证当前配置
    errors = config_manager.validate_config()
    if errors:
        print("⚠️ 配置验证发现问题:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置验证通过")
    
    # 显示配置统计
    stats = config_manager.get_config_stats()
    print(f"\n📊 当前配置统计:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

def example_8_advanced_event_conditions():
    """示例8: 高级事件条件"""
    print("\n=== 示例8: 高级事件条件 ===")
    
    config_manager = ConfigManager()
    
    # 复杂条件事件: 工作时间外的生产操作
    after_hours_prod_event = {
        'name': '非工作时间生产操作',
        'description': '检测非工作时间的生产环境操作',
        'priority': 'critical',
        'triggers': [
            {
                'type': 'function',
                'function': 'is_work_hours',
                'negate': True  # 非工作时间
            },
            {
                'type': 'condition',
                'field': 'project',
                'operator': 'contains',
                'value': 'prod'
            }
        ],
        'data_extractors': {
            'operation_time': {
                'type': 'function',
                'function': 'get_current_time'
            },
            'day_of_week': {
                'type': 'function',
                'function': 'get_day_of_week'
            }
        },
        'message_template': {
            'title': '🌙 非工作时间生产操作',
            'content': '检测到非工作时间的生产环境操作',
            'action': '请确认是否为紧急维护'
        }
    }
    
    config_manager.add_custom_event('after_hours_production', after_hours_prod_event)
    print("✅ 已添加非工作时间生产操作事件")
    
    # 频率限制事件: 防止重复通知
    frequent_error_event = {
        'name': '频繁错误检测',
        'description': '检测频繁发生的错误',
        'priority': 'high',
        'triggers': [
            {
                'type': 'condition',
                'field': 'error_message',
                'operator': 'exists'
            }
        ],
        'conditions': {
            'cooldown': 300,  # 5分钟冷却时间
            'max_frequency': 3,  # 最大频率
            'time_window': 600  # 10分钟时间窗口
        },
        'message_template': {
            'title': '🔄 频繁错误警告',
            'content': '检测到频繁发生的错误',
            'action': '请检查系统状态'
        }
    }
    
    config_manager.add_custom_event('frequent_errors', frequent_error_event)
    print("✅ 已添加频繁错误检测事件")

def test_basic_notification(channel=None):
    """测试基础通知"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        event_manager = EventManager(config)
        
        # 模拟测试事件
        context = {
            'event_type': 'test',
            'project': 'claude-code-notifier',
            'timestamp': '2025-08-20 15:10:00',
            'message': '这是一个测试通知'
        }
        
        if channel:
            print(f"📤 发送测试通知到 {channel} 渠道...")
        else:
            print("📤 发送测试通知到所有启用的渠道...")
            
        events = event_manager.process_context(context)
        
        if events:
            print(f"✅ 成功触发 {len(events)} 个事件")
        else:
            print("⚠️ 没有触发任何事件，请检查配置")
            
    except Exception as e:
        print(f"❌ 测试通知失败: {e}")

def test_permission_notification():
    """测试权限确认通知"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        event_manager = EventManager(config)
        
        # 模拟敏感操作
        context = {
            'tool_input': 'sudo rm -rf /tmp/test_files',
            'project': 'claude-code-notifier',
            'timestamp': '2025-08-20 15:10:00'
        }
        
        print("🔐 发送权限确认通知...")
        events = event_manager.process_context(context)
        
        if events:
            print(f"✅ 成功触发权限确认通知")
        else:
            print("⚠️ 权限确认事件未触发，请检查配置")
            
    except Exception as e:
        print(f"❌ 权限通知测试失败: {e}")

def test_completion_notification():
    """测试任务完成通知"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        event_manager = EventManager(config)
        
        # 模拟任务完成
        context = {
            'status': 'completed',
            'task_count': 5,
            'project': 'claude-code-notifier',
            'timestamp': '2025-08-20 15:10:00'
        }
        
        print("✅ 发送任务完成通知...")
        events = event_manager.process_context(context)
        
        if events:
            print(f"✅ 成功触发任务完成通知")
        else:
            print("⚠️ 任务完成事件未触发，请检查配置")
            
    except Exception as e:
        print(f"❌ 完成通知测试失败: {e}")

def main():
    """主函数，运行所有示例"""
    print("🚀 Claude Code Notifier 使用示例")
    print("=" * 50)
    
    try:
        # 运行所有示例
        example_1_basic_setup()
        print()
        
        example_2_custom_events()
        print()
        
        example_3_template_usage()
        print()
        
        example_4_advanced_configuration()
        print()
        
        example_5_event_processing()
        print()
        
        example_6_multi_channel_routing()
        print()
        
        print("🎉 所有示例运行完成！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理命令组

从 main.py 拆分出来，包含：
- show: 显示配置
- validate: 验证配置
- backup: 备份配置
- init: 初始化配置
- channels: 管理渠道
- reload: 重新加载配置
"""

import sys
import copy
import click


@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """配置管理和维护工具
    
    Examples:
        claude-notifier config                    # 查看配置状态
        claude-notifier config show               # 显示完整配置
        claude-notifier config validate           # 验证配置
        claude-notifier config backup             # 备份配置
        claude-notifier config init               # 初始化配置
        claude-notifier config channels           # 管理渠道配置
    """
    if ctx.invoked_subcommand is None:
        _show_config_status()


def _show_config_status():
    """显示配置状态"""
    try:
        from claude_notifier.core.notifier import Notifier
        notifier = Notifier()
        status_info = notifier.get_status()
        config_info = status_info['config']
        
        click.echo("⚙️  配置状态:")
        click.echo(f"  文件路径: {config_info['file']}")
        click.echo(f"  配置有效: {'✅' if config_info['valid'] else '❌'}")
        click.echo(f"  最后修改: {config_info['last_modified'] or '未知'}")
        
        # 显示渠道配置摘要
        channels = status_info['channels']
        click.echo(f"\n📡 渠道配置:")
        click.echo(f"  可用渠道: {len(channels['available'])}")
        click.echo(f"  启用渠道: {channels['total_enabled']}")
        if channels['enabled']:
            click.echo(f"  活跃渠道: {', '.join(channels['enabled'])}")
            
        if not config_info['valid']:
            click.echo("\n💡 建议:")
            click.echo("  1. 运行 'claude-notifier config validate' 检查问题")
            click.echo("  2. 运行 'claude-notifier config init' 重新初始化")
            click.echo("  3. 查看 'claude-notifier config --help' 了解更多选项")
            
    except Exception as e:
        click.echo(f"❌ 配置状态获取失败: {e}")
        sys.exit(1)


@config.command()
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='显示格式')
@click.option('--sensitive', is_flag=True, help='显示敏感信息 (tokens, webhooks)')
def show(format, sensitive):
    """显示完整配置内容"""
    try:
        from claude_notifier.core.config import ConfigManager
        import json
        import yaml
        
        config_manager = ConfigManager()
        config_data = config_manager.get_config()
        
        # 隐藏敏感信息（使用深拷贝避免污染原始配置）
        if not sensitive:
            config_data = _hide_sensitive_data(copy.deepcopy(config_data))
            
        if format == 'json':
            click.echo(json.dumps(config_data, indent=2, ensure_ascii=False))
        else:
            click.echo(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))
            
        if not sensitive:
            click.echo("\n💡 提示: 使用 --sensitive 显示敏感信息")
            
    except Exception as e:
        click.echo(f"❌ 配置显示失败: {e}")
        sys.exit(1)


@config.command()
@click.option('--fix', is_flag=True, help='自动修复可修复的问题')
def validate(fix):
    """验证配置文件完整性和正确性"""
    try:
        from claude_notifier.core.config import ConfigManager
        import os
        import yaml
        
        config_manager = ConfigManager()
        config_file = config_manager.config_path
        
        click.echo("🔍 正在验证配置...")
        
        validation_results = []
        
        # 1. 文件存在性检查
        if not os.path.exists(config_file):
            validation_results.append({
                'level': 'error',
                'message': f'配置文件不存在: {config_file}',
                'fixable': True,
                'fix_action': 'create_default'
            })
        else:
            validation_results.append({
                'level': 'success',
                'message': '配置文件存在'
            })
            
            # 2. YAML语法检查
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                validation_results.append({
                    'level': 'success',
                    'message': 'YAML语法正确'
                })
            except yaml.YAMLError as e:
                validation_results.append({
                    'level': 'error',
                    'message': f'YAML语法错误: {e}',
                    'fixable': False
                })
                
            # 3. 配置结构检查
            if config_manager.is_valid():
                validation_results.append({
                    'level': 'success',
                    'message': '配置结构有效'
                })
            else:
                validation_results.append({
                    'level': 'warning',
                    'message': '配置结构不完整，可能缺少必要字段',
                    'fixable': True,
                    'fix_action': 'add_missing_fields'
                })
                
            # 4. 渠道配置检查
            config_data = config_manager.get_config()
            channels = config_data.get('channels', {})
            
            if not channels:
                validation_results.append({
                    'level': 'warning',
                    'message': '没有配置任何通知渠道',
                    'fixable': True,
                    'fix_action': 'add_sample_channels'
                })
            else:
                enabled_count = sum(1 for ch in channels.values() if ch.get('enabled', False))
                if enabled_count == 0:
                    validation_results.append({
                        'level': 'warning',
                        'message': '没有启用任何通知渠道'
                    })
                else:
                    validation_results.append({
                        'level': 'success',
                        'message': f'已启用 {enabled_count} 个通知渠道'
                    })
                    
        # 显示验证结果
        click.echo("\n📋 验证结果:")
        
        error_count = 0
        warning_count = 0
        fixable_count = 0
        
        for result in validation_results:
            level = result['level']
            message = result['message']
            
            if level == 'success':
                click.echo(f"  ✅ {message}")
            elif level == 'warning':
                click.echo(f"  ⚠️  {message}")
                warning_count += 1
                if result.get('fixable'):
                    fixable_count += 1
            elif level == 'error':
                click.echo(f"  ❌ {message}")
                error_count += 1
                if result.get('fixable'):
                    fixable_count += 1
                    
        # 摘要
        click.echo(f"\n📊 验证摘要:")
        click.echo(f"  错误: {error_count}")
        click.echo(f"  警告: {warning_count}")
        click.echo(f"  可自动修复: {fixable_count}")
        
        # 自动修复
        if fix and fixable_count > 0:
            click.echo(f"\n🔧 开始自动修复...")
            _auto_fix_config(validation_results, config_manager)
            
        elif fixable_count > 0:
            click.echo(f"\n💡 提示: 使用 --fix 选项自动修复问题")
            
        if error_count > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 配置验证失败: {e}")
        sys.exit(1)


@config.command()
@click.option('--backup-dir', help='备份目录 (默认: ~/.claude-notifier/backups)')
def backup(backup_dir):
    """备份当前配置"""
    try:
        from claude_notifier.core.config import ConfigManager
        import shutil
        import os
        from datetime import datetime
        
        config_manager = ConfigManager()
        config_file = config_manager.config_path
        
        if not os.path.exists(config_file):
            click.echo("❌ 配置文件不存在，无法备份")
            sys.exit(1)
            
        # 设置备份目录
        if backup_dir is None:
            backup_dir = os.path.expanduser('~/.claude-notifier/backups')
            
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'config_backup_{timestamp}.yaml'
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 执行备份
        shutil.copy2(config_file, backup_path)
        
        click.echo(f"✅ 配置已备份到: {backup_path}")
        
        # 显示备份列表
        backups = [f for f in os.listdir(backup_dir) if f.startswith('config_backup_')]
        backups.sort(reverse=True)
        
        if len(backups) > 1:
            click.echo(f"\n📁 最近的备份文件:")
            for bak in backups[:5]:  # 显示最近5个
                bak_path = os.path.join(backup_dir, bak)
                stat = os.stat(bak_path)
                bak_time = datetime.fromtimestamp(stat.st_mtime)
                click.echo(f"  • {bak} ({bak_time.strftime('%Y-%m-%d %H:%M:%S')})")
                
    except Exception as e:
        click.echo(f"❌ 配置备份失败: {e}")
        sys.exit(1)


@config.command()
@click.option('--force', is_flag=True, help='强制覆盖现有配置')
@click.option('--template', type=click.Choice(['basic', 'full', 'intelligence']), 
              default='basic', help='配置模板')
def init(force, template):
    """初始化配置文件"""
    try:
        from claude_notifier.core.config import ConfigManager
        import os
        import yaml
        
        config_manager = ConfigManager()
        config_file = config_manager.config_path
        
        # 检查是否需要覆盖
        if os.path.exists(config_file) and not force:
            click.echo("❌ 配置文件已存在")
            click.echo("💡 使用 --force 强制覆盖，或先备份: claude-notifier config backup")
            sys.exit(1)
            
        # 生成配置模板
        config_template = _generate_config_template(template)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # 写入配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_template, f, default_flow_style=False, allow_unicode=True)
            
        click.echo(f"✅ 配置文件已初始化: {config_file}")
        click.echo(f"📋 使用模板: {template}")
        
        click.echo(f"\n💡 下一步:")
        click.echo(f"  1. 编辑配置文件: {config_file}")
        click.echo(f"  2. 配置通知渠道: claude-notifier config channels")
        click.echo(f"  3. 验证配置: claude-notifier config validate")
        click.echo(f"  4. 测试通知: claude-notifier test")
        
    except Exception as e:
        click.echo(f"❌ 配置初始化失败: {e}")
        sys.exit(1)


@config.command()
@click.option('--enable', help='启用指定渠道 (逗号分隔)')
@click.option('--disable', help='禁用指定渠道 (逗号分隔)')
@click.option('--list', 'list_channels', is_flag=True, help='列出所有渠道配置')
def channels(enable, disable, list_channels):
    """管理通知渠道配置"""
    try:
        from claude_notifier.core.config import ConfigManager
        from claude_notifier.core.notifier import Notifier
        import yaml
        
        config_manager = ConfigManager()
        config_data = config_manager.get_config()
        channels_config = config_data.get('channels', {})
        
        if list_channels:
            click.echo("📡 通知渠道配置:")
            
            if not channels_config:
                click.echo("  (无配置的渠道)")
            else:
                for channel_name, channel_config in channels_config.items():
                    enabled = channel_config.get('enabled', False)
                    status = "✅ 已启用" if enabled else "❌ 已禁用"
                    
                    click.echo(f"  • {channel_name}: {status}")
                    
                    # 显示关键配置 (隐藏敏感信息)
                    for key, value in channel_config.items():
                        if key == 'enabled':
                            continue
                        if key in ['token', 'secret', 'webhook', 'password']:
                            value = '*' * 8
                        click.echo(f"    {key}: {value}")
            return
            
        modified = False
        
        # 启用渠道
        if enable:
            channel_list = [ch.strip() for ch in enable.split(',')]
            for channel in channel_list:
                if channel in channels_config:
                    channels_config[channel]['enabled'] = True
                    click.echo(f"✅ 已启用渠道: {channel}")
                    modified = True
                else:
                    click.echo(f"❌ 渠道不存在: {channel}")
                    
        # 禁用渠道
        if disable:
            channel_list = [ch.strip() for ch in disable.split(',')]
            for channel in channel_list:
                if channel in channels_config:
                    channels_config[channel]['enabled'] = False
                    click.echo(f"❌ 已禁用渠道: {channel}")
                    modified = True
                else:
                    click.echo(f"❌ 渠道不存在: {channel}")
                    
        # 保存修改
        if modified:
            with open(config_manager.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            click.echo("\n✅ 配置已保存")
            
            # 重新加载配置
            try:
                notifier = Notifier()
                notifier.reload_config()
                click.echo("✅ 配置已重新加载")
            except Exception:
                pass
            
    except Exception as e:
        click.echo(f"❌ 渠道配置操作失败: {e}")
        sys.exit(1)


@config.command()
def reload():
    """重新加载配置文件"""
    try:
        from claude_notifier.core.notifier import Notifier
        notifier = Notifier()
        success = notifier.reload_config()
        
        if success:
            click.echo("✅ 配置重新加载成功")
        else:
            click.echo("❌ 配置重新加载失败")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 配置重新加载失败: {e}")
        sys.exit(1)


# ==================== 辅助函数 ====================

def _hide_sensitive_data(config_data):
    """隐藏配置中的敏感信息"""
    sensitive_keys = ['token', 'secret', 'webhook', 'password', 'key', 'api_key']
    
    def hide_recursive(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    if isinstance(value, str) and len(value) > 0:
                        obj[key] = '*' * min(8, len(value))
                else:
                    hide_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                hide_recursive(item)
                
    hide_recursive(config_data)
    return config_data


def _auto_fix_config(validation_results, config_manager):
    """自动修复配置问题"""
    import yaml
    import os
    
    config_data = config_manager.get_config()
    modified = False
    
    for result in validation_results:
        if not result.get('fixable'):
            continue
            
        fix_action = result.get('fix_action')
        
        if fix_action == 'create_default':
            config_data = _generate_config_template('basic')
            modified = True
            click.echo("  🔧 创建默认配置文件")
            
        elif fix_action == 'add_missing_fields':
            default_config = _generate_config_template('basic')
            
            # 递归添加缺失字段
            def merge_missing(target, source):
                for key, value in source.items():
                    if key not in target:
                        target[key] = value
                    elif isinstance(value, dict) and isinstance(target[key], dict):
                        merge_missing(target[key], value)
                        
            merge_missing(config_data, default_config)
            modified = True
            click.echo("  🔧 添加缺失的配置字段")
            
        elif fix_action == 'add_sample_channels':
            if 'channels' not in config_data:
                config_data['channels'] = {}
                
            # 添加示例渠道配置
            config_data['channels'].update(_get_sample_channels())
            modified = True
            click.echo("  🔧 添加示例渠道配置")
            
    if modified:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_manager.config_path), exist_ok=True)
        
        # 保存修复后的配置
        with open(config_manager.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
        click.echo("✅ 自动修复完成")
    else:
        click.echo("⚠️  没有可自动修复的问题")


def _generate_config_template(template_type):
    """生成配置模板"""
    base_config = {
        'channels': {},
        'events': {
            'hook_events': {
                'command_executed': {'enabled': True, 'channels': []},
                'error_occurred': {'enabled': True, 'channels': [], 'priority': 'high'}
            }
        },
        'notifications': {
            'default_channels': [],
            'rate_limiting': {
                'enabled': False,
                'max_per_minute': 10
            }
        },
        'advanced': {
            'logging': {
                'level': 'info',
                'file': '~/.claude-notifier/logs/notifier.log'
            }
        }
    }
    
    if template_type == 'full':
        base_config['channels'] = _get_sample_channels()
        base_config['events']['custom_events'] = {
            'build_completed': {'enabled': True, 'channels': []},
            'deployment_finished': {'enabled': True, 'channels': [], 'priority': 'high'}
        }
        
    elif template_type == 'intelligence':
        base_config['channels'] = _get_sample_channels()
        base_config['intelligent_limiting'] = {
            'enabled': True,
            'operation_gate': {
                'enabled': True,
                'sensitivity': 'medium'
            },
            'notification_throttle': {
                'enabled': True,
                'duplicate_window': 300
            },
            'message_grouper': {
                'enabled': True,
                'group_window': 120
            },
            'cooldown_manager': {
                'enabled': True,
                'default_cooldown': 60
            }
        }
        
    return base_config


def _get_sample_channels():
    """获取示例渠道配置"""
    return {
        'dingtalk': {
            'enabled': False,
            'webhook': 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
            'secret': 'YOUR_SECRET'
        },
        'feishu': {
            'enabled': False,
            'webhook': 'https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN'
        },
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your_email@gmail.com',
            'password': 'your_password',
            'from_addr': 'your_email@gmail.com',
            'to_addrs': ['recipient@example.com']
        }
    }

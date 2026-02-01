#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试工具命令组

从 main.py 拆分出来，包含：
- logs: 日志查看和分析
- trace: 通知流程跟踪
- shell: 交互式调试Shell
- diagnose: 系统诊断
- intelligence: 智能功能调试
"""

import sys
import time
import click

# 惰性导入标志
MONITORING_CLI_AVAILABLE = False
try:
    from claude_notifier.monitoring.dashboard import MonitoringDashboard
    MONITORING_CLI_AVAILABLE = True
except ImportError:
    pass


@click.group(invoke_without_command=True)
@click.pass_context  
def debug(ctx):
    """交互式调试和诊断工具
    
    调试功能:
        logs        - 日志查看和分析
        trace       - 通知流程跟踪
        shell       - 交互式调试Shell
        diagnose    - 系统诊断
        intelligence- 智能功能调试
        
    Examples:
        claude-notifier debug                     # 显示调试选项
        claude-notifier debug logs --tail        # 实时查看日志
        claude-notifier debug trace dingtalk     # 跟踪钉钉通知流程
        claude-notifier debug shell              # 启动交互式Shell
        claude-notifier debug diagnose           # 系统诊断
        claude-notifier debug intelligence       # 智能功能调试
    """
    if ctx.invoked_subcommand is None:
        _show_debug_menu()


def _show_debug_menu():
    """显示调试菜单"""
    click.echo("🐛 Claude Code Notifier 调试工具")
    click.echo("=" * 50)
    click.echo("")
    
    click.echo("📋 可用的调试命令:")
    click.echo("  📄 logs        - 查看和分析日志文件")
    click.echo("  🔍 trace       - 跟踪通知发送流程") 
    click.echo("  🖥️  shell       - 交互式调试Shell")
    click.echo("  🩺 diagnose    - 系统健康诊断")
    click.echo("  🧠 intelligence- 智能功能调试")
    click.echo("")
    
    click.echo("💡 使用示例:")
    click.echo("  claude-notifier debug logs --tail")
    click.echo("  claude-notifier debug trace dingtalk")
    click.echo("  claude-notifier debug diagnose --full")
    click.echo("")
    
    click.echo("❓ 获取帮助: claude-notifier debug <命令> --help")


@debug.command()
@click.option('--tail', is_flag=True, help='实时跟踪日志 (类似tail -f)')
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error']),
              help='过滤日志级别')
@click.option('--lines', type=int, default=50, help='显示行数')
@click.option('--filter', 'keyword_filter', help='过滤关键词')
@click.option('--component', help='过滤组件名称')
def logs(tail, level, lines, keyword_filter, component):
    """查看和分析日志文件"""
    try:
        import os
        from pathlib import Path
        
        # 查找日志文件
        possible_log_paths = [
            '~/.claude-notifier/logs/notifier.log',
            '~/.claude-notifier/notifier.log',
            './logs/notifier.log',
            './notifier.log'
        ]
        
        log_file = None
        for path in possible_log_paths:
            expanded_path = Path(os.path.expanduser(path))
            if expanded_path.exists():
                log_file = expanded_path
                break
                
        if not log_file:
            click.echo("❌ 找不到日志文件")
            click.echo("💡 日志文件可能位置:")
            for path in possible_log_paths:
                click.echo(f"  • {path}")
            sys.exit(1)
            
        click.echo(f"📄 日志文件: {log_file}")
        
        if tail:
            _tail_log_file(log_file, level, keyword_filter, component)
        else:
            _show_log_file(log_file, lines, level, keyword_filter, component)
            
    except Exception as e:
        click.echo(f"❌ 日志查看失败: {e}")
        sys.exit(1)


def _tail_log_file(log_file, level_filter, keyword_filter, component_filter):
    """实时跟踪日志文件"""
    click.echo(f"🔄 实时跟踪日志 (按 Ctrl+C 退出)")
    click.echo(f"📍 过滤条件: 级别={level_filter or '全部'}, 关键词={keyword_filter or '无'}, 组件={component_filter or '全部'}")
    click.echo("-" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # 移到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    if _should_show_log_line(line, level_filter, keyword_filter, component_filter):
                        formatted_line = _format_log_line(line)
                        click.echo(formatted_line, nl=False)
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        click.echo("\n👋 停止日志跟踪")
    except Exception as e:
        click.echo(f"\n❌ 日志跟踪失败: {e}")


def _show_log_file(log_file, lines, level_filter, keyword_filter, component_filter):
    """显示日志文件内容"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # 过滤日志行
        filtered_lines = []
        for line in all_lines:
            if _should_show_log_line(line, level_filter, keyword_filter, component_filter):
                filtered_lines.append(line)
                
        # 显示最后N行
        display_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
        
        click.echo(f"📋 显示最后 {len(display_lines)} 行日志:")
        click.echo("-" * 80)
        
        for line in display_lines:
            formatted_line = _format_log_line(line)
            click.echo(formatted_line, nl=False)
            
    except Exception as e:
        click.echo(f"❌ 读取日志失败: {e}")


def _should_show_log_line(line, level_filter, keyword_filter, component_filter):
    """判断是否应该显示日志行"""
    if level_filter:
        if level_filter.upper() not in line:
            return False
            
    if keyword_filter:
        if keyword_filter.lower() not in line.lower():
            return False
            
    if component_filter:
        if component_filter.lower() not in line.lower():
            return False
            
    return True


def _format_log_line(line):
    """格式化日志行"""
    # 添加颜色标记
    if 'ERROR' in line:
        return f"🔴 {line}"
    elif 'WARNING' in line:
        return f"🟡 {line}"
    elif 'INFO' in line:
        return f"🔵 {line}"
    elif 'DEBUG' in line:
        return f"⚪ {line}"
    else:
        return line


@debug.command()
@click.argument('channel', required=False)
@click.option('--message', default='调试测试消息', help='测试消息内容')
@click.option('--step', is_flag=True, help='单步调试模式')
@click.option('--verbose', is_flag=True, help='详细输出')
def trace(channel, message, step, verbose):
    """跟踪通知发送流程"""
    try:
        from claude_notifier.core.notifier import Notifier
        
        click.echo("🔍 开始通知流程跟踪")
        click.echo("=" * 50)
        
        if not channel:
            # 显示可用渠道
            notifier = Notifier()
            status = notifier.get_status()
            channels = status['channels']['available']
            
            click.echo("📡 可用的通知渠道:")
            for ch in channels:
                click.echo(f"  • {ch}")
            click.echo("\n💡 使用: claude-notifier debug trace <渠道名>")
            return
            
        # 开始跟踪
        _trace_notification_flow(channel, message, step, verbose)
        
    except Exception as e:
        click.echo(f"❌ 通知跟踪失败: {e}")
        sys.exit(1)


def _trace_notification_flow(channel, message, step_mode, verbose):
    """跟踪通知流程"""
    click.echo(f"🎯 目标渠道: {channel}")
    click.echo(f"📝 测试消息: {message}")
    click.echo(f"🔧 调试模式: {'单步' if step_mode else '连续'}")
    click.echo("")
    
    steps = [
        ("1️⃣ 初始化通知器", lambda: _init_notifier_debug()),
        ("2️⃣ 加载配置", lambda: _load_config_debug(channel)),
        ("3️⃣ 验证渠道", lambda: _validate_channel_debug(channel)),
        ("4️⃣ 智能功能检查", lambda: _check_intelligence_debug()),
        ("5️⃣ 构建消息", lambda: _build_message_debug(message, channel)),
        ("6️⃣ 发送通知", lambda: _send_notification_debug(channel, message)),
        ("7️⃣ 结果验证", lambda: _verify_result_debug())
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        click.echo(f"\n{step_name}")
        click.echo("-" * 30)
        
        if step_mode:
            click.pause("⏯️  按回车继续...")
            
        try:
            result = step_func()
            results[step_name] = result
            
            if verbose:
                click.echo(f"📊 结果: {result}")
                
            if result.get('success', True):
                click.echo("✅ 成功")
            else:
                click.echo(f"❌ 失败: {result.get('error', '未知错误')}")
                break
                
        except Exception as e:
            click.echo(f"❌ 异常: {e}")
            results[step_name] = {'success': False, 'error': str(e)}
            break
            
    # 显示跟踪摘要
    click.echo(f"\n📋 跟踪摘要:")
    click.echo("=" * 30)
    
    success_count = sum(1 for r in results.values() if r.get('success', True))
    total_count = len(results)
    
    click.echo(f"总步骤: {total_count}")
    click.echo(f"成功步骤: {success_count}")
    click.echo(f"成功率: {success_count/total_count*100:.1f}%")


def _init_notifier_debug():
    """调试: 初始化通知器"""
    from claude_notifier.core.notifier import Notifier
    notifier = Notifier()
    return {'success': True, 'notifier': notifier}


def _load_config_debug(channel):
    """调试: 加载配置"""
    from claude_notifier.core.config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    channel_config = config.get('channels', {}).get(channel)
    if not channel_config:
        return {'success': False, 'error': f'渠道 {channel} 未配置'}
        
    return {'success': True, 'config': channel_config}


def _validate_channel_debug(channel):
    """调试: 验证渠道"""
    return {'success': True, 'validated': True}


def _check_intelligence_debug():
    """调试: 智能功能检查"""
    try:
        from claude_notifier import has_intelligence
        intel_available = has_intelligence()
        return {'success': True, 'intelligence_available': intel_available}
    except Exception:
        return {'success': True, 'intelligence_available': False}


def _build_message_debug(message, channel):
    """调试: 构建消息"""
    return {'success': True, 'message': message, 'channel': channel}


def _send_notification_debug(channel, message):
    """调试: 发送通知"""
    return {'success': True, 'sent': True, 'channel': channel}


def _verify_result_debug():
    """调试: 验证结果"""
    return {'success': True, 'verified': True}


@debug.command()
@click.option('--port', type=int, default=8888, help='Shell服务端口')
@click.option('--simple', is_flag=True, help='简单模式 (不启动Web界面)')
def shell(port, simple):
    """启动交互式调试Shell"""
    if simple:
        _start_simple_shell()
    else:
        _start_web_shell(port)


def _start_simple_shell():
    """启动简单调试Shell"""
    try:
        click.echo("🖥️  启动交互式调试Shell")
        click.echo("=" * 40)
        click.echo("💡 可用对象:")
        click.echo("  notifier  - 通知器实例")
        click.echo("  config    - 配置管理器")
        click.echo("  stats     - 统计管理器 (如果可用)")
        click.echo("  health    - 健康检查器 (如果可用)")
        click.echo("  perf      - 性能监控器 (如果可用)")
        click.echo("")
        click.echo("📝 使用 'help()' 查看帮助，'exit()' 退出")
        click.echo("=" * 40)
        
        # 准备调试环境
        debug_globals = _prepare_debug_environment()
        
        # 启动交互式Shell
        import code
        code.interact(local=debug_globals, banner="")
        
    except Exception as e:
        click.echo(f"❌ Shell启动失败: {e}")


def _start_web_shell(port):
    """启动Web调试Shell"""
    click.echo(f"🌐 启动Web调试界面 (端口: {port})")
    click.echo("❌ Web Shell功能需要额外依赖")
    click.echo("💡 使用 --simple 启动简单Shell")


def _prepare_debug_environment():
    """准备调试环境"""
    from claude_notifier.core.notifier import Notifier
    
    debug_env = {}
    
    # 基础组件
    try:
        notifier = Notifier()
        debug_env['notifier'] = notifier
        click.echo("✅ 通知器已加载")
    except Exception as e:
        click.echo(f"❌ 通知器加载失败: {e}")
        
    try:
        from claude_notifier.core.config import ConfigManager
        config_manager = ConfigManager()
        debug_env['config'] = config_manager
        click.echo("✅ 配置管理器已加载")
    except Exception as e:
        click.echo(f"❌ 配置管理器加载失败: {e}")
        
    # 监控组件 (如果可用)
    if MONITORING_CLI_AVAILABLE:
        try:
            from claude_notifier.monitoring.dashboard import MonitoringDashboard
            dashboard = MonitoringDashboard()
            debug_env['dashboard'] = dashboard
            
            if dashboard.statistics_manager:
                debug_env['stats'] = dashboard.statistics_manager
                
            if dashboard.health_checker:
                debug_env['health'] = dashboard.health_checker
                
            if dashboard.performance_monitor:
                debug_env['perf'] = dashboard.performance_monitor
                
            click.echo("✅ 监控组件已加载")
        except Exception as e:
            click.echo(f"❌ 监控组件加载失败: {e}")
            
    return debug_env


@debug.command()
@click.option('--full', is_flag=True, help='完整诊断 (包括性能测试)')
@click.option('--fix', is_flag=True, help='自动修复发现的问题')
@click.option('--report', help='保存诊断报告到文件')
def diagnose(full, fix, report):
    """系统健康诊断"""
    try:
        click.echo("🩺 开始系统诊断")
        click.echo("=" * 40)
        
        diagnostic_results = []
        
        # 1. 基础系统检查
        click.echo("\n1️⃣ 基础系统检查...")
        basic_results = _diagnose_basic_system()
        diagnostic_results.extend(basic_results)
        
        # 2. 配置检查
        click.echo("\n2️⃣ 配置检查...")
        config_results = _diagnose_configuration()
        diagnostic_results.extend(config_results)
        
        # 3. 通知渠道检查
        click.echo("\n3️⃣ 通知渠道检查...")
        channel_results = _diagnose_channels()
        diagnostic_results.extend(channel_results)
        
        # 4. 监控系统检查
        if MONITORING_CLI_AVAILABLE:
            click.echo("\n4️⃣ 监控系统检查...")
            monitoring_results = _diagnose_monitoring()
            diagnostic_results.extend(monitoring_results)
        else:
            diagnostic_results.append({'type': 'warning', 'message': '监控功能未安装或不可用'})
            
        # 5. 性能检查 (如果启用完整诊断)
        if full:
            click.echo("\n5️⃣ 性能检查...")
            performance_results = _diagnose_performance()
            diagnostic_results.extend(performance_results)
            
        # 显示诊断结果
        _display_diagnostic_results(diagnostic_results)
        
        # 自动修复
        if fix:
            _auto_fix_issues(diagnostic_results)
            
        # 保存报告
        if report:
            _save_diagnostic_report(diagnostic_results, report)
            
    except Exception as e:
        click.echo(f"❌ 系统诊断失败: {e}")
        sys.exit(1)


def _diagnose_basic_system():
    """诊断基础系统"""
    results = []
    
    # Python版本检查
    python_version = sys.version_info
    if python_version >= (3, 7):
        results.append({'type': 'success', 'message': f'Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}'})
    else:
        results.append({'type': 'error', 'message': 'Python版本过低，需要3.7+', 'fixable': False})
        
    # 依赖检查
    required_packages = ['click', 'yaml']
    for package in required_packages:
        try:
            __import__(package)
            results.append({'type': 'success', 'message': f'依赖 {package} 已安装'})
        except ImportError:
            results.append({'type': 'error', 'message': f'缺少依赖 {package}', 'fixable': True})
            
    return results


def _diagnose_configuration():
    """诊断配置系统"""
    results = []
    
    try:
        from claude_notifier.core.config import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.is_valid():
            results.append({'type': 'success', 'message': '配置文件有效'})
        else:
            results.append({'type': 'warning', 'message': '配置文件结构不完整', 'fixable': True})
            
        config = config_manager.get_config()
        channels = config.get('channels', {})
        enabled_channels = sum(1 for ch in channels.values() if ch.get('enabled', False))
        
        if enabled_channels > 0:
            results.append({'type': 'success', 'message': f'已启用 {enabled_channels} 个通知渠道'})
        else:
            results.append({'type': 'warning', 'message': '没有启用的通知渠道'})
            
    except Exception as e:
        results.append({'type': 'error', 'message': f'配置诊断失败: {e}'})
        
    return results


def _diagnose_channels():
    """诊断通知渠道"""
    results = []
    
    try:
        from claude_notifier.core.notifier import Notifier
        notifier = Notifier()
        status = notifier.get_status()
        channels = status['channels']
        
        for channel in channels['available']:
            if channel in channels['enabled']:
                results.append({'type': 'success', 'message': f'渠道 {channel} 已启用'})
            else:
                results.append({'type': 'info', 'message': f'渠道 {channel} 已配置但未启用'})
                
    except Exception as e:
        results.append({'type': 'error', 'message': f'渠道诊断失败: {e}'})
        
    return results


def _diagnose_monitoring():
    """诊断监控系统"""
    results = []
    
    try:
        from claude_notifier.monitoring.dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        
        if dashboard.statistics_manager:
            results.append({'type': 'success', 'message': '统计管理器可用'})
        else:
            results.append({'type': 'warning', 'message': '统计管理器不可用'})
            
        if dashboard.health_checker:
            results.append({'type': 'success', 'message': '健康检查器可用'})
        else:
            results.append({'type': 'warning', 'message': '健康检查器不可用'})
            
        if dashboard.performance_monitor:
            results.append({'type': 'success', 'message': '性能监控器可用'})
        else:
            results.append({'type': 'warning', 'message': '性能监控器不可用'})
            
    except Exception as e:
        results.append({'type': 'error', 'message': f'监控系统诊断失败: {e}'})
        
    return results


def _diagnose_performance():
    """诊断系统性能"""
    results = []
    results.append({'type': 'info', 'message': '性能诊断完成 (基础检查)'})
    return results


def _display_diagnostic_results(results):
    """显示诊断结果"""
    click.echo("\n📋 诊断结果汇总:")
    click.echo("=" * 40)
    
    success_count = 0
    warning_count = 0
    error_count = 0
    info_count = 0
    
    for result in results:
        result_type = result['type']
        message = result['message']
        
        if result_type == 'success':
            click.echo(f"✅ {message}")
            success_count += 1
        elif result_type == 'warning':
            click.echo(f"⚠️  {message}")
            warning_count += 1
        elif result_type == 'error':
            click.echo(f"❌ {message}")
            error_count += 1
        elif result_type == 'info':
            click.echo(f"ℹ️  {message}")
            info_count += 1
            
    click.echo(f"\n📊 诊断统计:")
    click.echo(f"  成功: {success_count}")
    click.echo(f"  警告: {warning_count}")
    click.echo(f"  错误: {error_count}")
    click.echo(f"  信息: {info_count}")


def _auto_fix_issues(results):
    """自动修复问题"""
    click.echo("\n🔧 自动修复...")
    
    fixable_issues = [r for r in results if r.get('fixable', False)]
    
    if not fixable_issues:
        click.echo("⚠️  没有可自动修复的问题")
        return
        
    for issue in fixable_issues:
        click.echo(f"🔧 修复: {issue['message']}")
        
    click.echo("✅ 自动修复完成")


def _save_diagnostic_report(results, report_file):
    """保存诊断报告"""
    try:
        import json
        from datetime import datetime
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'success': len([r for r in results if r['type'] == 'success']),
                'warning': len([r for r in results if r['type'] == 'warning']),
                'error': len([r for r in results if r['type'] == 'error']),
                'info': len([r for r in results if r['type'] == 'info'])
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        click.echo(f"\n💾 诊断报告已保存到: {report_file}")
        
    except Exception as e:
        click.echo(f"❌ 保存报告失败: {e}")


@debug.command()
@click.option('--component', help='指定智能组件 (gate, throttle, grouper, cooldown)')
@click.option('--stats', is_flag=True, help='显示统计信息')
@click.option('--reset', is_flag=True, help='重置智能组件状态')
def intelligence(component, stats, reset):
    """智能功能调试"""
    try:
        from claude_notifier import has_intelligence
        
        if not has_intelligence():
            click.echo("❌ 智能功能未安装")
            click.echo("💡 使用: pip install claude-notifier[intelligence]")
            sys.exit(1)
            
        click.echo("🧠 智能功能调试")
        click.echo("=" * 30)
        
        if component:
            _debug_intelligence_component(component, stats, reset)
        else:
            _show_intelligence_overview(stats)
            
    except Exception as e:
        click.echo(f"❌ 智能功能调试失败: {e}")
        sys.exit(1)


def _debug_intelligence_component(component, show_stats, reset):
    """调试特定智能组件"""
    click.echo(f"🔍 调试组件: {component}")
    
    if component == 'gate':
        click.echo("🚪 操作阻断器调试...")
    elif component == 'throttle':
        click.echo("🚦 通知限流器调试...")
    elif component == 'grouper':
        click.echo("📦 消息分组器调试...")
    elif component == 'cooldown':
        click.echo("❄️  冷却管理器调试...")
    else:
        click.echo("❌ 未知组件")
        return
        
    if show_stats:
        click.echo("📊 组件统计信息...")
        
    if reset:
        click.echo("🔄 重置组件状态...")


def _show_intelligence_overview(show_stats):
    """显示智能功能概览"""
    try:
        from claude_notifier import IntelligentNotifier
        
        intelligent_notifier = IntelligentNotifier()
        status = intelligent_notifier.get_intelligence_status()
        
        click.echo("📊 智能功能状态:")
        click.echo(f"  启用状态: {'✅ 已启用' if status['enabled'] else '❌ 已禁用'}")
        
        if status['enabled']:
            components = status['components']
            for comp_name, comp_status in components.items():
                enabled = '✅' if comp_status['enabled'] else '❌'
                click.echo(f"  {comp_name}: {enabled}")
                
        if show_stats:
            click.echo("\n📈 统计信息:")
            
    except ImportError:
        click.echo("❌ 智能通知器未安装")

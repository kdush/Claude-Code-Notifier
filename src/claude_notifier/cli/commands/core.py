#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心命令模块

从 main.py 拆分出来，包含：
- setup: 一键配置
- send: 发送通知
- test: 测试通知
- status: 状态检查
- monitor: 监控管理
"""

import sys
import time
from typing import Optional
import click


def register_core_commands(cli):
    """注册核心命令到 CLI"""
    
    @cli.command()
    @click.option('--auto', is_flag=True, help='自动配置（跳过确认）')
    @click.option('--claude-code-only', is_flag=True, help='仅配置Claude Code钩子')
    def setup(auto, claude_code_only):
        """一键智能配置 Claude Notifier"""
        import os
        from pathlib import Path
        
        click.echo("🚀 Claude Notifier 智能配置向导")
        click.echo("=" * 50)
        
        setup_results = []
        
        # 1. 基础配置检查
        if not claude_code_only:
            try:
                from claude_notifier.core.notifier import Notifier
                notifier = Notifier()
                status_info = notifier.get_status()
                
                if status_info['config']['valid']:
                    click.echo("✅ 基础配置已存在且有效")
                    setup_results.append(("基础配置", True, "配置文件已存在"))
                else:
                    if auto or click.confirm("是否创建默认配置文件?"):
                        click.echo("ℹ️  基础配置初始化需要手动设置通知渠道")
                        setup_results.append(("基础配置", False, "需要手动配置"))
                    else:
                        setup_results.append(("基础配置", False, "用户跳过"))
                        
            except Exception as e:
                click.echo(f"⚠️  基础配置检查失败: {e}")
                setup_results.append(("基础配置", False, f"检查失败: {e}"))
        
        # 2. Claude Code钩子配置
        try:
            from claude_notifier.hooks.installer import ClaudeHookInstaller
            installer = ClaudeHookInstaller()
            
            claude_detected, claude_location = installer.detect_claude_code()
            
            if claude_detected:
                click.echo(f"🔍 检测到Claude Code: {claude_location}")
                
                status = installer.get_installation_status()
                
                if status['hooks_installed'] and status['hooks_valid']:
                    click.echo("✅ Claude Code钩子已配置")
                    setup_results.append(("Claude Code钩子", True, "已安装且有效"))
                else:
                    should_install = auto or click.confirm("是否安装Claude Code钩子集成?")
                    
                    if should_install:
                        click.echo("🔧 正在安装Claude Code钩子...")
                        success, message = installer.install_hooks(force=auto)
                        
                        if success:
                            click.echo(f"✅ {message}")
                            setup_results.append(("Claude Code钩子", True, "安装成功"))
                            
                            if installer.verify_installation():
                                click.echo("✅ 钩子配置验证通过")
                            else:
                                click.echo("⚠️  钩子配置验证失败，但基本功能可用")
                        else:
                            click.echo(f"❌ {message}")
                            setup_results.append(("Claude Code钩子", False, message))
                    else:
                        setup_results.append(("Claude Code钩子", False, "用户跳过"))
            else:
                click.echo("ℹ️  未检测到Claude Code安装")
                setup_results.append(("Claude Code检测", False, "未检测到安装"))
                
        except Exception as e:
            click.echo(f"❌ Claude Code钩子配置失败: {e}")
            setup_results.append(("Claude Code钩子", False, f"配置失败: {e}"))
        
        # 3. 权限检查
        try:
            config_dir = Path.home() / '.claude-notifier'
            if config_dir.exists():
                # 使用数值比较权限
                mode = config_dir.stat().st_mode & 0o777
                permissions = oct(mode)
                if mode >= 0o755:
                    setup_results.append(("目录权限", True, f"权限正常 ({permissions})"))
                else:
                    click.echo(f"⚠️  配置目录权限过低: {permissions}")
                    if auto or click.confirm("是否修复目录权限?"):
                        config_dir.chmod(0o755)
                        setup_results.append(("目录权限", True, "已修复"))
                    else:
                        setup_results.append(("目录权限", False, "权限过低，用户跳过修复"))
            else:
                setup_results.append(("目录权限", True, "配置目录将在首次使用时创建"))
                
        except Exception as e:
            setup_results.append(("目录权限", False, f"检查失败: {e}"))
        
        # 4. 创建设置完成标记
        try:
            setup_marker = Path.home() / '.claude-notifier' / '.setup_complete'
            os.makedirs(setup_marker.parent, exist_ok=True)
            setup_marker.touch()
        except Exception:
            pass
        
        # 5. 配置结果总结
        click.echo("\n" + "=" * 50)
        click.echo("📋 配置结果总结:")
        
        success_count = 0
        for item, success, details in setup_results:
            status_icon = "✅" if success else "❌" 
            click.echo(f"  {status_icon} {item}: {details}")
            if success:
                success_count += 1
        
        total_count = len(setup_results)
        click.echo(f"\n🎯 完成情况: {success_count}/{total_count} 项配置成功")
        
        if success_count == total_count:
            click.echo("🎉 恭喜！Claude Notifier 已完全配置完成")
        elif success_count > 0:
            click.echo("⚠️  部分配置完成，系统可以基本使用")
        else:
            click.echo("❌ 配置未完成，请检查错误并重试")
            sys.exit(1)

    @cli.command()
    @click.argument('message')
    @click.option('-c', '--channels', help='指定发送渠道 (逗号分隔)')
    @click.option('-t', '--type', 'event_type', default='custom', help='事件类型')
    @click.option('-p', '--priority', default='normal', 
                  type=click.Choice(['low', 'normal', 'high', 'critical']),
                  help='通知优先级')
    @click.option('--throttle', is_flag=True, help='启用智能限流')
    @click.option('--project', help='指定项目名称')
    def send(message, channels, event_type, priority, throttle, project):
        """发送通知消息"""
        try:
            channels_list = None
            if channels:
                channels_list = [c.strip() for c in channels.split(',')]
                
            if throttle:
                try:
                    from claude_notifier import IntelligentNotifier
                    notifier = IntelligentNotifier()
                except ImportError:
                    click.echo("❌ 智能功能未安装: pip install claude-notifier[intelligence]")
                    return False
            else:
                from claude_notifier.core.notifier import Notifier
                notifier = Notifier()
                
            kwargs = {'priority': priority}
            if project:
                kwargs['project'] = project
                
            status_info = notifier.get_status()
            enabled_channels = status_info['channels']['enabled']
            
            if not enabled_channels and not channels_list:
                click.echo("⚠️  没有配置的通知渠道，消息未发送")
                click.echo("💡 使用 'claude-notifier config init' 配置通知渠道")
                return False
                
            success = notifier.send(message, channels_list, event_type, **kwargs)
            
            if success:
                if enabled_channels or channels_list:
                    click.echo("✅ 通知发送成功")
                else:
                    click.echo("⚠️  通知已处理，但没有启用的渠道")
            else:
                click.echo("❌ 通知发送失败")
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"❌ 发送失败: {e}")
            sys.exit(1)

    @cli.command()
    @click.option('-c', '--channels', help='测试指定渠道 (逗号分隔)')
    def test(channels):
        """测试通知渠道配置"""
        try:
            from claude_notifier.core.notifier import Notifier
            notifier = Notifier()
            
            channels_list = None
            if channels:
                channels_list = [c.strip() for c in channels.split(',')]
                
            click.echo("🔔 开始测试通知渠道...")
            results = notifier.test_channels(channels_list)
            
            if not results:
                click.echo("⚠️  没有配置的通知渠道")
                return
                
            success_count = sum(results.values())
            total_count = len(results)
            
            click.echo(f"\n📊 测试结果 ({success_count}/{total_count} 成功):")
            
            for channel, success in results.items():
                status = "✅" if success else "❌"
                click.echo(f"  {status} {channel}")
                
            if success_count == total_count:
                click.echo("\n🎉 所有渠道测试通过!")
            elif success_count == 0:
                click.echo("\n❌ 所有渠道测试失败，请检查配置")
                sys.exit(1)
            else:
                click.echo("\n⚠️  部分渠道测试失败，请检查配置")
                
        except Exception as e:
            click.echo(f"❌ 测试失败: {e}")
            sys.exit(1)

    @cli.command()
    @click.option('--intelligence', is_flag=True, help='显示智能功能状态')
    @click.option('--export', 'export_file', help='导出基础状态数据到文件')
    def status(intelligence, export_file):
        """快速系统健康检查"""
        try:
            from claude_notifier import print_feature_status
            print_feature_status()
            
            from claude_notifier.core.notifier import Notifier
            notifier = Notifier()
            status_info = notifier.get_status()
            
            click.echo(f"\n📊 通知器状态:")
            click.echo(f"  版本: {status_info['version']}")
            click.echo(f"  配置文件: {status_info['config']['file']}")
            click.echo(f"  配置有效: {'✅' if status_info['config']['valid'] else '❌'}")
            
            click.echo(f"\n📡 通知渠道:")
            click.echo(f"  可用渠道: {', '.join(status_info['channels']['available'])}")
            click.echo(f"  启用渠道: {status_info['channels']['total_enabled']}")
            if status_info['channels']['enabled']:
                click.echo(f"  渠道列表: {', '.join(status_info['channels']['enabled'])}")
                
            if intelligence:
                try:
                    from claude_notifier import IntelligentNotifier
                    intelligent_notifier = IntelligentNotifier()
                    intel_status = intelligent_notifier.get_intelligence_status()
                    
                    click.echo(f"\n🧠 智能功能:")
                    click.echo(f"  智能功能: {'✅ 已启用' if intel_status['enabled'] else '❌ 已禁用'}")
                    
                except ImportError:
                    click.echo(f"\n🧠 智能功能: ❌ 未安装")
                    
            # 钩子状态
            click.echo(f"\n🔗 Claude Code集成:")
            try:
                from claude_notifier.hooks.installer import ClaudeHookInstaller
                installer = ClaudeHookInstaller()
                hook_status = installer.get_installation_status()
                
                if hook_status['claude_detected']:
                    click.echo(f"  Claude Code: ✅ 已检测到")
                    if hook_status['hooks_installed']:
                        click.echo(f"  钩子状态: ✅ 已安装")
                    else:
                        click.echo(f"  钩子状态: ❌ 未安装")
                else:
                    click.echo(f"  Claude Code: ❌ 未检测到")
                    
            except ImportError:
                click.echo(f"  钩子功能: ❌ 不可用")
                
            if export_file:
                import json
                export_data = {
                    'version': status_info['version'],
                    'config': status_info['config'],
                    'channels': status_info['channels']
                }
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                click.echo(f"\n💾 状态已导出到: {export_file}")
                
        except Exception as e:
            click.echo(f"❌ 状态获取失败: {e}")
            sys.exit(1)

    @cli.command()
    @click.option('--mode', type=click.Choice(['overview', 'detailed', 'alerts', 'historical', 'performance']),
                  default='overview', help='监控模式')
    @click.option('--start', is_flag=True, help='启动后台监控')
    @click.option('--stop', is_flag=True, help='停止后台监控')
    @click.option('--report', help='生成监控报告')
    @click.option('--export', 'export_file', help='导出监控数据')
    @click.option('--watch', is_flag=True, help='实时监控模式')
    @click.option('--interval', type=int, default=5, help='监控间隔(秒)')
    def monitor(mode, start, stop, report, export_file, watch, interval):
        """监控系统管理"""
        try:
            from claude_notifier.monitoring.dashboard import MonitoringDashboard, DashboardMode
        except ImportError:
            click.echo("❌ 监控功能不可用")
            sys.exit(1)
            
        try:
            dashboard_config = {
                'auto_refresh': start,
                'update_interval': interval,
                'cache_duration': 5
            }
            dashboard = MonitoringDashboard(dashboard_config)
            
            if start:
                click.echo("🚀 启动后台监控系统...")
                dashboard.start()
                click.echo("✅ 后台监控已启动")
                
            elif stop:
                click.echo("⏹️  停止后台监控系统...")
                dashboard.stop()
                click.echo("✅ 后台监控已停止")
                
            elif watch:
                _watch_monitoring(dashboard, mode, interval)
                
            elif report:
                click.echo("📋 生成监控报告...")
                dashboard_view = dashboard.get_dashboard_view(DashboardMode.DETAILED)
                with open(report, 'w', encoding='utf-8') as f:
                    f.write(dashboard_view)
                click.echo(f"✅ 报告已保存到: {report}")
                
            elif export_file:
                click.echo("💾 导出监控数据...")
                import json
                export_data = dashboard.export_dashboard_data(include_history=True)
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                click.echo(f"✅ 数据已导出到: {export_file}")
                
            else:
                dashboard_mode = DashboardMode(mode) if mode != 'performance' else DashboardMode.DETAILED
                dashboard_view = dashboard.get_dashboard_view(dashboard_mode)
                click.echo(dashboard_view)
                
            dashboard.cleanup()
                    
        except Exception as e:
            click.echo(f"❌ 监控操作失败: {e}")
            sys.exit(1)


def _watch_monitoring(dashboard, mode: str, interval: int):
    """监控实时显示模式"""
    import os
    from claude_notifier.monitoring.dashboard import DashboardMode
    
    try:
        click.echo(f"🔄 开始实时监控 (每{interval}秒刷新，按 Ctrl+C 退出)\n")
        
        while True:
            click.clear()
            
            click.echo(f"🔄 实时监控模式 (间隔: {interval}s)")
            click.echo(f"📅 刷新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 80)
            
            try:
                dashboard_mode = DashboardMode(mode) if mode != 'performance' else DashboardMode.DETAILED
                dashboard_view = dashboard.get_dashboard_view(dashboard_mode)
                click.echo(dashboard_view)
                
            except Exception as e:
                click.echo(f"❌ 监控数据获取失败: {e}")
                
            click.echo("\n" + "=" * 80)
            click.echo(f"⏱️  下次刷新: {interval}秒后 (按 Ctrl+C 退出)")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        click.echo("\n👋 退出实时监控模式")

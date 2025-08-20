#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Notifier 主CLI入口
统一的命令行工具，支持所有功能
"""

import sys
import click
from typing import Optional, List

# 核心功能导入
from ..core.notifier import Notifier
from .. import get_feature_status, print_feature_status


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='显示版本信息')
@click.option('--status', is_flag=True, help='显示状态信息')
@click.pass_context
def cli(ctx, version, status):
    """Claude Notifier - Claude Code智能通知系统
    
    基础使用:
        claude-notifier send "Hello World!"
        
    智能功能 (需要安装intelligence模块):
        claude-notifier send "通知" --throttle
        
    查看帮助:
        claude-notifier --help
        claude-notifier send --help
    """
    # 确保子命令可以访问上下文
    ctx.ensure_object(dict)
    
    if version:
        from ..__version__ import print_version_info
        print_version_info()
        return
        
    if status:
        print_feature_status()
        try:
            notifier = Notifier()
            status_info = notifier.get_status()
            print(f"\n📊 系统状态:")
            print(f"  配置文件: {status_info['config']['file']}")
            print(f"  配置有效: {'✅' if status_info['config']['valid'] else '❌'}")
            print(f"  启用渠道: {status_info['channels']['total_enabled']}")
            if status_info['channels']['enabled']:
                print(f"  渠道列表: {', '.join(status_info['channels']['enabled'])}")
        except Exception as e:
            print(f"❌ 状态获取失败: {e}")
        return
        
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('message')
@click.option('-c', '--channels', help='指定发送渠道 (逗号分隔)')
@click.option('-t', '--type', 'event_type', default='custom', help='事件类型')
@click.option('-p', '--priority', default='normal', 
              type=click.Choice(['low', 'normal', 'high', 'critical']),
              help='通知优先级')
@click.option('--throttle', is_flag=True, help='启用智能限流 (需要intelligence模块)')
@click.option('--project', help='指定项目名称')
def send(message, channels, event_type, priority, throttle, project):
    """发送通知消息
    
    Examples:
        claude-notifier send "Hello World!"
        claude-notifier send "重要通知" -c dingtalk,email -p high
        claude-notifier send "智能通知" --throttle
    """
    try:
        # 解析渠道列表
        channels_list = None
        if channels:
            channels_list = [c.strip() for c in channels.split(',')]
            
        # 选择通知器类型
        if throttle:
            # 尝试使用智能通知器
            try:
                from .. import IntelligentNotifier
                notifier = IntelligentNotifier()
            except ImportError:
                click.echo("❌ 智能功能未安装: pip install claude-notifier[intelligence]")
                return False
        else:
            notifier = Notifier()
            
        # 构建消息数据
        kwargs = {'priority': priority}
        if project:
            kwargs['project'] = project
            
        # 发送通知
        success = notifier.send(message, channels_list, event_type, **kwargs)
        
        if success:
            click.echo("✅ 通知发送成功")
        else:
            click.echo("❌ 通知发送失败")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 发送失败: {e}")
        sys.exit(1)


@cli.command()
@click.option('-c', '--channels', help='测试指定渠道 (逗号分隔，默认测试所有)')
def test(channels):
    """测试通知渠道配置
    
    Examples:
        claude-notifier test
        claude-notifier test -c dingtalk,email
    """
    try:
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
def status(intelligence):
    """显示详细状态信息"""
    try:
        # 基础状态
        print_feature_status()
        
        # 通知器状态
        notifier = Notifier()
        status_info = notifier.get_status()
        
        click.echo(f"\n📊 通知器状态:")
        click.echo(f"  版本: {status_info['version']}")
        click.echo(f"  配置文件: {status_info['config']['file']}")
        click.echo(f"  配置有效: {'✅' if status_info['config']['valid'] else '❌'}")
        click.echo(f"  最后修改: {status_info['config']['last_modified'] or '未知'}")
        
        click.echo(f"\n📡 通知渠道:")
        click.echo(f"  可用渠道: {', '.join(status_info['channels']['available'])}")
        click.echo(f"  启用渠道: {status_info['channels']['total_enabled']}")
        if status_info['channels']['enabled']:
            click.echo(f"  渠道列表: {', '.join(status_info['channels']['enabled'])}")
        else:
            click.echo("  ⚠️  没有启用的通知渠道")
            
        # 智能功能状态
        if intelligence:
            try:
                from .. import IntelligentNotifier
                intelligent_notifier = IntelligentNotifier()
                intel_status = intelligent_notifier.get_intelligence_status()
                
                click.echo(f"\n🧠 智能功能:")
                click.echo(f"  智能功能: {'✅ 已启用' if intel_status['enabled'] else '❌ 已禁用'}")
                
                if intel_status['enabled']:
                    components = intel_status['components']
                    click.echo(f"  操作阻止: {'✅' if components['operation_gate']['enabled'] else '❌'}")
                    click.echo(f"  通知限流: {'✅' if components['notification_throttle']['enabled'] else '❌'}")
                    click.echo(f"  消息分组: {'✅' if components['message_grouper']['enabled'] else '❌'}")
                    click.echo(f"  冷却管理: {'✅' if components['cooldown_manager']['enabled'] else '❌'}")
                    
            except ImportError:
                click.echo(f"\n🧠 智能功能: ❌ 未安装 (pip install claude-notifier[intelligence])")
                
    except Exception as e:
        click.echo(f"❌ 状态获取失败: {e}")
        sys.exit(1)


@cli.command()
@click.option('--reload', is_flag=True, help='重新加载配置文件')
def config(reload):
    """配置管理"""
    try:
        notifier = Notifier()
        
        if reload:
            success = notifier.reload_config()
            if success:
                click.echo("✅ 配置重新加载成功")
            else:
                click.echo("❌ 配置重新加载失败")
                sys.exit(1)
        else:
            status_info = notifier.get_status()
            config_info = status_info['config']
            
            click.echo("⚙️  配置信息:")
            click.echo(f"  文件路径: {config_info['file']}")
            click.echo(f"  配置有效: {'✅' if config_info['valid'] else '❌'}")
            click.echo(f"  最后修改: {config_info['last_modified'] or '未知'}")
            
            if not config_info['valid']:
                click.echo("\n💡 建议:")
                click.echo("  1. 检查配置文件语法")
                click.echo("  2. 运行 claude-notifier config --reload 重新加载")
                
    except Exception as e:
        click.echo(f"❌ 配置操作失败: {e}")
        sys.exit(1)


# 导入更新和卸载命令
try:
    from .update import update_cli
    from .uninstall import uninstall_cli
    
    cli.add_command(update_cli, name='update')
    cli.add_command(uninstall_cli, name='uninstall')
except ImportError:
    # 如果依赖不可用，则创建占位符命令
    @cli.command()
    def update():
        """更新Claude Notifier (需要requests库)"""
        click.echo("❌ 更新功能需要安装requests库: pip install requests")
        
    @cli.command() 
    def uninstall():
        """卸载Claude Notifier"""
        click.echo("❌ 卸载功能暂不可用")


# 智能功能相关命令 (可选)
def _add_intelligence_commands():
    """添加智能功能命令"""
    try:
        from .. import has_intelligence, IntelligentNotifier
        
        if not has_intelligence():
            return
            
        @cli.group()
        def intelligence():
            """智能功能管理"""
            pass
            
        @intelligence.command()
        @click.option('--component', help='指定组件 (operation_gate, throttle, grouper, cooldown)')
        def enable(component):
            """启用智能功能"""
            # 实现智能功能启用逻辑
            click.echo(f"启用智能功能: {component or 'all'}")
            
        @intelligence.command() 
        @click.option('--component', help='指定组件')
        def disable(component):
            """禁用智能功能"""
            # 实现智能功能禁用逻辑
            click.echo(f"禁用智能功能: {component or 'all'}")
            
        @intelligence.command()
        def stats():
            """查看智能功能统计"""
            try:
                notifier = IntelligentNotifier()
                intel_status = notifier.get_intelligence_status()
                
                click.echo("🧠 智能功能统计:")
                # 显示详细统计信息
                # ...实现统计显示逻辑
                
            except Exception as e:
                click.echo(f"❌ 统计获取失败: {e}")
                
    except ImportError:
        pass

# 添加智能功能命令 (如果可用)
_add_intelligence_commands()


def main():
    """主入口点"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 已取消操作")
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ 意外错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
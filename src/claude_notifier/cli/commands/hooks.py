#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code 钩子管理命令组

从 main.py 拆分出来，包含：
- install: 安装钩子配置
- uninstall: 卸载钩子配置
- status: 查看钩子状态
- verify: 验证钩子配置
"""

import sys
import click


@click.group(invoke_without_command=True)
@click.pass_context
def hooks(ctx):
    """Claude Code钩子管理
    
    管理Claude Code集成钩子，实现智能通知功能：
    
    Commands:
        install   - 安装钩子配置
        uninstall - 卸载钩子配置  
        status    - 查看钩子状态
        verify    - 验证钩子配置
        
    Examples:
        claude-notifier hooks                  # 查看钩子状态
        claude-notifier hooks install         # 安装钩子
        claude-notifier hooks status          # 检查钩子状态
        claude-notifier hooks verify          # 验证钩子配置
    """
    if ctx.invoked_subcommand is None:
        _show_hooks_status()


def _show_hooks_status():
    """显示钩子状态概览"""
    try:
        from claude_notifier.hooks.installer import ClaudeHookInstaller
        
        installer = ClaudeHookInstaller()
        installer.print_status()
        
    except ImportError:
        click.echo("❌ 钩子功能不可用")
        click.echo("💡 请确保在PyPI安装中包含钩子模块")
    except Exception as e:
        click.echo(f"❌ 钩子状态获取失败: {e}")


@hooks.command()
@click.option('--force', is_flag=True, help='强制安装（覆盖现有配置）')
@click.option('--detect-only', is_flag=True, help='只检测Claude Code，不安装')
def install(force, detect_only):
    """安装Claude Code钩子配置
    
    自动检测Claude Code安装并配置钩子，实现：
    - 会话开始时的通知
    - 命令执行时的权限检查
    - 任务完成时的庆祝通知
    - 错误发生时的报警通知
    """
    try:
        from claude_notifier.hooks.installer import ClaudeHookInstaller
        
        installer = ClaudeHookInstaller()
        
        if detect_only:
            # 只检测不安装
            claude_detected, claude_location = installer.detect_claude_code()
            if claude_detected:
                click.echo(f"✅ 检测到Claude Code: {claude_location}")
                click.echo("💡 运行 'claude-notifier hooks install' 开始安装")
            else:
                click.echo("❌ 未检测到Claude Code安装")
                click.echo("💡 请先安装Claude Code: npm install -g @anthropic-ai/claude-code")
            return
        
        # 执行安装
        success, message = installer.install_hooks(force=force)
        click.echo(message)
        
        if success:
            click.echo("\n🎉 Claude Code钩子安装完成！")
            click.echo("\n📋 后续步骤:")
            click.echo("  1. 重新启动Claude Code")
            click.echo("  2. 运行 'claude-notifier test' 测试通知")
            click.echo("  3. 开始使用增强的Claude Code体验")
        else:
            click.echo("\n💡 安装故障排除:")
            click.echo("  1. 确保Claude Code已正确安装")
            click.echo("  2. 检查~/.config/claude目录权限")
            click.echo("  3. 使用 --force 强制覆盖现有配置")
            sys.exit(1)
            
    except ImportError:
        click.echo("❌ 钩子安装器不可用")
        click.echo("💡 这可能是PyPI包问题，请联系开发者")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 钩子安装失败: {e}")
        sys.exit(1)


@hooks.command()
@click.option('--backup/--no-backup', default=True, help='是否备份现有配置')
@click.option('--yes', '-y', is_flag=True, help='跳过确认（用于脚本和CI/CD环境）')
def uninstall(backup, yes):
    """卸载Claude Code钩子配置
    
    移除已安装的钩子配置，恢复原始Claude Code行为。
    卸载后Claude Code将不再发送通知。
    """
    try:
        from claude_notifier.hooks.installer import ClaudeHookInstaller
        
        installer = ClaudeHookInstaller()
        
        # 确认卸载（除非使用 --yes 选项）
        if not yes and not click.confirm("确定要卸载Claude Code钩子吗？这将停止所有Claude Code通知功能"):
            click.echo("❌ 用户取消卸载")
            return
        
        success, message = installer.uninstall_hooks()
        click.echo(message)
        
        if success:
            click.echo("\n✅ Claude Code钩子已成功卸载")
            click.echo("💡 重新启动Claude Code以使更改生效")
        else:
            sys.exit(1)
            
    except ImportError:
        click.echo("❌ 钩子安装器不可用")
        sys.exit(1)  
    except Exception as e:
        click.echo(f"❌ 钩子卸载失败: {e}")
        sys.exit(1)


@hooks.command()
def status():
    """查看钩子详细状态
    
    显示完整的钩子系统状态，包括：
    - Claude Code检测结果
    - 钩子脚本状态
    - 配置文件状态
    - 启用的钩子列表
    """
    try:
        from claude_notifier.hooks.installer import ClaudeHookInstaller
        
        installer = ClaudeHookInstaller()
        installer.print_status()
        
        # 额外的诊断信息
        status_info = installer.get_installation_status()
        
        if status_info['claude_detected'] and status_info['hooks_installed'] and status_info['hooks_valid']:
            click.echo(f"\n💡 提示:")
            click.echo(f"  - 钩子已就绪，Claude Code启动时将自动加载")
            click.echo(f"  - 运行 'claude-notifier test' 测试通知功能")
            click.echo(f"  - 查看 ~/.claude-notifier/logs/ 了解详细日志")
        else:
            click.echo(f"\n⚠️ 问题修复建议:")
            if not status_info['claude_detected']:
                click.echo(f"  - 安装Claude Code: npm install -g @anthropic-ai/claude-code")
            if not status_info['hooks_installed']:
                click.echo(f"  - 安装钩子: claude-notifier hooks install")
            if not status_info['hooks_valid']:
                click.echo(f"  - 重新安装: claude-notifier hooks install --force")
                
    except ImportError:
        click.echo("❌ 钩子功能不可用")
    except Exception as e:
        click.echo(f"❌ 状态获取失败: {e}")


@hooks.command()
@click.option('--fix', is_flag=True, help='自动修复发现的问题')
def verify(fix):
    """验证钩子配置完整性
    
    全面验证钩子系统：
    - 检查钩子脚本文件
    - 验证配置文件格式
    - 测试钩子执行权限
    - 检查路径和依赖
    """
    try:
        from claude_notifier.hooks.installer import ClaudeHookInstaller
        
        installer = ClaudeHookInstaller()
        
        click.echo("🔍 开始钩子配置验证...")
        
        # 基础验证
        if installer.verify_installation():
            click.echo("✅ 钩子配置验证通过")
            
            # 执行钩子测试
            click.echo("\n🧪 测试钩子执行...")
            
            # 简单的钩子调用测试
            import subprocess
            
            hook_script = installer.hook_script_path
            if hook_script.exists():
                try:
                    # 测试钩子脚本语法
                    result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', str(hook_script)],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        click.echo("✅ 钩子脚本语法正确")
                    else:
                        click.echo(f"❌ 钩子脚本语法错误: {result.stderr}")
                        
                except Exception as e:
                    click.echo(f"⚠️ 钩子脚本测试失败: {e}")
            
            # 配置文件权限检查
            if installer.hooks_file.exists():
                import os
                stat_info = installer.hooks_file.stat()
                if stat_info.st_mode & 0o044:  # 检查读权限
                    click.echo("✅ 钩子配置文件权限正确")
                else:
                    click.echo("⚠️ 钩子配置文件权限异常")
                    
            click.echo("\n🎉 钩子系统验证完成")
            
        else:
            click.echo("❌ 钩子配置验证失败")
            
            if fix:
                click.echo("\n🔧 尝试自动修复...")
                success, message = installer.install_hooks(force=True)
                if success:
                    click.echo("✅ 自动修复成功")
                else:
                    click.echo(f"❌ 自动修复失败: {message}")
                    sys.exit(1)
            else:
                click.echo("💡 使用 --fix 选项尝试自动修复")
                sys.exit(1)
                
    except ImportError:
        click.echo("❌ 钩子验证功能不可用")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 钩子验证失败: {e}")
        sys.exit(1)

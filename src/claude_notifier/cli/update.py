#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新/升级管理系统
支持PyPI包更新、配置迁移、功能升级等
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from packaging import version
import click

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class UpdateManager:
    """更新管理器"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / '.claude-notifier'
        self.current_version = self._get_current_version()
        self.pypi_api_url = "https://pypi.org/pypi/claude-notifier/json"
        
    def _get_current_version(self) -> str:
        """获取当前安装版本"""
        try:
            from .. import __version__
            return __version__
        except ImportError:
            return "unknown"
            
    def check_for_updates(self) -> Dict[str, Any]:
        """检查是否有可用更新"""
        result = {
            'current_version': self.current_version,
            'latest_version': None,
            'update_available': False,
            'update_type': None,  # major, minor, patch
            'release_notes': None,
            'error': None
        }
        
        if not REQUESTS_AVAILABLE:
            result['error'] = "requests库未安装，无法检查更新"
            return result
            
        try:
            # 从PyPI获取最新版本信息
            response = requests.get(self.pypi_api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            latest_version = data['info']['version']
            result['latest_version'] = latest_version
            
            # 比较版本
            if self.current_version != "unknown":
                current_ver = version.parse(self.current_version)
                latest_ver = version.parse(latest_version)
                
                if latest_ver > current_ver:
                    result['update_available'] = True
                    result['update_type'] = self._get_update_type(current_ver, latest_ver)
                    result['release_notes'] = self._get_release_notes(data)
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _get_update_type(self, current: version.Version, latest: version.Version) -> str:
        """确定更新类型"""
        if latest.major > current.major:
            return "major"
        elif latest.minor > current.minor:
            return "minor"
        elif latest.micro > current.micro:
            return "patch"
        else:
            return "other"
            
    def _get_release_notes(self, pypi_data: Dict[str, Any]) -> Optional[str]:
        """提取发布说明"""
        try:
            description = pypi_data.get('info', {}).get('description', '')
            # 简单提取CHANGELOG部分
            if 'CHANGELOG' in description or '## ' in description:
                lines = description.split('\n')
                changelog_lines = []
                in_changelog = False
                
                for line in lines:
                    if 'CHANGELOG' in line.upper() or line.startswith('## '):
                        in_changelog = True
                    if in_changelog:
                        changelog_lines.append(line)
                        if len(changelog_lines) > 20:  # 限制长度
                            break
                            
                return '\n'.join(changelog_lines[:20]) if changelog_lines else None
        except Exception:
            pass
        return None
        
    def backup_current_config(self) -> Path:
        """备份当前配置"""
        backup_dir = self.config_dir.parent / f'claude-notifier-backup-{int(time.time())}'
        
        if self.config_dir.exists():
            shutil.copytree(self.config_dir, backup_dir)
            
        return backup_dir
        
    def update_package(self, 
                      target_version: Optional[str] = None,
                      extras: Optional[List[str]] = None) -> Dict[str, Any]:
        """更新Python包"""
        result = {
            'success': False,
            'old_version': self.current_version,
            'new_version': None,
            'command': None,
            'output': None,
            'error': None
        }
        
        # 构建pip命令
        cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
        
        if target_version:
            package_spec = f"claude-notifier=={target_version}"
        else:
            package_spec = "claude-notifier"
            
        # 添加可选功能
        if extras:
            package_spec += f"[{','.join(extras)}]"
            
        cmd.append(package_spec)
        result['command'] = ' '.join(cmd)
        
        try:
            # 执行更新
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5分钟超时
            )
            
            result['output'] = process.stdout
            
            if process.returncode == 0:
                result['success'] = True
                result['new_version'] = self._get_installed_version()
            else:
                result['error'] = process.stderr
                
        except subprocess.TimeoutExpired:
            result['error'] = "更新超时"
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _get_installed_version(self) -> str:
        """获取安装后的版本"""
        try:
            # 重新加载模块以获取新版本
            import importlib
            import claude_notifier
            importlib.reload(claude_notifier)
            return claude_notifier.__version__
        except Exception:
            return "unknown"
            
    def migrate_config(self, old_version: str, new_version: str) -> Dict[str, Any]:
        """配置迁移"""
        result = {
            'success': False,
            'changes_made': [],
            'backup_created': None,
            'error': None
        }
        
        try:
            config_file = self.config_dir / 'config.yaml'
            
            if not config_file.exists():
                result['success'] = True
                result['changes_made'].append("无配置文件需要迁移")
                return result
                
            # 备份配置文件
            backup_file = config_file.with_suffix(f'.yaml.pre-{new_version}-backup')
            shutil.copy2(config_file, backup_file)
            result['backup_created'] = str(backup_file)
            
            # 读取当前配置
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 版本特定的迁移逻辑
            changes = self._apply_config_migrations(config, old_version, new_version)
            result['changes_made'].extend(changes)
            
            # 如果有变更，保存配置
            if changes:
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                    
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    def _apply_config_migrations(self, 
                                config: Dict[str, Any], 
                                old_version: str, 
                                new_version: str) -> List[str]:
        """应用版本特定的配置迁移"""
        changes = []
        
        try:
            old_ver = version.parse(old_version) if old_version != "unknown" else version.parse("0.0.0")
            new_ver = version.parse(new_version)
        except Exception:
            return changes
            
        # 1.0.x -> 1.1.x: 添加智能功能配置
        if old_ver < version.parse("1.1.0") <= new_ver:
            if 'intelligent_limiting' not in config:
                config['intelligent_limiting'] = {
                    'enabled': False,  # 默认禁用，让用户主动启用
                    'operation_gate': {'enabled': True},
                    'notification_throttle': {'enabled': True},
                    'message_grouper': {'enabled': True}, 
                    'cooldown_manager': {'enabled': True}
                }
                changes.append("添加智能限流配置 (默认禁用)")
                
        # 1.1.x -> 1.2.x: 更新配置结构
        if old_ver < version.parse("1.2.0") <= new_ver:
            # 迁移旧的rate_limiting配置到新的intelligent_limiting
            if 'rate_limiting' in config and 'intelligent_limiting' in config:
                old_limiting = config.pop('rate_limiting', {})
                if old_limiting.get('enabled', False):
                    config['intelligent_limiting']['enabled'] = True
                    changes.append("迁移旧的限流配置到智能限流系统")
                    
        # 1.2.x -> 1.3.x: 添加监控配置
        if old_ver < version.parse("1.3.0") <= new_ver:
            if 'monitoring' not in config:
                config['monitoring'] = {
                    'enabled': False,
                    'dashboard': {'enabled': False, 'port': 8080},
                    'metrics': {'enabled': True}
                }
                changes.append("添加监控功能配置")
                
        return changes
        
    def verify_installation(self) -> Dict[str, Any]:
        """验证安装完整性"""
        result = {
            'success': True,
            'issues': [],
            'suggestions': []
        }
        
        try:
            # 检查包导入
            import claude_notifier
            from claude_notifier import Notifier
            
            # 检查核心功能
            notifier = Notifier()
            status = notifier.get_status()
            
            if not status['channels']['enabled']:
                result['issues'].append("没有启用的通知渠道")
                result['suggestions'].append("请配置至少一个通知渠道")
                
            # 检查可选功能
            from claude_notifier import has_intelligence, has_monitoring
            
            if not has_intelligence():
                result['suggestions'].append("可安装智能功能: pip install claude-notifier[intelligence]")
                
            if not has_monitoring():
                result['suggestions'].append("可安装监控功能: pip install claude-notifier[monitoring]")
                
        except ImportError as e:
            result['success'] = False
            result['issues'].append(f"包导入失败: {e}")
        except Exception as e:
            result['issues'].append(f"验证异常: {e}")
            
        return result
        
    def full_update(self, 
                   target_version: Optional[str] = None,
                   extras: Optional[List[str]] = None,
                   backup_config: bool = True) -> Dict[str, Any]:
        """完整更新流程"""
        results = {
            'check': None,
            'backup': None,
            'update': None,
            'migrate': None,
            'verify': None,
            'success': False
        }
        
        print("🔍 检查更新...")
        results['check'] = self.check_for_updates()
        
        if results['check']['error']:
            print(f"❌ 检查更新失败: {results['check']['error']}")
            return results
            
        if not results['check']['update_available'] and not target_version:
            print("✅ 已是最新版本")
            results['success'] = True
            return results
            
        latest = results['check']['latest_version']
        current = results['check']['current_version']
        
        print(f"📦 发现更新: {current} -> {latest}")
        
        if results['check']['release_notes']:
            print(f"\n📋 更新说明:\n{results['check']['release_notes']}")
            
        # 备份配置
        if backup_config:
            print("📦 备份当前配置...")
            try:
                backup_path = self.backup_current_config()
                results['backup'] = {'success': True, 'path': str(backup_path)}
                print(f"✅ 配置已备份: {backup_path}")
            except Exception as e:
                results['backup'] = {'success': False, 'error': str(e)}
                print(f"⚠️  配置备份失败: {e}")
        else:
            results['backup'] = {'success': True, 'skipped': True}
            
        # 更新包
        print("📥 更新Python包...")
        results['update'] = self.update_package(target_version, extras)
        
        if not results['update']['success']:
            print(f"❌ 包更新失败: {results['update']['error']}")
            return results
            
        print(f"✅ 包更新成功: {results['update']['new_version']}")
        
        # 配置迁移
        print("🔄 检查配置迁移...")
        results['migrate'] = self.migrate_config(
            current, results['update']['new_version']
        )
        
        if results['migrate']['success']:
            if results['migrate']['changes_made']:
                print("✅ 配置迁移完成:")
                for change in results['migrate']['changes_made']:
                    print(f"  • {change}")
            else:
                print("✅ 无需配置迁移")
        else:
            print(f"⚠️  配置迁移失败: {results['migrate']['error']}")
            
        # 验证安装
        print("🔍 验证安装...")
        results['verify'] = self.verify_installation()
        
        if results['verify']['success']:
            print("✅ 安装验证通过")
            if results['verify']['suggestions']:
                print("💡 建议:")
                for suggestion in results['verify']['suggestions']:
                    print(f"  • {suggestion}")
        else:
            print("⚠️  安装验证发现问题:")
            for issue in results['verify']['issues']:
                print(f"  • {issue}")
                
        results['success'] = results['update']['success']
        return results


@click.group()
def update_cli():
    """Claude Notifier 更新工具"""
    pass

@update_cli.command()
@click.option('--check-only', is_flag=True, help='仅检查更新，不执行更新')
def check(check_only):
    """检查可用更新"""
    manager = UpdateManager()
    result = manager.check_for_updates()
    
    if result['error']:
        print(f"❌ 检查更新失败: {result['error']}")
        return
        
    print(f"📦 当前版本: {result['current_version']}")
    print(f"📦 最新版本: {result['latest_version']}")
    
    if result['update_available']:
        print(f"🆕 发现 {result['update_type']} 更新！")
        if result['release_notes']:
            print(f"\n📋 更新说明:\n{result['release_notes']}")
            
        if not check_only:
            if click.confirm("是否立即更新？"):
                update_result = manager.full_update()
                if update_result['success']:
                    print("🎉 更新完成！")
                else:
                    print("❌ 更新失败")
    else:
        print("✅ 已是最新版本")

@update_cli.command() 
@click.option('--version', help='指定更新到的版本')
@click.option('--extras', help='额外功能模块 (intelligence,monitoring,all)')
@click.option('--no-backup', is_flag=True, help='不备份配置')
def upgrade(version, extras, no_backup):
    """升级到指定版本"""
    manager = UpdateManager()
    
    extras_list = []
    if extras:
        extras_list = [e.strip() for e in extras.split(',')]
        
    result = manager.full_update(
        target_version=version,
        extras=extras_list,
        backup_config=not no_backup
    )
    
    if result['success']:
        print("🎉 升级完成！")
    else:
        print("❌ 升级失败，请查看上述错误信息")

@update_cli.command()
def verify():
    """验证安装完整性"""
    manager = UpdateManager()
    result = manager.verify_installation()
    
    if result['success']:
        print("✅ 安装验证通过")
        if result['suggestions']:
            print("💡 优化建议:")
            for suggestion in result['suggestions']:
                print(f"  • {suggestion}")
    else:
        print("❌ 发现安装问题:")
        for issue in result['issues']:
            print(f"  • {issue}")

if __name__ == '__main__':
    update_cli()
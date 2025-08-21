#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
卸载支持系统
提供完整的卸载功能，包括配置文件、钩子、数据等
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import click


class UninstallManager:
    """卸载管理器"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / '.claude-notifier'
        self.claude_config_dir = self.home_dir / '.claude'
        
        # 需要清理的路径
        self.cleanup_paths = [
            # 配置目录
            self.config_dir,
            
            # 符号链接
            self.home_dir / '.local/bin/claude-notifier',
            self.home_dir / '.local/bin/claude-notify', 
            Path('/usr/local/bin/claude-notifier'),
            Path('/usr/local/bin/claude-notify'),
            
            # Claude Code钩子配置 (备份)
        ]
        
    def analyze_installation(self) -> Dict[str, Any]:
        """分析当前安装状态"""
        analysis = {
            'package_installed': False,
            'config_exists': False,
            'hooks_installed': False,
            'symlinks': [],
            'data_size': 0,
            'claude_hooks_modified': False
        }
        
        # 检查包安装状态
        try:
            import claude_notifier
            analysis['package_installed'] = True
        except ImportError:
            pass
            
        # 检查配置目录
        if self.config_dir.exists():
            analysis['config_exists'] = True
            analysis['data_size'] = self._calculate_dir_size(self.config_dir)
            
        # 检查符号链接
        for path in self.cleanup_paths[1:]:  # 跳过配置目录
            if path.is_symlink() or (path.exists() and 'claude-notif' in path.name):
                analysis['symlinks'].append(str(path))
                
        # 检查Claude Code钩子
        claude_settings = self.claude_config_dir / 'settings.json'
        if claude_settings.exists():
            try:
                import json
                with open(claude_settings) as f:
                    settings = json.load(f)
                    
                hooks = settings.get('hooks', {})
                for hook_type, hook_list in hooks.items():
                    for hook_config in hook_list:
                        for hook in hook_config.get('hooks', []):
                            command = hook.get('command', '')
                            if 'claude-notifier' in command:
                                analysis['hooks_installed'] = True
                                analysis['claude_hooks_modified'] = True
                                break
            except Exception:
                pass
                
        return analysis
        
    def _calculate_dir_size(self, path: Path) -> int:
        """计算目录大小 (字节)"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
        except Exception:
            pass
        return total_size
        
    def create_backup(self, backup_dir: Optional[Path] = None) -> Path:
        """创建备份"""
        if backup_dir is None:
            backup_dir = self.home_dir / f'claude-notifier-backup-{int(time.time())}'
            
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份配置目录
        if self.config_dir.exists():
            shutil.copytree(
                self.config_dir, 
                backup_dir / 'config',
                dirs_exist_ok=True
            )
            
        # 备份Claude配置 (仅相关部分)
        claude_settings = self.claude_config_dir / 'settings.json'
        if claude_settings.exists():
            shutil.copy2(claude_settings, backup_dir / 'claude_settings.json.backup')
            
        return backup_dir
        
    def remove_package(self) -> bool:
        """卸载Python包"""
        try:
            # 尝试使用pip卸载
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'uninstall', 'claude-notifier', '-y'
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception as e:
            print(f"包卸载失败: {e}")
            return False
            
    def remove_config_files(self, keep_backup: bool = True) -> bool:
        """删除配置文件"""
        try:
            if self.config_dir.exists():
                if keep_backup:
                    # 创建最终备份
                    backup_name = f'claude-notifier-removed-{int(time.time())}'
                    backup_path = self.home_dir / backup_name
                    shutil.move(str(self.config_dir), str(backup_path))
                    print(f"配置已备份至: {backup_path}")
                else:
                    shutil.rmtree(self.config_dir)
                    
            return True
        except Exception as e:
            print(f"配置删除失败: {e}")
            return False
            
    def remove_symlinks(self) -> bool:
        """删除符号链接"""
        success = True
        
        for path in self.cleanup_paths[1:]:  # 跳过配置目录
            try:
                if path.is_symlink():
                    path.unlink()
                    print(f"已删除符号链接: {path}")
                elif path.exists() and 'claude-notif' in path.name:
                    path.unlink()
                    print(f"已删除文件: {path}")
            except Exception as e:
                print(f"删除失败 {path}: {e}")
                success = False
                
        return success
        
    def restore_claude_hooks(self) -> bool:
        """恢复Claude Code钩子配置"""
        claude_settings = self.claude_config_dir / 'settings.json'
        
        if not claude_settings.exists():
            return True
            
        try:
            import json
            
            # 读取当前配置
            with open(claude_settings) as f:
                settings = json.load(f)
                
            # 查找并删除claude-notifier相关钩子
            modified = False
            hooks = settings.get('hooks', {})
            
            for hook_type in list(hooks.keys()):
                hook_list = hooks[hook_type]
                new_hook_list = []
                
                for hook_config in hook_list:
                    new_hooks = []
                    for hook in hook_config.get('hooks', []):
                        command = hook.get('command', '')
                        if 'claude-notifier' not in command:
                            new_hooks.append(hook)
                        else:
                            modified = True
                            print(f"移除钩子: {command}")
                            
                    if new_hooks:
                        hook_config['hooks'] = new_hooks
                        new_hook_list.append(hook_config)
                    elif len(hook_config.get('hooks', [])) > 0:
                        # 原来有钩子但现在没有了，说明全部都是claude-notifier的
                        modified = True
                        
                if new_hook_list:
                    hooks[hook_type] = new_hook_list
                else:
                    del hooks[hook_type]
                    modified = True
                    
            # 如果没有任何钩子了，删除整个hooks配置
            if not hooks:
                if 'hooks' in settings:
                    del settings['hooks']
                    modified = True
                    
            # 保存修改
            if modified:
                # 备份原文件
                backup_file = claude_settings.with_suffix('.json.pre-uninstall-backup')
                shutil.copy2(claude_settings, backup_file)
                
                # 写入新配置
                with open(claude_settings, 'w') as f:
                    json.dump(settings, f, indent=2)
                    
                print(f"Claude配置已恢复，原配置备份至: {backup_file}")
                
            return True
            
        except Exception as e:
            print(f"恢复Claude钩子失败: {e}")
            return False
            
    def cleanup_python_cache(self) -> bool:
        """清理Python缓存"""
        try:
            # 清理 __pycache__ 目录
            import claude_notifier
            package_path = Path(claude_notifier.__file__).parent
            
            for pycache_dir in package_path.rglob('__pycache__'):
                shutil.rmtree(pycache_dir, ignore_errors=True)
                
            return True
        except Exception:
            return True  # 不算失败
            
    def full_uninstall(self, 
                      keep_config_backup: bool = True,
                      create_backup: bool = True) -> Dict[str, bool]:
        """完整卸载"""
        results = {}
        
        print("🗑️  开始卸载 Claude Notifier...")
        
        # 1. 分析安装状态
        analysis = self.analyze_installation()
        print(f"📊 安装分析: {analysis}")
        
        # 2. 创建备份
        if create_backup and (analysis['config_exists'] or analysis['hooks_installed']):
            try:
                backup_path = self.create_backup()
                print(f"📦 备份已创建: {backup_path}")
                results['backup'] = True
            except Exception as e:
                print(f"⚠️  备份创建失败: {e}")
                results['backup'] = False
        else:
            results['backup'] = True
            
        # 3. 恢复Claude钩子
        if analysis['claude_hooks_modified']:
            results['claude_hooks'] = self.restore_claude_hooks()
        else:
            results['claude_hooks'] = True
            
        # 4. 删除符号链接
        results['symlinks'] = self.remove_symlinks()
        
        # 5. 删除配置文件
        if analysis['config_exists']:
            results['config'] = self.remove_config_files(keep_config_backup)
        else:
            results['config'] = True
            
        # 6. 清理Python缓存
        results['python_cache'] = self.cleanup_python_cache()
        
        # 7. 卸载Python包
        if analysis['package_installed']:
            results['package'] = self.remove_package()
        else:
            results['package'] = True
            
        return results
        

@click.command()
@click.option('--keep-config', is_flag=True, default=True, 
              help='保留配置文件备份')
@click.option('--no-backup', is_flag=True, default=False,
              help='不创建备份')
@click.option('--force', is_flag=True, default=False,
              help='强制卸载，不询问确认')
def uninstall_cli(keep_config, no_backup, force):
    """Claude Notifier 卸载工具"""
    
    uninstaller = UninstallManager()
    
    # 分析安装状态
    analysis = uninstaller.analyze_installation()
    
    if not any([
        analysis['package_installed'],
        analysis['config_exists'], 
        analysis['hooks_installed'],
        analysis['symlinks']
    ]):
        print("✅ Claude Notifier 未安装或已完全卸载")
        return
        
    # 显示将要删除的内容
    print("🔍 发现以下安装内容:")
    if analysis['package_installed']:
        print("  ✓ Python包已安装")
    if analysis['config_exists']:
        size_mb = analysis['data_size'] / (1024 * 1024)
        print(f"  ✓ 配置目录 (~/.claude-notifier, {size_mb:.1f}MB)")
    if analysis['hooks_installed']:
        print("  ✓ Claude Code钩子集成")
    if analysis['symlinks']:
        print(f"  ✓ 符号链接: {', '.join(analysis['symlinks'])}")
        
    # 确认卸载
    if not force:
        if not click.confirm("\n确认卸载 Claude Notifier？"):
            print("❌ 卸载已取消")
            return
            
    # 执行卸载
    results = uninstaller.full_uninstall(
        keep_config_backup=keep_config,
        create_backup=not no_backup
    )
    
    # 显示结果
    print("\n📋 卸载结果:")
    for component, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {component}")
        
    if all(results.values()):
        print("\n🎉 Claude Notifier 卸载完成！")
        if keep_config:
            print("💡 配置备份已保留，可手动删除")
    else:
        print("\n⚠️  部分组件卸载失败，请检查上述结果")
        

if __name__ == '__main__':
    uninstall_cli()
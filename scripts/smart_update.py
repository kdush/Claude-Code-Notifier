#!/usr/bin/env python3
"""
智能更新系统 - 解决更新困难问题
支持 PyPI 和 Git 两种安装方式的自动更新
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import urllib.request
import urllib.error

class SmartUpdater:
    """智能更新管理器"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.claude-notifier'
        self.version_file = self.config_dir / 'version.json'
        self.update_log = self.config_dir / 'update.log'
        self.update_state = self.config_dir / 'update_state.json'
        
    def get_installation_info(self) -> Dict:
        """获取当前安装信息"""
        if not self.version_file.exists():
            # 尝试自动检测
            return self._auto_detect_installation()
        
        with open(self.version_file) as f:
            return json.load(f)
    
    def _auto_detect_installation(self) -> Dict:
        """自动检测安装类型"""
        info = {
            'type': 'unknown',
            'version': '0.0.0',
            'detected_at': datetime.now().isoformat()
        }
        
        # 检测PyPI安装
        try:
            result = subprocess.run(
                ['pip3', 'show', 'claude-code-notifier'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        info['type'] = 'pypi'
                        info['version'] = line.split(':')[1].strip()
                        break
        except:
            pass
        
        # 检测Git安装
        git_path = Path.home() / 'Claude-Code-Notifier'
        if git_path.exists() and (git_path / '.git').exists():
            info['type'] = 'git'
            info['repo_path'] = str(git_path)
            try:
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--always'],
                    cwd=git_path, capture_output=True, text=True
                )
                info['version'] = result.stdout.strip()
            except:
                pass
        
        # 保存检测结果
        self.config_dir.mkdir(exist_ok=True)
        with open(self.version_file, 'w') as f:
            json.dump(info, f, indent=2)
        
        return info
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """检查是否有更新"""
        info = self.get_installation_info()
        
        if info['type'] == 'pypi':
            return self._check_pypi_updates(info)
        elif info['type'] == 'git':
            return self._check_git_updates(info)
        else:
            return False, None
    
    def _check_pypi_updates(self, info: Dict) -> Tuple[bool, Optional[str]]:
        """检查PyPI更新"""
        try:
            # 获取最新版本
            response = urllib.request.urlopen('https://pypi.org/pypi/claude-code-notifier/json')
            data = json.loads(response.read())
            latest_version = data['info']['version']
            
            current_version = info.get('version', '0.0.0')
            
            # 比较版本
            if self._compare_versions(latest_version, current_version) > 0:
                return True, latest_version
            
            return False, None
        except Exception as e:
            self._log(f"检查PyPI更新失败: {e}")
            return False, None
    
    def _check_git_updates(self, info: Dict) -> Tuple[bool, Optional[str]]:
        """检查Git更新"""
        repo_path = info.get('repo_path', str(Path.home() / 'Claude-Code-Notifier'))
        
        if not Path(repo_path).exists():
            return False, None
        
        try:
            # 获取远程更新
            subprocess.run(['git', 'fetch'], cwd=repo_path, capture_output=True)
            
            # 比较本地和远程
            local = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            
            remote = subprocess.run(
                ['git', 'rev-parse', '@{u}'],
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            
            if local != remote:
                # 获取新版本标签
                tags = subprocess.run(
                    ['git', 'describe', '--tags', remote],
                    cwd=repo_path, capture_output=True, text=True
                ).stdout.strip()
                return True, tags
            
            return False, None
        except Exception as e:
            self._log(f"检查Git更新失败: {e}")
            return False, None
    
    def perform_update(self, auto: bool = False) -> bool:
        """执行更新"""
        info = self.get_installation_info()
        
        has_update, new_version = self.check_for_updates()
        
        if not has_update:
            print("✅ 已是最新版本")
            return True
        
        print(f"🔔 发现新版本: {new_version}")
        
        if not auto:
            response = input("是否立即更新? [Y/n]: ")
            if response.lower() == 'n':
                print("更新已取消")
                return False
        
        if info['type'] == 'pypi':
            return self._update_pypi(new_version)
        elif info['type'] == 'git':
            return self._update_git(info, new_version)
        else:
            print("❌ 未知的安装类型")
            return False
    
    def _update_pypi(self, new_version: str) -> bool:
        """更新PyPI版本"""
        print(f"📦 更新到 PyPI 版本 {new_version}...")
        
        try:
            # 执行pip更新
            result = subprocess.run(
                ['pip3', 'install', '--upgrade', 'claude-code-notifier'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # 更新版本文件
                self._update_version_info('pypi', new_version)
                print(f"✅ 成功更新到版本 {new_version}")
                self._log(f"更新到PyPI版本 {new_version}")
                return True
            else:
                print(f"❌ 更新失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False
    
    def _update_git(self, info: Dict, new_version: str) -> bool:
        """更新Git版本"""
        repo_path = info.get('repo_path')
        
        if not repo_path:
            print("❌ Git仓库路径未找到")
            return False
        
        print(f"🔧 更新Git版本到 {new_version}...")
        
        try:
            # 拉取更新
            subprocess.run(['git', 'pull'], cwd=repo_path, check=True)
            
            # 重新安装
            subprocess.run(['pip3', 'install', '-e', '.'], cwd=repo_path, check=True)
            
            # 更新版本文件
            self._update_version_info('git', new_version)
            print(f"✅ 成功更新到版本 {new_version}")
            self._log(f"更新到Git版本 {new_version}")
            return True
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False
    
    def setup_auto_update(self, enabled: bool = True, check_interval: int = 86400):
        """设置自动更新"""
        state = {
            'enabled': enabled,
            'check_interval': check_interval,
            'last_check': None,
            'auto_install': False
        }
        
        if self.update_state.exists():
            with open(self.update_state) as f:
                existing = json.load(f)
                state.update(existing)
        
        state['enabled'] = enabled
        
        with open(self.update_state, 'w') as f:
            json.dump(state, f, indent=2)
        
        if enabled:
            self._setup_cron_job(check_interval)
            print(f"✅ 自动更新已启用（检查间隔: {check_interval}秒）")
        else:
            self._remove_cron_job()
            print("❌ 自动更新已禁用")
    
    def _setup_cron_job(self, interval: int):
        """设置定时任务"""
        script_path = Path(__file__).absolute()
        
        # 创建cron表达式
        if interval <= 3600:  # 每小时
            cron_expr = "0 * * * *"
        elif interval <= 86400:  # 每天
            cron_expr = "0 10 * * *"
        else:  # 每周
            cron_expr = "0 10 * * 1"
        
        # 添加到crontab
        try:
            # 获取现有crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            existing_cron = result.stdout if result.returncode == 0 else ""
            
            # 移除旧的条目
            lines = [l for l in existing_cron.split('\n') if 'smart_update.py' not in l]
            
            # 添加新条目
            lines.append(f"{cron_expr} /usr/bin/python3 {script_path} --check --auto")
            
            # 写入crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            process.communicate(input='\n'.join(lines).encode())
        except Exception as e:
            print(f"设置定时任务失败: {e}")
    
    def _remove_cron_job(self):
        """移除定时任务"""
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = [l for l in result.stdout.split('\n') if 'smart_update.py' not in l]
                process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
                process.communicate(input='\n'.join(lines).encode())
        except:
            pass
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""
        # 简单的版本比较
        def normalize(v):
            parts = v.split('.')
            return [int(x) if x.isdigit() else 0 for x in parts]
        
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    
    def _update_version_info(self, install_type: str, version: str):
        """更新版本信息"""
        info = self.get_installation_info()
        info['type'] = install_type
        info['version'] = version
        info['last_update'] = datetime.now().isoformat()
        
        with open(self.version_file, 'w') as f:
            json.dump(info, f, indent=2)
    
    def _log(self, message: str):
        """记录日志"""
        self.update_log.parent.mkdir(exist_ok=True)
        with open(self.update_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    
    def show_status(self):
        """显示更新状态"""
        info = self.get_installation_info()
        
        print("📊 Claude Notifier 更新状态")
        print("=" * 40)
        print(f"安装类型: {info.get('type', '未知')}")
        print(f"当前版本: {info.get('version', '未知')}")
        
        if info.get('last_update'):
            print(f"上次更新: {info['last_update']}")
        
        # 检查更新
        has_update, new_version = self.check_for_updates()
        if has_update:
            print(f"🔔 可用更新: {new_version}")
        else:
            print("✅ 已是最新版本")
        
        # 自动更新状态
        if self.update_state.exists():
            with open(self.update_state) as f:
                state = json.load(f)
                if state.get('enabled'):
                    print(f"⚙️ 自动更新: 已启用")
                    if state.get('last_check'):
                        print(f"上次检查: {state['last_check']}")
                else:
                    print("⚙️ 自动更新: 已禁用")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Claude Notifier 智能更新系统')
    parser.add_argument('--check', action='store_true', help='检查更新')
    parser.add_argument('--update', action='store_true', help='执行更新')
    parser.add_argument('--auto', action='store_true', help='自动确认更新')
    parser.add_argument('--enable-auto', action='store_true', help='启用自动更新')
    parser.add_argument('--disable-auto', action='store_true', help='禁用自动更新')
    parser.add_argument('--status', action='store_true', help='显示状态')
    
    args = parser.parse_args()
    
    updater = SmartUpdater()
    
    if args.enable_auto:
        updater.setup_auto_update(True)
    elif args.disable_auto:
        updater.setup_auto_update(False)
    elif args.check:
        has_update, version = updater.check_for_updates()
        if has_update:
            print(f"🔔 发现新版本: {version}")
            if args.auto:
                updater.perform_update(auto=True)
        else:
            print("✅ 已是最新版本")
    elif args.update:
        updater.perform_update(auto=args.auto)
    elif args.status:
        updater.show_status()
    else:
        updater.show_status()

if __name__ == "__main__":
    main()
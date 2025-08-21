#!/usr/bin/env python3
"""
统一安装器 - 解决双轨安装系统的问题
自动检测用户环境并提供最佳安装方案
"""

import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.request
import urllib.error

class UnifiedInstaller:
    """统一安装器系统，自动适配不同用户需求"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / '.claude-notifier'
        self.project_root = Path(__file__).parent.parent
        self.installation_mode = None
        
    def detect_environment(self) -> Dict:
        """智能环境检测"""
        env = {
            'os': platform.system().lower(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'has_git': self._command_exists('git'),
            'has_pip': self._command_exists('pip') or self._command_exists('pip3'),
            'has_venv': self._command_exists('python3') and self._can_import('venv'),
            'claude_code_detected': self._detect_claude_code(),
            'is_developer': self._detect_developer_environment(),
            'is_docker': self._detect_docker(),
            'is_ci': self._detect_ci_environment(),
            'network_available': self._check_network(),
            'pypi_accessible': self._check_pypi_access(),
            'existing_installation': self._detect_existing_installation()
        }
        return env
    
    def recommend_installation(self, env: Dict) -> str:
        """基于环境智能推荐安装方式"""
        # CI/CD环境 - 使用PyPI
        if env['is_ci']:
            return 'pypi-ci'
        
        # Docker环境 - 轻量级安装
        if env['is_docker']:
            return 'docker-optimized'
        
        # 开发者环境 - 可编辑安装
        if env['is_developer'] and env['has_git']:
            return 'developer-editable'
        
        # 已有安装 - 升级模式
        if env['existing_installation']:
            return 'upgrade-smart'
        
        # 网络受限 - 离线安装
        if not env['network_available']:
            return 'offline-bundle'
        
        # 普通用户 - PyPI标准安装
        if env['pypi_accessible']:
            return 'pypi-standard'
        
        # 备用方案 - Git轻量级
        if env['has_git']:
            return 'git-minimal'
        
        # 最终备用 - 手动安装
        return 'manual-guided'
    
    def execute_installation(self, mode: str, env: Dict) -> bool:
        """执行安装策略"""
        strategies = {
            'pypi-ci': self._install_pypi_ci,
            'docker-optimized': self._install_docker,
            'developer-editable': self._install_developer,
            'upgrade-smart': self._upgrade_existing,
            'offline-bundle': self._install_offline,
            'pypi-standard': self._install_pypi_standard,
            'git-minimal': self._install_git_minimal,
            'manual-guided': self._install_manual
        }
        
        strategy = strategies.get(mode, self._install_manual)
        return strategy(env)
    
    def _install_developer(self, env: Dict) -> bool:
        """开发者模式安装 - 可编辑模式"""
        print("🔧 开发者模式安装")
        print("→ 使用可编辑模式 (pip install -e .)")
        
        steps = [
            ("创建虚拟环境", self._create_venv),
            ("安装开发依赖", lambda: self._run_command("pip install -e .[dev,all]")),
            ("设置Git hooks", self._setup_git_hooks),
            ("配置IDE集成", self._setup_ide_integration),
            ("创建开发配置", self._create_dev_config)
        ]
        
        return self._execute_steps(steps)
    
    def _install_pypi_standard(self, env: Dict) -> bool:
        """标准PyPI安装"""
        print("📦 标准PyPI安装")
        
        # 检查并推荐版本
        version = self._get_recommended_version()
        
        steps = [
            ("安装包", lambda: self._run_command(f"pip install claude-code-notifier=={version}")),
            ("初始化配置", self._init_config),
            ("设置自动更新", self._setup_auto_update),
            ("验证安装", self._verify_installation)
        ]
        
        return self._execute_steps(steps)
    
    def _upgrade_existing(self, env: Dict) -> bool:
        """智能升级现有安装"""
        print("🔄 智能升级模式")
        
        current = env['existing_installation']
        
        # 备份现有配置
        self._backup_config()
        
        # 检测安装类型并升级
        if current.get('type') == 'pip':
            self._run_command("pip install --upgrade claude-code-notifier")
        elif current.get('type') == 'git':
            self._run_command("git pull")
            self._run_command("pip install -e .")
        
        # 迁移配置
        self._migrate_config(current.get('version'))
        
        return True
    
    def _setup_auto_update(self) -> bool:
        """设置自动更新机制"""
        update_script = self.config_dir / 'auto_update.py'
        
        update_code = '''#!/usr/bin/env python3
"""自动更新检查器"""
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

def check_updates():
    """检查并应用更新"""
    config_file = Path.home() / '.claude-notifier' / 'update_state.json'
    
    # 读取上次检查时间
    if config_file.exists():
        with open(config_file) as f:
            state = json.load(f)
            last_check = datetime.fromisoformat(state.get('last_check', '2020-01-01'))
    else:
        last_check = datetime(2020, 1, 1)
    
    # 每天检查一次
    if datetime.now() - last_check < timedelta(days=1):
        return
    
    # 检查新版本
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True, check=True
        )
        outdated = json.loads(result.stdout)
        
        for pkg in outdated:
            if pkg['name'] == 'claude-code-notifier':
                print(f"🔔 新版本可用: {pkg['latest_version']}")
                response = input("是否立即更新? [Y/n]: ")
                if response.lower() != 'n':
                    subprocess.run(["pip", "install", "--upgrade", "claude-code-notifier"])
                break
    except Exception:
        pass
    
    # 更新检查时间
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump({'last_check': datetime.now().isoformat()}, f)

if __name__ == "__main__":
    check_updates()
'''
        
        update_script.parent.mkdir(parents=True, exist_ok=True)
        update_script.write_text(update_code)
        update_script.chmod(0o755)
        
        # 添加到shell配置
        self._add_to_shell_rc(f'python3 {update_script} 2>/dev/null &')
        
        return True
    
    def _create_unified_entry(self):
        """创建统一入口点"""
        entry_script = self.config_dir / 'unified_entry.sh'
        
        entry_code = '''#!/bin/bash
# 统一入口点 - 自动检测并选择最佳执行方式

if command -v claude-notifier &> /dev/null; then
    # PyPI安装版本
    claude-notifier "$@"
elif [ -f "$HOME/Claude-Code-Notifier/src/claude_notifier/cli/main.py" ]; then
    # Git安装版本
    python3 "$HOME/Claude-Code-Notifier/src/claude_notifier/cli/main.py" "$@"
else
    echo "❌ Claude Notifier未安装"
    echo "运行以下命令安装："
    echo "  curl -sSL https://raw.githubusercontent.com/kdush/Claude-Code-Notifier/main/install.sh | bash"
    exit 1
fi
'''
        
        entry_script.write_text(entry_code)
        entry_script.chmod(0o755)
        
        # 创建别名
        self._add_to_shell_rc(f'alias cn="{entry_script}"')
    
    # 辅助方法
    def _command_exists(self, cmd: str) -> bool:
        """检查命令是否存在"""
        return shutil.which(cmd) is not None
    
    def _can_import(self, module: str) -> bool:
        """检查模块是否可导入"""
        try:
            __import__(module)
            return True
        except ImportError:
            return False
    
    def _detect_claude_code(self) -> bool:
        """检测Claude Code环境"""
        claude_markers = [
            self.home_dir / '.config' / 'claude',
            self.home_dir / '.claude',
            Path('/usr/local/bin/claude'),
        ]
        return any(p.exists() for p in claude_markers)
    
    def _detect_developer_environment(self) -> bool:
        """检测开发者环境"""
        dev_markers = [
            '.git',
            'pyproject.toml',
            'setup.py',
            'requirements-dev.txt',
            '.vscode',
            '.idea'
        ]
        return any((self.project_root / marker).exists() for marker in dev_markers)
    
    def _detect_docker(self) -> bool:
        """检测Docker环境"""
        return Path('/.dockerenv').exists() or Path('/proc/1/cgroup').exists()
    
    def _detect_ci_environment(self) -> bool:
        """检测CI/CD环境"""
        ci_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS']
        return any(os.environ.get(var) for var in ci_vars)
    
    def _check_network(self) -> bool:
        """检查网络连接"""
        try:
            urllib.request.urlopen('https://pypi.org', timeout=5)
            return True
        except (urllib.error.URLError, TimeoutError):
            return False
    
    def _check_pypi_access(self) -> bool:
        """检查PyPI访问"""
        try:
            urllib.request.urlopen('https://pypi.org/simple/claude-code-notifier/', timeout=5)
            return True
        except (urllib.error.URLError, TimeoutError):
            # 尝试镜像
            try:
                urllib.request.urlopen('https://pypi.doubanio.com/simple/claude-code-notifier/', timeout=5)
                return True
            except:
                return False
    
    def _detect_existing_installation(self) -> Optional[Dict]:
        """检测现有安装"""
        # 检查pip安装
        try:
            result = subprocess.run(
                ["pip", "show", "claude-code-notifier"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        version = line.split(':')[1].strip()
                        return {'type': 'pip', 'version': version}
        except:
            pass
        
        # 检查Git安装
        git_install = self.home_dir / 'Claude-Code-Notifier'
        if git_install.exists():
            return {'type': 'git', 'path': str(git_install)}
        
        return None
    
    def _run_command(self, cmd: str) -> bool:
        """执行命令"""
        try:
            subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _execute_steps(self, steps: list) -> bool:
        """执行安装步骤"""
        for desc, func in steps:
            print(f"  → {desc}...")
            if not func():
                print(f"  ❌ {desc} 失败")
                return False
            print(f"  ✅ {desc} 完成")
        return True
    
    def _add_to_shell_rc(self, line: str):
        """添加到shell配置"""
        for rc_file in ['.bashrc', '.zshrc']:
            rc_path = self.home_dir / rc_file
            if rc_path.exists():
                content = rc_path.read_text()
                if line not in content:
                    with open(rc_path, 'a') as f:
                        f.write(f'\n# Claude Notifier\n{line}\n')
    
    def _get_recommended_version(self) -> str:
        """获取推荐版本"""
        try:
            # 获取最新稳定版本
            response = urllib.request.urlopen('https://pypi.org/pypi/claude-code-notifier/json')
            data = json.loads(response.read())
            return data['info']['version']
        except:
            return "0.0.3b4"  # 默认版本

def main():
    """主入口"""
    print("🚀 Claude Code Notifier 统一安装器")
    print("=" * 50)
    
    installer = UnifiedInstaller()
    
    # 环境检测
    print("\n📊 检测环境...")
    env = installer.detect_environment()
    
    # 显示环境信息
    print(f"  OS: {env['os']}")
    print(f"  Python: {env['python_version']}")
    print(f"  网络: {'✅ 可用' if env['network_available'] else '❌ 受限'}")
    print(f"  开发者模式: {'✅' if env['is_developer'] else '❌'}")
    
    if env['existing_installation']:
        print(f"  现有安装: {env['existing_installation']}")
    
    # 推荐方案
    mode = installer.recommend_installation(env)
    
    mode_descriptions = {
        'pypi-ci': 'CI/CD环境优化安装',
        'docker-optimized': 'Docker容器优化安装',
        'developer-editable': '开发者可编辑安装',
        'upgrade-smart': '智能升级现有版本',
        'offline-bundle': '离线包安装',
        'pypi-standard': '标准PyPI安装',
        'git-minimal': 'Git轻量级安装',
        'manual-guided': '手动引导安装'
    }
    
    print(f"\n🎯 推荐方案: {mode_descriptions.get(mode, mode)}")
    
    # 确认安装
    response = input("\n是否继续? [Y/n]: ")
    if response.lower() == 'n':
        print("👋 安装已取消")
        return
    
    # 执行安装
    print(f"\n🔧 执行{mode_descriptions.get(mode, mode)}...")
    success = installer.execute_installation(mode, env)
    
    if success:
        print("\n✅ 安装成功!")
        print("\n📖 快速开始:")
        print("  1. 配置通知渠道: claude-notifier init")
        print("  2. 测试通知: claude-notifier test")
        print("  3. 查看状态: claude-notifier status")
    else:
        print("\n❌ 安装失败，请查看错误信息")
        print("💡 获取帮助: https://github.com/kdush/Claude-Code-Notifier/issues")

if __name__ == "__main__":
    main()
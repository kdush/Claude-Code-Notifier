#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code钩子安装器 - PyPI版本
为PyPI用户提供自动钩子配置功能
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

class ClaudeHookInstaller:
    """Claude Code钩子安装器"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.claude_config_dir = self.home_dir / '.config' / 'claude'
        self.hooks_file = self.claude_config_dir / 'hooks.json'
        self.notifier_config_dir = self.home_dir / '.claude-notifier'
        self.logger = logging.getLogger(__name__)
        
        # 获取钩子脚本路径
        self.hook_script_path = Path(__file__).parent / 'claude_hook.py'
        
    def detect_claude_code(self) -> Tuple[bool, Optional[str]]:
        """检测Claude Code安装"""
        # 检查常见的Claude Code安装位置
        possible_locations = [
            'claude',
            'claude-code',
            '/usr/local/bin/claude',
            '/opt/homebrew/bin/claude',
            str(self.home_dir / '.local/bin/claude'),
        ]
        
        for location in possible_locations:
            if shutil.which(location):
                return True, location
        
        # 检查Claude配置目录
        if self.claude_config_dir.exists():
            return True, str(self.claude_config_dir)
        
        return False, None
    
    def backup_existing_hooks(self) -> Optional[str]:
        """备份现有钩子配置"""
        if not self.hooks_file.exists():
            return None
        
        from datetime import datetime
        backup_name = f"hooks.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.hooks_file.parent / backup_name
        
        try:
            shutil.copy2(self.hooks_file, backup_path)
            self.logger.info(f"已备份现有钩子配置到: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"备份钩子配置失败: {e}")
            return None
    
    def create_hooks_config(self) -> Dict:
        """创建钩子配置"""
        # 统一使用当前 Python 解释器，避免 Windows 上找不到 python3
        py = sys.executable
        # 如路径内包含空格或在 Windows 上，使用引号包裹
        py_quoted = f'"{py}"' if (os.name == 'nt' or ' ' in py) else py
        hook_path = str(self.hook_script_path)
        hook_quoted = f'"{hook_path}"' if (os.name == 'nt' or ' ' in hook_path) else hook_path

        # 针对不同平台处理 JSON 参数引号
        if os.name == 'nt':
            # Windows: 外层使用双引号，需对内部双引号进行反斜杠转义
            json_cmd_plain = '{"command": "$COMMAND", "tool": "$TOOL"}'
            json_status_plain = '{"status": "$STATUS"}'
            json_error_plain = '{"error_type": "$ERROR_TYPE", "error_message": "$ERROR_MESSAGE"}'
            json_message_plain = '{"message": "$MESSAGE"}'

            def _escape_win(s: str) -> str:
                # 将双引号转义为 \" 以确保在 cmd/powershell 中作为单个参数传递
                return s.replace('"', '\\"')

            cmd_session_start = f"{py_quoted} {hook_quoted} session_start"
            cmd_command_execute = f"{py_quoted} {hook_quoted} command_execute \"{_escape_win(json_cmd_plain)}\""
            cmd_task_complete = f"{py_quoted} {hook_quoted} task_complete \"{_escape_win(json_status_plain)}\""
            cmd_error = f"{py_quoted} {hook_quoted} error \"{_escape_win(json_error_plain)}\""
            cmd_confirmation = f"{py_quoted} {hook_quoted} confirmation_required \"{_escape_win(json_message_plain)}\""
        else:
            # POSIX: 使用单引号避免 shell 展开
            json_cmd_tpl = '{"command": "$COMMAND", "tool": "$TOOL"}'
            json_status_tpl = '{"status": "$STATUS"}'
            json_error_tpl = '{"error_type": "$ERROR_TYPE", "error_message": "$ERROR_MESSAGE"}'
            json_message_tpl = '{"message": "$MESSAGE"}'
            cmd_session_start = f"{py_quoted} {hook_quoted} session_start"
            cmd_command_execute = f"{py_quoted} {hook_quoted} command_execute '{json_cmd_tpl}'"
            cmd_task_complete = f"{py_quoted} {hook_quoted} task_complete '{json_status_tpl}'"
            cmd_error = f"{py_quoted} {hook_quoted} error '{json_error_tpl}'"
            cmd_confirmation = f"{py_quoted} {hook_quoted} confirmation_required '{json_message_tpl}'"

        return {
            "hooks": {
                "on_session_start": {
                    "command": cmd_session_start,
                    "enabled": True,
                    "description": "Claude Code 会话开始时触发Claude Notifier"
                },
                "on_command_execute": {
                    "command": cmd_command_execute,
                    "enabled": True,
                    "description": "执行命令时触发通知检查"
                },
                "on_task_complete": {
                    "command": cmd_task_complete,
                    "enabled": True,
                    "description": "任务完成时发送通知"
                },
                "on_error": {
                    "command": cmd_error,
                    "enabled": True,
                    "description": "发生错误时触发错误通知"
                },
                "on_confirmation_required": {
                    "command": cmd_confirmation,
                    "enabled": True,
                    "description": "需要确认时发送权限通知"
                }
            },
            "settings": {
                "log_level": "info",
                "timeout": 5000,
                "claude_notifier": {
                    "enabled": True,
                    "version": "pypi",
                    "config_dir": str(self.notifier_config_dir)
                }
            },
            "_metadata": {
                "installer": "claude-notifier-pypi",
                "installed_at": str(os.times()),
                "hook_script": str(self.hook_script_path)
            }
        }
    
    def install_hooks(self, force: bool = False) -> Tuple[bool, str]:
        """安装钩子配置"""
        try:
            # 1. 检测Claude Code
            claude_detected, claude_location = self.detect_claude_code()
            if not claude_detected:
                return False, "❌ 未检测到Claude Code安装，请先安装Claude Code"
            
            print(f"✅ 检测到Claude Code: {claude_location}")
            
            # 2. 创建配置目录
            self.claude_config_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 配置目录: {self.claude_config_dir}")
            
            # 3. 备份现有配置
            if self.hooks_file.exists() and not force:
                response = input("发现现有钩子配置，是否备份并继续? [Y/n]: ")
                if response.lower() == 'n':
                    return False, "❌ 用户取消安装"
            
            backup_path = self.backup_existing_hooks()
            if backup_path:
                print(f"📄 已备份现有配置: {backup_path}")
            
            # 4. 创建钩子配置
            hooks_config = self.create_hooks_config()
            
            # 5. 写入配置文件
            with open(self.hooks_file, 'w', encoding='utf-8') as f:
                json.dump(hooks_config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 钩子配置已安装: {self.hooks_file}")
            
            # 6. 验证配置
            if self.verify_installation():
                return True, "🎉 Claude Code钩子安装成功！"
            else:
                return False, "⚠️ 钩子配置可能存在问题"
                
        except Exception as e:
            self.logger.error(f"安装钩子失败: {e}")
            return False, f"❌ 安装失败: {str(e)}"
    
    def verify_installation(self) -> bool:
        """验证钩子安装"""
        try:
            # 检查配置文件
            if not self.hooks_file.exists():
                return False
            
            # 检查配置格式
            with open(self.hooks_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查必要的钩子
            required_hooks = ['on_session_start', 'on_command_execute', 'on_task_complete']
            hooks = config.get('hooks', {})
            
            for hook_name in required_hooks:
                if hook_name not in hooks:
                    self.logger.error(f"缺少必要钩子: {hook_name}")
                    return False
                
                if not hooks[hook_name].get('enabled', False):
                    self.logger.warning(f"钩子未启用: {hook_name}")
            
            # 检查钩子脚本
            if not self.hook_script_path.exists():
                self.logger.error(f"钩子脚本不存在: {self.hook_script_path}")
                return False
            
            print("✅ 钩子配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证钩子安装失败: {e}")
            return False
    
    def uninstall_hooks(self) -> Tuple[bool, str]:
        """卸载钩子配置"""
        try:
            if not self.hooks_file.exists():
                return True, "钩子配置不存在，无需卸载"
            
            # 备份现有配置
            backup_path = self.backup_existing_hooks()
            
            # 删除钩子配置
            self.hooks_file.unlink()
            
            message = "✅ Claude Code钩子已卸载"
            if backup_path:
                message += f"，配置已备份到: {backup_path}"
            
            return True, message
            
        except Exception as e:
            return False, f"❌ 卸载失败: {str(e)}"
    
    def get_installation_status(self) -> Dict:
        """获取安装状态"""
        status = {
            'claude_detected': False,
            'claude_location': None,
            'hooks_installed': False,
            'hooks_file': str(self.hooks_file),
            'hooks_valid': False,
            'hook_script_exists': self.hook_script_path.exists(),
            'enabled_hooks': []
        }
        
        # 检测Claude Code
        status['claude_detected'], status['claude_location'] = self.detect_claude_code()
        
        # 检查钩子文件
        if self.hooks_file.exists():
            status['hooks_installed'] = True
            
            try:
                with open(self.hooks_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                status['hooks_valid'] = True
                hooks = config.get('hooks', {})
                
                for hook_name, hook_config in hooks.items():
                    if hook_config.get('enabled', False):
                        status['enabled_hooks'].append(hook_name)
                        
            except Exception as e:
                status['hooks_valid'] = False
                status['error'] = str(e)
        
        return status
    
    def print_status(self):
        """打印安装状态"""
        status = self.get_installation_status()
        
        print("📊 Claude Code钩子状态")
        print("=" * 40)
        
        # Claude Code检测
        if status['claude_detected']:
            print(f"✅ Claude Code: {status['claude_location']}")
        else:
            print("❌ Claude Code: 未检测到")
        
        # 钩子脚本
        if status['hook_script_exists']:
            print(f"✅ 钩子脚本: {self.hook_script_path}")
        else:
            print(f"❌ 钩子脚本: 未找到")
        
        # 钩子配置
        if status['hooks_installed']:
            if status['hooks_valid']:
                print(f"✅ 钩子配置: {status['hooks_file']}")
                if status['enabled_hooks']:
                    print(f"🔗 已启用钩子: {', '.join(status['enabled_hooks'])}")
                else:
                    print("⚠️ 没有启用的钩子")
            else:
                print(f"❌ 钩子配置: 格式错误 - {status.get('error', '未知错误')}")
        else:
            print("❌ 钩子配置: 未安装")
        
        # 总体状态
        if (status['claude_detected'] and 
            status['hook_script_exists'] and 
            status['hooks_installed'] and 
            status['hooks_valid'] and 
            status['enabled_hooks']):
            print("\n🎉 钩子系统完全就绪！")
        else:
            print("\n⚠️ 钩子系统需要配置")
            print("运行 'claude-notifier hooks install' 进行安装")

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Code钩子安装器')
    parser.add_argument('action', choices=['install', 'uninstall', 'status', 'verify'],
                       help='操作类型')
    parser.add_argument('--force', action='store_true',
                       help='强制执行（跳过确认）')
    
    args = parser.parse_args()
    
    installer = ClaudeHookInstaller()
    
    if args.action == 'install':
        success, message = installer.install_hooks(force=args.force)
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.action == 'uninstall':
        success, message = installer.uninstall_hooks()
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        installer.print_status()
    
    elif args.action == 'verify':
        if installer.verify_installation():
            print("✅ 钩子配置验证成功")
            sys.exit(0)
        else:
            print("❌ 钩子配置验证失败")
            sys.exit(1)

if __name__ == "__main__":
    main()
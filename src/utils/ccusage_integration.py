#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ccusage 集成模块
集成 https://github.com/ryoppippi/ccusage 进行Claude使用统计
"""

import subprocess
import json
import logging
import os
from typing import Dict, Any, Optional


class CCUsageIntegration:
    """ccusage 集成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ccusage_installed = self._check_ccusage()
        
    def _check_ccusage(self) -> bool:
        """检查 ccusage 是否已安装"""
        try:
            result = subprocess.run(['ccusage', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("ccusage 已安装")
                return True
        except FileNotFoundError:
            pass
            
        self.logger.warning("ccusage 未安装，请运行: npm install -g ccusage")
        return False
        
    def install_ccusage(self) -> bool:
        """安装 ccusage（仅在用户明确选择时调用）"""
        try:
            self.logger.info("正在安装 ccusage...")
            result = subprocess.run(['npm', 'install', '-g', 'ccusage'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("ccusage 安装成功")
                self.ccusage_installed = True
                return True
            else:
                self.logger.error(f"ccusage 安装失败: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"安装 ccusage 时出错: {e}")
            return False
            
    def get_usage_stats(self, format: str = 'json') -> Optional[Dict[str, Any]]:
        """获取使用统计"""
        if not self.ccusage_installed:
            self.logger.error("ccusage 未安装")
            return None
            
        try:
            # 调用 ccusage 获取统计
            cmd = ['ccusage']
            if format == 'json':
                cmd.append('--json')
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if format == 'json':
                    return json.loads(result.stdout)
                else:
                    return {'output': result.stdout}
            else:
                self.logger.error(f"获取统计失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"调用 ccusage 时出错: {e}")
            return None
            
    def get_cost_report(self) -> Optional[str]:
        """获取成本报告"""
        if not self.ccusage_installed:
            return None
            
        try:
            result = subprocess.run(['ccusage', '--cost'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            self.logger.error(f"获取成本报告失败: {e}")
            return None
            
    def get_token_usage(self) -> Optional[Dict[str, Any]]:
        """获取Token使用情况"""
        if not self.ccusage_installed:
            return None
            
        try:
            result = subprocess.run(['ccusage', '--tokens', '--json'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            self.logger.error(f"获取Token使用情况失败: {e}")
            return None
            
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """检查限流状态"""
        stats = self.get_usage_stats('json')
        if not stats:
            return None
            
        # 从 ccusage 数据中提取限流信息
        rate_info = {
            'status': 'normal',
            'warnings': []
        }
        
        # 检查是否接近限制
        if 'rate_limits' in stats:
            limits = stats['rate_limits']
            for limit_type, data in limits.items():
                usage_percent = (data.get('current', 0) / data.get('limit', 1)) * 100
                if usage_percent >= 90:
                    rate_info['status'] = 'critical'
                    rate_info['warnings'].append(f"{limit_type}: {usage_percent:.1f}%")
                elif usage_percent >= 75:
                    if rate_info['status'] == 'normal':
                        rate_info['status'] = 'warning'
                    rate_info['warnings'].append(f"{limit_type}: {usage_percent:.1f}%")
                    
        return rate_info
        
    def format_usage_notification(self) -> str:
        """格式化使用通知"""
        stats = self.get_usage_stats('json')
        if not stats:
            return "无法获取使用统计"
            
        lines = []
        lines.append("📊 Claude 使用统计")
        lines.append("-" * 30)
        
        # Token使用
        if 'tokens' in stats:
            tokens = stats['tokens']
            lines.append(f"🎯 Token使用:")
            lines.append(f"  • 今日: {tokens.get('today', 0):,}")
            lines.append(f"  • 本周: {tokens.get('week', 0):,}")
            lines.append(f"  • 本月: {tokens.get('month', 0):,}")
            
        # 成本
        if 'cost' in stats:
            cost = stats['cost']
            lines.append(f"\n💰 成本:")
            lines.append(f"  • 今日: ${cost.get('today', 0):.2f}")
            lines.append(f"  • 本月: ${cost.get('month', 0):.2f}")
            
        # 限流状态
        rate_info = self.check_rate_limits()
        if rate_info and rate_info['warnings']:
            lines.append(f"\n⚠️ 限流警告:")
            for warning in rate_info['warnings']:
                lines.append(f"  • {warning}")
                
        return '\n'.join(lines)


def setup_ccusage_hook(install_if_missing: bool = False):
    """设置 ccusage 钩子"""
    integration = CCUsageIntegration()
    
    # 检查 ccusage 是否已安装
    if not integration.ccusage_installed:
        if install_if_missing:
            print("正在安装 ccusage...")
            if not integration.install_ccusage():
                print("❌ ccusage 安装失败，请手动安装: npm install -g ccusage")
                return False
        else:
            print("⚠️ ccusage 未安装，统计功能将不可用")
            print("如需启用统计功能，请运行: npm install -g ccusage")
            return False
            
    # 创建钩子脚本
    hook_script = """#!/bin/bash
# Claude Code Notifier - ccusage 集成钩子

# 记录Claude使用
ccusage track "$@"

# 检查限流
python3 -c "
from src.utils.ccusage_integration import CCUsageIntegration
from src.managers.event_manager import EventManager
from src.config_manager import ConfigManager

integration = CCUsageIntegration()
rate_info = integration.check_rate_limits()

if rate_info and rate_info['status'] in ['warning', 'critical']:
    # 触发限流警告事件
    config = ConfigManager().get_config()
    manager = EventManager(config)
    
    context = {
        'event_type': 'rate_limit',
        'rate_status': rate_info['status'],
        'warnings': rate_info['warnings'],
        'usage_report': integration.format_usage_notification()
    }
    
    manager.process_context(context)
"
"""
    
    hook_path = os.path.expanduser('~/.claude-notifier/hooks/ccusage_hook.sh')
    os.makedirs(os.path.dirname(hook_path), exist_ok=True)
    
    with open(hook_path, 'w') as f:
        f.write(hook_script)
        
    os.chmod(hook_path, 0o755)
    print(f"✅ ccusage 钩子已创建: {hook_path}")
    
    return True


if __name__ == '__main__':
    # 测试集成
    integration = CCUsageIntegration()
    
    if not integration.ccusage_installed:
        print("请先安装 ccusage: npm install -g ccusage")
        exit(1)
        
    # 获取统计
    stats = integration.get_usage_stats()
    if stats:
        print("使用统计:")
        print(json.dumps(stats, indent=2))
        
    # 获取格式化通知
    notification = integration.format_usage_notification()
    print("\n" + notification)
    
    # 检查限流
    rate_info = integration.check_rate_limits()
    if rate_info:
        print(f"\n限流状态: {rate_info['status']}")
        if rate_info['warnings']:
            for warning in rate_info['warnings']:
                print(f"  ⚠️ {warning}")
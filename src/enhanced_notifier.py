#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强通知系统
支持在通知中包含统计信息
"""

import time
import logging
from typing import Dict, Any, List, Optional

from .notifier import ClaudeCodeNotifier
from .utils.ccusage_integration import CCUsageIntegration
from .utils.statistics import StatisticsManager
from .utils.time_utils import TimeManager


class EnhancedNotifier(ClaudeCodeNotifier):
    """增强的通知管理器，支持统计信息"""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        # 初始化统计组件
        self.stats_enabled = self.config.get('statistics', {}).get('enabled', False)
        self.ccusage_enabled = self.config.get('statistics', {}).get('ccusage', {}).get('enabled', False)
        self.builtin_stats_enabled = self.config.get('statistics', {}).get('builtin', {}).get('enabled', True)
        
        # 初始化统计管理器
        self.ccusage_integration = None
        self.statistics_manager = None
        self.time_manager = TimeManager()
        
        if self.stats_enabled:
            if self.ccusage_enabled:
                self.ccusage_integration = CCUsageIntegration()
                
            if self.builtin_stats_enabled:
                self.statistics_manager = StatisticsManager()
        
    def _should_include_stats_in_notification(self, event_type: str) -> bool:
        """检查是否应该在通知中包含统计信息"""
        if not self.stats_enabled:
            return False
            
        # 获取统计通知配置
        stats_config = self.config.get('statistics', {})
        
        # 检查通知类型的统计配置
        notification_configs = {
            'task_completion': stats_config.get('builtin', {}).get('reports', {}).get('completion_stats', False),
            'rate_limit': stats_config.get('ccusage', {}).get('notifications', {}).get('rate_limit_warnings', True),
            'session_start': stats_config.get('builtin', {}).get('track_sessions', True),
            'daily_summary': stats_config.get('ccusage', {}).get('notifications', {}).get('daily_summary', False),
        }
        
        # 默认规则：特定事件类型包含统计
        return notification_configs.get(event_type, False)
        
    def _get_statistics_summary(self, event_type: str = None) -> Dict[str, Any]:
        """获取统计摘要"""
        summary = {}
        
        # ccusage 统计
        if self.ccusage_integration and self.ccusage_integration.ccusage_installed:
            try:
                ccusage_stats = self.ccusage_integration.get_usage_stats('json')
                if ccusage_stats:
                    summary['ccusage'] = {
                        'tokens_today': ccusage_stats.get('tokens', {}).get('today', 0),
                        'cost_today': ccusage_stats.get('cost', {}).get('today', 0),
                        'requests_today': ccusage_stats.get('requests', {}).get('today', 0),
                        'rate_limit_status': self.ccusage_integration.check_rate_limits()
                    }
            except Exception as e:
                self.logger.warning(f"获取ccusage统计失败: {e}")
                
        # 内置统计
        if self.statistics_manager:
            try:
                builtin_stats = self.statistics_manager.get_summary(1)  # 1天统计
                summary['builtin'] = {
                    'events_today': builtin_stats.get('recent_events', 0),
                    'notifications_sent': builtin_stats.get('total_notifications', 0),
                    'success_rate': builtin_stats.get('success_rate', '100%'),
                    'sessions_today': builtin_stats.get('total_sessions', 0),
                    'most_used_channel': builtin_stats.get('most_used_channel', 'N/A')
                }
            except Exception as e:
                self.logger.warning(f"获取内置统计失败: {e}")
                
        return summary
        
    def _format_stats_for_notification(self, stats: Dict[str, Any], event_type: str) -> str:
        """格式化统计信息用于通知"""
        if not stats:
            return ""
            
        lines = []
        
        # 根据事件类型决定显示内容
        if event_type == 'task_completion':
            lines.append("\n📊 会话统计:")
            
            if 'builtin' in stats:
                builtin = stats['builtin']
                lines.append(f"  • 本次会话通知: {builtin.get('events_today', 0)}")
                lines.append(f"  • 通知成功率: {builtin.get('success_rate', 'N/A')}")
                
            if 'ccusage' in stats:
                ccusage = stats['ccusage']
                lines.append(f"  • 今日Token: {ccusage.get('tokens_today', 0):,}")
                lines.append(f"  • 今日成本: ${ccusage.get('cost_today', 0):.2f}")
                
        elif event_type == 'rate_limit':
            lines.append("\n📈 使用状态:")
            
            if 'ccusage' in stats:
                ccusage = stats['ccusage']
                rate_status = ccusage.get('rate_limit_status', {})
                if rate_status:
                    lines.append(f"  • 限流状态: {rate_status.get('status', 'unknown').upper()}")
                    
                    # 显示具体限流信息
                    if 'requests_per_minute' in rate_status:
                        rpm = rate_status['requests_per_minute']
                        lines.append(f"  • 请求/分钟: {rpm.get('current', 0)}/{rpm.get('limit', 0)}")
                        
                    if 'tokens_per_day' in rate_status:
                        tpd = rate_status['tokens_per_day']
                        lines.append(f"  • Token/天: {tpd.get('current', 0):,}/{tpd.get('limit', 0):,}")
                        
        elif event_type == 'daily_summary':
            lines.append("\n📊 今日统计:")
            
            if 'ccusage' in stats:
                ccusage = stats['ccusage']
                lines.append(f"  • Token使用: {ccusage.get('tokens_today', 0):,}")
                lines.append(f"  • 总成本: ${ccusage.get('cost_today', 0):.2f}")
                lines.append(f"  • 请求数: {ccusage.get('requests_today', 0):,}")
                
            if 'builtin' in stats:
                builtin = stats['builtin']
                lines.append(f"  • 触发事件: {builtin.get('events_today', 0)}")
                lines.append(f"  • 发送通知: {builtin.get('notifications_sent', 0)}")
                lines.append(f"  • 常用渠道: {builtin.get('most_used_channel', 'N/A')}")
                
        else:
            # 通用格式
            lines.append("\n📊 系统状态:")
            
            if 'builtin' in stats:
                builtin = stats['builtin']
                lines.append(f"  • 今日事件: {builtin.get('events_today', 0)}")
                lines.append(f"  • 通知成功率: {builtin.get('success_rate', 'N/A')}")
                
            if 'ccusage' in stats and stats['ccusage'].get('tokens_today', 0) > 0:
                ccusage = stats['ccusage']
                lines.append(f"  • Token使用: {ccusage.get('tokens_today', 0):,}")
                
        return '\n'.join(lines)
        
    def send_notification_with_stats(self, 
                                   template_data: Dict[str, Any], 
                                   event_type: str,
                                   channels: List[str] = None) -> bool:
        """发送包含统计信息的通知"""
        
        # 检查是否需要包含统计
        if self._should_include_stats_in_notification(event_type):
            stats = self._get_statistics_summary(event_type)
            stats_text = self._format_stats_for_notification(stats, event_type)
            
            if stats_text:
                # 将统计信息添加到模板数据中
                if 'message' in template_data:
                    template_data['message'] += stats_text
                elif 'status' in template_data:
                    template_data['status'] += stats_text
                elif 'content' in template_data:
                    template_data['content'] += stats_text
                else:
                    template_data['statistics'] = stats_text
                    
        # 记录统计
        if self.statistics_manager:
            self.statistics_manager.record_event(event_type, channels or [])
            
        # 发送通知
        return self._send_to_channels(template_data, event_type, channels)
        
    def _send_to_channels(self, 
                         template_data: Dict[str, Any], 
                         event_type: str,
                         channels: List[str] = None) -> bool:
        """发送到指定渠道"""
        if not channels:
            channels = self._get_enabled_channels(event_type)
            
        if not channels:
            return True  # 没有渠道配置不算失败
            
        success = True
        
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    start_time = time.time()
                    result = self.channels[channel_name].send_notification(template_data, event_type)
                    response_time = time.time() - start_time
                    
                    # 记录通知结果
                    if self.statistics_manager:
                        self.statistics_manager.record_notification(
                            channel_name, result, response_time
                        )
                        
                    if not result:
                        success = False
                        self.logger.error(f"通知发送失败: {channel_name}")
                        
                except Exception as e:
                    success = False
                    self.logger.error(f"通知发送异常 {channel_name}: {e}")
                    
                    # 记录失败
                    if self.statistics_manager:
                        self.statistics_manager.record_notification(channel_name, False)
                        
        return success
        
    def send_permission_notification(self, operation: str) -> bool:
        """发送权限确认通知（重写以支持统计）"""
        data = {
            'project': self._get_project_name(),
            'operation': operation,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.send_notification_with_stats(data, 'sensitive_operation')
        
    def send_completion_notification(self, status: str) -> bool:
        """发送任务完成通知（重写以支持统计）"""
        data = {
            'project': self._get_project_name(),
            'status': status,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.send_notification_with_stats(data, 'task_completion')
        
    def send_daily_summary(self) -> bool:
        """发送每日使用摘要"""
        if not self.stats_enabled:
            return False
            
        data = {
            'project': '系统摘要',
            'summary_type': 'daily',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.send_notification_with_stats(data, 'daily_summary')
        
    def get_stats_report(self, format: str = 'text') -> str:
        """获取统计报告"""
        if not self.stats_enabled:
            return "统计功能未启用"
            
        report_parts = []
        
        # ccusage 报告
        if self.ccusage_integration and self.ccusage_integration.ccusage_installed:
            try:
                ccusage_report = self.ccusage_integration.get_usage_stats('json')
                if ccusage_report and format == 'text':
                    report_parts.append("📊 Claude 使用统计 (ccusage):")
                    report_parts.append(self.ccusage_integration.format_usage_notification())
            except Exception as e:
                report_parts.append(f"ccusage 统计获取失败: {e}")
                
        # 内置统计报告
        if self.statistics_manager:
            try:
                builtin_report = self.statistics_manager.generate_report()
                report_parts.append(builtin_report)
            except Exception as e:
                report_parts.append(f"内置统计获取失败: {e}")
                
        return '\n\n'.join(report_parts) if report_parts else "暂无统计数据"
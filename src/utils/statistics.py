#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

class StatisticsManager:
    """统计监控管理器"""
    
    def __init__(self, stats_file: str = None):
        self.stats_file = stats_file or os.path.expanduser('~/.claude-notifier/statistics.json')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = self.load_stats()
        
    def load_stats(self) -> Dict[str, Any]:
        """加载统计数据"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}")
            
        return self.get_default_stats()
        
    def get_default_stats(self) -> Dict[str, Any]:
        """获取默认统计结构"""
        return {
            'events': {
                'total_triggered': 0,
                'by_type': defaultdict(int),
                'by_channel': defaultdict(int),
                'by_date': defaultdict(int),
                'by_hour': defaultdict(int)
            },
            'notifications': {
                'total_sent': 0,
                'total_failed': 0,
                'success_rate': 0.0,
                'by_channel': {
                    'sent': defaultdict(int),
                    'failed': defaultdict(int)
                }
            },
            'usage': {
                'sessions': 0,
                'commands_executed': 0,
                'sensitive_operations': 0,
                'errors_occurred': 0,
                'average_session_duration': 0,
                'total_active_time': 0
            },
            'rate_limits': {
                'warnings_sent': 0,
                'limits_hit': 0,
                'by_level': defaultdict(int)
            },
            'performance': {
                'average_response_time': 0,
                'max_response_time': 0,
                'min_response_time': float('inf')
            },
            'last_updated': None
        }
        
    def save_stats(self):
        """保存统计数据"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            self.stats['last_updated'] = time.time()
            
            # 转换 defaultdict 为普通 dict 以便序列化
            stats_to_save = self._convert_defaultdicts(self.stats)
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存统计数据失败: {e}")
            
    def _convert_defaultdicts(self, obj):
        """递归转换 defaultdict 为普通 dict"""
        if isinstance(obj, defaultdict):
            return dict(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_defaultdicts(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_defaultdicts(item) for item in obj]
        else:
            return obj
            
    def record_event(self, event_type: str, channels: List[str] = None):
        """记录事件触发"""
        self.stats['events']['total_triggered'] += 1
        self.stats['events']['by_type'][event_type] = \
            self.stats['events']['by_type'].get(event_type, 0) + 1
            
        # 记录日期和时间分布
        now = datetime.now()
        date_key = now.strftime('%Y-%m-%d')
        hour_key = str(now.hour)
        
        self.stats['events']['by_date'][date_key] = \
            self.stats['events']['by_date'].get(date_key, 0) + 1
        self.stats['events']['by_hour'][hour_key] = \
            self.stats['events']['by_hour'].get(hour_key, 0) + 1
            
        # 记录渠道
        if channels:
            for channel in channels:
                self.stats['events']['by_channel'][channel] = \
                    self.stats['events']['by_channel'].get(channel, 0) + 1
                    
        self.save_stats()
        
    def record_notification(self, channel: str, success: bool, response_time: float = None):
        """记录通知发送结果"""
        if success:
            self.stats['notifications']['total_sent'] += 1
            channel_sent = self.stats['notifications']['by_channel'].get('sent', {})
            channel_sent[channel] = channel_sent.get(channel, 0) + 1
            self.stats['notifications']['by_channel']['sent'] = channel_sent
        else:
            self.stats['notifications']['total_failed'] += 1
            channel_failed = self.stats['notifications']['by_channel'].get('failed', {})
            channel_failed[channel] = channel_failed.get(channel, 0) + 1
            self.stats['notifications']['by_channel']['failed'] = channel_failed
            
        # 更新成功率
        total = self.stats['notifications']['total_sent'] + self.stats['notifications']['total_failed']
        if total > 0:
            self.stats['notifications']['success_rate'] = \
                (self.stats['notifications']['total_sent'] / total) * 100
                
        # 记录响应时间
        if response_time is not None and success:
            self.update_performance_metrics(response_time)
            
        self.save_stats()
        
    def update_performance_metrics(self, response_time: float):
        """更新性能指标"""
        perf = self.stats['performance']
        
        # 更新最大最小值
        perf['max_response_time'] = max(perf.get('max_response_time', 0), response_time)
        
        min_time = perf.get('min_response_time', float('inf'))
        if min_time == float('inf'):
            perf['min_response_time'] = response_time
        else:
            perf['min_response_time'] = min(min_time, response_time)
            
        # 更新平均值（简化计算）
        avg = perf.get('average_response_time', 0)
        count = self.stats['notifications']['total_sent']
        if count > 0:
            perf['average_response_time'] = (avg * (count - 1) + response_time) / count
            
    def record_session(self, duration: int):
        """记录会话信息"""
        self.stats['usage']['sessions'] += 1
        
        # 更新平均会话时长
        sessions = self.stats['usage']['sessions']
        avg_duration = self.stats['usage'].get('average_session_duration', 0)
        self.stats['usage']['average_session_duration'] = \
            (avg_duration * (sessions - 1) + duration) / sessions
            
        # 更新总活跃时间
        self.stats['usage']['total_active_time'] = \
            self.stats['usage'].get('total_active_time', 0) + duration
            
        self.save_stats()
        
    def record_command(self, is_sensitive: bool = False):
        """记录命令执行"""
        self.stats['usage']['commands_executed'] = \
            self.stats['usage'].get('commands_executed', 0) + 1
            
        if is_sensitive:
            self.stats['usage']['sensitive_operations'] = \
                self.stats['usage'].get('sensitive_operations', 0) + 1
                
        self.save_stats()
        
    def record_error(self):
        """记录错误发生"""
        self.stats['usage']['errors_occurred'] = \
            self.stats['usage'].get('errors_occurred', 0) + 1
        self.save_stats()
        
    def record_rate_limit(self, level: str, is_warning: bool = True):
        """记录限流事件"""
        if is_warning:
            self.stats['rate_limits']['warnings_sent'] = \
                self.stats['rate_limits'].get('warnings_sent', 0) + 1
        else:
            self.stats['rate_limits']['limits_hit'] = \
                self.stats['rate_limits'].get('limits_hit', 0) + 1
                
        by_level = self.stats['rate_limits'].get('by_level', {})
        by_level[level] = by_level.get(level, 0) + 1
        self.stats['rate_limits']['by_level'] = by_level
        
        self.save_stats()
        
    def get_summary(self, period_days: int = 7) -> Dict[str, Any]:
        """获取统计摘要"""
        cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        
        # 计算期间内的事件数
        recent_events = sum(
            count for date, count in self.stats['events'].get('by_date', {}).items()
            if date >= cutoff_date
        )
        
        # 找出最活跃的时间段
        by_hour = self.stats['events'].get('by_hour', {})
        most_active_hour = max(by_hour.items(), key=lambda x: x[1])[0] if by_hour else 'N/A'
        
        # 找出最常用的渠道
        by_channel = self.stats['events'].get('by_channel', {})
        most_used_channel = max(by_channel.items(), key=lambda x: x[1])[0] if by_channel else 'N/A'
        
        summary = {
            'period_days': period_days,
            'total_events': self.stats['events']['total_triggered'],
            'recent_events': recent_events,
            'total_notifications': self.stats['notifications']['total_sent'],
            'success_rate': f"{self.stats['notifications']['success_rate']:.1f}%",
            'total_sessions': self.stats['usage']['sessions'],
            'total_commands': self.stats['usage']['commands_executed'],
            'sensitive_operations': self.stats['usage']['sensitive_operations'],
            'errors_occurred': self.stats['usage']['errors_occurred'],
            'average_session_duration': self._format_duration(
                self.stats['usage'].get('average_session_duration', 0)
            ),
            'most_active_hour': f"{most_active_hour}:00",
            'most_used_channel': most_used_channel,
            'rate_limit_warnings': self.stats['rate_limits']['warnings_sent'],
            'rate_limits_hit': self.stats['rate_limits']['limits_hit']
        }
        
        return summary
        
    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds / 60)}分钟"
        else:
            return f"{seconds / 3600:.1f}小时"
            
    def generate_report(self) -> str:
        """生成统计报告"""
        summary = self.get_summary()
        
        report = []
        report.append("=" * 50)
        report.append("📊 Claude Code Notifier 统计报告")
        report.append("=" * 50)
        report.append("")
        
        report.append(f"📅 统计周期: 最近 {summary['period_days']} 天")
        report.append("")
        
        report.append("📈 事件统计:")
        report.append(f"  • 总触发事件: {summary['total_events']}")
        report.append(f"  • 最近事件数: {summary['recent_events']}")
        report.append(f"  • 最活跃时段: {summary['most_active_hour']}")
        report.append("")
        
        report.append("📮 通知统计:")
        report.append(f"  • 发送成功: {summary['total_notifications']}")
        report.append(f"  • 成功率: {summary['success_rate']}")
        report.append(f"  • 最常用渠道: {summary['most_used_channel']}")
        report.append("")
        
        report.append("💻 使用统计:")
        report.append(f"  • 会话总数: {summary['total_sessions']}")
        report.append(f"  • 执行命令: {summary['total_commands']}")
        report.append(f"  • 敏感操作: {summary['sensitive_operations']}")
        report.append(f"  • 错误次数: {summary['errors_occurred']}")
        report.append(f"  • 平均会话时长: {summary['average_session_duration']}")
        report.append("")
        
        report.append("⚠️ 限流统计:")
        report.append(f"  • 警告次数: {summary['rate_limit_warnings']}")
        report.append(f"  • 触发限制: {summary['rate_limits_hit']}")
        report.append("")
        
        report.append("=" * 50)
        
        return '\n'.join(report)
        
    def reset_stats(self):
        """重置统计数据"""
        self.stats = self.get_default_stats()
        self.save_stats()
        self.logger.info("统计数据已重置")
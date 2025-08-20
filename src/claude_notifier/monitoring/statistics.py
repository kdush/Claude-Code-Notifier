#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统计数据收集器
从原有utils/statistics.py迁移而来，增强为支持智能功能监控
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict
from pathlib import Path
import logging


class StatisticsManager:
    """统计监控管理器 - 增强版"""
    
    def __init__(self, stats_file: Optional[str] = None, auto_save: bool = True):
        """初始化统计管理器
        
        Args:
            stats_file: 统计数据文件路径
            auto_save: 是否自动保存
        """
        if stats_file is None:
            stats_file = os.path.expanduser('~/.claude-notifier/statistics.json')
            
        self.stats_file = Path(stats_file)
        self.auto_save = auto_save
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 加载统计数据
        self.stats = self.load_stats()
        
        # 实时统计缓存
        self._realtime_cache = {
            'current_session': {
                'start_time': time.time(),
                'events_count': 0,
                'notifications_sent': 0,
                'errors_count': 0
            }
        }
        
    def load_stats(self) -> Dict[str, Any]:
        """加载统计数据"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                    
                # 升级旧格式统计数据
                return self._upgrade_stats_format(loaded_stats)
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}")
            
        return self.get_default_stats()
        
    def _upgrade_stats_format(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """升级统计数据格式到最新版本"""
        default_stats = self.get_default_stats()
        
        # 递归合并，保持新字段的默认值
        def merge_recursive(default_dict, loaded_dict):
            result = default_dict.copy()
            if not isinstance(loaded_dict, dict):
                return result
                
            for key, value in loaded_dict.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_recursive(result[key], value)
                else:
                    result[key] = value
                    
            return result
            
        return merge_recursive(default_stats, stats)
        
    def get_default_stats(self) -> Dict[str, Any]:
        """获取默认统计结构 - 增强版本"""
        return {
            'version': '1.2.0',
            'created_at': time.time(),
            'events': {
                'total_triggered': 0,
                'by_type': defaultdict(int),
                'by_channel': defaultdict(int),
                'by_date': defaultdict(int),
                'by_hour': defaultdict(int),
                'by_priority': defaultdict(int)
            },
            'notifications': {
                'total_sent': 0,
                'total_failed': 0,
                'success_rate': 0.0,
                'by_channel': {
                    'sent': defaultdict(int),
                    'failed': defaultdict(int),
                    'response_times': defaultdict(list)
                },
                'by_priority': {
                    'sent': defaultdict(int),
                    'failed': defaultdict(int)
                }
            },
            'intelligence': {
                'operation_gate': {
                    'total_allowed': 0,
                    'total_blocked': 0,
                    'total_deferred': 0,
                    'by_strategy': defaultdict(int)
                },
                'notification_throttle': {
                    'total_allowed': 0,
                    'total_blocked': 0,
                    'total_delayed': 0,
                    'duplicates_filtered': 0
                },
                'message_grouper': {
                    'groups_created': 0,
                    'messages_grouped': 0,
                    'groups_sent': 0
                },
                'cooldown_manager': {
                    'cooldowns_applied': 0,
                    'cooldowns_bypassed': 0,
                    'active_cooldowns': 0
                }
            },
            'usage': {
                'sessions': 0,
                'commands_executed': 0,
                'sensitive_operations': 0,
                'errors_occurred': 0,
                'average_session_duration': 0,
                'total_active_time': 0,
                'concurrent_operations': 0
            },
            'rate_limits': {
                'warnings_sent': 0,
                'limits_hit': 0,
                'by_level': defaultdict(int),
                'by_component': defaultdict(int)
            },
            'performance': {
                'average_response_time': 0,
                'max_response_time': 0,
                'min_response_time': float('inf'),
                'response_time_samples': 0,
                'memory_usage': defaultdict(float),
                'cpu_usage': defaultdict(float)
            },
            'health': {
                'last_health_check': None,
                'component_status': defaultdict(str),
                'error_frequency': defaultdict(int),
                'uptime_percentage': 100.0
            },
            'last_updated': None
        }
        
    def save_stats(self, force: bool = False):
        """保存统计数据"""
        if not self.auto_save and not force:
            return
            
        try:
            with self._lock:
                # 确保目录存在
                self.stats_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 更新时间戳
                self.stats['last_updated'] = time.time()
                
                # 转换 defaultdict 为普通 dict 以便序列化
                stats_to_save = self._convert_defaultdicts(self.stats)
                
                # 写入临时文件然后原子性替换
                temp_file = self.stats_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(stats_to_save, f, indent=2, ensure_ascii=False)
                    
                # 原子性替换
                temp_file.replace(self.stats_file)
                
        except Exception as e:
            self.logger.error(f"保存统计数据失败: {e}")
            
    def _convert_defaultdicts(self, obj):
        """递归转换 defaultdict 为普通 dict"""
        if isinstance(obj, defaultdict):
            return {k: self._convert_defaultdicts(v) for k, v in dict(obj).items()}
        elif isinstance(obj, dict):
            return {k: self._convert_defaultdicts(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_defaultdicts(item) for item in obj]
        else:
            return obj
            
    def record_event(self, event_type: str, channels: Optional[List[str]] = None, 
                    priority: str = 'normal', **kwargs):
        """记录事件触发"""
        with self._lock:
            self.stats['events']['total_triggered'] += 1
            self.stats['events']['by_type'][event_type] += 1
            self.stats['events']['by_priority'][priority] += 1
            
            # 记录日期和时间分布
            now = datetime.now()
            date_key = now.strftime('%Y-%m-%d')
            hour_key = str(now.hour)
            
            self.stats['events']['by_date'][date_key] += 1
            self.stats['events']['by_hour'][hour_key] += 1
                
            # 记录渠道
            if channels:
                for channel in channels:
                    self.stats['events']['by_channel'][channel] += 1
                    
            # 实时缓存更新
            self._realtime_cache['current_session']['events_count'] += 1
                    
            if self.auto_save:
                self.save_stats()
        
    def record_notification(self, channel: str, success: bool, 
                          response_time: Optional[float] = None, 
                          priority: str = 'normal'):
        """记录通知发送结果"""
        with self._lock:
            if success:
                self.stats['notifications']['total_sent'] += 1
                self.stats['notifications']['by_channel']['sent'][channel] += 1
                self.stats['notifications']['by_priority']['sent'][priority] += 1
                
                # 记录响应时间
                if response_time is not None:
                    response_times = self.stats['notifications']['by_channel']['response_times']
                    response_times[channel].append(response_time)
                    
                    # 保持响应时间列表大小
                    if len(response_times[channel]) > 100:
                        response_times[channel] = response_times[channel][-50:]
                        
                    self.update_performance_metrics(response_time)
                    
                # 实时缓存更新
                self._realtime_cache['current_session']['notifications_sent'] += 1
                
            else:
                self.stats['notifications']['total_failed'] += 1
                self.stats['notifications']['by_channel']['failed'][channel] += 1
                self.stats['notifications']['by_priority']['failed'][priority] += 1
                
                # 记录错误
                self._realtime_cache['current_session']['errors_count'] += 1
                
            # 更新成功率
            total_sent = self.stats['notifications']['total_sent']
            total_failed = self.stats['notifications']['total_failed']
            total = total_sent + total_failed
            
            if total > 0:
                self.stats['notifications']['success_rate'] = (total_sent / total) * 100
                
            if self.auto_save:
                self.save_stats()
        
    def record_intelligence_event(self, component: str, event_type: str, details: Optional[Dict[str, Any]] = None):
        """记录智能功能事件"""
        with self._lock:
            if component not in self.stats['intelligence']:
                self.stats['intelligence'][component] = defaultdict(int)
                
            comp_stats = self.stats['intelligence'][component]
            
            # 根据组件类型记录不同的事件
            if component == 'operation_gate':
                if event_type in ['allowed', 'blocked', 'deferred']:
                    comp_stats[f'total_{event_type}'] += 1
                    if details and 'strategy' in details:
                        comp_stats['by_strategy'][details['strategy']] += 1
                        
            elif component == 'notification_throttle':
                if event_type in ['allowed', 'blocked', 'delayed']:
                    comp_stats[f'total_{event_type}'] += 1
                elif event_type == 'duplicate_filtered':
                    comp_stats['duplicates_filtered'] += 1
                    
            elif component == 'message_grouper':
                if event_type in ['group_created', 'message_grouped', 'group_sent']:
                    comp_stats[event_type.replace('_', 's_')] += 1
                    
            elif component == 'cooldown_manager':
                if event_type in ['applied', 'bypassed']:
                    comp_stats[f'cooldowns_{event_type}'] += 1
                elif event_type == 'active_count':
                    if details and 'count' in details:
                        comp_stats['active_cooldowns'] = details['count']
                        
            if self.auto_save:
                self.save_stats()
        
    def update_performance_metrics(self, response_time: float):
        """更新性能指标"""
        with self._lock:
            perf = self.stats['performance']
            
            # 更新最大最小值
            perf['max_response_time'] = max(perf.get('max_response_time', 0), response_time)
            
            min_time = perf.get('min_response_time', float('inf'))
            if min_time == float('inf'):
                perf['min_response_time'] = response_time
            else:
                perf['min_response_time'] = min(min_time, response_time)
                
            # 更新平均值
            samples = perf.get('response_time_samples', 0)
            avg = perf.get('average_response_time', 0)
            
            samples += 1
            perf['response_time_samples'] = samples
            perf['average_response_time'] = (avg * (samples - 1) + response_time) / samples
        
    def record_session(self, duration: Optional[int] = None, end_session: bool = False):
        """记录会话信息"""
        with self._lock:
            if end_session:
                # 结束当前会话
                if duration is None:
                    current_session = self._realtime_cache['current_session']
                    duration = int(time.time() - current_session['start_time'])
                    
                self.stats['usage']['sessions'] += 1
                
                # 更新平均会话时长
                sessions = self.stats['usage']['sessions']
                avg_duration = self.stats['usage'].get('average_session_duration', 0)
                self.stats['usage']['average_session_duration'] = \
                    (avg_duration * (sessions - 1) + duration) / sessions
                    
                # 更新总活跃时间
                self.stats['usage']['total_active_time'] += duration
                
                # 重置实时缓存
                self._realtime_cache['current_session'] = {
                    'start_time': time.time(),
                    'events_count': 0,
                    'notifications_sent': 0,
                    'errors_count': 0
                }
                
                if self.auto_save:
                    self.save_stats()
        
    def record_command(self, command_type: Optional[str] = None, is_sensitive: bool = False):
        """记录命令执行"""
        with self._lock:
            self.stats['usage']['commands_executed'] += 1
                
            if is_sensitive:
                self.stats['usage']['sensitive_operations'] += 1
                
            if self.auto_save:
                self.save_stats()
        
    def record_error(self, error_type: Optional[str] = None, component: Optional[str] = None):
        """记录错误发生"""
        with self._lock:
            self.stats['usage']['errors_occurred'] += 1
            
            # 按组件记录错误频率
            if component:
                self.stats['health']['error_frequency'][component] += 1
                
            self._realtime_cache['current_session']['errors_count'] += 1
            
            if self.auto_save:
                self.save_stats()
        
    def record_rate_limit(self, level: str, component: str = 'global', is_warning: bool = True):
        """记录限流事件"""
        with self._lock:
            if is_warning:
                self.stats['rate_limits']['warnings_sent'] += 1
            else:
                self.stats['rate_limits']['limits_hit'] += 1
                
            self.stats['rate_limits']['by_level'][level] += 1
            self.stats['rate_limits']['by_component'][component] += 1
            
            if self.auto_save:
                self.save_stats()
        
    def update_health_status(self, component: str, status: str):
        """更新组件健康状态"""
        with self._lock:
            self.stats['health']['component_status'][component] = status
            self.stats['health']['last_health_check'] = time.time()
            
            if self.auto_save:
                self.save_stats()
        
    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时统计数据"""
        with self._lock:
            current_session = self._realtime_cache['current_session']
            session_duration = int(time.time() - current_session['start_time'])
            
            return {
                'current_session': {
                    'duration': session_duration,
                    'events_count': current_session['events_count'],
                    'notifications_sent': current_session['notifications_sent'],
                    'errors_count': current_session['errors_count'],
                    'start_time': current_session['start_time']
                },
                'intelligence_status': {
                    comp: dict(stats) for comp, stats in self.stats['intelligence'].items()
                },
                'performance': {
                    'avg_response_time': self.stats['performance'].get('average_response_time', 0),
                    'max_response_time': self.stats['performance'].get('max_response_time', 0),
                    'min_response_time': self.stats['performance'].get('min_response_time', 0)
                }
            }
        
    def get_summary(self, period_days: int = 7) -> Dict[str, Any]:
        """获取统计摘要"""
        with self._lock:
            cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            
            # 计算期间内的事件数
            by_date = dict(self.stats['events'].get('by_date', {}))
            recent_events = sum(
                count for date, count in by_date.items()
                if date >= cutoff_date
            )
            
            # 找出最活跃的时间段
            by_hour = dict(self.stats['events'].get('by_hour', {}))
            most_active_hour = max(by_hour.items(), key=lambda x: x[1])[0] if by_hour else 'N/A'
            
            # 找出最常用的渠道
            by_channel = dict(self.stats['events'].get('by_channel', {}))
            most_used_channel = max(by_channel.items(), key=lambda x: x[1])[0] if by_channel else 'N/A'
            
            # 智能功能统计
            intelligence_summary = {}
            for component, stats in self.stats['intelligence'].items():
                if isinstance(stats, dict):
                    intelligence_summary[component] = dict(stats)
                    
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
                'rate_limits_hit': self.stats['rate_limits']['limits_hit'],
                'intelligence': intelligence_summary,
                'performance': {
                    'avg_response_time': f"{self.stats['performance'].get('average_response_time', 0):.2f}ms",
                    'max_response_time': f"{self.stats['performance'].get('max_response_time', 0):.2f}ms"
                }
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
            
    def generate_report(self, include_intelligence: bool = True, 
                       include_performance: bool = True) -> str:
        """生成详细统计报告"""
        summary = self.get_summary()
        
        report = []
        report.append("=" * 60)
        report.append("📊 Claude Code Notifier 统计报告")
        report.append("=" * 60)
        report.append("")
        
        report.append(f"📅 统计周期: 最近 {summary['period_days']} 天")
        report.append(f"🕐 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 基础统计
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
        
        # 智能功能统计
        if include_intelligence and summary.get('intelligence'):
            report.append("🧠 智能功能统计:")
            for component, stats in summary['intelligence'].items():
                report.append(f"  • {component}:")
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        report.append(f"    - {key}: {value}")
            report.append("")
        
        # 性能统计
        if include_performance:
            report.append("⚡ 性能统计:")
            perf = summary.get('performance', {})
            report.append(f"  • 平均响应时间: {perf.get('avg_response_time', 'N/A')}")
            report.append(f"  • 最大响应时间: {perf.get('max_response_time', 'N/A')}")
            report.append("")
        
        report.append("⚠️ 限流统计:")
        report.append(f"  • 警告次数: {summary['rate_limit_warnings']}")
        report.append(f"  • 触发限制: {summary['rate_limits_hit']}")
        report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)
        
    def export_data(self, include_raw: bool = False) -> Dict[str, Any]:
        """导出统计数据"""
        with self._lock:
            export_data = {
                'version': '1.2.0',
                'export_time': time.time(),
                'summary': self.get_summary(),
                'realtime': self.get_realtime_stats()
            }
            
            if include_raw:
                export_data['raw_stats'] = self._convert_defaultdicts(self.stats)
                
            return export_data
        
    def reset_stats(self, backup: bool = True):
        """重置统计数据"""
        with self._lock:
            if backup and self.stats_file.exists():
                backup_file = self.stats_file.with_suffix(f'.backup.{int(time.time())}')
                self.stats_file.rename(backup_file)
                self.logger.info(f"统计数据已备份至: {backup_file}")
                
            self.stats = self.get_default_stats()
            self._realtime_cache['current_session'] = {
                'start_time': time.time(),
                'events_count': 0,
                'notifications_sent': 0,
                'errors_count': 0
            }
            
            self.save_stats(force=True)
            self.logger.info("统计数据已重置")
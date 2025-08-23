#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from typing import Dict, Any
from .base import BaseChannel

class ServerChanChannel(BaseChannel):
    """Server酱通知渠道 - 微信推送服务"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.send_key = config.get('send_key', '')
        self.api_url = config.get('api_url', 'https://sctapi.ftqq.com')
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.send_key:
            self.logger.error("Server酱 SendKey 未配置")
            return False
        return True
        
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通知"""
        try:
            # 构建请求URL
            url = f"{self.api_url}/{self.send_key}.send"
            
            # 构建通知内容
            title = self._get_title(event_type, template_data)
            content = self._build_markdown_content(template_data, event_type)
            
            # 发送请求
            payload = {
                'title': title,
                'desp': content,
                'channel': 9  # 使用企业微信应用通道，支持markdown
            }
            
            response = requests.post(url, data=payload, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                self.logger.info(f"Server酱通知发送成功: {title}")
                return True
            else:
                self.logger.error(f"Server酱通知发送失败: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Server酱通知发送异常: {e}")
            return False
            
    def _get_title(self, event_type: str, data: Dict[str, Any]) -> str:
        """获取通知标题"""
        titles = {
            'sensitive_operation': '🔐 权限确认',
            'task_completion': '✅ 任务完成',
            'rate_limit': '⚠️ 限流警告',
            'error_occurred': '❌ 错误通知',
            'session_start': '🚀 会话开始',
            'confirmation_required': '⏸️ 需要确认',
            'test': '🧪 测试通知'
        }
        
        title = titles.get(event_type, '📢 Claude Code 通知')
        project = data.get('project', '')
        
        if project:
            title = f"{title} [{project}]"
            
        return title[:32]  # Server酱标题限制32字符
        
    def _build_markdown_content(self, data: Dict[str, Any], event_type: str) -> str:
        """构建Markdown格式内容"""
        content = []
        
        # 添加时间戳
        timestamp = data.get('timestamp', '')
        if timestamp:
            content.append(f"**时间:** {timestamp}\n")
        
        # 根据事件类型构建内容
        if event_type == 'sensitive_operation':
            content.append("### ⚠️ 检测到敏感操作\n")
            content.append(f"**项目:** {data.get('project', 'Unknown')}\n")
            content.append(f"**操作:** `{data.get('operation', 'Unknown')}`\n")
            content.append("\n> Claude Code 已自动暂停执行")
            content.append("\n> 请在终端中确认是否继续")
            
        elif event_type == 'task_completion':
            content.append("### 🎉 任务已完成\n")
            content.append(f"**项目:** {data.get('project', 'Unknown')}\n")
            status = data.get('status', '任务执行完成')
            content.append(f"**状态:** {status}\n")
            content.append("\n> 工作完成，可以休息了！")
            content.append("\n> 建议检查执行结果")
            
        elif event_type == 'rate_limit':
            content.append("### ⚠️ 触发限流\n")
            content.append(f"**当前频率:** {data.get('current_rate', 'Unknown')}\n")
            content.append(f"**限制频率:** {data.get('limit_rate', 'Unknown')}\n")
            content.append("\n> 通知发送过于频繁")
            content.append("\n> 部分通知已被限流")
            
        elif event_type == 'error_occurred':
            content.append("### ❌ 发生错误\n")
            content.append(f"**错误类型:** {data.get('error_type', 'Unknown')}\n")
            content.append(f"**错误信息:** {data.get('error_message', 'Unknown')}\n")
            if data.get('traceback'):
                content.append(f"\n```\n{data.get('traceback')[:500]}\n```\n")
            content.append("\n> 请检查错误详情")
            
        elif event_type == 'session_start':
            content.append("### 🚀 会话已开始\n")
            content.append(f"**项目:** {data.get('project', 'Unknown')}\n")
            content.append(f"**用户:** {data.get('user', 'Unknown')}\n")
            content.append("\n> Claude Code 已就绪")
            
        elif event_type == 'confirmation_required':
            content.append("### ⏸️ 需要确认\n")
            content.append(f"**待确认内容:** {data.get('confirmation_message', 'Unknown')}\n")
            content.append("\n> 操作已暂停，等待确认")
            
        elif event_type == 'test':
            content.append("### 🧪 测试通知\n")
            content.append("这是一条测试通知\n")
            content.append("\n> Server酱配置正常")
            content.append("\n> 通知发送成功")
            
        else:
            # 通用格式
            content.append(f"### 📢 {event_type}\n")
            for key, value in data.items():
                if key not in ['event_id', 'event_type', 'priority', 'channels', 'rendered', 'timestamp']:
                    # 格式化键名
                    formatted_key = key.replace('_', ' ').title()
                    content.append(f"**{formatted_key}:** {value}\n")
        
        # 添加页脚
        content.append("\n---")
        content.append("\n*由 Claude Code Notifier 自动发送*")
        
        return '\n'.join(content)
        
    def supports_actions(self) -> bool:
        """是否支持交互操作"""
        return False  # Server酱不支持交互按钮
        
    def get_max_content_length(self) -> int:
        """获取最大内容长度"""
        return 10000  # Server酱支持较长内容
        
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        return self.send_notification(data, 'sensitive_operation')
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知"""
        return self.send_notification(data, 'task_completion')
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        test_data = {
            'project': data.get('project', 'Test Project'),
            'timestamp': data.get('timestamp', '2025-08-20 12:00:00')
        }
        return self.send_notification(test_data, 'test')
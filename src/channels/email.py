#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from .base import BaseChannel

class EmailChannel(BaseChannel):
    """邮箱通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get('smtp_host', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender = config.get('sender', '')
        self.password = config.get('password', '')
        self.receivers = config.get('receivers', [])
        self.use_tls = config.get('use_tls', True)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.sender:
            self.logger.error("邮箱发送者未配置")
            return False
            
        if not self.password:
            self.logger.error("邮箱密码未配置")
            return False
            
        if not self.receivers:
            self.logger.error("邮箱接收者未配置")
            return False
            
        if not self.smtp_host:
            self.logger.error("SMTP服务器未配置")
            return False
            
        return True
        
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通知"""
        try:
            # 构建邮件内容
            subject = self._get_subject(event_type, template_data)
            content = self._build_email_content(template_data, event_type)
            
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.receivers)
            
            # 添加HTML内容
            html_part = MIMEText(content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
                
            self.logger.info(f"邮件通知发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件通知发送失败: {e}")
            return False
            
    def _get_subject(self, event_type: str, data: Dict[str, Any]) -> str:
        """获取邮件主题"""
        subjects = {
            'sensitive_operation': '🔐 Claude Code 权限确认',
            'task_completion': '✅ Claude Code 任务完成',
            'rate_limit': '⚠️ Claude Code 限流警告',
            'error_occurred': '❌ Claude Code 错误通知',
            'session_start': '🚀 Claude Code 会话开始',
            'test': '🧪 Claude Code 测试通知'
        }
        return subjects.get(event_type, '📧 Claude Code 通知')
        
    def _build_email_content(self, data: Dict[str, Any], event_type: str) -> str:
        """构建邮件HTML内容"""
        # 基础样式
        style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
            .content { background: #f7f7f7; padding: 30px; border-radius: 0 0 10px 10px; }
            .info-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .button { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
        """
        
        # 构建HTML内容
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            {style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self._get_subject(event_type, data)}</h1>
                    <p>{self._get_event_description(event_type)}</p>
                </div>
                <div class="content">
        """
        
        # 添加事件特定内容
        if event_type == 'sensitive_operation':
            html += f"""
                    <div class="info-item">
                        <strong>📂 项目:</strong> {data.get('project', 'Unknown')}
                    </div>
                    <div class="info-item">
                        <strong>⚡ 操作:</strong> <code>{data.get('operation', 'Unknown')}</code>
                    </div>
                    <div class="info-item">
                        <strong>⏰ 时间:</strong> {data.get('timestamp', 'Unknown')}
                    </div>
                    <div class="info-item" style="background: #fff3cd; border-color: #ffc107;">
                        <strong>⚠️ 注意:</strong> Claude Code 已自动暂停，请在终端中确认操作
                    </div>
            """
        elif event_type == 'task_completion':
            html += f"""
                    <div class="info-item">
                        <strong>📂 项目:</strong> {data.get('project', 'Unknown')}
                    </div>
                    <div class="info-item">
                        <strong>📋 状态:</strong> {data.get('status', '任务已完成')}
                    </div>
                    <div class="info-item">
                        <strong>⏰ 完成时间:</strong> {data.get('timestamp', 'Unknown')}
                    </div>
                    <div class="info-item" style="background: #d4edda; border-color: #28a745;">
                        <strong>🎉 恭喜:</strong> 工作完成，建议休息一下或检查结果
                    </div>
            """
        else:
            # 通用格式
            for key, value in data.items():
                if key not in ['event_id', 'event_type', 'priority', 'channels', 'rendered']:
                    html += f"""
                    <div class="info-item">
                        <strong>{key}:</strong> {value}
                    </div>
                    """
        
        html += """
                </div>
                <div class="footer">
                    <p>此邮件由 Claude Code Notifier 自动发送</p>
                    <p>请勿直接回复此邮件</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def _get_event_description(self, event_type: str) -> str:
        """获取事件描述"""
        descriptions = {
            'sensitive_operation': '检测到需要确认的敏感操作',
            'task_completion': '您的任务已成功完成',
            'rate_limit': '触发了通知频率限制',
            'error_occurred': '发生了需要关注的错误',
            'session_start': '新的工作会话已开始',
            'test': '这是一条测试通知'
        }
        return descriptions.get(event_type, 'Claude Code 通知')
        
    def supports_actions(self) -> bool:
        """是否支持交互操作"""
        return False  # 邮件不支持直接交互
        
    def get_max_content_length(self) -> int:
        """获取最大内容长度"""
        return 50000  # 邮件内容可以很长
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        test_data = {
            'project': data.get('project', 'Test Project'),
            'timestamp': data.get('timestamp', '2025-08-20 12:00:00'),
            'message': '这是一条测试通知，确认邮件配置正常工作'
        }
        return self.send_notification(test_data, 'test')
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webhook 通知渠道
通用 HTTP 回调机制，支持发送到任意 HTTP 端点
"""

import json
import time
import base64
import hashlib
from typing import Dict, Any, Optional, Union, Tuple
from urllib.parse import urlparse
from datetime import datetime, timezone

# 可选依赖处理
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .base import BaseChannel


class WebhookAuthManager:
    """Webhook 认证管理器"""
    
    @staticmethod
    def apply_auth(headers: Dict[str, str], auth_config: Dict[str, Any]) -> Dict[str, str]:
        """应用认证配置到请求头
        
        Args:
            headers: 现有请求头
            auth_config: 认证配置
            
        Returns:
            更新后的请求头
        """
        auth_type = auth_config.get('type', 'none').lower()
        headers = headers.copy()
        
        if auth_type == 'bearer':
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
                
        elif auth_type == 'basic':
            username = auth_config.get('username', '')
            password = auth_config.get('password', '')
            if username or password:
                credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
                
        elif auth_type == 'api_key':
            key_name = auth_config.get('key_name', 'X-API-Key')
            key_value = auth_config.get('key_value')
            if key_value:
                headers[key_name] = key_value
                
        elif auth_type == 'custom':
            custom_headers = auth_config.get('headers', {})
            headers.update(custom_headers)
            
        return headers


class WebhookMessageFormatter:
    """Webhook 消息格式化器"""
    
    def __init__(self, format_config: Dict[str, Any]):
        """初始化格式化器
        
        Args:
            format_config: 格式化配置
        """
        self.template = format_config.get('template', 'default')
        self.include_metadata = format_config.get('include_metadata', True)
        self.timestamp_format = format_config.get('timestamp_format', 'iso')
        
    def format_message(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """格式化消息
        
        Args:
            data: 原始消息数据
            event_type: 事件类型
            
        Returns:
            格式化后的消息
        """
        if self.template == 'slack':
            return self._format_slack_message(data, event_type)
        elif self.template == 'discord':
            return self._format_discord_message(data, event_type)
        elif self.template == 'custom':
            return self._format_custom_message(data, event_type)
        else:
            return self._format_default_message(data, event_type)
            
    def _format_default_message(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """默认消息格式"""
        message = {
            'event_type': event_type,
            'timestamp': self._format_timestamp(),
            'title': data.get('title', '通知'),
            'message': data.get('content', data.get('message', '')),
            'priority': data.get('priority', 'normal')
        }
        
        if self.include_metadata:
            metadata = {}
            for key in ['project', 'operation', 'status', 'source']:
                if key in data:
                    metadata[key] = data[key]
            
            if metadata:
                message['metadata'] = metadata
                
        return message
        
    def _format_slack_message(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Slack 兼容格式"""
        # 事件类型对应的颜色和图标
        event_styles = {
            'completion': {'color': 'good', 'icon': '✅'},
            'error': {'color': 'danger', 'icon': '❌'},
            'permission': {'color': 'warning', 'icon': '🔐'},
            'test': {'color': '#36a64f', 'icon': '🧪'},
            'rate_limit': {'color': 'warning', 'icon': '⚠️'},
            'generic': {'color': '#2eb886', 'icon': '📢'}
        }
        
        style = event_styles.get(event_type, event_styles['generic'])
        title = data.get('title', '通知')
        content = data.get('content', data.get('message', ''))
        
        message = {
            'text': f"{style['icon']} {title}",
            'attachments': [{
                'color': style['color'],
                'title': content,
                'ts': int(time.time())
            }]
        }
        
        # 添加字段
        fields = []
        for key, label in [('project', '项目'), ('operation', '操作'), ('status', '状态')]:
            if key in data:
                fields.append({
                    'title': label,
                    'value': str(data[key]),
                    'short': True
                })
                
        if fields:
            message['attachments'][0]['fields'] = fields
            
        return message
        
    def _format_discord_message(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Discord 兼容格式"""
        # Discord 颜色代码（十进制）
        event_colors = {
            'completion': 3066993,    # 绿色
            'error': 15158332,        # 红色
            'permission': 16776960,   # 黄色
            'test': 3447003,          # 蓝色
            'rate_limit': 16753920,   # 橙色
            'generic': 2895667        # 深蓝色
        }
        
        title = data.get('title', '通知')
        content = data.get('content', data.get('message', ''))
        color = event_colors.get(event_type, event_colors['generic'])
        
        embed = {
            'title': title,
            'description': content,
            'color': color,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 添加字段
        fields = []
        for key, name in [('project', '项目'), ('operation', '操作'), ('status', '状态')]:
            if key in data:
                fields.append({
                    'name': name,
                    'value': str(data[key]),
                    'inline': True
                })
                
        if fields:
            embed['fields'] = fields
            
        return {'embeds': [embed]}
        
    def _format_custom_message(self, data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """自定义格式（直接返回原始数据）"""
        return data
        
    def _format_timestamp(self) -> str:
        """格式化时间戳"""
        now = datetime.now(timezone.utc)
        
        if self.timestamp_format == 'unix':
            return str(int(now.timestamp()))
        elif self.timestamp_format == 'rfc3339':
            return now.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:  # iso
            return now.isoformat()


class WebhookRetryHandler:
    """Webhook 重试处理器"""
    
    def __init__(self, retry_count: int = 3, retry_delay: float = 2.0):
        """初始化重试处理器
        
        Args:
            retry_count: 重试次数
            retry_delay: 基础重试延迟（秒）
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
    def should_retry(self, response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """判断是否应该重试
        
        Args:
            response: HTTP 响应对象
            exception: 异常对象
            
        Returns:
            是否应该重试
        """
        # 网络异常总是重试
        if exception:
            return True
            
        # HTTP 状态码判断
        if response:
            # 5xx 服务器错误重试
            if 500 <= response.status_code < 600:
                return True
            # 429 限流重试
            if response.status_code == 429:
                return True
            # 408 请求超时重试
            if response.status_code == 408:
                return True
                
        return False
        
    def get_retry_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避）
        
        Args:
            attempt: 当前重试次数（从1开始）
            
        Returns:
            延迟时间（秒）
        """
        return self.retry_delay * (2 ** (attempt - 1))


class WebhookChannel(BaseChannel):
    """Webhook 通知渠道"""
    
    # 渠道元信息
    DISPLAY_NAME = "Webhook"
    DESCRIPTION = "通用 HTTP 回调通知，支持发送到任意 HTTP 端点"
    REQUIRED_CONFIG = ["url"]
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 Webhook 渠道
        
        Args:
            config: Webhook 配置字典
        """
        super().__init__(config)
        self.url = config.get('url', '')
        self.method = config.get('method', 'POST').upper()
        self.content_type = config.get('content_type', 'application/json')
        self.timeout = config.get('timeout', 30)
        
        # 认证配置
        self.auth_config = config.get('auth', {})
        self.auth_manager = WebhookAuthManager()
        
        # 消息格式配置
        format_config = config.get('message_format', {})
        self.message_formatter = WebhookMessageFormatter(format_config)
        
        # 重试配置
        retry_count = config.get('retry_count', 3)
        retry_delay = config.get('retry_delay', 2.0)
        self.retry_handler = WebhookRetryHandler(retry_count, retry_delay)
        
        # 安全配置
        self.security_config = config.get('security', {})
        self.verify_ssl = self.security_config.get('verify_ssl', True)
        self.allow_redirects = self.security_config.get('allow_redirects', False)
        self.max_content_length = self.security_config.get('max_content_length', 1048576)  # 1MB
        
        # 自定义Headers
        self.custom_headers = config.get('headers', {})
        
    def validate_config(self) -> bool:
        """验证 Webhook 配置
        
        Returns:
            配置是否有效
        """
        if not REQUESTS_AVAILABLE:
            self.logger.error("Webhook 渠道需要 requests 库: pip install requests")
            return False
            
        if not self.url:
            self.logger.error("Webhook URL 未配置")
            return False
            
        # 验证 URL 格式
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                self.logger.error("Webhook URL 格式不正确")
                return False
        except Exception as e:
            self.logger.error(f"Webhook URL 解析失败: {e}")
            return False
            
        # 验证 HTTP 方法
        valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        if self.method not in valid_methods:
            self.logger.error(f"不支持的 HTTP 方法: {self.method}")
            return False
            
        # 验证内容类型
        valid_content_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'text/plain',
            'application/xml',
            'text/xml'
        ]
        if self.content_type not in valid_content_types:
            self.logger.warning(f"非标准内容类型: {self.content_type}")
            
        return True
        
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送 Webhook 通知
        
        Args:
            template_data: 模板数据
            event_type: 事件类型
            
        Returns:
            发送是否成功
        """
        if not self.is_enabled():
            return False
            
        if not self.validate_config():
            return False
            
        try:
            # 格式化消息
            formatted_data = self.format_message_for_channel(template_data)
            message = self.message_formatter.format_message(formatted_data, event_type)
            
            # 发送请求（带重试）
            return self._send_with_retry(message)
            
        except Exception as e:
            self.logger.error(f"Webhook 通知处理异常: {e}")
            return False
            
    def _send_with_retry(self, message: Dict[str, Any]) -> bool:
        """带重试机制的发送
        
        Args:
            message: 消息内容
            
        Returns:
            发送是否成功
        """
        last_exception = None
        last_response = None
        
        for attempt in range(self.retry_handler.retry_count + 1):
            try:
                response = self._send_request(message)
                
                # 检查响应
                if self._is_success_response(response):
                    if attempt > 0:
                        self.logger.info(f"Webhook 重试成功，尝试次数: {attempt + 1}")
                    return True
                    
                last_response = response
                
                # 判断是否需要重试
                if attempt < self.retry_handler.retry_count:
                    if self.retry_handler.should_retry(response, None):
                        delay = self.retry_handler.get_retry_delay(attempt + 1)
                        self.logger.warning(
                            f"Webhook 请求失败 (状态码: {response.status_code}), "
                            f"{delay}秒后重试..."
                        )
                        time.sleep(delay)
                        continue
                        
                # 不需要重试或已达到最大重试次数
                self.logger.error(f"Webhook 发送失败: HTTP {response.status_code}")
                return False
                
            except Exception as e:
                last_exception = e
                
                # 判断是否需要重试
                if attempt < self.retry_handler.retry_count:
                    if self.retry_handler.should_retry(None, e):
                        delay = self.retry_handler.get_retry_delay(attempt + 1)
                        self.logger.warning(f"Webhook 请求异常: {e}, {delay}秒后重试...")
                        time.sleep(delay)
                        continue
                        
                # 不需要重试或已达到最大重试次数
                self.logger.error(f"Webhook 发送异常: {e}")
                return False
                
        return False
        
    def _send_request(self, message: Dict[str, Any]) -> requests.Response:
        """发送 HTTP 请求
        
        Args:
            message: 消息内容
            
        Returns:
            HTTP 响应对象
        """
        # 构建请求头
        headers = {
            'Content-Type': self.content_type,
            'User-Agent': 'Claude-Code-Notifier/1.0'
        }
        
        # 添加自定义Headers
        headers.update(self.custom_headers)
        
        # 应用认证
        headers = self.auth_manager.apply_auth(headers, self.auth_config)
        
        # 准备请求体
        if self.content_type == 'application/json':
            data = json.dumps(message, ensure_ascii=False)
        elif self.content_type == 'application/x-www-form-urlencoded':
            data = self._dict_to_form_data(message)
        else:
            # 其他格式直接转换为字符串
            data = str(message) if not isinstance(message, str) else message
            
        # 检查内容长度
        if len(data.encode('utf-8')) > self.max_content_length:
            raise ValueError(f"消息内容过长: {len(data)} 字节，最大允许: {self.max_content_length} 字节")
            
        # 发送请求
        response = requests.request(
            method=self.method,
            url=self.url,
            headers=headers,
            data=data,
            timeout=self.timeout,
            verify=self.verify_ssl,
            allow_redirects=self.allow_redirects
        )
        
        return response
        
    def _dict_to_form_data(self, data: Dict[str, Any]) -> str:
        """将字典转换为表单数据
        
        Args:
            data: 字典数据
            
        Returns:
            表单数据字符串
        """
        from urllib.parse import urlencode
        
        # 扁平化嵌套字典
        flat_data = {}
        
        def flatten(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}.{key}" if prefix else key
                    flatten(value, new_key)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{prefix}.{i}" if prefix else str(i)
                    flatten(value, new_key)
            else:
                flat_data[prefix] = str(obj)
                
        flatten(data)
        return urlencode(flat_data)
        
    def _is_success_response(self, response: requests.Response) -> bool:
        """判断响应是否成功
        
        Args:
            response: HTTP 响应对象
            
        Returns:
            是否成功
        """
        # 2xx 状态码为成功
        return 200 <= response.status_code < 300
        
    def get_max_content_length(self) -> int:
        """获取最大内容长度
        
        Returns:
            最大内容长度
        """
        return self.max_content_length
        
    def supports_rich_content(self) -> bool:
        """支持富文本内容
        
        Returns:
            是否支持富文本
        """
        return self.content_type == 'application/json'
        
    def supports_actions(self) -> bool:
        """支持交互按钮（取决于目标服务）
        
        Returns:
            是否支持交互按钮
        """
        # Slack 和 Discord 格式支持按钮
        template = self.message_formatter.template
        return template in ['slack', 'discord']
        
    def get_channel_info(self) -> Dict[str, Any]:
        """获取渠道信息
        
        Returns:
            渠道信息字典
        """
        info = super().get_channel_info()
        info.update({
            'url': self.url,
            'method': self.method,
            'content_type': self.content_type,
            'template': self.message_formatter.template,
            'retry_count': self.retry_handler.retry_count,
            'auth_type': self.auth_config.get('type', 'none')
        })
        return info
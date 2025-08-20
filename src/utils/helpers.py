#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import hmac
import base64
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

def generate_signature(secret: str, timestamp: str, content: str = "") -> str:
    """生成签名（用于钉钉、飞书等）"""
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign

def get_current_timestamp() -> str:
    """获取当前时间戳（毫秒）"""
    return str(int(time.time() * 1000))

def format_timestamp(timestamp: Optional[float] = None) -> str:
    """格式化时间戳为可读格式"""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def escape_markdown(text: str) -> str:
    """转义Markdown特殊字符"""
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def parse_command_output(output: str) -> Dict[str, Any]:
    """解析命令输出，提取关键信息"""
    result = {
        'has_error': False,
        'error_lines': [],
        'warning_lines': [],
        'info_lines': [],
        'summary': ''
    }
    
    lines = output.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'error' in line_lower or 'failed' in line_lower:
            result['has_error'] = True
            result['error_lines'].append(line)
        elif 'warning' in line_lower or 'warn' in line_lower:
            result['warning_lines'].append(line)
        else:
            result['info_lines'].append(line)
    
    # 生成摘要
    if result['has_error']:
        result['summary'] = f"发现 {len(result['error_lines'])} 个错误"
    elif result['warning_lines']:
        result['summary'] = f"发现 {len(result['warning_lines'])} 个警告"
    else:
        result['summary'] = "执行成功"
    
    return result

def is_sensitive_operation(command: str) -> bool:
    """检查是否为敏感操作"""
    sensitive_patterns = [
        r'\bsudo\b',
        r'\brm\s+-rf?\b',
        r'\bchmod\s+[0-7]{3}',
        r'\bgit\s+push\b',
        r'\bnpm\s+publish\b',
        r'\bdocker\s+(push|rm|stop)',
        r'\bkubectl\s+(delete|apply)',
        r'\b(DROP|DELETE|TRUNCATE)\s+',
        r'\bshutdown\b',
        r'\breboot\b',
        r'\b(kill|killall)\b',
        r'\bformat\b',
        r'\bdd\s+if=',
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def calculate_idle_time(last_activity: float, idle_threshold: int = 300) -> Optional[int]:
    """计算空闲时间（秒）"""
    current_time = time.time()
    idle_time = current_time - last_activity
    
    if idle_time >= idle_threshold:
        return int(idle_time)
    return None

def check_rate_limit_status(usage_count: int, limit: int, window_minutes: int = 60) -> Dict[str, Any]:
    """检查Claude使用限流状态"""
    usage_percentage = (usage_count / limit) * 100 if limit > 0 else 0
    
    status = {
        'current_usage': usage_count,
        'limit': limit,
        'percentage': usage_percentage,
        'remaining': max(0, limit - usage_count),
        'window_minutes': window_minutes,
        'is_limited': usage_count >= limit,
        'warning_level': 'normal'
    }
    
    # 设置警告级别
    if usage_percentage >= 100:
        status['warning_level'] = 'critical'
    elif usage_percentage >= 90:
        status['warning_level'] = 'high'
    elif usage_percentage >= 75:
        status['warning_level'] = 'medium'
    elif usage_percentage >= 50:
        status['warning_level'] = 'low'
    
    return status


def validate_webhook_url(url: str) -> bool:
    """验证Webhook URL格式"""
    webhook_patterns = [
        r'^https://oapi\.dingtalk\.com/robot/send',  # 钉钉
        r'^https://open\.feishu\.cn/open-apis/bot',  # 飞书
        r'^https://qyapi\.weixin\.qq\.com/cgi-bin/webhook',  # 企业微信
        r'^https://hooks\.slack\.com/services/',  # Slack
        r'^https://.*\.webhook\.office\.com/',  # Teams
    ]
    
    for pattern in webhook_patterns:
        if re.match(pattern, url):
            return True
    
    # 通用HTTPS URL检查
    return url.startswith('https://')


def get_project_info(project_path: str) -> Dict[str, Any]:
    """获取项目信息"""
    import os
    
    info = {
        'name': os.path.basename(project_path),
        'path': project_path,
        'type': 'unknown',
        'language': 'unknown',
        'framework': None
    }
    
    # 检测项目类型
    if os.path.exists(os.path.join(project_path, 'package.json')):
        info['type'] = 'node'
        info['language'] = 'javascript'
        # 尝试读取package.json获取更多信息
        try:
            with open(os.path.join(project_path, 'package.json'), 'r') as f:
                pkg = json.load(f)
                info['name'] = pkg.get('name', info['name'])
                # 检测框架
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'react' in deps:
                    info['framework'] = 'react'
                elif 'vue' in deps:
                    info['framework'] = 'vue'
                elif 'angular' in deps:
                    info['framework'] = 'angular'
                elif 'express' in deps:
                    info['framework'] = 'express'
        except:
            pass
    
    elif os.path.exists(os.path.join(project_path, 'requirements.txt')) or \
         os.path.exists(os.path.join(project_path, 'setup.py')):
        info['type'] = 'python'
        info['language'] = 'python'
        # 检测框架
        try:
            req_file = os.path.join(project_path, 'requirements.txt')
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    requirements = f.read().lower()
                    if 'django' in requirements:
                        info['framework'] = 'django'
                    elif 'flask' in requirements:
                        info['framework'] = 'flask'
                    elif 'fastapi' in requirements:
                        info['framework'] = 'fastapi'
        except:
            pass
    
    elif os.path.exists(os.path.join(project_path, 'go.mod')):
        info['type'] = 'go'
        info['language'] = 'go'
    
    elif os.path.exists(os.path.join(project_path, 'Cargo.toml')):
        info['type'] = 'rust'
        info['language'] = 'rust'
    
    return info
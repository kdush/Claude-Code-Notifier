#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具函数
从原有utils/helpers.py迁移而来，适配新架构
"""

import os
import re
import time
import json
import hashlib
import hmac
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


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


def format_duration(seconds: int) -> str:
    """格式化持续时间为可读格式"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒" if secs > 0 else f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{hours}小时"


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


def sanitize_for_notification(text: str, max_length: int = 1000) -> str:
    """清理文本用于通知发送"""
    if not isinstance(text, str):
        text = str(text)
        
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 截断过长的文本
    text = truncate_text(text, max_length)
    
    return text


def validate_webhook_url(url: str) -> bool:
    """验证webhook URL的有效性"""
    if not url or not isinstance(url, str):
        return False
        
    try:
        parsed = urlparse(url)
        return all([
            parsed.scheme in ('http', 'https'),
            parsed.netloc,
            not any(suspicious in url.lower() for suspicious in [
                'localhost', '127.0.0.1', '0.0.0.0', 'internal'
            ])
        ])
    except Exception:
        return False


def is_sensitive_operation(operation: str) -> bool:
    """判断是否为敏感操作"""
    if not operation:
        return False
        
    operation_lower = operation.lower()
    
    # 危险操作模式
    dangerous_patterns = [
        r'rm\s+-rf',
        r'sudo\s+rm',
        r'delete\s+from.*where',
        r'drop\s+table',
        r'truncate\s+table',
        r'git\s+push\s+--force',
        r'npm\s+publish',
        r'docker\s+rm.*-f',
        r'systemctl\s+stop',
        r'kill\s+-9',
        r'chmod\s+777',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, operation_lower):
            return True
            
    return False


def get_project_info(project_path: Optional[str] = None) -> Dict[str, Any]:
    """获取项目信息"""
    if project_path is None:
        project_path = os.getcwd()
        
    project_path = Path(project_path)
    
    info = {
        'name': project_path.name,
        'path': str(project_path),
        'is_git_repo': (project_path / '.git').exists(),
        'has_package_json': (project_path / 'package.json').exists(),
        'has_requirements_txt': (project_path / 'requirements.txt').exists(),
        'has_pyproject_toml': (project_path / 'pyproject.toml').exists(),
    }
    
    # 获取git信息
    if info['is_git_repo']:
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                info['git_branch'] = result.stdout.strip()
        except Exception:
            pass
            
    # 获取包信息
    if info['has_package_json']:
        try:
            with open(project_path / 'package.json', 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                info['package_name'] = package_data.get('name')
                info['package_version'] = package_data.get('version')
        except Exception:
            pass
            
    return info


def merge_dict_recursive(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并字典"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dict_recursive(result[key], value)
            else:
                result[key] = value
        else:
            result[key] = value
            
    return result


def parse_command_output(output: str) -> Dict[str, Any]:
    """解析命令输出，提取关键信息"""
    if not output:
        return {'has_content': False}
        
    lines = output.strip().split('\n')
    
    result = {
        'has_content': True,
        'line_count': len(lines),
        'has_error': False,
        'error_lines': [],
        'warning_lines': [],
        'success_indicators': [],
    }
    
    # 分析每一行
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # 错误指示器
        if any(indicator in line_lower for indicator in ['error', 'failed', 'exception', 'traceback']):
            result['has_error'] = True
            result['error_lines'].append((i + 1, line))
            
        # 警告指示器  
        elif any(indicator in line_lower for indicator in ['warning', 'warn', 'deprecated']):
            result['warning_lines'].append((i + 1, line))
            
        # 成功指示器
        elif any(indicator in line_lower for indicator in ['success', 'completed', 'done', '✅', 'ok']):
            result['success_indicators'].append((i + 1, line))
            
    return result


def calculate_content_hash(content: Union[str, Dict[str, Any]]) -> str:
    """计算内容哈希值"""
    if isinstance(content, dict):
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
    else:
        content_str = str(content)
        
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:8]


def extract_error_summary(error_text: str, max_lines: int = 5) -> str:
    """提取错误摘要"""
    if not error_text:
        return "无错误信息"
        
    lines = error_text.strip().split('\n')
    
    # 查找关键错误行
    key_lines = []
    for line in lines:
        line_clean = line.strip()
        if any(keyword in line_clean.lower() for keyword in [
            'error', 'exception', 'failed', 'traceback', 'raised'
        ]):
            key_lines.append(line_clean)
            
    if key_lines:
        return '\n'.join(key_lines[:max_lines])
    else:
        # 返回最后几行
        return '\n'.join(lines[-max_lines:])


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def is_text_file(filename: str) -> bool:
    """判断是否为文本文件"""
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml',
        '.xml', '.html', '.css', '.sh', '.bat', '.cfg', '.ini', '.conf',
        '.log', '.sql', '.php', '.rb', '.go', '.rs', '.cpp', '.c', '.h'
    }
    
    ext = get_file_extension(filename)
    return ext in text_extensions


def create_backup_filename(original_filename: str) -> str:
    """创建备份文件名"""
    path = Path(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return str(path.with_suffix(f'.{timestamp}{path.suffix}.backup'))


def ensure_directory_exists(directory_path: str) -> bool:
    """确保目录存在"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False
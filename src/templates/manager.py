#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from string import Template

class TemplateManager:
    """模板管理器"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.expanduser('~/.claude-notifier/templates')
        self.builtin_templates_dir = os.path.join(os.path.dirname(__file__), 'builtin')
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保模板目录存在
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.builtin_templates_dir, exist_ok=True)
        
        # 创建内置模板
        self._create_builtin_templates()
        
    def _create_builtin_templates(self):
        """创建内置模板"""
        builtin_templates = self._get_builtin_templates()
        
        for template_name, template_data in builtin_templates.items():
            template_file = os.path.join(self.builtin_templates_dir, f'{template_name}.yaml')
            if not os.path.exists(template_file):
                with open(template_file, 'w', encoding='utf-8') as f:
                    yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
                    
    def get_template(self, template_name: str, channel: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        # 优先查找用户自定义模板
        user_template_file = os.path.join(self.templates_dir, f'{template_name}_{channel}.yaml')
        if os.path.exists(user_template_file):
            return self._load_template_file(user_template_file)
            
        # 查找通用用户模板
        user_template_file = os.path.join(self.templates_dir, f'{template_name}.yaml')
        if os.path.exists(user_template_file):
            template = self._load_template_file(user_template_file)
            return template.get(channel) if template else None
            
        # 查找内置模板
        builtin_template_file = os.path.join(self.builtin_templates_dir, f'{template_name}.yaml')
        if os.path.exists(builtin_template_file):
            template = self._load_template_file(builtin_template_file)
            return template.get(channel) if template else None
            
        self.logger.warning(f'模板不存在: {template_name} for {channel}')
        return None
        
    def _load_template_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载模板文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f'加载模板文件失败 {file_path}: {e}')
            return None
            
    def render_template(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """渲染模板"""
        try:
            # 递归渲染模板中的所有字符串
            return self._render_recursive(template, data)
        except Exception as e:
            self.logger.error(f'模板渲染失败: {e}')
            return template
            
    def _render_recursive(self, obj: Any, data: Dict[str, Any]) -> Any:
        """递归渲染对象"""
        if isinstance(obj, str):
            template = Template(obj)
            return template.safe_substitute(data)
        elif isinstance(obj, dict):
            return {k: self._render_recursive(v, data) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._render_recursive(item, data) for item in obj]
        else:
            return obj
            
    def create_custom_template(self, template_name: str, channel: str, template_data: Dict[str, Any]) -> bool:
        """创建自定义模板"""
        try:
            template_file = os.path.join(self.templates_dir, f'{template_name}_{channel}.yaml')
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
                
            self.logger.info(f'自定义模板已创建: {template_file}')
            return True
        except Exception as e:
            self.logger.error(f'创建自定义模板失败: {e}')
            return False
            
    def list_templates(self) -> Dict[str, List[str]]:
        """列出所有模板"""
        templates = {'builtin': [], 'custom': []}
        
        # 内置模板
        if os.path.exists(self.builtin_templates_dir):
            for file in os.listdir(self.builtin_templates_dir):
                if file.endswith('.yaml'):
                    templates['builtin'].append(file[:-5])
                    
        # 自定义模板
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.yaml'):
                    templates['custom'].append(file[:-5])
                    
        return templates
        
    def _get_builtin_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取内置模板定义"""
        return {
            'sensitive_operation_default': {
                'dingtalk': {
                    'msgtype': 'actionCard',
                    'actionCard': {
                        'title': '$title',
                        'text': """---

### ⚠️ 检测到敏感操作

> Claude Code 已自动暂停执行，等待您在终端确认

---

**📂 项目名称**

`$project`

**⚡ 检测操作**

```
$operation
```

**🕐 检测时间**

$timestamp

**⚠️ 风险等级**

$risk_level

---

💡 **温馨提示**：请在 Claude Code 终端中确认是否继续执行此操作""",
                        'btnOrientation': '1',
                        'btns': [
                            {
                                'title': '📱 查看终端',
                                'actionURL': 'https://claude.ai'
                            }
                        ]
                    }
                },
                'feishu': {
                    'msg_type': 'interactive',
                    'card': {
                        'header': {
                            'template': 'orange',
                            'title': {'content': '$title', 'tag': 'plain_text'}
                        },
                        'elements': [
                            {
                                'tag': 'div',
                                'text': {'content': '**⚠️ 检测到敏感操作**\n\n项目: $project\n操作: $operation', 'tag': 'lark_md'}
                            }
                        ]
                    }
                },
                'telegram': {
                    'text': """🔐 *$title*

⚠️ *检测到敏感操作*

━━━━━━━━━━━━━━━━━━

📂 *项目*: `$project`
⚡ *操作*: $operation
🕐 *时间*: $timestamp

━━━━━━━━━━━━━━━━━━

💡 请在 Claude Code 终端中确认操作""",
                    'parse_mode': 'Markdown'
                }
            },
            'task_completion_default': {
                'dingtalk': {
                    'msgtype': 'markdown',
                    'markdown': {
                        'title': '$title',
                        'text': """# 🎉 任务执行完成

---

### 📊 执行摘要

**📂 项目名称**

> `$project`

**📋 执行状态**

> $status

**⏰ 完成时间**

> $timestamp

---

### 🎯 建议操作

- ☕ **休息一下** - 您辛苦了！
- 🔍 **检查结果** - 查看 Claude Code 的执行成果
- 📝 **记录总结** - 如需要可以整理工作记录

---

> 💝 **Claude Code** 已完成所有任务，感谢您的信任！"""
                    }
                },
                'telegram': {
                    'text': """✅ *$title*

🎉 *工作完成，可以休息了！*

━━━━━━━━━━━━━━━━━━

📂 *项目*: `$project`
📋 *状态*: $status
⏰ *时间*: $timestamp

━━━━━━━━━━━━━━━━━━

💝 Claude Code 已完成所有任务！""",
                    'parse_mode': 'Markdown'
                }
            }
        }

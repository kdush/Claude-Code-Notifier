#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from string import Template
from pathlib import Path

class TemplateEngine:
    """通知模板引擎"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or os.path.expanduser('~/.claude-notifier/templates')
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保模板目录存在
        os.makedirs(self.template_dir, exist_ok=True)
        
        # 加载默认模板
        self._load_default_templates()
        
        # 加载用户自定义模板
        self._load_user_templates()
        
    def _load_default_templates(self):
        """加载默认模板"""
        default_templates = {
            'sensitive_operation_default': {
                'title': '🔐 敏感操作检测',
                'content': '检测到可能的敏感操作：${operation}',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '操作', 'value': '${operation}', 'short': False},
                    {'label': '风险等级', 'value': '${risk_level}', 'short': True},
                    {'label': '时间', 'value': '${timestamp}', 'short': True}
                ],
                'actions': [
                    {'text': '查看终端', 'type': 'button', 'url': 'terminal://'}
                ],
                'color': '#ff6b6b'
            },
            'task_completion_default': {
                'title': '✅ 任务完成',
                'content': '🎉 ${project} 项目任务已完成！',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '状态', 'value': '${status}', 'short': True},
                    {'label': '完成时间', 'value': '${timestamp}', 'short': True}
                ],
                'actions': [
                    {'text': '查看结果', 'type': 'button', 'url': 'file://'}
                ],
                'color': '#51cf66'
            },
            'rate_limit_default': {
                'title': '⏰ Claude 额度限流',
                'content': '检测到 Claude 额度限制，请稍后再试',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '错误类型', 'value': '${error_type}', 'short': True},
                    {'label': '冷却时间', 'value': '${cooldown_time}', 'short': True},
                    {'label': '时间', 'value': '${timestamp}', 'short': True}
                ],
                'color': '#ffd43b'
            },
            'confirmation_required_default': {
                'title': '⚠️ 需要确认',
                'content': '检测到需要用户确认的操作：${operation}',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '操作', 'value': '${operation}', 'short': False},
                    {'label': '原因', 'value': '${reason}', 'short': False},
                    {'label': '风险等级', 'value': '${risk_level}', 'short': True}
                ],
                'actions': [
                    {'text': '确认执行', 'type': 'button', 'style': 'primary'},
                    {'text': '取消操作', 'type': 'button', 'style': 'danger'}
                ],
                'color': '#ff922b'
            },
            'session_start_default': {
                'title': '🚀 会话开始',
                'content': 'Claude Code 会话已启动，开始编程之旅！',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '会话ID', 'value': '${session_id}', 'short': True},
                    {'label': '开始时间', 'value': '${start_time}', 'short': True}
                ],
                'color': '#339af0'
            },
            'error_occurred_default': {
                'title': '❌ 错误发生',
                'content': '检测到执行错误：${error_message}',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '错误类型', 'value': '${error_type}', 'short': True},
                    {'label': '错误信息', 'value': '${error_message}', 'short': False},
                    {'label': '时间', 'value': '${timestamp}', 'short': True}
                ],
                'color': '#e03131'
            },
            'custom_event_default': {
                'title': '🔔 ${event_name}',
                'content': '${description}',
                'fields': [
                    {'label': '项目', 'value': '${project}', 'short': True},
                    {'label': '事件名称', 'value': '${event_name}', 'short': True},
                    {'label': '时间', 'value': '${timestamp}', 'short': True}
                ],
                'color': '#868e96'
            }
        }
        
        self.templates.update(default_templates)
        
    def _load_user_templates(self):
        """加载用户自定义模板"""
        try:
            template_files = Path(self.template_dir).glob('*.yaml')
            for template_file in template_files:
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        user_templates = yaml.safe_load(f)
                        if isinstance(user_templates, dict):
                            self.templates.update(user_templates)
                            self.logger.info(f"加载用户模板: {template_file.name}")
                except Exception as e:
                    self.logger.error(f"加载模板文件失败 {template_file}: {e}")
        except Exception as e:
            self.logger.error(f"扫描模板目录失败: {e}")
            
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        return self.templates.get(template_name)
        
    def render_template(self, template_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """渲染模板"""
        template = self.get_template(template_name)
        if not template:
            self.logger.warning(f"模板不存在: {template_name}")
            return None
            
        try:
            rendered = {}
            
            # 渲染标题
            if 'title' in template:
                rendered['title'] = Template(template['title']).safe_substitute(data)
                
            # 渲染内容
            if 'content' in template:
                rendered['content'] = Template(template['content']).safe_substitute(data)
                
            # 渲染字段
            if 'fields' in template:
                rendered['fields'] = []
                for field in template['fields']:
                    rendered_field = {}
                    if 'label' in field:
                        rendered_field['label'] = Template(field['label']).safe_substitute(data)
                    if 'value' in field:
                        rendered_field['value'] = Template(field['value']).safe_substitute(data)
                    if 'short' in field:
                        rendered_field['short'] = field['short']
                    rendered['fields'].append(rendered_field)
                    
            # 渲染动作按钮
            if 'actions' in template:
                rendered['actions'] = []
                for action in template['actions']:
                    rendered_action = action.copy()
                    if 'text' in action:
                        rendered_action['text'] = Template(action['text']).safe_substitute(data)
                    if 'url' in action:
                        rendered_action['url'] = Template(action['url']).safe_substitute(data)
                    rendered['actions'].append(rendered_action)
                    
            # 复制其他属性
            for key in ['color', 'image', 'thumbnail']:
                if key in template:
                    rendered[key] = template[key]
                    
            return rendered
            
        except Exception as e:
            self.logger.error(f"渲染模板失败 {template_name}: {e}")
            return None
            
    def create_template(self, template_name: str, template_config: Dict[str, Any]) -> bool:
        """创建新模板"""
        try:
            # 验证模板配置
            validation_errors = self.validate_template(template_config)
            if validation_errors:
                self.logger.error(f"模板配置无效: {validation_errors}")
                return False
                
            self.templates[template_name] = template_config
            
            # 保存到文件
            template_file = Path(self.template_dir) / f"{template_name}.yaml"
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump({template_name: template_config}, f, 
                         default_flow_style=False, allow_unicode=True)
                         
            self.logger.info(f"创建模板: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建模板失败 {template_name}: {e}")
            return False
            
    def update_template(self, template_name: str, template_config: Dict[str, Any]) -> bool:
        """更新模板"""
        if template_name not in self.templates:
            self.logger.warning(f"模板不存在: {template_name}")
            return False
            
        return self.create_template(template_name, template_config)
        
    def delete_template(self, template_name: str) -> bool:
        """删除模板"""
        if template_name not in self.templates:
            return False
            
        # 不允许删除默认模板
        if template_name.endswith('_default'):
            self.logger.warning(f"不能删除默认模板: {template_name}")
            return False
            
        try:
            del self.templates[template_name]
            
            # 删除文件
            template_file = Path(self.template_dir) / f"{template_name}.yaml"
            if template_file.exists():
                template_file.unlink()
                
            self.logger.info(f"删除模板: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除模板失败 {template_name}: {e}")
            return False
            
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.templates.keys())
        
    def validate_template(self, template_config: Dict[str, Any]) -> List[str]:
        """验证模板配置"""
        errors = []
        
        # 检查必需字段
        if 'title' not in template_config:
            errors.append("缺少 title 字段")
            
        if 'content' not in template_config:
            errors.append("缺少 content 字段")
            
        # 验证字段配置
        if 'fields' in template_config:
            if not isinstance(template_config['fields'], list):
                errors.append("fields 必须是数组")
            else:
                for i, field in enumerate(template_config['fields']):
                    if not isinstance(field, dict):
                        errors.append(f"字段 {i} 必须是对象")
                        continue
                    if 'label' not in field:
                        errors.append(f"字段 {i} 缺少 label")
                    if 'value' not in field:
                        errors.append(f"字段 {i} 缺少 value")
                        
        # 验证动作配置
        if 'actions' in template_config:
            if not isinstance(template_config['actions'], list):
                errors.append("actions 必须是数组")
            else:
                for i, action in enumerate(template_config['actions']):
                    if not isinstance(action, dict):
                        errors.append(f"动作 {i} 必须是对象")
                        continue
                    if 'text' not in action:
                        errors.append(f"动作 {i} 缺少 text")
                    if 'type' not in action:
                        errors.append(f"动作 {i} 缺少 type")
                        
        return errors
        
    def export_template(self, template_name: str, file_path: str) -> bool:
        """导出模板到文件"""
        template = self.get_template(template_name)
        if not template:
            return False
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump({template_name: template}, f, 
                         default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            self.logger.error(f"导出模板失败: {e}")
            return False
            
    def import_template(self, file_path: str) -> int:
        """从文件导入模板"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
                
            if not isinstance(templates, dict):
                self.logger.error("模板文件格式错误")
                return 0
                
            imported_count = 0
            for template_name, template_config in templates.items():
                if self.create_template(template_name, template_config):
                    imported_count += 1
                    
            return imported_count
            
        except Exception as e:
            self.logger.error(f"导入模板失败: {e}")
            return 0

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import time
from typing import Dict, Any, List, Optional, Callable
from .base import BaseEvent, EventType, EventPriority

class CustomEvent(BaseEvent):
    """自定义事件类"""
    
    def __init__(self, event_id: str, config: Dict[str, Any]):
        """
        初始化自定义事件
        
        Args:
            event_id: 事件ID
            config: 事件配置
                - name: 事件名称
                - description: 事件描述
                - priority: 优先级 (low/normal/high/critical)
                - triggers: 触发条件列表
                - data_extractors: 数据提取器配置
                - message_template: 消息模板
        """
        priority_map = {
            'low': EventPriority.LOW,
            'normal': EventPriority.NORMAL,
            'high': EventPriority.HIGH,
            'critical': EventPriority.CRITICAL
        }
        
        priority = priority_map.get(config.get('priority', 'normal'), EventPriority.NORMAL)
        super().__init__(event_id, EventType.CUSTOM_EVENT, priority)
        
        self.config = config
        self.name = config.get('name', event_id)
        self.description = config.get('description', '')
        self.triggers = config.get('triggers', [])
        self.data_extractors = config.get('data_extractors', {})
        self.message_template = config.get('message_template', {})
        
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """检查是否应该触发事件"""
        if not self.triggers:
            return False
            
        for trigger in self.triggers:
            if self._evaluate_trigger(trigger, context):
                return True
        return False
        
    def _evaluate_trigger(self, trigger: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估单个触发条件"""
        trigger_type = trigger.get('type', 'pattern')
        
        if trigger_type == 'pattern':
            return self._evaluate_pattern_trigger(trigger, context)
        elif trigger_type == 'condition':
            return self._evaluate_condition_trigger(trigger, context)
        elif trigger_type == 'function':
            return self._evaluate_function_trigger(trigger, context)
        else:
            self.logger.warning(f"未知的触发器类型: {trigger_type}")
            return False
            
    def _evaluate_pattern_trigger(self, trigger: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估模式匹配触发器"""
        pattern = trigger.get('pattern', '')
        field = trigger.get('field', 'tool_input')
        flags = trigger.get('flags', 0)
        
        if isinstance(flags, list):
            flag_value = 0
            for flag in flags:
                if flag == 'IGNORECASE':
                    flag_value |= re.IGNORECASE
                elif flag == 'MULTILINE':
                    flag_value |= re.MULTILINE
                elif flag == 'DOTALL':
                    flag_value |= re.DOTALL
            flags = flag_value
            
        value = context.get(field, '')
        if not isinstance(value, str):
            value = str(value)
            
        try:
            return bool(re.search(pattern, value, flags))
        except re.error as e:
            self.logger.error(f"正则表达式错误: {e}")
            return False
            
    def _evaluate_condition_trigger(self, trigger: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估条件触发器"""
        field = trigger.get('field', '')
        operator = trigger.get('operator', 'equals')
        value = trigger.get('value')
        
        context_value = context.get(field)
        
        if operator == 'equals':
            return context_value == value
        elif operator == 'not_equals':
            return context_value != value
        elif operator == 'contains':
            return value in str(context_value) if context_value else False
        elif operator == 'not_contains':
            return value not in str(context_value) if context_value else True
        elif operator == 'exists':
            return field in context
        elif operator == 'not_exists':
            return field not in context
        elif operator == 'greater_than':
            try:
                return float(context_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than':
            try:
                return float(context_value) < float(value)
            except (ValueError, TypeError):
                return False
        else:
            self.logger.warning(f"未知的操作符: {operator}")
            return False
            
    def _evaluate_function_trigger(self, trigger: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估函数触发器"""
        function_name = trigger.get('function', '')
        
        # 内置函数
        if function_name == 'is_weekend':
            return time.localtime().tm_wday >= 5
        elif function_name == 'is_work_hours':
            hour = time.localtime().tm_hour
            return 9 <= hour <= 18
        elif function_name == 'has_error_keywords':
            text = str(context.get('tool_input', '')) + str(context.get('error_message', ''))
            error_keywords = ['error', 'exception', 'failed', 'timeout', '错误', '异常', '失败']
            return any(keyword in text.lower() for keyword in error_keywords)
        else:
            self.logger.warning(f"未知的函数: {function_name}")
            return False
            
    def extract_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文中提取事件数据"""
        data = {
            'event_name': self.name,
            'description': self.description
        }
        
        # 使用配置的数据提取器
        for key, extractor in self.data_extractors.items():
            if isinstance(extractor, str):
                # 简单字段提取
                data[key] = context.get(extractor, '')
            elif isinstance(extractor, dict):
                # 复杂提取器
                extractor_type = extractor.get('type', 'field')
                if extractor_type == 'field':
                    field = extractor.get('field', '')
                    default = extractor.get('default', '')
                    data[key] = context.get(field, default)
                elif extractor_type == 'regex':
                    pattern = extractor.get('pattern', '')
                    field = extractor.get('field', 'tool_input')
                    group = extractor.get('group', 0)
                    text = context.get(field, '')
                    try:
                        match = re.search(pattern, str(text))
                        data[key] = match.group(group) if match else ''
                    except (re.error, IndexError):
                        data[key] = ''
                elif extractor_type == 'function':
                    function_name = extractor.get('function', '')
                    data[key] = self._execute_extractor_function(function_name, context)
                        
        return data
        
    def _execute_extractor_function(self, function_name: str, context: Dict[str, Any]) -> Any:
        """执行数据提取函数"""
        if function_name == 'get_project_name':
            return self._get_project_name()
        elif function_name == 'get_current_time':
            return time.strftime('%Y-%m-%d %H:%M:%S')
        elif function_name == 'get_file_count':
            import os
            try:
                return len([f for f in os.listdir('.') if os.path.isfile(f)])
            except:
                return 0
        else:
            return ''
            
    def _get_project_name(self) -> str:
        """获取项目名称"""
        import os
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
        if project_dir:
            return os.path.basename(project_dir)
        current_dir = os.getcwd()
        if current_dir not in ['/', os.path.expanduser('~')]:
            return os.path.basename(current_dir)
        return 'claude-code'
        
    def get_default_message(self) -> Dict[str, Any]:
        """获取默认消息模板"""
        if self.message_template:
            return self.message_template.copy()
            
        return {
            'title': f'🔔 {self.name}',
            'content': self.description or '自定义事件触发',
            'action': '请查看详细信息'
        }

class CustomEventRegistry:
    """自定义事件注册表"""
    
    def __init__(self):
        self.events: Dict[str, CustomEvent] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def register_event(self, event_id: str, config: Dict[str, Any]) -> bool:
        """注册自定义事件"""
        try:
            event = CustomEvent(event_id, config)
            self.events[event_id] = event
            self.logger.info(f"注册自定义事件: {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"注册事件失败 {event_id}: {e}")
            return False
            
    def unregister_event(self, event_id: str) -> bool:
        """注销自定义事件"""
        if event_id in self.events:
            del self.events[event_id]
            self.logger.info(f"注销自定义事件: {event_id}")
            return True
        return False
        
    def get_event(self, event_id: str) -> Optional[CustomEvent]:
        """获取自定义事件"""
        return self.events.get(event_id)
        
    def list_events(self) -> List[str]:
        """列出所有自定义事件ID"""
        return list(self.events.keys())
        
    def load_from_config(self, config: Dict[str, Any]) -> int:
        """从配置中加载自定义事件"""
        custom_events = config.get('custom_events', {})
        loaded_count = 0
        
        for event_id, event_config in custom_events.items():
            if self.register_event(event_id, event_config):
                loaded_count += 1
                
        self.logger.info(f"加载了 {loaded_count} 个自定义事件")
        return loaded_count
        
    def validate_event_config(self, config: Dict[str, Any]) -> List[str]:
        """验证事件配置"""
        errors = []
        
        if not config.get('name'):
            errors.append("缺少事件名称")
            
        triggers = config.get('triggers', [])
        if not triggers:
            errors.append("至少需要一个触发条件")
        else:
            for i, trigger in enumerate(triggers):
                trigger_errors = self._validate_trigger(trigger, i)
                errors.extend(trigger_errors)
                
        return errors
        
    def _validate_trigger(self, trigger: Dict[str, Any], index: int) -> List[str]:
        """验证触发器配置"""
        errors = []
        trigger_type = trigger.get('type', 'pattern')
        
        if trigger_type == 'pattern':
            if not trigger.get('pattern'):
                errors.append(f"触发器 {index}: 缺少 pattern")
        elif trigger_type == 'condition':
            if not trigger.get('field'):
                errors.append(f"触发器 {index}: 缺少 field")
            if not trigger.get('operator'):
                errors.append(f"触发器 {index}: 缺少 operator")
        elif trigger_type == 'function':
            if not trigger.get('function'):
                errors.append(f"触发器 {index}: 缺少 function")
        else:
            errors.append(f"触发器 {index}: 未知类型 {trigger_type}")
            
        return errors

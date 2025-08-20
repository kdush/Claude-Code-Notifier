#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json
from typing import Dict, Any
from .base import BaseChannel

class DingtalkChannel(BaseChannel):
    """钉钉机器人通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook = config.get('webhook', '')
        self.secret = config.get('secret', '')
        
    def _sign_webhook(self) -> str:
        """生成签名后的 webhook URL"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f'{self.webhook}&timestamp={timestamp}&sign={sign}'
        
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到钉钉"""
        try:
            url = self._sign_webhook() if self.secret else self.webhook
            
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(message),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("钉钉通知发送成功")
                    return True
                else:
                    self.logger.error(f"钉钉通知发送失败: {result}")
                    return False
            else:
                self.logger.error(f"钉钉 API 请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"钉钉通知发送异常: {str(e)}")
            return False
            
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通用通知"""
        # 如果有渲染后的模板数据，优先使用
        if 'rendered' in template_data:
            return self._send_template_message(template_data['rendered'])
        
        # 否则根据事件类型使用默认格式
        if event_type == 'permission':
            return self._send_permission_message(template_data)
        elif event_type == 'completion':
            return self._send_completion_message(template_data)
        elif event_type == 'rate_limit':
            return self._send_rate_limit_message(template_data)
        elif event_type == 'error':
            return self._send_error_message(template_data)
        elif event_type == 'session_start':
            return self._send_session_start_message(template_data)
        elif event_type == 'test':
            return self._send_test_message(template_data)
        else:
            return self._send_generic_message(template_data)
    
    def _send_template_message(self, rendered_data: Dict[str, Any]) -> bool:
        """发送基于模板渲染的消息"""
        title = rendered_data.get('title', '通知')
        content = rendered_data.get('content', '')
        fields = rendered_data.get('fields', [])
        actions = rendered_data.get('actions', [])
        color = rendered_data.get('color', '#108ee9')
        
        # 构建字段文本
        field_text = ""
        if fields:
            for field in fields:
                label = field.get('label', '')
                value = field.get('value', '')
                if label and value:
                    field_text += f"\n\n**{label}**\n\n`{value}`"
        
        # 构建按钮
        btns = []
        if actions and self.supports_actions():
            for action in actions:
                if action.get('type') == 'button':
                    btns.append({
                        "title": action.get('text', '按钮'),
                        "actionURL": action.get('url', 'https://claude.ai')
                    })
        
        # 选择消息类型
        if btns:
            message = {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": title,
                    "text": f"{content}{field_text}",
                    "hideAvatar": "0",
                    "btnOrientation": "1",
                    "btns": btns
                }
            }
        else:
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"# {title}\n\n{content}{field_text}"
                }
            }
        
        return self._send_message(message)
    
    def _send_permission_message(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        project = data.get('project', 'claude-code')
        operation = data.get('operation', '未知操作')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": "🔐 Claude Code 权限检测",
                "text": f"""---

### ⚠️ 检测到敏感操作

> Claude Code 已自动暂停执行，等待您在终端确认

---

**📂 项目名称**

`{project}`

**⚡ 检测操作**

```
{operation}
```

**🕐 检测时间**

{timestamp}

---

💡 **温馨提示**：请在 Claude Code 终端中确认是否继续执行此操作""",
                "hideAvatar": "0",
                "btnOrientation": "1",
                "btns": [
                    {
                        "title": "📱 查看终端",
                        "actionURL": "https://claude.ai"
                    }
                ]
            }
        }
        
        return self._send_message(message)
    
    def _send_completion_message(self, data: Dict[str, Any]) -> bool:
        """发送任务完成消息"""
        project = data.get('project', 'claude-code')
        status = data.get('status', 'Claude Code 执行完成')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "✅ Claude Code 任务完成",
                "text": f"""# 🎉 任务执行完成

---

### 📊 执行摘要

**📂 项目名称**

> `{project}`

**📋 执行状态**

> {status}

**⏰ 完成时间**

> {timestamp}

---

### 🎯 建议操作

- ☕ **休息一下** - 您辛苦了！
- 🔍 **检查结果** - 查看 Claude Code 的执行成果
- 📝 **记录总结** - 如需要可以整理工作记录

---

> 💝 **Claude Code** 已完成所有任务，感谢您的信任！"""
            }
        }
        
        return self._send_message(message)
    
    def _send_rate_limit_message(self, data: Dict[str, Any]) -> bool:
        """发送限流通知"""
        project = data.get('project', 'claude-code')
        cooldown_time = data.get('cooldown_time', '未知')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "⏰ Claude 额度限流",
                "text": f"""# ⏰ Claude 额度限流

---

### 📊 限流信息

**📂 项目名称**

> `{project}`

**⏳ 冷却时间**

> {cooldown_time}

**🕐 限流时间**

> {timestamp}

---

### 💡 建议

- ☕ **稍作休息** - 等待额度恢复
- 📚 **整理代码** - 利用时间优化项目
- 🔄 **稍后重试** - 额度恢复后继续

---

> 🤖 **Claude Code** 将在额度恢复后继续为您服务"""
            }
        }
        
        return self._send_message(message)
    
    def _send_error_message(self, data: Dict[str, Any]) -> bool:
        """发送错误通知"""
        project = data.get('project', 'claude-code')
        error_type = data.get('error_type', 'unknown')
        error_message = data.get('error_message', '未知错误')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "❌ 执行错误",
                "text": f"""# ❌ 执行错误

---

### 📊 错误信息

**📂 项目名称**

> `{project}`

**🔍 错误类型**

> {error_type}

**📝 错误详情**

```
{error_message[:500]}
```

**🕐 发生时间**

> {timestamp}

---

### 🔧 建议操作

- 🔍 **检查错误** - 查看详细错误信息
- 🛠️ **修复问题** - 根据错误提示进行修复
- 🔄 **重新执行** - 修复后重新运行

---

> ⚠️ **Claude Code** 遇到问题，请检查并修复"""
            }
        }
        
        return self._send_message(message)
    
    def _send_session_start_message(self, data: Dict[str, Any]) -> bool:
        """发送会话开始通知"""
        project = data.get('project', 'claude-code')
        session_id = data.get('session_id', 'unknown')
        start_time = data.get('start_time', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🚀 会话开始",
                "text": f"""# 🚀 Claude Code 会话开始

---

### 📊 会话信息

**📂 项目名称**

> `{project}`

**🆔 会话ID**

> `{session_id}`

**🕐 开始时间**

> {start_time}

---

### 🎯 准备就绪

- 🤖 **AI 助手** - Claude Code 已启动
- 📝 **代码编写** - 准备协助您编程
- 🔧 **问题解决** - 随时为您排忧解难

---

> 🌟 **Claude Code** 已准备就绪，开始您的编程之旅！"""
            }
        }
        
        return self._send_message(message)
    
    def _send_test_message(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        project = data.get('project', 'claude-code')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🧪 Claude Code 测试通知",
                "text": f"""### 🔧 系统测试

---

**📂 当前项目**

`{project}`

**🕐 测试时间**

{timestamp}

**📡 通知状态**

✅ 钉钉机器人连接正常

✅ 消息推送功能正常

✅ 签名验证通过

---

> 🎊 **Claude Code 钉钉通知系统运行正常！**"""
            }
        }
        
        return self._send_message(message)
    
    def _send_generic_message(self, data: Dict[str, Any]) -> bool:
        """发送通用消息"""
        title = data.get('title', '通知')
        content = data.get('content', '收到新的通知')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"""# {title}

{content}

---

**时间**: {timestamp}"""
            }
        }
        
        return self._send_message(message)
    
    def supports_actions(self) -> bool:
        """钉钉支持交互按钮"""
        return True
        
    def get_max_content_length(self) -> int:
        """钉钉消息最大长度限制"""
        return 20000
        
    def format_message_for_channel(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """为钉钉格式化消息"""
        # 钉钉特定的消息格式化
        formatted_data = template_data.copy()
        
        # 截断过长的内容
        if 'content' in formatted_data:
            formatted_data['content'] = self.truncate_content(formatted_data['content'])
            
        # 处理字段值长度
        if 'fields' in formatted_data:
            for field in formatted_data['fields']:
                if 'value' in field:
                    field['value'] = self.truncate_content(field['value'], 500)
                    
        return formatted_data
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知（兼容旧接口）"""
        return self._send_completion_message(data)
        
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知（兼容旧接口）"""
        return self._send_permission_message(data)
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        project = data.get('project', 'claude-code')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🧪 Claude Code 测试通知",
                "text": f"""### 🔧 系统测试

---

**📂 当前项目**

`{project}`

**🕐 测试时间**

{timestamp}

**📡 通知状态**

✅ 钉钉机器人连接正常

✅ 消息推送功能正常

✅ 签名验证通过

---

> 🎊 **Claude Code 钉钉通知系统运行正常！**"""
            }
        }
        
        return self._send_message(message)
        
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        if not self.webhook:
            self.logger.error("钉钉 webhook 配置为空")
            return False
            
        if not self.webhook.startswith('https://oapi.dingtalk.com/robot/send?access_token='):
            self.logger.error("钉钉 webhook 格式不正确")
            return False
            
        return True

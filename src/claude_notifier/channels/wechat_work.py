#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import json
from typing import Dict, Any
from .base import BaseChannel

class WechatWorkChannel(BaseChannel):
    """企业微信机器人通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook = config.get('webhook', '')
        
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到企业微信"""
        try:
            response = requests.post(
                self.webhook,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(message),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("企业微信通知发送成功")
                    return True
                else:
                    self.logger.error(f"企业微信通知发送失败: {result}")
                    return False
            else:
                self.logger.error(f"企业微信 API 请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"企业微信通知发送异常: {str(e)}")
            return False
            
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        project = data.get('project', 'claude-code')
        operation = data.get('operation', '未知操作')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""## 🔐 Claude Code 权限检测

> **⚠️ 检测到敏感操作**
> Claude Code 已自动暂停执行，等待您在终端确认

**📂 项目名称**: <font color=\"info\">{project}</font>

**⚡ 检测操作**: 
```
{operation}
```

**🕐 检测时间**: {timestamp}

> 💡 **温馨提示**：请在 Claude Code 终端中确认是否继续执行此操作"""
            }
        }
        
        return self._send_message(message)
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知"""
        project = data.get('project', 'claude-code')
        status = data.get('status', 'Claude Code 执行完成')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""## ✅ Claude Code 任务完成

> **🎉 工作完成，可以休息了！**

**📂 项目名称**: <font color=\"info\">{project}</font>

**📋 执行状态**: <font color=\"comment\">{status}</font>

**⏰ 完成时间**: {timestamp}

### 🎯 建议操作
- ☕ **休息一下** - 您辛苦了！
- 🔍 **检查结果** - 查看 Claude Code 的执行成果
- 📝 **记录总结** - 如需要可以整理工作记录

> 💝 **Claude Code** 已完成所有任务，感谢您的信任！"""
            }
        }
        
        return self._send_message(message)
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        project = data.get('project', 'claude-code')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"🧪 Claude Code 企业微信通知测试\n\n📂 项目: {project}\n🕐 时间: {timestamp}\n\n✅ 企业微信机器人连接正常\n✅ 消息推送功能正常\n\n🎊 Claude Code 企业微信通知系统运行正常！"
            }
        }
        
        return self._send_message(message)
        
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        if not self.webhook:
            self.logger.error("企业微信 webhook 配置为空")
            return False
            
        if not self.webhook.startswith('https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key='):
            self.logger.error("企业微信 webhook 格式不正确")
            return False
            
        return True

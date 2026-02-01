#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import json
from typing import Dict, Any
from .base import BaseChannel

class TelegramChannel(BaseChannel):
    """Telegram Bot 通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        self.api_url = f'https://api.telegram.org/bot{self.bot_token}'
        
    def _send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """发送消息到 Telegram"""
        try:
            url = f'{self.api_url}/sendMessage'
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.info("Telegram 通知发送成功")
                    return True
                else:
                    self.logger.error(f"Telegram 通知发送失败: {result}")
                    return False
            else:
                self.logger.error(f"Telegram API 请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram 通知发送异常: {str(e)}")
            return False
            
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        project = data.get('project', 'claude-code')
        operation = data.get('operation', '未知操作')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        text = f"""🔐 *Claude Code 权限检测*

⚠️ *检测到敏感操作*

Claude Code 已自动暂停执行，等待您在终端确认

━━━━━━━━━━━━━━━━━━

📂 *项目名称*: `{project}`

⚡ *检测操作*:
```
{operation}
```

🕐 *检测时间*: {timestamp}

━━━━━━━━━━━━━━━━━━

💡 *温馨提示*：请在 Claude Code 终端中确认是否继续执行此操作

[🔗 查看 Claude Code](https://claude.ai)"""

        return self._send_message(text)
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知"""
        project = data.get('project', 'claude-code')
        status = data.get('status', 'Claude Code 执行完成')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        text = f"""✅ *Claude Code 任务完成*

🎉 *工作完成，可以休息了！*

━━━━━━━━━━━━━━━━━━

📂 *项目名称*: `{project}`

📋 *执行状态*: {status}

⏰ *完成时间*: {timestamp}

━━━━━━━━━━━━━━━━━━

🎯 *建议操作*:
• ☕ *休息一下* - 您辛苦了！
• 🔍 *检查结果* - 查看 Claude Code 的执行成果
• 📝 *记录总结* - 如需要可以整理工作记录

━━━━━━━━━━━━━━━━━━

💝 *Claude Code* 已完成所有任务，感谢您的信任！"""

        return self._send_message(text)
        
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        project = data.get('project', 'claude-code')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        text = f"""🧪 *Claude Code Telegram 通知测试*

━━━━━━━━━━━━━━━━━━

📂 *当前项目*: `{project}`

🕐 *测试时间*: {timestamp}

📡 *通知状态*:
✅ Telegram Bot 连接正常
✅ 消息推送功能正常
✅ Markdown 格式支持正常

━━━━━━━━━━━━━━━━━━

🎊 *Claude Code Telegram 通知系统运行正常！*"""

        return self._send_message(text)
        
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        if not self.bot_token:
            self.logger.error("Telegram bot_token 配置为空")
            return False
            
        if not self.chat_id:
            self.logger.error("Telegram chat_id 配置为空")
            return False
            
        # 测试 Bot 连接
        try:
            url = f'{self.api_url}/getMe'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.info(f"Telegram Bot 连接正常: @{result['result']['username']}")
                    return True
                else:
                    self.logger.error(f"Telegram Bot 验证失败: {result}")
                    return False
            else:
                self.logger.error(f"Telegram Bot 连接失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Telegram Bot 验证异常: {str(e)}")
            return False

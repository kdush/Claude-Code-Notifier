#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import hmac
import hashlib
import base64
import requests
import json
from typing import Dict, Any
from .base import BaseChannel

class FeishuChannel(BaseChannel):
    """飞书机器人通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook = config.get('webhook', '')
        self.secret = config.get('secret', '')
        
    def _sign_message(self, timestamp: str) -> str:
        """生成消息签名"""
        if not self.secret:
            return ''
            
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
        
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到飞书"""
        try:
            # 添加签名
            if self.secret:
                timestamp = str(int(time.time()))
                sign = self._sign_message(timestamp)
                message['timestamp'] = timestamp
                message['sign'] = sign
                
            response = requests.post(
                self.webhook,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(message),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.logger.info("飞书通知发送成功")
                    return True
                else:
                    self.logger.error(f"飞书通知发送失败: {result}")
                    return False
            else:
                self.logger.error(f"飞书 API 请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"飞书通知发送异常: {str(e)}")
            return False
            
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        """发送权限确认通知"""
        project = data.get('project', 'claude-code')
        operation = data.get('operation', '未知操作')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": "**🔐 Claude Code 权限检测**\n\n⚠️ 检测到敏感操作，Claude Code 已自动暂停执行",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**📂 项目名称**\n{project}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**🕐 检测时间**\n{timestamp}",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**⚡ 检测操作**\n```\n{operation}\n```",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": "💡 **温馨提示**：请在 Claude Code 终端中确认是否继续执行此操作",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "content": "📱 查看终端",
                                    "tag": "plain_text"
                                },
                                "type": "primary",
                                "url": "https://claude.ai"
                            }
                        ]
                    }
                ],
                "header": {
                    "template": "orange",
                    "title": {
                        "content": "🔐 Claude Code 权限检测",
                        "tag": "plain_text"
                    }
                }
            }
        }
        
        return self._send_message(message)
        
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        """发送任务完成通知"""
        project = data.get('project', 'claude-code')
        status = data.get('status', 'Claude Code 执行完成')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": "**🎉 任务执行完成**\n\n工作完成，可以休息了！",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**📂 项目名称**\n{project}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**⏰ 完成时间**\n{timestamp}",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**📋 执行状态**\n{status}",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": "**🎯 建议操作**\n- ☕ 休息一下 - 您辛苦了！\n- 🔍 检查结果 - 查看执行成果\n- 📝 记录总结 - 整理工作记录",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": "💝 **Claude Code** 已完成所有任务，感谢您的信任！",
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "template": "green",
                    "title": {
                        "content": "✅ Claude Code 任务完成",
                        "tag": "plain_text"
                    }
                }
            }
        }
        
        return self._send_message(message)
        
    def send_notification(self, template_data: Dict[str, Any], event_type: str = 'generic') -> bool:
        """发送通用通知"""
        # 如果有渲染好的模板数据，优先使用
        if 'rendered' in template_data:
            return self._send_template_message(template_data['rendered'])
        
        # 根据事件类型发送对应的通知
        if event_type == 'permission':
            return self.send_permission_notification(template_data)
        elif event_type == 'completion':
            return self.send_completion_notification(template_data)
        elif event_type == 'rate_limit':
            return self._send_rate_limit_message(template_data)
        elif event_type == 'error':
            return self._send_error_message(template_data)
        elif event_type == 'session_start':
            return self._send_session_start_message(template_data)
        elif event_type == 'test':
            return self.send_test_notification(template_data)
        else:
            return self._send_generic_message(template_data)
    
    def _send_template_message(self, template_data: Dict[str, Any]) -> bool:
        """发送基于模板的消息"""
        try:
            title = template_data.get('title', '通知')
            content = template_data.get('content', '')
            color = template_data.get('color', 'blue')
            buttons = template_data.get('buttons', [])
            
            # 颜色映射
            color_map = {
                'red': 'red',
                'orange': 'orange', 
                'yellow': 'yellow',
                'green': 'green',
                'blue': 'blue',
                'purple': 'purple',
                'grey': 'grey'
            }
            
            elements = [
                {
                    "tag": "div",
                    "text": {
                        "content": content,
                        "tag": "lark_md"
                    }
                }
            ]
            
            # 添加按钮
            if buttons and self.supports_actions():
                actions = []
                for button in buttons:
                    actions.append({
                        "tag": "button",
                        "text": {
                            "content": button.get('text', '按钮'),
                            "tag": "plain_text"
                        },
                        "type": "primary" if button.get('primary', False) else "default",
                        "url": button.get('url', 'https://claude.ai')
                    })
                
                if actions:
                    elements.append({
                        "tag": "action",
                        "actions": actions
                    })
            
            message = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "elements": elements,
                    "header": {
                        "template": color_map.get(color, 'blue'),
                        "title": {
                            "content": title,
                            "tag": "plain_text"
                        }
                    }
                }
            }
            
            return self._send_message(message)
            
        except Exception as e:
            self.logger.error(f"发送模板消息失败: {e}")
            return False
    
    def _send_rate_limit_message(self, data: Dict[str, Any]) -> bool:
        """发送限流通知"""
        project = data.get('project', 'claude-code')
        limit_type = data.get('limit_type', 'API调用')
        cooldown_time = data.get('cooldown_time', '未知')
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**⏰ Claude 限流通知**\n\n🚦 {limit_type}已达到限制，系统将自动等待",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**📂 项目**\n{project}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**⏳ 冷却时间**\n{cooldown_time}",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    }
                ],
                "header": {
                    "template": "yellow",
                    "title": {
                        "content": "⏰ Claude 限流通知",
                        "tag": "plain_text"
                    }
                }
            }
        }
        
        return self._send_message(message)
    
    def _send_error_message(self, data: Dict[str, Any]) -> bool:
        """发送错误通知"""
        project = data.get('project', 'claude-code')
        error_type = data.get('error_type', '未知错误')
        error_message = data.get('error_message', '')
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**❌ 错误通知**\n\n🚨 Claude Code 执行过程中发生错误",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**📂 项目**\n{project}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**🏷️ 错误类型**\n{error_type}",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**📝 错误详情**\n```\n{error_message}\n```",
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "template": "red",
                    "title": {
                        "content": "❌ Claude Code 错误",
                        "tag": "plain_text"
                    }
                }
            }
        }
        
        return self._send_message(message)
    
    def _send_session_start_message(self, data: Dict[str, Any]) -> bool:
        """发送会话开始通知"""
        project = data.get('project', 'claude-code')
        user = data.get('user', '用户')
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**🚀 会话开始**\n\n👋 {user}，Claude Code 已启动",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**📂 项目**\n{project}",
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "template": "blue",
                    "title": {
                        "content": "🚀 Claude Code 会话开始",
                        "tag": "plain_text"
                    }
                }
            }
        }
        
        return self._send_message(message)
    
    def _send_generic_message(self, data: Dict[str, Any]) -> bool:
        """发送通用消息"""
        title = data.get('title', '通知')
        content = data.get('content', str(data))
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"{title}\n\n{content}"
            }
        }
        
        return self._send_message(message)
    
    def supports_actions(self) -> bool:
        """是否支持操作按钮"""
        return True
    
    def get_max_content_length(self) -> int:
        """获取最大内容长度"""
        return 4000
    
    def format_message_for_channel(self, message: str) -> str:
        """为渠道格式化消息"""
        # 飞书支持 Markdown，直接返回
        if len(message) > self.get_max_content_length():
            return message[:self.get_max_content_length() - 3] + "..."
        return message

    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        """发送测试通知"""
        project = data.get('project', 'claude-code')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"🧪 Claude Code 飞书通知测试\n\n📂 项目: {project}\n🕐 时间: {timestamp}\n\n✅ 飞书机器人连接正常\n✅ 消息推送功能正常\n\n🎊 Claude Code 飞书通知系统运行正常！"
            }
        }
        
        return self._send_message(message)
        
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        if not self.webhook:
            self.logger.error("飞书 webhook 配置为空")
            return False
            
        if not self.webhook.startswith('https://open.feishu.cn/open-apis/bot/v2/hook/'):
            self.logger.error("飞书 webhook 格式不正确")
            return False
            
        return True

[中文文档](channels.md)

# 📱 Notification Channels Configuration Guide

## Supported Channels Overview

| Channel | Status | Features | Difficulty |
|--------|--------|----------|------------|
| 🔔 DingTalk Bot | ✅ Mature | ActionCard + Markdown + HMAC Sign | ⭐⭐ |
| 🚀 Feishu (Lark) Bot | ✅ Mature | Rich text + Interactive cards | ⭐⭐ |
| 💼 WeCom (WeChat Work) Bot | ✅ Mature | Markdown + News | ⭐⭐ |
| 🤖 Telegram | ✅ Mature | Bot messaging | ⭐⭐⭐ |
| 📮 SMTP Email | ✅ Mature | HTML emails | ⭐⭐⭐⭐ |
| 📧 ServerChan | ✅ Mature | WeChat push | ⭐ |

## 🔔 DingTalk Bot

### Steps

1. Create Bot
   - Open DingTalk group, click the settings at top-right
   - Choose "Bot" → "Add Bot"
   - Select "Custom Bot", set bot name
   - Security setting: choose "HMAC Sign" (recommended)

2. Obtain Credentials
   - Copy Webhook URL
   - Copy Secret (string starting with SEC)

3. Configuration File
```yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    secret: "SECxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # optional but recommended
```

### Message Formats

Permission Confirmation (ActionCard)
```json
{
    "msgtype": "actionCard",
    "actionCard": {
        "title": "🔐 Claude Code Permission Check",
        "text": "### ⚠️ Sensitive operation detected\n\n> Claude Code has paused execution\n\n**📂 Project:** test-project\n**⚡ Operation:** sudo systemctl restart nginx\n\n💡 Please confirm in your terminal",
        "singleTitle": "📱 Open Terminal",
        "singleURL": "https://claude.ai"
    }
}
```

Task Completed (Markdown)
```json
{
    "msgtype": "markdown",
    "markdown": {
        "title": "✅ Claude Code Task Completed",
        "text": "### 🎉 Job done, take a break!\n\n**📂 Project:** test-project\n**📋 Status:** Refactor completed\n**⏰ Time:** 2025-08-20 15:30:20\n\n☕ Consider reviewing the result"
    }
}
```

### Troubleshooting

1. Send Failure (error code 310000)
   - Check Webhook URL
   - Ensure the bot is added to the group

2. Signature Verification Failed
   - Secret must include SEC prefix
   - Ensure timestamp calculation is correct

---

## 🚀 Feishu (Lark) Bot

### Steps

1. Create Bot
   - Enter Lark group, click settings
   - "Bot" → "Add Bot"
   - Choose "Custom Bot"

2. Get Webhook
   - Copy generated Webhook URL

3. Configuration
```yaml
channels:
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK_ID"
```

### Message Formats

Interactive Card
```json
{
    "msg_type": "interactive",
    "card": {
        "config": {
            "wide_screen_mode": true
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "🔐 **Claude Code Permission Check**\n\n⚠️ Sensitive operation detected\n📂 Project: test-project\n⚡ Operation: sudo systemctl restart nginx",
                    "tag": "lark_md"
                }
            }
        ],
        "header": {
            "title": {
                "content": "Permission Confirmation",
                "tag": "plain_text"
            },
            "template": "orange"
        }
    }
}
```

---

## 💼 WeCom (WeChat Work) Bot

### Steps

1. Create Bot
   - Enter WeCom group
   - Add group bot
   - Choose "Custom Bot"

2. Get Credentials
   - Copy Webhook URL

3. Configuration
```yaml
channels:
  wechat_work:
    enabled: true
    webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
```

### Message Format
```json
{
    "msgtype": "markdown",
    "markdown": {
        "content": "## 🔐 Claude Code Permission Check\n\n> ⚠️ Sensitive operation detected\n\n**Project:** test-project\n**Operation:** `sudo systemctl restart nginx`\n\nPlease confirm in terminal"
    }
}
```

---

## 🤖 Telegram Bot

### Steps

1. Create Bot
   - Find @BotFather in Telegram
   - Send `/newbot`
   - Set bot name and username
   - Get Bot Token

2. Get Chat ID
```bash
# Send a message to your bot, then visit:
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# Read chat.id from the response
```

3. Configuration
```yaml
channels:
  telegram:
    enabled: true
    bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    chat_id: "-1001234567890"  # group ID or personal chat ID
```

### Message Format
```json
{
    "chat_id": "-1001234567890",
    "text": "🔐 *Claude Code Permission Check*\n\n⚠️ Sensitive operation detected\n\n📂 Project: test\\-project\n⚡ Operation: `sudo systemctl restart nginx`\n\n💡 Please confirm in terminal",
    "parse_mode": "MarkdownV2"
}
```

### Troubleshooting

1. Bot can’t send messages
   - Ensure bot is added to the group
   - Check send message permissions

2. Wrong Chat ID
   - Personal chat: positive integer
   - Group chat: negative integer (starts with -100)

---

## 📮 SMTP Email

### Steps

1. Gmail (recommended)
   - Enable 2FA
   - Create an App Password
   - Use App Password instead of account password

2. Configuration
```yaml
channels:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"  # app password
    from_email: "your-email@gmail.com"
    to_email: "recipient@example.com"
    use_tls: true
```

### Supported Providers

| Provider | SMTP Server | Port | Encryption |
|---------|-------------|------|------------|
| Gmail | smtp.gmail.com | 587 | TLS |
| Outlook | smtp.office365.com | 587 | TLS |
| QQ Mail | smtp.qq.com | 587 | TLS |
| 163 Mail | smtp.163.com | 25 | None/TLS |
| Enterprise | mail.company.com | 587 | TLS |

### HTML Email Template
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { padding: 20px; border: 1px solid #e9ecef; }
        .footer { background: #f8f9fa; padding: 10px 20px; border-radius: 0 0 8px 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔐 Claude Code Permission Check</h2>
        </div>
        <div class="content">
            <p>⚠️ Sensitive operation detected</p>
            <ul>
                <li><strong>Project:</strong> {{ project }}</li>
                <li><strong>Operation:</strong> <code>{{ operation }}</code></li>
                <li><strong>Time:</strong> {{ timestamp }}</li>
            </ul>
            <p>💡 Please confirm in your terminal</p>
        </div>
        <div class="footer">
            <small>Claude Code Notifier — Smart Dev Assistant</small>
        </div>
    </div>
</body>
</html>
```

---

## 📧 ServerChan

### Steps

1. Get SendKey
   - Visit https://sct.ftqq.com/
   - Login with WeChat
   - Copy SendKey

2. Configuration
```yaml
channels:
  serverchan:
    enabled: true
    send_key: "SCTxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Message Format
```json
{
    "title": "🔐 Claude Code Permission Check",
    "desp": "⚠️ Sensitive operation detected\n\n**Project:** test-project\n**Operation:** sudo systemctl restart nginx\n\n💡 Please confirm in terminal"
}
```

---

## Multi-channel Strategies

### By Event Type
```yaml
events:
  # High-priority → Multi-channel
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "telegram", "email"]
    
  # Normal → Single channel
  task_completion:
    enabled: true
    channels: ["dingtalk"]
    
  # Low priority → Email
  session_info:
    enabled: true
    channels: ["email"]
```

### By Working Hours
```yaml
advanced:
  time_based_routing:
    work_hours:  # real-time notifications
      start: "09:00"
      end: "18:00"
      channels: ["dingtalk", "feishu"]
      
    after_hours:  # send via email with delay
      channels: ["email"]
      delay: 300  # delay 5 minutes
```

### Channel Priority
```yaml
channels:
  dingtalk:
    enabled: true
    priority: 1  # highest
    
  telegram:
    enabled: true
    priority: 2
    
  email:
    enabled: true
    priority: 3  # lowest, as fallback
```

## Performance Tips

1. Async Sending
```yaml
advanced:
  performance:
    async_send: true
    max_concurrent: 3
```

2. Message Grouping
```yaml
intelligence:
  message_grouper:
    enabled: true
    group_window: 60
    max_group_size: 5
```

3. Rate Limiting
```yaml
intelligence:
  notification_throttle:
    enabled: true
    max_per_minute: 10
    cooldown_period: 300
```

## Security Best Practices

1. Environment Variables
```bash
export CLAUDE_NOTIFIER_DINGTALK_SECRET="your_secret"
export CLAUDE_NOTIFIER_TELEGRAM_TOKEN="your_token"
```

2. Rotate Secrets Regularly
- Quarterly key rotation
- Strong passwords for email
- Enable 2FA

3. Network Security
```yaml
advanced:
  security:
    validate_ssl: true
    timeout: 30
    retry_attempts: 3
```

4. Message Content Safety
- Avoid sensitive data in notifications
- Use truncation and filtering
- Enable message encryption (enterprise)

## Troubleshooting Guide

### General

1. Network connectivity
```bash
curl -I https://oapi.dingtalk.com
```

2. Configuration validation
```bash
claude-notifier config validate

# Test a specific channel
claude-notifier test --channel dingtalk
```

3. Logs
```bash
tail -f ~/.claude-notifier/logs/notifier.log

# Debug mode
CLAUDE_NOTIFIER_DEBUG=1 claude-notifier test
```

### Channel-specific

See each channel’s troubleshooting section. For more help, check:
- Configuration Guide: configuration_en.md
- Developer Docs: development_en.md
- GitHub Issues: https://github.com/your-repo/claude-code-notifier/issues

# 📱 通知渠道配置指南

## 支持的渠道概览

| 渠道 | 状态 | 特性 | 配置难度 |
|------|------|------|----------|
| 🔔 钉钉机器人 | ✅ 完善 | ActionCard + Markdown + 签名验证 | ⭐⭐ |
| 🚀 飞书机器人 | ✅ 完善 | 富文本 + 交互卡片 | ⭐⭐ |
| 💼 企业微信机器人 | ✅ 完善 | Markdown + 图文消息 | ⭐⭐ |
| 🤖 Telegram | ✅ 完善 | Bot 消息推送 | ⭐⭐⭐ |
| 📮 邮箱 SMTP | ✅ 完善 | HTML 邮件 | ⭐⭐⭐⭐ |
| 📧 Server酱 | ✅ 完善 | 微信推送 | ⭐ |

## 🔔 钉钉机器人

### 配置步骤

1. **创建机器人**
   - 打开钉钉群聊，点击右上角设置
   - 选择"机器人" → "添加机器人"
   - 选择"自定义机器人"，填写机器人名称
   - 安全设置选择"加签"模式（推荐）

2. **获取配置信息**
   - 复制 Webhook URL
   - 复制签名密钥（SEC开头的字符串）

3. **配置文件设置**
```yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    secret: "SECxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 可选，但推荐使用
```

### 消息格式

**权限确认 (ActionCard 格式)**
```json
{
    "msgtype": "actionCard",
    "actionCard": {
        "title": "🔐 Claude Code 权限检测",
        "text": "### ⚠️ 检测到敏感操作\n\n> Claude Code 已自动暂停执行\n\n**📂 项目:** test-project\n**⚡ 操作:** sudo systemctl restart nginx\n\n💡 请在终端中确认操作",
        "singleTitle": "📱 查看终端",
        "singleURL": "https://claude.ai"
    }
}
```

**任务完成 (Markdown 格式)**
```json
{
    "msgtype": "markdown",
    "markdown": {
        "title": "✅ Claude Code 任务完成",
        "text": "### 🎉 工作完成，可以休息了！\n\n**📂 项目:** test-project\n**📋 状态:** 代码重构任务已完成\n**⏰ 时间:** 2025-08-20 15:30:20\n\n☕ 建议您休息一下或检查结果"
    }
}
```

### 故障排除

1. **发送失败 (错误码 310000)**
   - 检查 Webhook URL 是否正确
   - 验证机器人是否被添加到群聊

2. **签名验证失败**
   - 确认密钥格式正确（包含 SEC 前缀）
   - 检查时间戳计算是否准确

---

## 🚀 飞书机器人

### 配置步骤

1. **创建机器人**
   - 进入飞书群聊，点击右上角设置
   - 选择"机器人" → "添加机器人"
   - 选择"Custom Bot"，设置机器人信息

2. **获取 Webhook**
   - 复制生成的 Webhook URL

3. **配置文件设置**
```yaml
channels:
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK_ID"
```

### 消息格式

**富文本消息**
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
                    "content": "🔐 **Claude Code 权限检测**\n\n⚠️ 检测到敏感操作\n📂 项目: test-project\n⚡ 操作: sudo systemctl restart nginx",
                    "tag": "lark_md"
                }
            }
        ],
        "header": {
            "title": {
                "content": "权限确认通知",
                "tag": "plain_text"
            },
            "template": "orange"
        }
    }
}
```

---

## 💼 企业微信机器人

### 配置步骤

1. **创建机器人**
   - 进入企业微信群聊
   - 右键群聊 → 添加群机器人
   - 选择"自定义机器人"

2. **获取配置信息**
   - 复制 Webhook URL

3. **配置文件设置**
```yaml
channels:
  wechat_work:
    enabled: true
    webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
```

### 消息格式

```json
{
    "msgtype": "markdown",
    "markdown": {
        "content": "## 🔐 Claude Code 权限检测\n\n> ⚠️ 检测到敏感操作\n\n**项目:** test-project\n**操作:** `sudo systemctl restart nginx`\n\n请在终端中确认操作"
    }
}
```

---

## 🤖 Telegram Bot

### 配置步骤

1. **创建 Bot**
   - 在 Telegram 中找到 @BotFather
   - 发送 `/newbot` 命令
   - 按提示设置 Bot 名称和用户名
   - 获取 Bot Token

2. **获取 Chat ID**
   ```bash
   # 给你的 Bot 发送一条消息，然后访问：
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   # 从响应中获取 chat.id
   ```

3. **配置文件设置**
```yaml
channels:
  telegram:
    enabled: true
    bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    chat_id: "-1001234567890"  # 群组 ID 或个人 Chat ID
```

### 消息格式

```json
{
    "chat_id": "-1001234567890",
    "text": "🔐 *Claude Code 权限检测*\n\n⚠️ 检测到敏感操作\n\n📂 项目: test\\-project\n⚡ 操作: `sudo systemctl restart nginx`\n\n💡 请在终端中确认操作",
    "parse_mode": "MarkdownV2"
}
```

### 故障排除

1. **Bot 无法发送消息**
   - 确认 Bot 已被添加到群组
   - 检查 Bot 是否有发送消息权限

2. **Chat ID 错误**
   - 个人聊天：正整数
   - 群组聊天：负整数（以 -100 开头）

---

## 📮 SMTP 邮箱

### 配置步骤

1. **Gmail 配置（推荐）**
   - 开启二步验证
   - 生成应用程序密码
   - 使用应用程序密码而非账户密码

2. **配置文件设置**
```yaml
channels:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"  # 应用程序密码
    from_email: "your-email@gmail.com"
    to_email: "recipient@example.com"
    use_tls: true
```

### 支持的邮件服务商

| 服务商 | SMTP 服务器 | 端口 | 加密 |
|--------|-------------|------|------|
| Gmail | smtp.gmail.com | 587 | TLS |
| Outlook | smtp.office365.com | 587 | TLS |
| QQ 邮箱 | smtp.qq.com | 587 | TLS |
| 163 邮箱 | smtp.163.com | 25 | 无/TLS |
| 企业邮箱 | mail.company.com | 587 | TLS |

### HTML 邮件模板

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
            <h2>🔐 Claude Code 权限检测</h2>
        </div>
        <div class="content">
            <p>⚠️ 检测到敏感操作</p>
            <ul>
                <li><strong>项目:</strong> {{ project }}</li>
                <li><strong>操作:</strong> <code>{{ operation }}</code></li>
                <li><strong>时间:</strong> {{ timestamp }}</li>
            </ul>
            <p>💡 请在终端中确认操作</p>
        </div>
        <div class="footer">
            <small>Claude Code Notifier - 智能开发助手</small>
        </div>
    </div>
</body>
</html>
```

---

## 📧 Server酱

### 配置步骤

1. **获取 SendKey**
   - 访问 [Server酱官网](https://sct.ftqq.com/)
   - 使用微信登录
   - 复制 SendKey

2. **配置文件设置**
```yaml
channels:
  serverchan:
    enabled: true
    send_key: "SCTxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 消息格式

```json
{
    "title": "🔐 Claude Code 权限检测",
    "desp": "⚠️ 检测到敏感操作\n\n**项目:** test-project\n**操作:** sudo systemctl restart nginx\n\n💡 请在终端中确认操作"
}
```

---

## 多渠道配置策略

### 按事件类型配置

```yaml
events:
  # 高优先级事件 → 多渠道通知
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "telegram", "email"]
    
  # 普通事件 → 单一渠道
  task_completion:
    enabled: true
    channels: ["dingtalk"]
    
  # 低优先级事件 → 邮件通知
  session_info:
    enabled: true
    channels: ["email"]
```

### 按工作时间配置

```yaml
advanced:
  time_based_routing:
    work_hours:  # 工作时间：即时通知
      start: "09:00"
      end: "18:00"
      channels: ["dingtalk", "feishu"]
      
    after_hours:  # 非工作时间：邮件通知
      channels: ["email"]
      delay: 300  # 延迟5分钟发送
```

### 渠道优先级配置

```yaml
channels:
  dingtalk:
    enabled: true
    priority: 1  # 最高优先级
    
  telegram:
    enabled: true
    priority: 2
    
  email:
    enabled: true
    priority: 3  # 最低优先级，作为备用
```

## 性能优化建议

1. **异步发送**
   ```yaml
   advanced:
     performance:
       async_send: true
       max_concurrent: 3
   ```

2. **消息合并**
   ```yaml
   intelligence:
     message_grouper:
       enabled: true
       group_window: 60
       max_group_size: 5
   ```

3. **限流保护**
   ```yaml
   intelligence:
     notification_throttle:
       enabled: true
       max_per_minute: 10
       cooldown_period: 300
   ```

## 安全最佳实践

1. **使用环境变量**
   ```bash
   export CLAUDE_NOTIFIER_DINGTALK_SECRET="your_secret"
   export CLAUDE_NOTIFIER_TELEGRAM_TOKEN="your_token"
   ```

2. **定期更新密钥**
   - 每季度更新 API 密钥
   - 使用强密码保护邮箱账户
   - 启用二步验证

3. **网络安全**
   ```yaml
   advanced:
     security:
       validate_ssl: true
       timeout: 30
       retry_attempts: 3
   ```

4. **消息内容安全**
   - 避免在通知中包含敏感信息
   - 使用消息截断和过滤
   - 启用消息加密（企业版功能）

## 故障排除指南

### 通用问题

1. **网络连接问题**
   ```bash
   # 测试网络连通性
   curl -I https://oapi.dingtalk.com
   ```

2. **配置验证**
   ```bash
   # 验证配置文件
   claude-notifier config validate
   
   # 测试特定渠道
   claude-notifier test --channel dingtalk
   ```

3. **日志分析**
   ```bash
   # 查看详细日志
   tail -f ~/.claude-notifier/logs/notifier.log
   
   # 调试模式运行
   CLAUDE_NOTIFIER_DEBUG=1 claude-notifier test
   ```

### 渠道特定问题

详见各渠道的故障排除部分。如需更多帮助，请查看：
- [配置指南](configuration.md)
- [开发文档](development.md)
- [GitHub Issues](https://github.com/your-repo/claude-code-notifier/issues)
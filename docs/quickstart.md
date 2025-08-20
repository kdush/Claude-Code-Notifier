# 🚀 快速开始

## 系统要求

- Python 3.6+
- Claude Code (推荐最新版本)
- macOS / Linux / Windows

## 一分钟安装

```bash
# 1. 克隆项目
git clone https://github.com/your-username/claude-code-notifier.git
cd claude-code-notifier

# 2. 运行安装脚本
./install.sh

# 3. 配置通知渠道
./scripts/configure.sh

# 4. 测试通知功能
./scripts/test.sh
```

## 配置示例

### 钉钉机器人
1. 在钉钉群中添加自定义机器人
2. 获取 Webhook URL 和密钥
3. 运行配置向导，选择钉钉机器人
4. 输入 URL 和密钥

### 飞书机器人
1. 在飞书群中添加自定义机器人
2. 获取 Webhook URL
3. 运行配置向导，选择飞书机器人
4. 输入 URL

### Telegram Bot
1. 与 @BotFather 对话创建 Bot
2. 获取 Bot Token
3. 获取 Chat ID (可以通过给 Bot 发消息后访问 API 获取)
4. 运行配置向导，选择 Telegram Bot

## 使用效果

安装完成后，在任何项目中使用 Claude Code：

```bash
cd your-project
claude

# 当 Claude Code 执行敏感操作时 → 📱 收到权限确认通知
# 当 Claude Code 完成任务时 → 📱 收到完成庆祝通知
```

## 故障排除

### 通知发送失败
1. 检查网络连接
2. 验证配置信息
3. 查看日志: `~/.claude-notifier/logs/notifier.log`

### Claude Code 钩子不生效
1. 确认 Claude Code 版本支持钩子
2. 检查 `~/.claude/settings.json` 配置
3. 重启 Claude Code

## 获取帮助

- 📖 [完整文档](../README.md)
- 🐛 [问题反馈](https://github.com/your-username/claude-code-notifier/issues)
- 💬 [讨论区](https://github.com/your-username/claude-code-notifier/discussions)

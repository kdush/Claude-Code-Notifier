<div align="center">

# 🔔 Claude Code Notifier

<img src="assets/logo.png" alt="Claude Code Notifier Logo" width="200" height="200">

**一个强大的 Claude Code 通知系统，支持多种通知渠道，让你随时掌握 Claude Code 的执行状态。**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![GitHub Stars](https://img.shields.io/github/stars/kdush/Claude-Code-Notifier?style=social)](https://github.com/kdush/Claude-Code-Notifier)

</div>

## ✨ 特性

- 🎯 **智能检测** - 自动检测权限操作和任务完成
- 🌍 **全局生效** - 一次配置，所有项目自动启用  
- 🔌 **多渠道支持** - 支持 10+ 种通知渠道
- 🎨 **美化通知** - 精美的卡片格式和分层设计
- ⚙️ **易于配置** - 简单的配置文件和安装脚本
- 🔒 **安全可靠** - 支持签名验证和加密传输
- 🎛️ **事件开关** - 灵活的事件启用/禁用配置
- 🔧 **自定义事件** - 支持用户自定义触发条件和通知内容
- 📋 **模板系统** - 可自定义通知卡片样式和内容
- 🔄 **多渠道路由** - 不同事件可配置不同的通知渠道组合
- ⏰ **智能限流** - 防止通知轰炸，支持冷却时间和频率控制
- 📊 **统计监控** - 事件统计和通知效果分析

## 📱 支持的通知渠道

| 渠道 | 状态 | 特性 |
|------|------|------|
| 🔔 钉钉机器人 | ✅ | ActionCard + Markdown |
| 🚀 飞书机器人 | ✅ | 富文本 + 交互卡片 |
| 💼 企业微信机器人 | ✅ | Markdown + 图文消息 |
| 🤖 Telegram | ✅ | Bot 消息推送 |
| 📮 邮箱 | ✅ | SMTP 邮件推送 |
| 📧 Server酱 | ✅ | 微信推送 |

## 🚀 快速开始

### 方式一：快速配置（推荐）

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
chmod +x install.sh scripts/quick_setup.py
./install.sh
python3 scripts/quick_setup.py
```

快速配置脚本将引导您：
- 📱 配置通知渠道（钉钉、飞书、Telegram、邮箱等）
- 🎯 选择要启用的事件类型
- 🔧 添加自定义事件
- ⚙️ 设置高级选项（频率限制、静默时间等）
- 🧪 测试通知配置

### 方式二：手动配置

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
chmod +x install.sh
./install.sh

# 复制配置模板
cp config/enhanced_config.yaml.template config/config.yaml

# 编辑配置文件
vim config/config.yaml
```

### 3. 测试

```bash
./scripts/test.sh

# 测试特定渠道
./scripts/test.sh --channel dingtalk
```

## 📋 使用场景

### 🔐 权限确认通知
当 Claude Code 检测到敏感操作时：
- 自动暂停执行
- 发送权限确认通知
- 在终端中等待用户确认

### ✅ 任务完成通知  
当 Claude Code 完成所有任务时：
- 发送完成庆祝通知
- 显示执行摘要
- 提供操作建议

## 📊 通知效果预览

### 钉钉机器人通知

**权限确认 (ActionCard 格式)**
```
🔐 Claude Code 权限检测

---

⚠️ 检测到敏感操作

> Claude Code 已自动暂停执行

---

📂 项目: my-awesome-project
⚡ 操作: sudo systemctl restart nginx

💡 请在终端中确认操作

[📱 查看终端] 按钮
```

**任务完成 (Markdown 格式)**
```
✅ Claude Code 任务完成

🎉 工作完成，可以休息了！

📂 项目: my-awesome-project  
📋 状态: 代码重构任务已完成
⏰ 时间: 2025-08-20 15:30:20

☕ 建议您休息一下或检查结果
```

## ⚙️ 配置文件

配置文件位于 `~/.claude-notifier/config.yaml`：

```yaml
# 通知渠道配置
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=..."
    secret: "SEC..."
    
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/..."

# 通知设置
notifications:
  permission:
    enabled: true
    channels: ["dingtalk", "feishu"]
    
  completion:
    enabled: true
    channels: ["dingtalk"]
    delay: 3

# 检测规则
detection:
  permission_patterns:
    - "sudo"
    - "rm -"
    - "chmod"
    - "git push"
    - "npm publish"
    - "docker"
    - "kubectl"
```

## 🛠️ 开发指南

### 添加新的通知渠道

1. 在 `src/channels/` 创建新的渠道文件
2. 实现 `BaseChannel` 接口
3. 在配置文件中添加渠道配置
4. 更新文档和测试

### 自定义检测规则

编辑 `~/.claude-notifier/config.yaml` 中的 `detection` 部分。

## 📚 文档

- [快速开始](docs/quickstart.md)
- [配置指南](docs/configuration.md)
- [渠道配置](docs/channels.md)
- [开发文档](docs/development.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Apache License

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kdush/Claude-Code-Notifier&type=Date)](https://star-history.com/#kdush/Claude-Code-Notifier&Date)


---

> 💡 让 Claude Code 更智能，让开发更高效！

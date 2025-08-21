[中文文档](README.md)

# 🔔 Claude Code Notifier

<p align="center">
  <img src="assets/logo.png" alt="Claude Code Notifier Logo" width="160">
</p>

An intelligent Claude Code notification system providing real-time, multi-channel notifications and smart throttling/controls.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%2B-brightgreen.svg)](tests/)
[![Performance](https://img.shields.io/badge/performance-244K%20ops%2Fs-orange.svg)](tests/test_performance_benchmarks.py)
[![Release](https://img.shields.io/badge/release-Beta-orange.svg)](#)

## ✨ Features

### 🎯 Core
- Smart detection for privileged operations and task completion
- Global enablement via one-time setup across projects
- 6+ popular notification channels
- Beautified messages with rich cards and layered design
- Easy configuration with scripts and templates
- Secure with signature verification and encrypted transport

### 🧠 Intelligence
- Smart rate limiting to prevent notification flooding
- Message grouping for deduplication
- Operation gating for sensitive actions with user confirmation
- Adaptive strategy tuning based on usage patterns

### ⚙️ Advanced Configuration
- Event toggles with fine-grained control
- Custom events with user-defined triggers and payloads
- Template engine with unified styles
- Multi-channel routing per event type
- Metrics and effectiveness analysis
- Config backup and restore

## 🆕 What's New (v0.0.3b1 - Beta)

- PEP 440 compliant versioning adopted for pre-releases (`a`/`b`/`rc`), e.g., `0.0.3b1`
- CLI `--version` now shows “Version Type: Beta” and a pre-release warning line
- README adds a Beta badge to highlight current pre-release status
- CI/CD: automatically publish pre-releases to TestPyPI; stable releases to PyPI

## 📱 Supported Channels

| Channel | Status | Features |
|--------|--------|----------|
| 🔔 DingTalk Bot | ✅ | ActionCard + Markdown |
| 🔗 Webhook | ✅ | HTTP callback + Multi-format + Multi-auth |
| 🚀 Feishu (Lark) Bot | 🚧 In Development | Rich text + Interactive cards |
| 💼 WeCom (WeChat Work) Bot | 🚧 In Development | Markdown + News |
| 🤖 Telegram | 🚧 In Development | Bot message push |
| 📮 Email | 🚧 In Development | SMTP delivery |
| 📧 ServerChan | 🚧 In Development | WeChat push |

## 🚀 Quick Start

### Method 1: Quick Setup (Recommended)

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
chmod +x install.sh scripts/quick_setup.py
./install.sh
python3 scripts/quick_setup.py
```

The quick setup script will guide you to:
- Configure channels (DingTalk, Feishu/Lark, Telegram, Email, etc.)
- Select event types to enable
- Add custom events
- Set advanced options (rate limits, quiet hours, etc.)
- Test your notification setup

### Method 2: Manual Setup

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
chmod +x install.sh
./install.sh

# Copy config template
cp config/enhanced_config.yaml.template config/config.yaml

# Edit configuration
vim config/config.yaml
```

### 3. Test

```bash
./scripts/test.sh

# Test a specific channel
./scripts/test.sh --channel dingtalk
```

## 📋 Use Cases

### 🔐 Permission Confirmation
When Claude Code detects a sensitive operation:
- Execution is paused automatically
- A confirmation notification is sent
- Terminal waits for your confirmation

### ✅ Task Completion
When Claude Code finishes all tasks:
- A celebration notification is sent
- Execution summary is shown
- Action suggestions are provided

## 📊 Notification Previews

### DingTalk Bot

**Permission Confirmation (ActionCard)**
```
🔐 Claude Code Permission Check

---

⚠️ Sensitive operation detected

> Claude Code paused execution automatically

---

📂 Project: my-awesome-project
⚡ Operation: sudo systemctl restart nginx

💡 Please confirm in your terminal

[📱 Open Terminal] button
```

**Task Completion (Markdown)**
```
✅ Claude Code Task Completed

🎉 Great job! It's time for a break.

📂 Project: my-awesome-project  
📋 Status: Code refactor task completed
⏰ Time: 2025-08-20 15:30:20

☕ Consider taking a break or reviewing the results
```

## ⚙️ Configuration

Config file path: `~/.claude-notifier/config.yaml`

```yaml
# Channels configuration
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=..."
    secret: "SEC..."
  
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/..."

# Notification settings
notifications:
  permission:
    enabled: true
    channels: ["dingtalk", "feishu"]
  
  completion:
    enabled: true
    channels: ["dingtalk"]
    delay: 3

# Detection rules
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

## 🛠️ Development Guide

### Add a New Channel
1. Create a new file under `src/claude_notifier/core/channels/`
2. Implement the `BaseChannel` interface and required class attributes
3. Register the channel in `src/claude_notifier/core/channels/__init__.py`
4. Add channel configuration template to config file
5. Update documentation and tests

See `docs/development.md` for detailed development guide

### Custom Detection Rules
Edit the `detection` section in `~/.claude-notifier/config.yaml`.

## 🔧 CLI Examples

```bash
# Send a notification
claude-notifier send "Hello World!"

# Test configuration
claude-notifier test

# Show status
claude-notifier status --intelligence

# Config management
claude-notifier config show
claude-notifier config backup

# Real-time monitor
claude-notifier monitor --watch

# System diagnostics
claude-notifier debug diagnose --full
```

## 📚 Documentation

- Quickstart: `docs/quickstart.md` (Chinese)
- Configuration: `docs/configuration.md` (Chinese)
- Channels: `docs/channels.md` (Chinese)
- Advanced Usage: `docs/advanced-usage.md` (Chinese)
- Development: `docs/development.md` (Chinese)

## 📊 Usage Analytics

This project integrates with [ccusage](https://github.com/ryoppippi/ccusage) to analyze Claude Code token usage and costs:

```bash
# Analyze local usage data
npx ccusage
bunx ccusage

# Monthly stats
ccusage --monthly

# Generate usage report
ccusage --output usage-report.json
```

ccusage features:
- Token usage analytics with detailed breakdowns
- Cost tracking per Claude model
- Time-based reports (daily/monthly/session)
- Real-time monitoring of 5-hour billing windows
- Offline analysis from local JSONL files

Thanks to [@ryoppippi](https://github.com/ryoppippi) for this great tool!

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

Apache License

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kdush/Claude-Code-Notifier&type=Date)](https://star-history.com/#kdush/Claude-Code-Notifier&Date)

---

> 💡 Make Claude Code smarter. Make development more efficient!

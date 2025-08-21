[中文文档](quickstart.md)

# 🚀 Quick Start Guide

## 🔧 System Requirements

- Python: 3.8+ (3.9+ recommended)
- Claude Code: Latest version
- OS: macOS / Linux / Windows
- Network: Access to notification service APIs

## ⚡ One‑Minute Installation

### Method 1: PyPI Installation (Recommended for General Users) 🚀

```bash
# 1. Install latest version
pip install claude-code-notifier

# 2. Verify installation
claude-notifier --version

# 3. 🚀 One-Click Smart Setup (New Feature!)
claude-notifier setup --auto

# 4. Test configuration
claude-notifier test
```

**🎉 New Feature Highlights**:
- ✅ **Auto Claude Code Detection** - Smart discovery of various installation locations
- ✅ **One-Click Hook Setup** - Automatic Claude Code integration
- ✅ **Complete CLI Support** - hooks install/status/verify commands
- ✅ **Zero Manual Config** - Intelligent setup process

### Method 2: Git Installation (For Developers)

#### 2.1 Automated Install (Recommended)

```bash
# 1. Clone the project
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier

# 2. Run the one‑click install script
chmod +x install.sh scripts/quick_setup.py
./install.sh

# 3. Start the interactive setup wizard
python3 scripts/quick_setup.py
```

#### 2.2 Manual Install

```bash
# 1. Clone and enter the project
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Copy config template
cp config/enhanced_config.yaml.template ~/.claude-notifier/config.yaml

# 4. Edit configuration
vim ~/.claude-notifier/config.yaml

# 5. Test configuration
./scripts/test.sh
```

### 📊 Installation Method Comparison

| Feature | PyPI Install | Git Install |
|---------|-------------|-------------|
| ⚡ Install Speed | 30 seconds | 2-3 minutes |
| 🎯 Target Users | General users | Developers |
| 🔧 Config Complexity | One-click | Manual setup |
| 🚀 Claude Code Integration | ✅ Automatic | ✅ Automatic |
| 📦 Update Method | `pip install --upgrade` | `git pull` |

## 🛠️ PyPI User Configuration Guide

### 💡 Smart Configuration Process

```bash
# 🚀 One-Click Setup (Recommended)
claude-notifier setup --auto

# 🔧 Interactive Configuration
claude-notifier setup

# 📊 Check Configuration Status
claude-notifier --status
```

### 🔗 Claude Code Hook Management

```bash
# Install Claude Code hooks
claude-notifier hooks install

# View hook status
claude-notifier hooks status

# Verify hook configuration
claude-notifier hooks verify

# Uninstall hooks (if needed)
claude-notifier hooks uninstall
```

**Hook Features Explanation**:
- 🎯 **Session Notifications** - Notifications when Claude Code starts
- 📋 **Task Tracking** - Automatic task execution status tracking
- ⚠️ **Error Monitoring** - Real-time notifications for exceptions
- 🔐 **Permission Checks** - Confirmation notifications for sensitive operations

## 📱 Quick Channel Configuration

### DingTalk Bot (Recommended)
```bash
# PyPI users - Use configuration wizard
claude-notifier setup

# Git users - Interactive setup
python3 scripts/quick_setup.py

# Manual steps:
# 1. DingTalk group → Settings → Bot → Add Bot → Custom Bot
# 2. Security setting: choose "HMAC Sign", obtain Webhook URL and Secret
# 3. Fill webhook and secret in your config file
```

### Feishu (Lark) Bot
```bash
# 1. Lark group → Settings → Bot → Add Bot → Custom Bot
# 2. Obtain the Webhook URL 
# 3. Fill the webhook in your config file
```

### Other Channels
- WeCom (WeChat Work): Markdown messages and rich cards supported
- Telegram: Requires Bot Token and Chat ID
- SMTP Email: Gmail, Outlook, enterprise mail supported
- ServerChan: WeChat push with SendKey only

Detailed configuration: [📖 Channel Guide](channels_en.md)

## 🎯 Smart Features

### Smart Operation Control
```bash
# When Claude Code attempts sensitive operations:
claude implement "delete temp files"
# → 🛡️ Automatically detects 'rm -rf' operations
# → 📱 Sends permission confirmation
# → ⏸️ Pauses execution awaiting confirmation
```

### Intelligent Notification Rate Limiting
```bash
# Prevent notification floods by grouping similar messages
claude analyze large-project/
# → 🧠 Automatically groups related notifications
# → ⏰ Intelligently throttles sending frequency
# → 📊 Real‑time delivery stats
```

### Real‑time Monitoring Dashboard
```bash
# View system status and statistics
claude-notifier status
claude-notifier stats --days 7
claude-notifier monitor  # Real‑time dashboard
```

## 🚀 Usage Scenarios

### Scenario 1: Sensitive Operation Guard
```bash
cd your-project
claude

# User: "Please remove node_modules directory"
# Claude Code: Prepares to run 'rm -rf node_modules'
# → 📱 DingTalk: "🔐 Sensitive operation detected: rm -rf node_modules"
# → 📱 "Project: your-project, please confirm to proceed"
# → ⏸️ Waits for terminal confirmation
```

### Scenario 2: Task Completion Celebration
```bash
# User: "Refactor this module"
# Claude Code: Finishes refactor
# → 📱 DingTalk: "🎉 Claude Code task completed!"
# → 📱 "Project: your-project"
# → 📱 "Status: Refactor completed"
# → 📱 "Suggestion: Review code quality"
```

### Scenario 3: Performance Monitoring
```bash
# Automatic performance monitoring
# → 📊 Throughput: 244K+ ops/sec capability
# → 📈 Monitoring: Zero memory leaks
# → ⚡ Latency: <1ms average response time
# → 🎯 Success: 99.9% notification delivery rate
```

## 🔧 Verify Installation

### System Self‑Check
```bash
# Check install status
claude-notifier --version
claude-notifier health

# Validate configuration
claude-notifier config validate

# Test all channels
claude-notifier test --all-channels
```

### Performance Verification
```bash
# Run performance benchmarks
python tests/test_performance_benchmarks.py

# Expected metrics: 244K+ ops/s, zero memory leaks, <1ms latency
```

## 🛠️ Troubleshooting

### Notification Delivery Failure
```bash
# 1. Check network connectivity
curl -I https://oapi.dingtalk.com

# 2. Validate configuration
claude-notifier config validate

# 3. Inspect detailed logs
tail -f ~/.claude-notifier/logs/notifier.log

# 4. Test a specific channel
claude-notifier test --channel dingtalk --debug
```

### Smart Feature Issues
```bash
# 1. Check intelligence component status
claude-notifier monitor

# 2. Reset intelligence configuration
claude-notifier config reset --intelligence

# 3. Inspect component logs
grep "intelligence" ~/.claude-notifier/logs/notifier.log
```

### Claude Code Hook Issues
```bash
# 1. Verify hook installation status
ls -la ~/.claude/hooks/

# 2. Check Claude Code settings
cat ~/.claude/settings.json | jq '.hooks'

# 3. Reinstall hooks
claude-notifier hooks install --force

# 4. Restart Claude Code
pkill claude && claude
```

### Performance Diagnostics
```bash
# 1. Inspect system resource usage
claude-notifier stats --resource

# 2. Analyze notification latency
claude-notifier benchmark --latency

# 3. Check cache status
claude-notifier cache status
```

## 📚 Learn More

### Next Steps
1. 📖 [Configuration Guide](configuration_en.md) — Explore all options in depth
2. 📱 [Channel Guide](channels_en.md) — Configure various notification channels
3. 🛠️ [Developer Docs](development_en.md) — Architecture and extension development
4. 🤝 [Contributing Guide](contributing_en.md) — Get involved

### Community
- 📖 [Main Documentation](../README_en.md)
- 🐛 [Issues](https://github.com/kdush/Claude-Code-Notifier/issues)
- 💬 [Discussions](https://github.com/kdush/Claude-Code-Notifier/discussions)
- 🎥 [Video Tutorials](https://example.com/videos)
- 📱 [Community Group](https://example.com/community)

## 🎉 You're All Set!

Congrats! You’ve completed the quick setup for Claude Code Notifier.

Next, you can:
- ✨ Try the Smart Operation Protection
- 📊 View real‑time monitoring and stats
- 🔧 Tweak advanced configuration
- 🚀 Explore more channels and customization

Need help?
- Check the troubleshooting guide above
- Join the community for support
- Open an issue for assistance

Happy building! 🚀

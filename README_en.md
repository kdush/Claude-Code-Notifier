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

## 🆕 What's New (v0.0.3b4 - Beta)

### 🚀 PyPI Version Claude Code Hook Auto-Configuration (Major Update)

**🎉 Breakthrough Feature: PyPI users now enjoy the same seamless experience as Git users!**

- ✅ **⚡ One-Click Smart Setup** - `claude-notifier setup --auto` auto-detects and configures all features
- ✅ **🔧 Complete Hook Management** - New `hooks` command group provides install/uninstall/status/verify
- ✅ **💡 Smart Environment Detection** - Auto-discover Claude Code installation, supports multiple locations
- ✅ **📊 Enhanced Status Display** - `--status` now includes complete hook system status
- ✅ **🛡️ Error Recovery** - Works even with missing dependencies, provides graceful degradation
- ✅ **🔄 Dual-Mode Compatibility** - Hook system supports both PyPI and Git modes with smart switching

### 🔧 Version Management Improvements

- ✅ **PEP 440 Versioning** - Pre-release specification (`a`/`b`/`rc`), e.g., `0.0.3b4`
- ✅ **Enhanced CLI Version Info** - `--version` shows "Version Type: Beta" and pre-release warning
- ✅ **README Beta Badge** - Highlights current pre-release status
- ✅ **CI/CD Workflow** - GitHub Actions build and publish stable releases to PyPI; pre-releases via repo tags/releases

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

### Method 1: PyPI Installation (Recommended for General Users)

```bash
# Install latest stable version
pip install claude-code-notifier

# Or install specific version
pip install claude-code-notifier==0.0.3b4

# Verify installation
claude-notifier --version

# 🚀 One-Click Smart Setup (New Feature!)
claude-notifier setup --auto
```

**🎉 New Feature: PyPI version now supports Claude Code hook auto-configuration!**

After installation, the system will automatically:
- 📦 Create configuration directory `~/.claude-notifier/`
- ⚙️ Generate default configuration files
- 🔧 Set up CLI commands
- 🔍 **Smart Claude Code detection with integration prompts**
- ⚡ **One-click Claude Code hook configuration**

**Suitable for**: General users, quick setup, production use

### Method 2: Git Source Installation (For Developers)

#### 2.1 Smart Installation (Recommended)

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
./install.sh
```

**✨ New Smart Installation System Features**:
- 🎯 **Intelligent Mode Selection** - Auto-detect environment and recommend best installation method
- 📦 **Three Installation Modes** - PyPI/Git/Hybrid to meet different needs
- 🔄 **Auto-Update Mechanism** - Scheduled checks with one-click updates
- 🔗 **Unified Command Interface** - `cn` command auto-routes to correct execution method
- 📊 **Version Management** - Unified version info and upgrade paths

**Quick Setup**:
```bash
# Run configuration wizard after installation
python3 scripts/quick_setup.py
```

The quick setup script will guide you to:
- Configure channels (DingTalk, Feishu/Lark, Telegram, Email, etc.)
- Select event types to enable
- Add custom events
- Set advanced options (rate limits, quiet hours, etc.)
- Test your notification setup

#### 2.2 Manual Setup

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

**Suitable for**: Developers, contributors, custom features needed, testing latest features

### Installation Method Comparison

| Feature | PyPI Installation | Git Source Installation |
|---------|-------------------|------------------------|
| 🎯 Target Users | General users | Developers |
| ⚡ Installation Speed | Fast | Slower |
| 🔄 Update Method | `pip install --upgrade` | `git pull` + reinstall |
| 🧪 Version | Stable releases | Latest development |
| 🛠️ Customization | Basic configuration | Full customization |
| 📦 Dependency Management | Automatic | Manual |
| 🔗 Claude Code Integration | Manual setup | Auto Hook setup |
| 📁 Directory Structure | Standard Python package | Full project structure |

### Configuration and Testing

#### PyPI Users Configuration

```bash
# Initialize configuration
claude-notifier init

# Test notifications
claude-notifier test

# Check status
claude-notifier status
```

#### Unified Command Interface

**🔗 Regardless of installation method, use the unified `cn` command**:

```bash
# Smart command routing - auto-selects correct execution method
cn init      # Initialize configuration
cn test      # Test notifications
cn status    # Check status
cn --help    # Show help
```

#### Update Management

**🔄 Smart Update System**:

```bash
# Check for updates
python3 scripts/smart_update.py --check

# Perform update
python3 scripts/smart_update.py --update

# Enable auto-update
python3 scripts/smart_update.py --enable-auto

# Show update status
python3 scripts/smart_update.py --status
```

**Auto-Update Features**:
- ✅ Auto-detect installation type (PyPI/Git)
- ✅ Smart version comparison and updates
- ✅ Scheduled checks (daily)
- ✅ Configuration backup and migration
- ✅ Update logging

#### Git Source Users Testing

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

## 📦 Versioning and Pre-release Process

- **Versioning (PEP 440)**
  - Pre-releases: `aN` (Alpha), `bN` (Beta), `rcN` (Release Candidate), e.g., `0.0.3a1`, `0.0.3b4`, `0.0.3rc1`
  - Stable: remove the suffix, e.g., `0.0.3`
  - Version source file: `src/claude_notifier/__version__.py`

- **Pre-release policy**
  - Publish pre-releases via Git tags (e.g., `v0.0.3b4`) and create a repo Release with change notes
  - CLI `--version` displays “Version Type: Alpha/Beta/RC” and a pre-release notice
  - If distribution is needed, you may manually publish pre-releases to PyPI (optional)

- **Stable release (default)**
  - Tag `vX.Y.Z` triggers GitHub Actions to build (sdist + wheel) and publish to PyPI
  - Update `CHANGELOG.md` and docs accordingly

See details: `docs/development_en.md`

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

## 💻 Platform Compatibility

### Tested Environment
- ✅ **macOS 15** - Fully tested and supported
- 🚧 **Windows/Linux** - Theoretically supported, but not extensively tested

### Cross-Platform Compatibility
This project is designed with cross-platform compatibility in mind:
- 🪟 **Windows Support** - Hook installer has been optimized for Windows command line and path handling
- 🐧 **Linux Support** - Uses standard Python and shell commands, should work normally
- 🔧 **Automatic Platform Detection** - Code includes `os.name` and platform-specific processing logic

### Welcome Contributions
**🙏 We warmly invite users on other platforms to test and improve**:
- If you use it on Windows or Linux, please share your experience
- Please submit Issues for any problems you encounter, we will actively resolve them
- Welcome to submit platform-specific improvements and fixes via PR

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

Apache License

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kdush/Claude-Code-Notifier&type=Date)](https://star-history.com/#kdush/Claude-Code-Notifier&Date)

---

> 💡 Make Claude Code smarter. Make development more efficient!

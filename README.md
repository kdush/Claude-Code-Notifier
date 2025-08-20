# 🔔 Claude Code Notifier

![Claude Code Notifier Logo](assets/logo.png)

**智能化的 Claude Code 通知系统 - 提供实时、多渠道的操作通知和智能限制功能**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%2B-brightgreen.svg)](tests/)
[![Performance](https://img.shields.io/badge/performance-244K%20ops%2Fs-orange.svg)](tests/test_performance_benchmarks.py)

## ✨ 特性

### 🎯 核心功能
- **智能检测** - 自动检测权限操作和任务完成
- **全局生效** - 一次配置，所有项目自动启用  
- **多渠道支持** - 支持 6+ 种主流通知渠道
- **美化通知** - 精美的卡片格式和分层设计
- **易于配置** - 简单的配置文件和安装脚本
- **安全可靠** - 支持签名验证和加密传输

### 🧠 智能功能
- **智能限流** - 防止通知轰炸，支持冷却时间和频率控制
- **消息分组** - 自动合并相似通知，避免重复打扰
- **操作门控** - 智能识别敏感操作，需要用户确认
- **自适应调节** - 根据使用模式自动优化通知策略

### ⚙️ 高级配置
- **事件开关** - 灵活的事件启用/禁用配置
- **自定义事件** - 支持用户自定义触发条件和通知内容
- **模板系统** - 统一的模板引擎，支持自定义样式
- **多渠道路由** - 不同事件可配置不同的通知渠道组合
- **统计监控** - 事件统计和通知效果分析
- **配置备份** - 支持配置备份和恢复功能

## 🆕 最新改进 (v0.0.2)

- ✅ **配置系统增强** - 修复配置备份/恢复功能，确保配置安全
- ✅ **模板系统统一** - 统一模板引擎API，消除重复实现 
- ✅ **导入问题修复** - 解决模块导入问题，提高兼容性
- ✅ **文档完善** - 更新所有文档以反映当前功能状态

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

## 🔧 CLI 使用示例

```bash
# 发送通知
claude-notifier send "Hello World!"

# 测试配置
claude-notifier test

# 查看状态
claude-notifier status --intelligence

# 配置管理
claude-notifier config show
claude-notifier config backup

# 实时监控
claude-notifier monitor --watch

# 系统诊断
claude-notifier debug diagnose --full
```

## 📚 文档

- [快速开始](docs/quickstart.md) - 安装和基础配置
- [配置指南](docs/configuration.md) - 详细配置说明
- [渠道配置](docs/channels.md) - 各渠道具体配置
- [高级使用](docs/advanced-usage.md) - 自定义事件和高级功能
- [ccusage 集成](docs/ccusage-integration.md) - 使用统计和成本分析
- [开发文档](docs/development.md) - 架构和开发指南

## 📊 使用统计与分析

本项目集成了 [ccusage](https://github.com/ryoppippi/ccusage) 来分析 Claude Code 的 token 使用和成本统计：

```bash
# 分析本地使用数据
npx ccusage
bunx ccusage

# 查看月度统计
ccusage --monthly

# 生成使用报告
ccusage --output usage-report.json
```

**ccusage 功能**：
- 📈 **令牌使用分析** - 详细的 token 消费统计
- 💰 **成本追踪** - 不同 Claude 模型的费用分解  
- 📅 **时间段报告** - 日/月/会话级别的使用分析
- ⚡ **实时监控** - 5小时计费窗口监控
- 📊 **离线分析** - 基于本地 JSONL 文件的数据处理

感谢 [@ryoppippi](https://github.com/ryoppippi) 开发的这个优秀工具！

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Apache License

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kdush/Claude-Code-Notifier&type=Date)](https://star-history.com/#kdush/Claude-Code-Notifier&Date)


---

> 💡 让 Claude Code 更智能，让开发更高效！

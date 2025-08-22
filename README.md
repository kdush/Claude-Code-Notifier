[English Version](README_en.md)

# 🔔 Claude Code Notifier

<p align="center">
  <img src="assets/logo.png" alt="Claude Code Notifier Logo" width="160">
  
</p>

**智能化的 Claude Code 通知系统 - 提供实时、多渠道的操作通知和智能限制功能**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%2B-brightgreen.svg)](tests/)
[![Performance](https://img.shields.io/badge/performance-244K%20ops%2Fs-orange.svg)](tests/test_performance_benchmarks.py)
[![Release](https://img.shields.io/badge/release-Stable-brightgreen.svg)](#)

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

## 🆕 最新改进 (v0.0.5 - Stable)

### 🧰 CI/CD 与稳定性
- 修复并稳定跨平台 `test-install` 导入验证：移除 heredoc 与多进程导入测试，改为同步 `import` 并打印版本，避免 macOS/Windows 上 `<stdin>` 导致的 `FileNotFoundError`。
- 强化 GitHub Actions 跨平台一致性（macOS/Windows/Ubuntu），简化 `python -c` 使用以规避续行与转义差异。

### 📦 打包与内容优化
- 在 `MANIFEST.in` 明确 `prune src/hooks`，避免将原始钩子脚本打入 sdist；不影响包内 `claude_notifier/hooks` 资源。

### 🛠️ 其他修复
- 规范换行符处理，保证通知文本渲染正确。

### 🚀 PyPI版本Claude Code钩子自动配置（重大更新）

**🎉 突破性功能：PyPI用户现在享受与Git用户相同的无缝体验！**

- ✅ **⚡ 一键智能配置** - `claude-notifier setup --auto` 自动检测和配置所有功能
- ✅ **🔧 完整钩子管理** - 新增 `hooks` 命令组，提供安装/卸载/状态/验证功能
- ✅ **💡 智能环境检测** - 自动发现Claude Code安装，支持多种安装位置
- ✅ **📊 增强状态显示** - `--status` 现在包含完整的钩子系统状态
- ✅ **🛡️ 错误恢复机制** - 即使依赖缺失也能基本工作，提供优雅降级
- ✅ **🔄 双模式兼容** - 钩子系统支持PyPI和Git两种模式，智能切换

### 🔧 版本管理改进

- ✅ **PEP 440 版本规范** - 采用 `a/b/rc` 预发行规范与稳定版并行策略
- ✅ **CLI 版本提示** - 稳定版不显示预发行提示；预发行显示"版本类型: Alpha/Beta/RC"
- ✅ **README 徽章** - 更新为 Stable 徽章
- ✅ **CI/CD 工作流** - 使用 GitHub Actions 构建并发布稳定版到 PyPI；预发行通过仓库 Tag/Release 管理

## 📱 支持的通知渠道

| 渠道 | 状态 | 特性 |
|------|------|------|
| 🔔 钉钉机器人 | ✅ | ActionCard + Markdown |
| 🔗 Webhook | ✅ | HTTP 回调 + 多格式 + 多认证 |
| 🚀 飞书机器人 | 🚧 开发中 | 富文本 + 交互卡片 |
| 💼 企业微信机器人 | 🚧 开发中 | Markdown + 图文消息 |
| 🤖 Telegram | 🚧 开发中 | Bot 消息推送 |
| 📮 邮箱 | 🚧 开发中 | SMTP 邮件推送 |
| 📧 Server酱 | 🚧 开发中 | 微信推送 |

## 🚀 快速开始

### 方式一：PyPI 安装（推荐，适合普通用户）

```bash
# 安装最新稳定版
pip install claude-code-notifier

# 或安装指定版本
pip install claude-code-notifier==0.0.5

# 验证安装
claude-notifier --version

# 🚀 一键智能配置（新功能！）
claude-notifier setup --auto
```

**🎉 新功能：PyPI版本现已支持Claude Code钩子自动配置！**

安装后系统会自动：
- 📦 创建配置目录 `~/.claude-notifier/`
- ⚙️ 生成默认配置文件
- 🔧 设置 CLI 命令
- 🔍 **智能检测Claude Code并提示集成**
- ⚡ **一键配置Claude Code钩子**

**适合人群**：普通用户、快速体验、生产环境使用

### 方式二：Git 源码安装（适合开发者）

#### 2.1 智能安装（推荐）

```bash
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier
./install.sh
```

**✨ 新版智能安装系统特性**：
- 🎯 **智能模式选择** - 自动检测环境并推荐最佳安装方式
- 📦 **三种安装模式** - PyPI/Git/混合，满足不同需求
- 🔄 **自动更新机制** - 定时检查，一键更新
- 🔗 **统一命令接口** - `cn` 命令自动路由到正确执行方式
- 📊 **版本管理** - 统一的版本信息和升级路径

**快速配置**：
```bash
# 安装后运行配置向导
python3 scripts/quick_setup.py
```

快速配置脚本将引导您：
- 📱 配置通知渠道（钉钉、飞书、Telegram、邮箱等）
- 🎯 选择要启用的事件类型
- 🔧 添加自定义事件
- ⚙️ 设置高级选项（频率限制、静默时间等）
- 🧪 测试通知配置

#### 2.2 手动配置

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

**适合人群**：开发者、贡献者、需要自定义功能、测试最新特性

### 安装方式对比

| 特性 | PyPI 安装 | Git 源码安装 |
|------|-----------|-------------|
| 🎯 目标用户 | 普通用户 | 开发者 |
| ⚡ 安装速度 | 快速 | 较慢 |
| 🔄 更新方式 | `pip install --upgrade` | `git pull` + 重新安装 |
| 🧪 测试版本 | 稳定版本 | 最新开发版 |
| 🛠️ 自定义能力 | 基础配置 | 完全自定义 |
| 📦 依赖管理 | 自动处理 | 手动管理 |
| 🔗 Claude Code 集成 | ✅ **自动配置钩子** | ✅ 自动设置 Hook |
| 📁 目录结构 | 标准 Python 包 | 完整项目结构 |
| 🚀 一键配置 | ✅ `setup` 命令 | ✅ 安装脚本 |

### 配置和测试

#### PyPI 用户配置

```bash
# 🚀 一键智能配置（推荐）
claude-notifier setup --auto

# 🔧 分步配置
claude-notifier setup                    # 交互式配置
claude-notifier hooks install            # 配置Claude Code钩子
claude-notifier test                     # 测试通知
claude-notifier --status                 # 查看完整状态

# 📊 钩子管理
claude-notifier hooks status             # 查看钩子状态
claude-notifier hooks verify             # 验证钩子配置
claude-notifier hooks uninstall          # 卸载钩子（如需要）
```

#### 统一命令接口

**🔗 无论使用哪种安装方式，都可以使用统一的 `cn` 命令**：

```bash
# 智能命令路由 - 自动选择正确的执行方式
cn init      # 初始化配置
cn test      # 测试通知
cn status    # 查看状态
cn --help    # 查看帮助
```

#### 更新管理

**🔄 智能更新系统**：

```bash
# 检查更新
python3 scripts/smart_update.py --check

# 执行更新
python3 scripts/smart_update.py --update

# 启用自动更新
python3 scripts/smart_update.py --enable-auto

# 查看更新状态
python3 scripts/smart_update.py --status
```

**自动更新特性**：
- ✅ 自动检测安装类型（PyPI/Git）
- ✅ 智能版本比较和更新
- ✅ 定时检查（每天一次）
- ✅ 配置备份和迁移
- ✅ 更新日志记录

#### Git 源码用户测试

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

![钉钉通知示例 - 任务完成](assets/dingtallk-demo.png)

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

1. 在 `src/claude_notifier/core/channels/` 创建新的渠道文件
2. 实现 `BaseChannel` 接口和必需的类属性
3. 在 `src/claude_notifier/core/channels/__init__.py` 中注册渠道
4. 在配置文件中添加渠道配置模板
5. 更新文档和测试

详细开发指南请参考 `docs/development.md`

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

## 📦 版本规范与预发行流程

- **版本规范（PEP 440）**
  - 预发行：`aN`（Alpha）、`bN`（Beta）、`rcN`（候选），如：`0.0.3a1`、`0.0.3b4`、`0.0.3rc1`
  - 稳定版：去掉预发行后缀，如：`0.0.3`
  - 版本源文件：`src/claude_notifier/__version__.py`

- **预发行策略**
  - 使用 Git 标签发布预发行（如 `v0.0.3b4`），创建仓库 Release 并附带变更说明
  - CLI `--version` 显示“版本类型: Alpha/Beta/RC”和预发行提示
  - 如需分发，可手动将预发行上传至 PyPI（可选）

- **稳定版发布（默认）**
  - `vX.Y.Z` 标签触发 GitHub Actions 构建（sdist + wheel）并发布到 PyPI
  - 同步更新 `CHANGELOG.md` 与文档

详见：[开发文档（版本规范与预发行流程章节）](docs/development.md)

## 📚 文档

- [快速开始](docs/quickstart.md) - 安装和基础配置
- [配置指南](docs/configuration.md) - 详细配置说明
- [渠道配置](docs/channels.md) - 各渠道具体配置
- [高级使用](docs/advanced-usage.md) - 自定义事件和ccusage集成
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

## 💻 平台兼容性

### 测试环境
- ✅ **macOS 15** - 完全测试和支持
- 🚧 **Windows/Linux** - 理论支持，但尚未充分测试

### 跨平台兼容性
本项目在设计时考虑了跨平台兼容性：
- 🪟 **Windows支持** - 钩子安装器已针对Windows命令行和路径处理进行优化
- 🐧 **Linux支持** - 使用标准Python和shell命令，应该可以正常工作
- 🔧 **自动平台检测** - 代码中包含`os.name`和平台特定的处理逻辑

### 欢迎贡献
**🙏 诚邀其他平台用户测试和完善**：
- 如果您在Windows或Linux上使用，欢迎反馈使用体验
- 发现问题请提交Issue，我们会积极解决
- 欢迎提交平台特定的改进和修复PR

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Apache License

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kdush/Claude-Code-Notifier&type=Date)](https://star-history.com/#kdush/Claude-Code-Notifier&Date)


---

> 💡 让 Claude Code 更智能，让开发更高效！

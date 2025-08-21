# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> 此处记录尚未发布版本的变更。未来规划请查看开发路线图文档：`docs/development-roadmap.md`。

## [0.0.3b1] - 2025-08-21 (Pre-release: Beta)

### Added - Claude Code钩子自动配置 🚀
- **🔧 PyPI版本钩子支持** - PyPI用户现在可以自动配置Claude Code钩子，实现与Git版本相同的集成体验
- **⚡ 智能安装器** - 新增`ClaudeHookInstaller`类，提供完整的钩子生命周期管理（安装/卸载/验证/状态检查）
- **🎯 一键配置命令** - 新增`claude-notifier setup`命令，支持交互式和自动化配置
- **📊 完整CLI支持** - 新增`claude-notifier hooks`命令组：
  - `hooks install` - 安装Claude Code钩子配置
  - `hooks uninstall` - 卸载钩子配置
  - `hooks status` - 查看钩子详细状态  
  - `hooks verify` - 验证钩子配置完整性

### Enhanced - 用户体验优化 ✨
- **💡 智能首次运行检测** - 自动检测Claude Code并提示用户启用集成
- **📈 增强状态显示** - `--status`命令现在包含完整的钩子系统状态
- **🛡️ 错误恢复机制** - 钩子系统即使在依赖缺失时也能基本工作
- **🔍 智能环境检测** - 支持多种Claude Code安装位置的自动检测

### Technical - 架构改进 🏗️
- **📦 包结构优化** - 更新`pyproject.toml`正确包含钩子文件分发
- **🔄 双模式兼容** - 钩子脚本支持PyPI和Git两种安装模式，智能切换
- **⚙️ 配置管理** - 完整的`hooks.json`配置生成和验证系统
- **✨ 状态跟踪** - 新增钩子会话状态文件和进度管理
- **🧹 安装系统清理** - 删除冗余安装脚本，统一Git和PyPI安装体验

### Version Management
- 采用符合 PEP 440 的预发行版本规范（a/b/rc），本次为 `b`，示例：`0.0.3b1`
- CLI `--version` 显示预发行提示，包括"版本类型: Beta"与"这是预发行版本，可能包含变更"

### Documentation
- README 新增 Beta 徽章，突出当前预发行状态
- 全面同步中英文文档以反映PyPI钩子自动配置功能
- 更新快速开始指南，重构安装流程说明

### CI/CD
- 预发行版本自动发布至 TestPyPI；正式版本发布至 PyPI
- 增强CI/CD工作流以支持钩子系统测试和验证

## [0.0.2] - 2025-08-20

### Fixed
- 🔧 修复配置备份/恢复功能bug - import_config方法现在正确处理配置替换操作
- 🎯 修复模板引擎API不一致问题 - 移除冲突的TemplateManager类，统一使用TemplateEngine
- 📦 修复模块相对导入问题 - 将问题的相对导入转换为绝对导入，提高模块兼容性

### Technical Improvements
- 配置管理器的import_config方法现在正确处理merge=False场景
- 模板系统API现在完全统一，消除了重复实现
- 解决了managers和claude_notifier包中的导入路径问题

### Documentation Improvements
- 📊 新增ccusage集成文档和使用指南
- 🔗 增加对ccusage工具的正式声明和致谢
- 📖 完善高级使用文档，包含统计分析功能

## [0.0.1] - 2025-08-20

### Added
- 初始版本发布
- 基础通知功能
- 钉钉和飞书渠道支持
- 简单配置管理
- 基础CLI工具
- 多渠道通知支持 (钉钉、飞书、Telegram、邮件、Server酱)
- Claude Code钩子集成
- 基础限流机制
- 配置文件支持
- 统计功能集成
- 🧠 智能操作阻止机制
- 📊 通知频率自动控制
- 🔄 消息智能分组合并
- ❄️ 多层级冷却管理系统
- 📈 实时监控和统计功能
- 🎯 自适应限流策略
- PyPI标准化发布流程
- 轻量化模块化架构
- 自动卸载和更新机制

### Changed
- 改进通知模板系统
- 优化配置管理
- 增强日志功能
- 重构架构为模块化设计
- 优化性能和内存使用
- 增强配置管理和验证
- 完善错误处理和恢复机制

### Breaking Changes
- 配置文件格式升级到 enhanced_config.yaml
- 钩子系统API变更
- 部分函数签名调整

### Fixed
- 修复网络连接超时问题
- 解决配置加载错误
- 修复多线程并发安全问题
- 解决内存泄漏问题
- 改进错误处理逻辑

### Security
- 初始安全配置
- 敏感信息保护
- webhook URL验证
- 修复配置文件权限问题
- 增强敏感信息保护
- 改进钩子验证机制
- 输入数据清理

### Dependencies
- requests: >=2.25.0
- PyYAML: >=5.4.0
- pytz: >=2021.1 (新增时区处理)
- click: >=8.0.0

---

> 未来版本规划已迁移至开发路线图文档：`docs/development-roadmap.md`。

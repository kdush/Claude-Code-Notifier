# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> 此处记录尚未发布版本的变更。未来规划请查看开发路线图文档：`docs/development-roadmap.md`。

## [0.0.3b1] - 2025-08-21 (Pre-release: Beta)

### Added
- 采用符合 PEP 440 的预发行版本规范（a/b/rc），本次为 `b`，示例：`0.0.3b1`
- CLI `--version` 显示预发行提示，包括“版本类型: Beta”与“这是预发行版本，可能包含变更”

### Documentation
- README 新增 Beta 徽章，突出当前预发行状态

### CI/CD
- 预发行版本自动发布至 TestPyPI；正式版本发布至 PyPI

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

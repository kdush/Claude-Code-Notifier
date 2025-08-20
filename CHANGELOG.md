# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## 版本规划

### [1.3.0] - 计划中
- 📊 Web监控面板
- 🔌 插件系统
- 🌐 国际化支持
- 🔒 增强安全功能

### [1.4.0] - 未来版本
- 🤖 AI驱动的通知优化
- 📱 移动端支持
- ☁️ 云同步功能
- 🎨 主题系统

## 迁移指南

### 1.1.x → 1.2.x
1. 备份现有配置: `cp config.yaml config.yaml.backup`
2. 运行升级: `pip install --upgrade claude-notifier`
3. 检查新配置: `claude-notifier status`
4. 根据需要启用智能功能

### 1.0.x → 1.1.x
1. 更新配置文件格式
2. 重新配置通知渠道
3. 更新Claude Code钩子

## 支持的Python版本

- Python 3.7+ (推荐 3.9+)
- 已测试版本: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12

## 依赖更新记录

已合并至上方 0.0.1 版本的 Dependencies 小节。

## 安全更新

已合并至上方 0.0.1 版本的 Security 小节。
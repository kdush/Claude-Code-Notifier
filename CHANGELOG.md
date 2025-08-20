# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PyPI标准化发布流程
- 轻量化模块化架构
- 自动卸载和更新机制

## [1.2.0] - 2024-01-20

### Added
- 🧠 智能操作阻止机制
- 📊 通知频率自动控制
- 🔄 消息智能分组合并
- ❄️ 多层级冷却管理系统
- 📈 实时监控和统计功能
- 🎯 自适应限流策略

### Changed
- 重构架构为模块化设计
- 优化性能和内存使用
- 增强配置管理和验证
- 完善错误处理和恢复机制

### Breaking Changes
- 配置文件格式升级到enhanced_config.yaml
- 钩子系统API变更
- 部分函数签名调整

### Fixed
- 修复多线程并发安全问题
- 解决内存泄漏问题
- 改进错误处理逻辑

## [1.1.0] - 2024-01-15

### Added
- 多渠道通知支持 (钉钉、飞书、Telegram、邮件、Server酱)
- Claude Code钩子集成
- 基础限流机制
- 配置文件支持
- 统计功能集成

### Changed
- 改进通知模板系统
- 优化配置管理
- 增强日志功能

### Fixed
- 修复网络连接超时问题
- 解决配置加载错误

## [1.0.0] - 2024-01-10

### Added
- 初始版本发布
- 基础通知功能
- 钉钉和飞书渠道支持
- 简单配置管理
- 基础CLI工具

### Security
- 初始安全配置
- 敏感信息保护

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

### 1.2.0
- requests: >=2.25.0
- PyYAML: >=5.4.0  
- pytz: >=2021.1
- click: >=8.0.0 (新增)

### 1.1.0
- 添加 pytz 支持时区处理
- 更新 PyYAML 到 5.4.0+

## 安全更新

### 1.2.0
- 修复配置文件权限问题
- 增强敏感信息保护
- 改进钩子验证机制

### 1.1.0
- 初始安全配置
- webhook URL验证
- 输入数据清理
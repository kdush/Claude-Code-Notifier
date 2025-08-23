# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> 此处记录尚未发布版本的变更。未来规划请查看开发路线图文档：`docs/development-roadmap.md`。

## [0.0.7b1] - 2025-08-23 (Pre-release: Beta)

### PyPI Compatibility Fixes 🔧
- **解决PyPI包相对导入错误**：修复 `attempted relative import with no known parent package` 问题，确保从PyPI安装的包能正常工作。
- **导入系统重构**：将 `src/claude_notifier/cli/main.py` 中所有相对导入（如 `from ..core` 等）改为绝对导入（`from claude_notifier.core`）。
- **包结构优化**：移动 `events/`、`templates/`、`managers/` 目录到 `claude_notifier/` 包内，统一包结构，避免导入冲突。

### Testing & Validation ✅
- **开发环境测试**：通过 `pip install -e .` 开发模式安装测试。
- **生产环境测试**：通过虚拟环境 `pip install .` 生产模式安装测试。
- **CLI功能验证**：确认 `claude-notifier` 和 `cn` 命令正常工作，`cn setup` 不再报错。

### Package Structure 📦
- **清理孤立文件**：移除 `src/managers/` 等孤立目录，避免包结构混乱。
- **版本信息更新**：升级版本至 `0.0.7b1`，标记为Beta版本进行测试。

## [0.0.6] - 2025-08-22 (Stable)

### Publishing & Release Workflow 🚀
- TestPyPI 版本存在检查：发布前调用 API 检测目标版本是否已存在，若已存在则跳过上传，避免 400 重复上传错误。
- 工作流步骤顺序与 YAML 修复：移除 heredoc，统一采用单行 `python -c`；规范缩进与转义，提升跨平台稳定性。
- 安装测试稳健性：引入重试与超时控制；在 Python 3.8 环境中固定 pip/setuptools 版本以提升兼容性。

### Documentation 📚
- 同步更新 README/README_en 的 “What's New/最新改进” 至 0.0.6，并更新固定版本安装示例。
- 补充发布流程说明，明确 TestPyPI 跳过策略与主 PyPI 发布建议。

## [0.0.5] - 2025-08-22 (Stable)

### CI/CD 🧰
- 修复并稳定跨平台 `test-install` 导入验证：移除 heredoc 与多进程导入测试，改为同步 `import` 并打印版本，避免 macOS/Windows 上 `<stdin>` 导致的 `FileNotFoundError`。
- 强化 GitHub Actions 跨平台一致性（macOS/Windows/Ubuntu），简化 `python -c` 使用以规避续行与转义差异。

### Packaging 📦
- `MANIFEST.in` 明确 `prune src/hooks`，避免将非包内的原始钩子脚本打入 sdist；不影响包内 `claude_notifier/hooks` 资源分发。

### Documentation 📚
- README/README_en 同步至稳定版：更换徽章为 Stable，安装示例固定版本更新至 `0.0.5`，对齐 0.0.5 说明。
- 同步更新本 Changelog 并标记 0.0.5 为首个稳定版本。

## [0.0.4b2] - 2025-08-22 (Pre-release: Beta)

### CI/CD 🧰
- 移除 GitHub Actions `release.yml` 中 `test-install` 步骤的 heredoc + multiprocessing 导入测试，改为同步导入并打印版本，彻底规避 `<stdin>` 导致的 `FileNotFoundError`（macOS/Windows `spawn` 需要物理文件路径）。
- 增强跨平台稳定性，保留控制台脚本与模块 CLI 的超时与输出校验。

### Packaging 📦
- 通过 `MANIFEST.in` 明确 `prune src/hooks`，避免将非包内的原始钩子脚本打入 sdist；包内 `claude_notifier/hooks` 资源不受影响。

### Fixed 🛠️
- 修复 `src/utils/ccusage_integration.py` 中字符串拼接换行问题，使用真实的 `\n` 换行符，保证通知文本展示正确。

### Documentation 📚
- 更新 `README.md` 与 `README_en.md` 的 “What's New/最新改进” 版本号与说明，并修正固定版本安装示例为 `0.0.4b2`；英文版同步说明 PyPI 版本支持自动配置 Claude Code 钩子。

## [0.0.4b1] - 2025-08-22 (Pre-release: Beta)

### Fixed - CLI系统稳定性与用户体验优化 🛠️
- **🔧 调试诊断系统修复** - 修复`debug diagnose`命令中MONITORING_CLI_AVAILABLE未定义错误
  - 添加监控模块导入的异常处理机制
  - 提供优雅的降级处理，确保诊断功能在缺少监控模块时正常工作
- **📦 包名引用标准化** - 修正更新检查中的包名错误
  - 将包名从"claude-notifier"统一更正为"claude-code-notifier"
  - 确保PyPI API调用和pip安装命令使用正确包名
- **⚙️ 配置状态验证增强** - 解决配置状态显示矛盾问题
  - 在`is_valid()`方法中添加文件存在性检查
  - 确保配置验证结果与实际文件状态完全一致
- **💬 用户反馈体验优化** - 改进CLI命令反馈逻辑
  - `send`命令现在在无配置渠道时显示准确警告而非误导性成功消息
  - 提供清晰的下一步操作指引，提升用户体验

### Enhanced - 日志系统智能化 ✨
- **🔇 CLI输出清洁化** - 优化日志系统CLI兼容性
  - 在CLI模式下自动调整日志级别，避免显示不必要的INFO消息
  - 保持日志功能完整性的同时确保CLI输出简洁专业
  - 智能检测运行环境，动态调整日志行为

### Technical - 代码质量与维护性 🏗️
- **🧪 全面系统测试** - 完成CLI命令全覆盖测试，发现并修复15%命令的稳定性问题
- **📊 问题分级处理** - 采用P0/P1优先级系统，确保关键问题优先解决
- **🔄 质量保证流程** - 建立系统化测试验证流程，确保所有修复的有效性

## [0.0.3b4] - 2025-08-21 (Pre-release: Beta)

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

### Packaging - 发布元数据与安装说明 📦
- 对齐 Python Classifiers：移除 3.7，新增 3.12（与 `python_requires >= 3.8` 保持一致）
- 安装命令文案统一为 `claude-code-notifier[...]`，避免包名混淆

### Version Management
- 采用符合 PEP 440 的预发行版本规范（a/b/rc），本次为 `b`，示例：`0.0.3b4`
- CLI `--version` 显示预发行提示，包括"版本类型: Beta"与"这是预发行版本，可能包含变更"

### Documentation
- README 新增 Beta 徽章，突出当前预发行状态
- 全面同步中英文文档以反映PyPI钩子自动配置功能
- 更新快速开始指南，重构安装流程说明

### CI/CD & Build Improvements
- 预发行版本自动发布至 TestPyPI；正式版本发布至 PyPI
- 增强CI/CD工作流以支持钩子系统测试和验证
- **🔧 工作流Python执行优化** - 简化GitHub Actions中的多行Python脚本为单行命令，提升构建性能
- **📦 包安装验证增强** - 使用Python脚本替代直接pip命令，增强错误检测和wheel文件验证
- **🌐 跨平台CI测试稳定性** - 添加UTF-8编码环境变量，简化测试输出为ASCII避免Windows编码问题
- **⚡ 发布流程优化** - 升级构件处理到actions/v4，修复版本校验逻辑，增强发布可靠性

### Fixed - 跨平台兼容性与CLI优化 🛠️
- **🪟 Windows兼容性增强** - 钩子安装器现在完全支持Windows平台：
  - 使用`sys.executable`替代固定python3命令
  - 实现Windows和POSIX平台的JSON参数引号处理差异化
  - 自动检测并处理包含空格的文件路径引号包装
- **⚙️ 配置初始化修复** - 修复ConfigManager构造函数中logger初始化顺序问题，避免运行时错误
- **📋 CLI模块路径验证** - 新增`python -m claude_notifier.cli.main --version`提升Windows PATH兼容性
- **🔧 CLI命令优化** - 重构status和monitor命令功能分工：
  - status命令专注于快速系统健康检查（版本、配置、渠道、钩子基础信息）
  - monitor命令提供详细监控和性能分析
  - 消除重复功能，提升用户体验和工具专业性
- **🛠️ 卸载功能修复** - 修复卸载功能中缺少time模块导入的问题，确保卸载流程正常运行
- **📦 包分类器优化** - 优化PyPI包分类器配置，提升包在PyPI上的发现性和专业性

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

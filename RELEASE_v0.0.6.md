# 🎉 Claude Code Notifier v0.0.6 发布

这是一个专注于**CI/CD发布流程稳定性**和**跨平台兼容性**的增强版本。

## ✨ 主要亮点

### 🧰 CI/CD 工作流全面增强
- **🔍 智能版本检查**: TestPyPI 发布前自动检测版本是否存在，避免重复上传导致的 400 错误
- **⚙️ 工作流优化**: 彻底移除 heredoc，统一使用 `python -c`，显著提升跨平台稳定性
- **🔄 重试机制**: 安装测试增加智能重试逻辑，提高CI流程可靠性
- **🎯 灵活发布**: 支持手动触发 PyPI 发布，增强发布流程灵活性

### 📦 跨平台兼容性优化
- **🐍 Python 3.8 支持**: 固定 pip/setuptools 版本，避免新版本兼容性问题
- **🌍 系统兼容**: macOS/Windows/Ubuntu 三平台一致性改进
- **📝 YAML 语法**: 修复 GitHub Actions 输出引用语法，提升解析准确性

### 📚 文档与用户体验
- **📖 文档同步**: README/README_en 更新到 v0.0.6，提供最新安装指南
- **📋 变更记录**: 完善 CHANGELOG.md，详细记录所有改进内容
- **🎯 版本示例**: 更新所有安装示例到当前稳定版本

## 🔧 技术改进详情

### CI/CD 流程优化
- 替换所有 heredoc 语法为单行 `python -c` 命令，避免跨平台转义问题
- TestPyPI 发布增加版本存在性检查，智能跳过已存在版本
- 安装测试引入重试机制（最多8次，智能延迟策略）
- Python 3.8 环境中限制 pip<25 和 setuptools<70 版本

### 发布流程增强
```yaml
# 新增功能
- 版本检查 API 调用
- 智能跳过逻辑
- 手动触发支持
- 重试机制优化
```

### 跨平台兼容性
- **macOS**: 修复 multiprocessing 导致的 FileNotFoundError
- **Windows**: 优化命令行参数转义和路径处理  
- **Ubuntu**: 统一 shell 脚本语法，避免平台差异

## 📊 改进统计

- **文件变更**: 7个文件优化
- **代码行数**: +177/-109 (净增68行)
- **工作流步骤**: 新增3个关键检查点
- **测试覆盖**: 增强跨平台测试场景

## 🎯 适用场景

此版本特别适合：
- **CI/CD 集成**: 需要稳定自动化发布流程的项目
- **跨平台部署**: macOS/Windows/Linux 混合环境
- **企业环境**: 对发布流程稳定性有高要求的团队
- **开源项目**: 需要可靠 PyPI 发布流程的开源项目

## 📥 安装升级

### 全新安装
```bash
pip install claude-code-notifier==0.0.6
claude-notifier setup --auto
```

### 现有用户升级
```bash
pip install --upgrade claude-code-notifier
claude-notifier --version
```

## 🔗 相关链接

- **PyPI**: https://pypi.org/project/claude-code-notifier/0.0.6/
- **文档**: [README.md](README.md) | [README_en.md](README_en.md)
- **变更日志**: [CHANGELOG.md](CHANGELOG.md)
- **问题反馈**: [GitHub Issues](https://github.com/kdush/Claude-Code-Notifier/issues)

## 🙏 致谢

感谢所有使用和反馈的用户，你们的建议让 Claude Code Notifier 变得更好！

---

**📱 快速体验**: `claude-notifier setup --auto`

**🤖 Generated with [Claude Code](https://claude.ai/code)**
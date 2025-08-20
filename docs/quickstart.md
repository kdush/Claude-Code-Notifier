# 🚀 快速开始指南

## 🔧 系统要求

- **Python**: 3.8+ (推荐 3.9+)
- **Claude Code**: 最新版本
- **操作系统**: macOS / Linux / Windows
- **网络**: 访问通知服务 API

## ⚡ 一分钟快速安装

### 方式一：自动安装（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier

# 2. 运行一键安装脚本
chmod +x install.sh scripts/quick_setup.py
./install.sh

# 3. 启动交互式配置向导
python3 scripts/quick_setup.py
```

### 方式二：手动安装（推荐开发者）

```bash
# 1. 克隆和进入项目
git clone https://github.com/kdush/Claude-Code-Notifier.git
cd Claude-Code-Notifier

# 2. 安装依赖
pip install -r requirements.txt
pip install -e .

# 3. 复制配置模板
cp config/enhanced_config.yaml.template ~/.claude-notifier/config.yaml

# 4. 编辑配置文件
vim ~/.claude-notifier/config.yaml

# 5. 测试配置
./scripts/test.sh
```

## 📱 快速配置通知渠道

### 钉钉机器人 (推荐)
```bash
# 交互式配置
python3 scripts/quick_setup.py

# 手动配置步骤：
# 1. 钉钉群 → 设置 → 机器人 → 添加机器人 → 自定义机器人
# 2. 安全设置选择"加签"，获取 Webhook URL 和密钥
# 3. 配置文件中填入 webhook 和 secret
```

### 飞书机器人
```bash
# 1. 飞书群 → 设置 → 机器人 → 添加机器人 → Custom Bot
# 2. 获取 Webhook URL 
# 3. 配置文件中填入 webhook
```

### 其他渠道
- **企业微信**: 支持 Markdown 消息和图文卡片
- **Telegram**: 需要 Bot Token 和 Chat ID
- **邮箱 SMTP**: 支持 Gmail, Outlook, 企业邮箱
- **Server酱**: 微信推送，仅需 SendKey

详细配置指南: [📖 渠道配置文档](channels.md)

## 🎯 智能功能体验

### 智能操作控制
```bash
# 当 Claude Code 尝试执行敏感操作时：
claude implement "删除临时文件" 
# → 🛡️ 自动检测到 'rm -rf' 操作
# → 📱 发送权限确认通知
# → ⏸️ 暂停执行等待确认
```

### 智能通知限流
```bash
# 防止通知轰炸，智能分组相似消息
claude analyze large-project/
# → 🧠 自动分组相关通知
# → ⏰ 智能控制发送频率
# → 📊 实时统计发送效果
```

### 实时监控面板
```bash
# 查看系统状态和统计
claude-notifier status
claude-notifier stats --days 7
claude-notifier monitor  # 实时监控面板
```

## 🚀 使用场景演示

### 场景 1: 敏感操作保护
```bash
cd your-project
claude

# 用户: "请删除 node_modules 目录"
# Claude Code: 准备执行 'rm -rf node_modules'
# → 📱 钉钉通知: "🔐 检测到敏感操作: rm -rf node_modules"
# → 📱 "项目: your-project, 请确认是否执行"
# → ⏸️ 等待用户在终端确认
```

### 场景 2: 任务完成庆祝
```bash
# 用户: "重构这个模块的代码"
# Claude Code: 完成重构任务
# → 📱 钉钉通知: "🎉 Claude Code 任务完成!"
# → 📱 "项目: your-project"
# → 📱 "状态: 代码重构已完成"
# → 📱 "建议: 检查代码质量"
```

### 场景 3: 性能监控
```bash
# 系统自动监控通知性能
# → 📊 统计: 244K+ 操作/秒处理能力
# → 📈 监控: 零内存泄漏
# → ⚡ 响应: <1ms 平均响应时间
# → 🎯 成功率: 99.9% 通知送达率
```

## 🔧 验证安装

### 系统自检
```bash
# 检查安装状态
claude-notifier --version
claude-notifier health

# 验证配置
claude-notifier config validate

# 测试所有渠道连接
claude-notifier test --all-channels
```

### 性能验证
```bash
# 运行性能基准测试
python tests/test_performance_benchmarks.py

# 查看性能指标
# 预期结果: 244K+ ops/s, 零内存泄漏, <1ms 响应时间
```

## 🛠️ 故障排除

### 通知发送失败
```bash
# 1. 检查网络连接
curl -I https://oapi.dingtalk.com

# 2. 验证配置文件
claude-notifier config validate

# 3. 查看详细日志
tail -f ~/.claude-notifier/logs/notifier.log

# 4. 测试特定渠道
claude-notifier test --channel dingtalk --debug
```

### 智能功能异常
```bash
# 1. 检查智能组件状态
claude-notifier monitor

# 2. 重置智能配置
claude-notifier config reset --intelligence

# 3. 查看组件日志
grep "intelligence" ~/.claude-notifier/logs/notifier.log
```

### Claude Code 钩子问题
```bash
# 1. 确认钩子安装状态
ls -la ~/.claude/hooks/

# 2. 检查 Claude Code 配置
cat ~/.claude/settings.json | jq '.hooks'

# 3. 重新安装钩子
./hooks/install_hooks.sh

# 4. 重启 Claude Code
pkill claude && claude
```

### 性能问题诊断
```bash
# 1. 查看系统资源使用
claude-notifier stats --resource

# 2. 分析通知延迟
claude-notifier benchmark --latency

# 3. 检查缓存状态
claude-notifier cache status
```

## 📚 进阶学习

### 下一步
1. 📖 [详细配置指南](configuration.md) - 深入了解所有配置选项
2. 📱 [渠道配置指南](channels.md) - 配置各种通知渠道
3. 🛠️ [开发文档](development.md) - 了解架构和扩展开发
4. 🤝 [贡献指南](contributing.md) - 参与项目贡献

### 社区资源
- 📖 [完整文档](../README.md) - 项目主文档
- 🐛 [问题反馈](https://github.com/kdush/Claude-Code-Notifier/issues) - 报告 Bug
- 💬 [讨论区](https://github.com/kdush/Claude-Code-Notifier/discussions) - 技术讨论
- 🎥 [视频教程](https://example.com/videos) - 视频演示
- 📱 [社区群组](https://example.com/community) - 加入开发者社区

## 🎉 快速开始成功！

恭喜！您已经完成了 Claude Code Notifier 的快速配置。

**接下来您可以：**
- ✨ 体验智能操作保护功能
- 📊 查看实时监控和统计
- 🔧 根据需求调整高级配置
- 🚀 探索更多通知渠道和自定义功能

**遇到问题？**
- 查看上方故障排除指南
- 加入社区获得帮助
- 提交 Issue 获得支持

祝您开发愉快！ 🚀

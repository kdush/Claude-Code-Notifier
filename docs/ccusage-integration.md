# 📊 ccusage 集成指南

## 概述

Claude Code Notifier 集成了 [ccusage](https://github.com/ryoppippi/ccusage) 工具来提供详细的 Claude Code token 使用和成本分析。ccusage 是由 [@ryoppippi](https://github.com/ryoppippi) 开发的优秀开源工具。

## 🚀 快速开始

### 安装使用
```bash
# 通过 npx 直接使用（推荐）
npx ccusage

# 或通过 bunx 使用
bunx ccusage

# 全局安装（可选）
npm install -g ccusage
```

### 基础命令
```bash
# 查看基本使用统计
ccusage

# 查看月度报告
ccusage --monthly

# 查看每日详细统计
ccusage --daily

# 查看会话统计
ccusage --session
```

## 📈 核心功能

### Token 使用分析
- **实时统计**: 分析本地 JSONL 文件的 token 消费
- **模型区分**: 区分不同 Claude 模型的使用情况
- **时间维度**: 支持日、月、会话级别的统计

### 成本追踪
- **费用计算**: 基于不同模型的定价计算实际成本
- **趋势分析**: 追踪使用趋势和成本变化
- **预算管理**: 帮助控制 AI 使用成本

### 报告生成
```bash
# 生成 JSON 格式报告
ccusage --output usage-report.json

# 指定时间范围
ccusage --from 2025-08-01 --to 2025-08-31

# 紧凑显示模式
ccusage --compact
```

## 🔧 高级配置

### 时区设置
```bash
# 设置时区
ccusage --timezone Asia/Shanghai

# 使用本地时区
ccusage --locale zh-CN
```

### 实时监控
```bash
# 实时监控模式
ccusage --watch

# 5小时计费窗口监控
ccusage --billing-window
```

## 🤖 与通知系统集成

### 自动化统计报告
在 Claude Code Notifier 配置中添加定期统计通知：

```yaml
custom_events:
  # 每日使用报告
  daily_usage_report:
    enabled: true
    schedule: "0 8 * * *"  # 每天早上8点
    channels: ["email"]
    template: "usage_report_daily"
    command: "npx ccusage --daily --json"
    
  # 每周成本报告
  weekly_cost_report:
    enabled: true
    schedule: "0 9 * * 1"  # 每周一早上9点
    channels: ["dingtalk", "email"]
    template: "usage_report_weekly"
    command: "npx ccusage --weekly --output /tmp/weekly-usage.json"
    
  # 月度详细报告
  monthly_detailed_report:
    enabled: true
    schedule: "0 10 1 * *"  # 每月1号早上10点
    channels: ["email", "feishu"]
    template: "usage_report_monthly"
    command: "npx ccusage --monthly --detailed --json"
```

### 阈值告警
配置使用量阈值告警：

```yaml
intelligence:
  usage_monitoring:
    enabled: true
    daily_token_limit: 100000
    monthly_cost_limit: 50.00
    alert_channels: ["telegram", "email"]
    check_command: "npx ccusage --today --json"
```

## 📊 报告模板

### 基础使用报告模板
```yaml
templates:
  usage_report_daily:
    title: "📊 Claude Code 每日使用报告"
    content: |
      **使用统计**
      - Token 消耗: {{total_tokens}}
      - 成本: ${{total_cost}}
      - 会话数: {{session_count}}
      
      **模型分布**
      - Sonnet: {{sonnet_tokens}} tokens (${{sonnet_cost}})
      - Opus: {{opus_tokens}} tokens (${{opus_cost}})
      
      详细报告请查看附件。
    fields:
      - label: "日期"
        value: "{{date}}"
      - label: "总计 Token"
        value: "{{total_tokens}}"
      - label: "总成本"
        value: "${{total_cost}}"
```

## 🛠️ 故障排除

### 常见问题

**Q: ccusage 找不到数据文件？**
```bash
# 检查 Claude Code JSONL 文件位置
ls -la ~/.claude/usage/

# 指定数据文件路径
ccusage --data-dir ~/.claude/usage/
```

**Q: 统计数据不准确？**
```bash
# 重新扫描所有文件
ccusage --refresh

# 验证数据完整性
ccusage --validate
```

**Q: 如何导出历史数据？**
```bash
# 导出全部历史数据
ccusage --export-all --output claude-usage-history.json

# 导出指定时间段
ccusage --from 2025-01-01 --to 2025-08-31 --export --output usage-2025.json
```

## 📚 参考资源

- [ccusage 官方文档](https://ccusage.com)
- [GitHub 仓库](https://github.com/ryoppippi/ccusage)
- [使用示例](https://github.com/ryoppippi/ccusage#usage)

## 🙏 致谢

感谢 [@ryoppippi](https://github.com/ryoppippi) 开发并维护了这个优秀的 Claude Code 使用分析工具！ccusage 为我们提供了：

- 🚀 **极快的分析速度** - 高效处理大量使用数据
- 📊 **详细的统计报告** - 全面的使用和成本分析
- 🎯 **精确的成本追踪** - 准确计算不同模型的费用
- 📅 **灵活的时间维度** - 支持多种时间范围分析
- 💻 **离线分析能力** - 基于本地数据，保护隐私

这个工具大大增强了 Claude Code Notifier 的监控和分析能力！
# 🚀 Claude Code Notifier 高级使用指南

本文档介绍 Claude Code Notifier 的高级功能，包括自定义事件、模板系统和多渠道配置。

## 📊 使用统计与成本分析

Claude Code Notifier 集成了 [ccusage](https://github.com/ryoppippi/ccusage) 工具来提供详细的 Claude Code token 使用和成本分析。ccusage 是由 [@ryoppippi](https://github.com/ryoppippi) 开发的优秀开源工具。

### 快速开始

#### 安装使用
```bash
# 通过 npx 直接使用（推荐）
npx ccusage

# 或通过 bunx 使用
bunx ccusage

# 全局安装（可选）
npm install -g ccusage
```

#### 基础命令
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

### 核心功能

#### Token 使用分析
- **实时统计**: 分析本地 JSONL 文件的 token 消费
- **模型区分**: 区分不同 Claude 模型的使用情况
- **时间维度**: 支持日、月、会话级别的统计

#### 成本追踪
- **费用计算**: 基于不同模型的定价计算实际成本
- **趋势分析**: 追踪使用趋势和成本变化
- **预算管理**: 帮助控制 AI 使用成本

#### 报告生成
```bash
# 生成 JSON 格式报告
ccusage --output usage-report.json

# 指定时间范围
ccusage --from 2025-08-01 --to 2025-08-31

# 紧凑显示模式
ccusage --compact
```

### 高级配置

#### 时区设置
```bash
# 设置时区
ccusage --timezone Asia/Shanghai

# 使用本地时区
ccusage --locale zh-CN
```

#### 实时监控
```bash
# 实时监控模式
ccusage --watch

# 5小时计费窗口监控
ccusage --billing-window
```

### 与通知系统集成

#### 自动化统计报告
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

#### 阈值告警
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

### 报告模板

#### 基础使用报告模板
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

### 故障排除

#### 常见问题

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

### 致谢

感谢 [@ryoppippi](https://github.com/ryoppippi) 开发并维护了这个优秀的 Claude Code 使用分析工具！ccusage 为我们提供了：

- 🚀 **极快的分析速度** - 高效处理大量使用数据
- 📊 **详细的统计报告** - 全面的使用和成本分析
- 🎯 **精确的成本追踪** - 准确计算不同模型的费用
- 📅 **灵活的时间维度** - 支持多种时间范围分析
- 💻 **离线分析能力** - 基于本地数据，保护隐私

这个工具大大增强了 Claude Code Notifier 的监控和分析能力！

### 参考资源

- [ccusage 官方文档](https://ccusage.com)
- [GitHub 仓库](https://github.com/ryoppippi/ccusage)
- [使用示例](https://github.com/ryoppippi/ccusage#usage)

## 📋 目录

- [使用统计与成本分析](#使用统计与成本分析)
- [自定义事件配置](#自定义事件配置)
- [模板系统使用](#模板系统使用)
- [多渠道配置](#多渠道配置)
- [事件开关管理](#事件开关管理)
- [配置管理工具](#配置管理工具)
- [实际使用案例](#实际使用案例)

## 🎯 自定义事件配置

### 基本自定义事件

在配置文件中添加自定义事件：

```yaml
custom_events:
  # Git 提交检测
  git_commit_detected:
    enabled: true
    priority: normal
    channels: ["dingtalk"]
    template: "git_commit_custom"
    triggers:
      - type: "pattern"
        pattern: "git\\s+commit"
        field: "tool_input"
        flags: ["IGNORECASE"]
    data_extractors:
      commit_message:
        type: "regex"
        pattern: "-m\\s+[\"']([^\"']+)[\"']"
        field: "tool_input"
        group: 1
      project_name:
        type: "function"
        function: "get_project_name"
    message_template:
      title: "📝 代码提交检测"
      content: "在项目 ${project} 中检测到 Git 提交"
      action: "请确认提交内容"
```

### 触发器类型

#### 1. 模式匹配触发器
```yaml
triggers:
  - type: "pattern"
    pattern: "docker\\s+(run|build|push)"
    field: "tool_input"
    flags: ["IGNORECASE", "MULTILINE"]
```

#### 2. 条件触发器
```yaml
triggers:
  - type: "condition"
    field: "tool_name"
    operator: "equals"
    value: "run_command"
```

#### 3. 函数触发器
```yaml
triggers:
  - type: "function"
    function: "is_work_hours"  # 内置函数
```

#### 4. 复合条件
```yaml
triggers:
  - type: "condition"
    field: "project"
    operator: "contains"
    value: "production"
  - type: "pattern"
    pattern: "rm\\s+-rf"
    field: "tool_input"
```

### 数据提取器

#### 字段提取器
```yaml
data_extractors:
  simple_field: "tool_name"  # 简单字段提取
  
  complex_field:
    type: "field"
    field: "error_message"
    default: "无错误信息"
```

#### 正则提取器
```yaml
data_extractors:
  file_name:
    type: "regex"
    pattern: "\\b([\\w-]+\\.py)\\b"
    field: "tool_input"
    group: 1
```

#### 函数提取器
```yaml
data_extractors:
  current_time:
    type: "function"
    function: "get_current_time"
```

## 🎨 模板系统使用

### 创建自定义模板

在 `~/.claude-notifier/templates/` 目录下创建 YAML 文件：

```yaml
# my_custom_template.yaml
production_alert:
  title: '🚨 生产环境操作警告'
  content: '⚠️ 检测到生产环境操作：${operation}'
  fields:
    - label: '项目'
      value: '${project}'
      short: true
    - label: '操作类型'
      value: '${tool_name}'
      short: true
    - label: '详细命令'
      value: '${tool_input}'
      short: false
    - label: '风险等级'
      value: '🔴 高风险'
      short: true
  actions:
    - text: '立即确认'
      type: 'button'
      style: 'danger'
    - text: '查看日志'
      type: 'button'
      url: 'logs://'
  color: '#dc3545'
```

### 模板变量

可用的模板变量：

- `${project}` - 项目名称
- `${timestamp}` - 时间戳
- `${event_type}` - 事件类型
- `${priority}` - 优先级
- `${tool_name}` - 工具名称
- `${tool_input}` - 工具输入
- `${error_message}` - 错误信息
- `${operation}` - 操作内容

### 渠道特定模板

为不同渠道创建专门的模板：

```yaml
# 钉钉专用模板
dingtalk_production_alert:
  title: '🚨 生产环境操作'
  content: |
    ### ⚠️ 高风险操作检测
    
    **项目**: ${project}
    **操作**: ${operation}
    **时间**: ${timestamp}
    
    请立即确认此操作！
  # 钉钉支持 ActionCard
  actions:
    - text: '确认执行'
      type: 'button'
    - text: '取消操作'
      type: 'button'

# Telegram 专用模板  
telegram_production_alert:
  title: '🚨 Production Alert'
  content: |
    *High Risk Operation Detected*
    
    Project: `${project}`
    Operation: `${operation}`
    Time: ${timestamp}
    
    Please confirm immediately!
  # Telegram 不支持复杂按钮
```

## 🔀 多渠道配置

### 渠道优先级配置

```yaml
# 不同事件使用不同渠道组合
events:
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "telegram"]  # 敏感操作双渠道通知
    
  task_completion:
    enabled: true
    channels: ["dingtalk"]  # 任务完成只用钉钉
    
  rate_limit:
    enabled: true
    channels: ["telegram"]  # 限流用 Telegram（更及时）

# 默认渠道配置
notifications:
  default_channels: ["dingtalk"]  # 未指定渠道的事件使用默认渠道
```

### 渠道故障转移

```yaml
notifications:
  failover:
    enabled: true
    primary_channels: ["dingtalk"]
    fallback_channels: ["telegram", "email"]
    retry_interval: 30  # 秒
```

### 渠道特定设置

```yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=..."
    secret: "SEC..."
    # 钉钉特定设置
    at_all: false
    at_mobiles: []
    
  telegram:
    enabled: true
    bot_token: "123456:ABC-DEF..."
    chat_id: "-123456789"
    # Telegram 特定设置
    parse_mode: "Markdown"
    disable_web_page_preview: true
```

## ⚙️ 事件开关管理

### 批量事件管理

```python
from src.config_manager import ConfigManager

config_manager = ConfigManager()

# 启用所有内置事件
builtin_events = [
    'sensitive_operation',
    'task_completion', 
    'rate_limit',
    'error_occurred'
]

for event_id in builtin_events:
    config_manager.enable_event(event_id)

# 禁用会话开始事件（避免频繁通知）
config_manager.disable_event('session_start')
```

### 条件性事件启用

```yaml
events:
  sensitive_operation:
    enabled: true
    conditions:
      # 只在工作时间通知
      time_window:
        start: "09:00"
        end: "18:00"
      # 只通知高风险操作
      risk_levels: ["high", "critical"]
      # 项目过滤
      project_patterns: ["prod-*", "*-production"]
```

## 🛠️ 配置管理工具

### 使用配置管理器

```python
from src.config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 获取配置统计
stats = config_manager.get_config_stats()
print(f"启用的渠道数: {stats['enabled_channels']}")
print(f"启用的事件数: {stats['enabled_events']}")

# 设置默认渠道
config_manager.set_default_channels(['dingtalk', 'telegram'])

# 添加自定义事件
custom_event_config = {
    'name': '数据库操作检测',
    'priority': 'high',
    'triggers': [{
        'type': 'pattern',
        'pattern': 'mysql|postgres|mongodb',
        'field': 'tool_input'
    }],
    'message_template': {
        'title': '🗄️ 数据库操作',
        'content': '检测到数据库相关操作'
    }
}

config_manager.add_custom_event('db_operation', custom_event_config)

# 备份配置
backup_file = config_manager.backup_config()
print(f"配置已备份到: {backup_file}")
```

### 配置验证

```python
# 验证配置
errors = config_manager.validate_config()
if errors:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置验证通过")
```

## 📚 实际使用案例

### 案例1：生产环境监控

```yaml
custom_events:
  production_deployment:
    enabled: true
    priority: critical
    channels: ["dingtalk", "telegram", "email"]
    triggers:
      - type: "condition"
        field: "project"
        operator: "contains"
        value: "prod"
      - type: "pattern"
        pattern: "deploy|kubectl apply|docker push"
        field: "tool_input"
    template: "production_deployment_alert"
    
  database_migration:
    enabled: true
    priority: critical
    channels: ["dingtalk", "email"]
    triggers:
      - type: "pattern"
        pattern: "migrate|schema|alter table"
        field: "tool_input"
    template: "database_migration_alert"
```

### 案例2：开发团队协作

```yaml
custom_events:
  code_review_ready:
    enabled: true
    priority: normal
    channels: ["dingtalk"]
    triggers:
      - type: "pattern"
        pattern: "git push.*origin.*feature"
        field: "tool_input"
    template: "code_review_notification"
    
  build_failure:
    enabled: true
    priority: high
    channels: ["dingtalk", "telegram"]
    triggers:
      - type: "condition"
        field: "error_message"
        operator: "contains"
        value: "build failed"
    template: "build_failure_alert"
```

### 案例3：安全监控

```yaml
custom_events:
  security_scan:
    enabled: true
    priority: high
    channels: ["telegram", "email"]
    triggers:
      - type: "pattern"
        pattern: "nmap|sqlmap|nikto|burp"
        field: "tool_input"
    template: "security_tool_alert"
    
  privilege_escalation:
    enabled: true
    priority: critical
    channels: ["dingtalk", "telegram", "email"]
    triggers:
      - type: "pattern"
        pattern: "sudo su|su -|chmod 777"
        field: "tool_input"
    template: "privilege_escalation_alert"
```

## 🔧 高级配置技巧

### 1. 事件分组和批处理

```yaml
notifications:
  grouping:
    enabled: true
    group_window: 300  # 5分钟内的相似事件分组
    max_group_size: 5
    similar_events: true
```

### 2. 智能静默

```yaml
notifications:
  smart_silence:
    enabled: true
    duplicate_threshold: 3  # 相同事件3次后静默
    silence_duration: 1800  # 静默30分钟
    escalation_threshold: 10  # 10次后升级通知
```

### 3. 动态渠道选择

```yaml
events:
  critical_error:
    enabled: true
    priority: critical
    dynamic_channels:
      work_hours: ["dingtalk", "telegram"]
      off_hours: ["telegram", "email"]
      weekend: ["email"]
```

### 4. 模板继承

```yaml
# 基础模板
base_alert_template:
  fields:
    - label: '项目'
      value: '${project}'
      short: true
    - label: '时间'
      value: '${timestamp}'
      short: true
  color: '#ffc107'

# 继承基础模板
custom_alert_template:
  extends: "base_alert_template"
  title: '自定义警告'
  content: '${custom_message}'
  additional_fields:
    - label: '自定义字段'
      value: '${custom_value}'
      short: false
```

## 🚀 性能优化

### 1. 事件处理优化

```yaml
advanced:
  event_processing:
    async_enabled: true
    queue_size: 100
    worker_threads: 2
    batch_size: 10
```

### 2. 模板缓存

```yaml
templates:
  cache_enabled: true
  cache_ttl: 3600
  preload_templates: true
```

### 3. 渠道连接池

```yaml
channels:
  connection_pool:
    enabled: true
    max_connections: 10
    connection_timeout: 30
    read_timeout: 60
```

通过这些高级配置，您可以构建一个功能强大、高度定制化的 Claude Code 通知系统，满足各种复杂的使用场景需求。

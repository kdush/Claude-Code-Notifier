# 🚀 Claude Code Notifier 高级使用指南

本文档介绍 Claude Code Notifier 的高级功能，包括自定义事件、模板系统和多渠道配置。

## 📊 使用统计与成本分析

Claude Code Notifier 集成了 [ccusage](https://github.com/ryoppippi/ccusage) 工具来提供详细的使用统计：

### 基础使用统计
```bash
# 快速查看使用统计
npx ccusage

# 查看详细的月度报告
npx ccusage --monthly --detailed

# 按模型分析成本
npx ccusage --by-model
```

### 高级统计功能
```bash
# 生成 JSON 格式报告
npx ccusage --output usage-stats.json

# 实时监控模式
npx ccusage --watch

# 指定日期范围分析
npx ccusage --from 2025-08-01 --to 2025-08-31
```

### 集成到通知系统
可以将 ccusage 统计结果集成到通知中：

```yaml
custom_events:
  usage_report:
    enabled: true
    schedule: "0 9 * * 1"  # 每周一早上9点
    channels: ["email", "dingtalk"]
    template: "weekly_usage_report"
    command: "npx ccusage --monthly --json"
```

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

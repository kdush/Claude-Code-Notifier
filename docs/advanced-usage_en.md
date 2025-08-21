[中文文档](advanced-usage.md)

# 🚀 Claude Code Notifier Advanced Usage Guide

This document covers advanced features of Claude Code Notifier, including custom events, the template system, and multi-channel configuration.

## 📊 Usage Statistics & Cost Analysis

Claude Code Notifier integrates with [ccusage](https://github.com/ryoppippi/ccusage) to provide detailed token usage and cost analysis for Claude Code. ccusage is an excellent open-source tool by [@ryoppippi](https://github.com/ryoppippi).

### Quick Start

#### Install & Use
```bash
# Use via npx (recommended)
npx ccusage

# Or via bunx
bunx ccusage

# Global install (optional)
npm install -g ccusage
```

#### Basic Commands
```bash
# Show basic usage stats
ccusage

# Monthly report
ccusage --monthly

# Daily detailed stats
ccusage --daily

# Session statistics
ccusage --session
```

### Core Features

#### Token Usage Analysis
- Real-time stats: analyze local JSONL token consumption
- Model breakdown: separate usage per Claude model
- Time dimensions: daily, monthly, and session granularity

#### Cost Tracking
- Cost calculation: compute actual costs by model pricing
- Trend analysis: track usage trends and cost changes
- Budget management: keep AI usage costs under control

#### Report Generation
```bash
# Generate JSON report
ccusage --output usage-report.json

# Specify time range
ccusage --from 2025-08-01 --to 2025-08-31

# Compact display
ccusage --compact
```

### Advanced Configuration

#### Time Zone
```bash
# Set time zone
ccusage --timezone Asia/Shanghai

# Use locale
ccusage --locale zh-CN
```

#### Real-time Monitoring
```bash
# Real-time watch mode
ccusage --watch

# 5-hour billing window monitoring
ccusage --billing-window
```

### Integration with Notifier

#### Automated Periodic Reports
Add scheduled usage notifications in Claude Code Notifier config:

```yaml
custom_events:
  # Daily usage report
  daily_usage_report:
    enabled: true
    schedule: "0 8 * * *"  # 8:00 AM daily
    channels: ["email"]
    template: "usage_report_daily"
    command: "npx ccusage --daily --json"
    
  # Weekly cost report
  weekly_cost_report:
    enabled: true
    schedule: "0 9 * * 1"  # 9:00 AM every Monday
    channels: ["dingtalk", "email"]
    template: "usage_report_weekly"
    command: "npx ccusage --weekly --output /tmp/weekly-usage.json"
    
  # Monthly detailed report
  monthly_detailed_report:
    enabled: true
    schedule: "0 10 1 * *"  # 10:00 AM on the 1st of each month
    channels: ["email", "feishu"]
    template: "usage_report_monthly"
    command: "npx ccusage --monthly --detailed --json"
```

#### Threshold Alerts
Configure usage threshold alerts:

```yaml
intelligence:
  usage_monitoring:
    enabled: true
    daily_token_limit: 100000
    monthly_cost_limit: 50.00
    alert_channels: ["telegram", "email"]
    check_command: "npx ccusage --today --json"
```

### Report Templates

#### Basic Usage Report Template
```yaml
templates:
  usage_report_daily:
    title: "📊 Claude Code Daily Usage Report"
    content: |
      **Usage**
      - Tokens: {{total_tokens}}
      - Cost: ${{total_cost}}
      - Sessions: {{session_count}}
      
      **Model Breakdown**
      - Sonnet: {{sonnet_tokens}} tokens (${{sonnet_cost}})
      - Opus: {{opus_tokens}} tokens (${{opus_cost}})
      
      See attachment for detailed report.
    fields:
      - label: "Date"
        value: "{{date}}"
      - label: "Total Tokens"
        value: "{{total_tokens}}"
      - label: "Total Cost"
        value: "${{total_cost}}"
```

### Troubleshooting

#### FAQ

Q: ccusage cannot find data files?
```bash
# Check Claude Code JSONL location
ls -la ~/.claude/usage/

# Specify data directory
ccusage --data-dir ~/.claude/usage/
```

Q: Stats look inaccurate?
```bash
# Rescan all files
ccusage --refresh

# Validate data integrity
ccusage --validate
```

Q: How to export historical data?
```bash
# Export all history
ccusage --export-all --output claude-usage-history.json

# Export a time range
ccusage --from 2025-01-01 --to 2025-08-31 --export --output usage-2025.json
```

### Acknowledgements

Thanks to [@ryoppippi](https://github.com/ryoppippi) for creating and maintaining the excellent ccusage tool, which gives us:

- 🚀 Blazing analysis speed — handle large usage data efficiently
- 📊 Detailed reports — comprehensive usage and cost analytics
- 🎯 Precise cost tracking — accurate per-model pricing
- 📅 Flexible time dimensions — multiple ranges supported
- 💻 Offline analysis — local data to protect privacy

This tool greatly enhances the monitoring and analytics capability of Claude Code Notifier!

### References

- ccusage Docs: https://ccusage.com
- GitHub Repo: https://github.com/ryoppippi/ccusage
- Usage Examples: https://github.com/ryoppippi/ccusage#usage

## 📋 Table of Contents

- Usage Statistics & Cost Analysis
- Custom Events Configuration
- Template System Usage
- Multi-channel Configuration
- Event Toggle Management
- Configuration Tooling
- Real-world Use Cases

## 🎯 Custom Events Configuration

### Basic Custom Event
Add a custom event in your configuration file:

```yaml
custom_events:
  # Git commit detection
  git_commit_detected:
    enabled: true
    priority: normal
    channels: ["dingtalk"]
    template: "git_commit_custom"
    triggers:
      - type: "pattern"
        pattern: "git\s+commit"
        field: "tool_input"
        flags: ["IGNORECASE"]
    data_extractors:
      commit_message:
        type: "regex"
        pattern: "-m\s+[\"']([^\"']+)[\"']"
        field: "tool_input"
        group: 1
      project_name:
        type: "function"
        function: "get_project_name"
    message_template:
      title: "📝 Code Commit Detected"
      content: "Detected a Git commit in project ${project}"
      action: "Please review commit content"
```

### Trigger Types

#### 1. Pattern Trigger
```yaml
triggers:
  - type: "pattern"
    pattern: "docker\s+(run|build|push)"
    field: "tool_input"
    flags: ["IGNORECASE", "MULTILINE"]
```

#### 2. Condition Trigger
```yaml
triggers:
  - type: "condition"
    field: "tool_name"
    operator: "equals"
    value: "run_command"
```

#### 3. Function Trigger
```yaml
triggers:
  - type: "function"
    function: "is_work_hours"  # built-in
```

#### 4. Composite Conditions
```yaml
triggers:
  - type: "condition"
    field: "project"
    operator: "contains"
    value: "production"
  - type: "pattern"
    pattern: "rm\s+-rf"
    field: "tool_input"
```

### Data Extractors

#### Field Extractor
```yaml
data_extractors:
  simple_field: "tool_name"  # simple field extraction
  
  complex_field:
    type: "field"
    field: "error_message"
    default: "No error message"
```

#### Regex Extractor
```yaml
data_extractors:
  file_name:
    type: "regex"
    pattern: "\b([\w-]+\.py)\b"
    field: "tool_input"
    group: 1
```

#### Function Extractor
```yaml
data_extractors:
  current_time:
    type: "function"
    function: "get_current_time"
```

## 🎨 Template System Usage

### Create a Custom Template
Create YAML files under `~/.claude-notifier/templates/`:

```yaml
# my_custom_template.yaml
production_alert:
  title: '🚨 Production Operation Warning'
  content: '⚠️ Detected production operation: ${operation}'
  fields:
    - label: 'Project'
      value: '${project}'
      short: true
    - label: 'Operation Type'
      value: '${tool_name}'
      short: true
    - label: 'Command'
      value: '${tool_input}'
      short: false
    - label: 'Risk Level'
      value: '🔴 High'
      short: true
  actions:
    - text: 'Confirm Now'
      type: 'button'
      style: 'danger'
    - text: 'View Logs'
      type: 'button'
      url: 'logs://'
  color: '#dc3545'
```

### Template Variables

Available variables:

- ${project} — Project name
- ${timestamp} — Timestamp
- ${event_type} — Event type
- ${priority} — Priority
- ${tool_name} — Tool name
- ${tool_input} — Tool input
- ${error_message} — Error message
- ${operation} — Operation content

### Channel-specific Templates

Create templates per channel:

```yaml
# DingTalk-specific template
dingtalk_production_alert:
  title: '🚨 Production Operation'
  content: |
    ### ⚠️ High Risk Operation Detected
    
    **Project**: ${project}
    **Operation**: ${operation}
    **Time**: ${timestamp}
    
    Please confirm immediately!
  # DingTalk supports ActionCard
  actions:
    - text: 'Confirm'
      type: 'button'
    - text: 'Cancel'
      type: 'button'

# Telegram-specific template  
telegram_production_alert:
  title: '🚨 Production Alert'
  content: |
    *High Risk Operation Detected*
    
    Project: `${project}`
    Operation: `${operation}`
    Time: ${timestamp}
    
    Please confirm immediately!
  # Telegram has limited button support
```

## 🔀 Multi-channel Configuration

### Channel Priority
```yaml
# Different channels for different events
events:
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "telegram"]  # dual-channel for sensitive ops
    
  task_completion:
    enabled: true
    channels: ["dingtalk"]  # only DingTalk for task completion
    
  rate_limit:
    enabled: true
    channels: ["telegram"]  # Telegram for throttling notifications

# Default channels
notifications:
  default_channels: ["dingtalk"]  # used when event has no explicit channels
```

### Failover
```yaml
notifications:
  failover:
    enabled: true
    primary_channels: ["dingtalk"]
    fallback_channels: ["telegram", "email"]
    retry_interval: 30  # seconds
```

### Channel-specific Settings
```yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=..."
    secret: "SEC..."
    # DingTalk specifics
    at_all: false
    at_mobiles: []
    
  telegram:
    enabled: true
    bot_token: "123456:ABC-DEF..."
    chat_id: "-123456789"
    # Telegram specifics
    parse_mode: "Markdown"
    disable_web_page_preview: true
```

## ⚙️ Event Toggle Management

### Bulk Manage Events
```python
from src.config_manager import ConfigManager

config_manager = ConfigManager()

# Enable all builtin events
builtin_events = [
    'sensitive_operation',
    'task_completion', 
    'rate_limit',
    'error_occurred'
]

for event_id in builtin_events:
    config_manager.enable_event(event_id)

# Disable session start event (to reduce noise)
config_manager.disable_event('session_start')
```

### Conditional Enablement
```yaml
events:
  sensitive_operation:
    enabled: true
    conditions:
      # Notify only during work hours
      time_window:
        start: "09:00"
        end: "18:00"
      # Notify only for high-risk operations
      risk_levels: ["high", "critical"]
      # Project filter
      project_patterns: ["prod-*", "*-production"]
```

## 🛠️ Configuration Tooling

### Using the Config Manager
```python
from src.config_manager import ConfigManager

# Initialize
config_manager = ConfigManager()

# Get config stats
stats = config_manager.get_config_stats()
print(f"Enabled channels: {stats['enabled_channels']}")
print(f"Enabled events: {stats['enabled_events']}")

# Set default channels
config_manager.set_default_channels(['dingtalk', 'telegram'])

# Add a custom event
custom_event_config = {
    'name': 'Database Operation',
    'priority': 'high',
    'triggers': [{
        'type': 'pattern',
        'pattern': 'mysql|postgres|mongodb',
        'field': 'tool_input'
    }],
    'message_template': {
        'title': '🗄️ Database Operation',
        'content': 'Detected a database-related operation'
    }
}

config_manager.add_custom_event('db_operation', custom_event_config)

# Backup configuration
backup_file = config_manager.backup_config()
print(f"Config backed up to: {backup_file}")
```

### Configuration Validation
```python
# Validate configuration
errors = config_manager.validate_config()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid")
```

## 📚 Real-world Use Cases

### Case 1: Production Monitoring
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

### Case 2: Dev Team Collaboration
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

### Case 3: Security Monitoring
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

## 🔧 Advanced Configuration Tips

### 1. Event Grouping & Batching
```yaml
notifications:
  grouping:
    enabled: true
    group_window: 300  # group similar events within 5 minutes
    max_group_size: 5
    similar_events: true
```

### 2. Smart Silence
```yaml
notifications:
  smart_silence:
    enabled: true
    duplicate_threshold: 3  # silence after 3 duplicates
    silence_duration: 1800  # 30 minutes
    escalation_threshold: 10  # escalate after 10 occurrences
```

### 3. Dynamic Channel Selection
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

### 4. Template Inheritance
```yaml
# Base template
base_alert_template:
  fields:
    - label: 'Project'
      value: '${project}'
      short: true
    - label: 'Time'
      value: '${timestamp}'
      short: true
  color: '#ffc107'

# Inherit from base
custom_alert_template:
  extends: "base_alert_template"
  title: 'Custom Alert'
  content: '${custom_message}'
  additional_fields:
    - label: 'Custom Field'
      value: '${custom_value}'
      short: false
```

## 🚀 Performance Optimization

### 1. Event Processing
```yaml
advanced:
  event_processing:
    async_enabled: true
    queue_size: 100
    worker_threads: 2
    batch_size: 10
```

### 2. Template Cache
```yaml
templates:
  cache_enabled: true
  cache_ttl: 3600
  preload_templates: true
```

### 3. Channel Connection Pool
```yaml
channels:
  connection_pool:
    enabled: true
    max_connections: 10
    connection_timeout: 30
    read_timeout: 60
```

With these advanced configurations, you can build a powerful, highly customizable Claude Code notification system to meet complex real-world needs.

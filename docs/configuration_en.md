[中文文档](configuration.md)

# ⚙️ Configuration Guide

## Configuration File Structure

Claude Code Notifier uses YAML for configuration. The main configuration files are located at:
- `~/.claude-notifier/config.yaml` (global config)
- `./config.yaml` (project-level config, overrides global)

## Full Configuration Example

```yaml
# Notification channels
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    secret: "YOUR_SECRET"  # Optional: signature verification key
    
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK_ID"
    
  wechat_work:
    enabled: false
    webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    
  telegram:
    enabled: false
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
    
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_email: "your-email@gmail.com"
    to_email: "recipient@gmail.com"
    
  serverchan:
    enabled: false
    send_key: "YOUR_SEND_KEY"

# Events
events:
  # Permission confirmation
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "feishu"]  # Channels to use
    template: "permission_request"      # Message template
    priority: "high"                    # Priority: high/normal/low
    
  # Task completion
  task_completion:
    enabled: true
    channels: ["dingtalk"]
    template: "task_completion"
    priority: "normal"
    delay: 3  # Delay in seconds
    
  # Error
  error:
    enabled: true
    channels: ["dingtalk", "telegram"]
    template: "error_notification"
    priority: "high"
    
  # Session start/end
  session_start:
    enabled: false
    channels: ["email"]
    template: "session_info"
    priority: "low"
    
  session_end:
    enabled: true
    channels: ["dingtalk"]
    template: "session_info"
    priority: "low"

# Intelligence limits (optional)
intelligence:
  # Operation gate (blocklist)
  operation_gate:
    enabled: true
    # Blocked patterns
    blocked_patterns:
      - "sudo rm -rf"
      - "DROP TABLE"
      - "DELETE FROM"
      - "> /dev/null"
    # High-risk paths
    protected_paths:
      - "/etc"
      - "/usr/bin"
      - "/System"
    
  # Notification throttling
  notification_throttle:
    enabled: true
    max_per_minute: 10        # Max notifications per minute
    max_per_hour: 60          # Max per hour
    cooldown_period: 300      # Cooldown seconds
    
  # Message grouping
  message_grouper:
    enabled: true
    group_window: 60          # Window in seconds
    similarity_threshold: 0.8 # Similarity threshold
    max_group_size: 5         # Max group size

# Monitoring
monitoring:
  # Statistics collection
  statistics:
    enabled: true
    retention_days: 30        # Retention days
    
  # Health checks
  health_check:
    enabled: true
    check_interval: 300       # Interval (s)
    
  # Performance monitoring
  performance:
    enabled: true
    sample_rate: 0.1          # Sampling rate

# Detection rules
detection:
  # Sensitive operation patterns
  sensitive_patterns:
    # System administration
    - "sudo"
    - "su -"
    - "chmod [0-9]+"
    - "chown"
    
    # File operations
    - "rm -rf"
    - "rmdir"
    - "> /dev/null"
    
    # Network operations
    - "curl.*|.*sh"
    - "wget.*|.*sh"
    
    # Version control
    - "git push.*force"
    - "git reset.*hard"
    
    # Package management
    - "npm publish"
    - "pip install.*--force"
    - "brew install"
    
    # Containers/Deployment
    - "docker"
    - "kubectl"
    - "helm"
    
    # Database
    - "DROP"
    - "DELETE.*FROM"
    - "TRUNCATE"
    
  # Safe patterns (not treated as sensitive)
  safe_patterns:
    - "ls"
    - "cat"
    - "echo"
    - "pwd"
    - "cd"
    - "mkdir"
    - "touch"

# Templates
templates:
  # Custom template directory
  custom_templates_dir: "~/.claude-notifier/templates"
  
  # Template variables
  variables:
    user_name: "Developer"
    project_emoji: "🚀"
    completion_emoji: "🎉"

# Advanced settings
advanced:
  # Logging
  logging:
    level: "INFO"             # DEBUG/INFO/WARNING/ERROR
    file: "~/.claude-notifier/logs/notifier.log"
    max_size: "10MB"
    backup_count: 3
    
  # Network
  network:
    timeout: 30               # Request timeout (s)
    retry_attempts: 3         # Retry times
    retry_delay: 1            # Retry delay (s)
    
  # Security
  security:
    validate_ssl: true        # SSL certificate validation
    max_message_size: 4096    # Max message size (bytes)
    
  # Performance
  performance:
    async_send: true          # Async sending
    cache_templates: true     # Cache templates
    batch_notifications: false  # Batch sending
```

## Configuration Validation

### Validate configuration files
```bash
# Check syntax and validity
claude-notifier config validate

# Test channel connectivity
claude-notifier config test --channel dingtalk
```

### Common Configuration Errors

1. YAML syntax errors
   ```
   Issue: inconsistent indentation
   Fix: use spaces instead of tabs, keep indentation consistent
   ```

2. Channel misconfiguration
   ```
   Issue: invalid webhook URL
   Fix: check URL format and access permissions
   ```

3. Event configuration errors
   ```
   Issue: referencing disabled or non-existent channel
   Fix: ensure channels in list are enabled and correctly configured
   ```

## Environment Variables

You can override some configuration values via environment variables:

```bash
# DingTalk
export CLAUDE_NOTIFIER_DINGTALK_WEBHOOK="your_webhook"
export CLAUDE_NOTIFIER_DINGTALK_SECRET="your_secret"

# Feishu
export CLAUDE_NOTIFIER_FEISHU_WEBHOOK="your_webhook"

# Telegram
export CLAUDE_NOTIFIER_TELEGRAM_TOKEN="your_bot_token"
export CLAUDE_NOTIFIER_TELEGRAM_CHAT_ID="your_chat_id"

# Enable debug mode
export CLAUDE_NOTIFIER_DEBUG=1
```

## Multi-environment Configuration

### Development
```yaml
# config/development.yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=DEV_TOKEN"

events:
  sensitive_operation:
    enabled: true
    channels: ["dingtalk"]
    
detection:
  sensitive_patterns:
    - "rm -rf"  # Only monitor high-risk commands
```

### Production
```yaml
# config/production.yaml
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=PROD_TOKEN"
  
  email:
    enabled: true
    smtp_server: "smtp.company.com"
    to_email: "devops-team@company.com"

events:
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "email"]
    
  error:
    enabled: true
    channels: ["email"]
    priority: "high"
```

## Best Practices

1. Security
   - Store sensitive values in environment variables
   - Rotate API keys and tokens regularly
   - Enable SSL verification

2. Performance
   - Configure reasonable notification throttling
   - Enable message grouping to reduce noise
   - Use async sending for better responsiveness

3. Maintainability
   - Keep a clear configuration structure
   - Document special configurations with comments
   - Manage environment-specific files separately

4. Monitoring
   - Enable statistics collection
   - Check health status regularly
   - Monitor notification success rate

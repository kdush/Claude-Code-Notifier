[中文文档](deployment-guide.md)

# Claude Code Notifier Deployment Guide

## 📋 Project Overview

Claude Code Notifier is a full-featured notification system supporting multiple event types, customizable configuration, multi-channel delivery, and a flexible template system.

### 🎯 Core Features

- Built-in events: sensitive operation detection, task completion, rate limit alerts, error handling, session management
- Custom events: pattern matching, conditional triggers, function callbacks
- Multi-channel: DingTalk, Feishu (Lark), Telegram, Email, etc.
- Template system: customizable card styles and content
- Configuration management: validation, backup, and restore
- Event switches: enable/disable control per event

## 🚀 Quick Deployment

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd claude-code-notifier

# Install dependencies
pip install -r requirements.txt

# Or use a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Quick Configuration

```bash
# Run quick setup script
python3 scripts/quick_setup.py
```

The quick setup will guide you to:
- Configure notification channels (DingTalk, Feishu, etc.)
- Select events to enable
- Add custom events
- Set advanced options

### 3. Manual Configuration

```bash
# Copy template
cp config/enhanced_config.yaml.template config/config.yaml

# Edit configuration
vim config/config.yaml
```

### 4. Verify Deployment

```bash
# Run system tests
python3 scripts/run_tests.py

# Run specific tests
python3 tests/test_events.py

# Test notification channels
./scripts/test.sh
```

## 📁 Project Structure

```
claude-code-notifier/
├── src/                    # Source code
│   ├── channels/          # Channel implementations
│   │   ├── base.py        # Base class
│   │   ├── dingtalk.py    # DingTalk
│   │   ├── feishu.py      # Feishu (Lark)
│   │   └── ...
│   ├── events/            # Event system
│   │   ├── base.py        # Base event
│   │   ├── builtin.py     # Built-in events
│   │   └── custom.py      # Custom events
│   ├── managers/          # Managers
│   │   └── event_manager.py
│   ├── templates/         # Template system
│   │   └── template_engine.py
│   └── config_manager.py  # Config management
├── config/                # Config files
├── templates/             # Notification templates
├── scripts/               # Utility scripts
├── tests/                 # Tests
├── docs/                  # Docs
└── examples/              # Examples
```

## ⚙️ Configuration

### Basic Configuration

```yaml
# Notification channels
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: "your-secret"
  
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    secret: "your-secret"

# Events
events:
  builtin:
    sensitive_operation:
      enabled: true
      channels: ["dingtalk", "feishu"]
    task_completion:
      enabled: true
      channels: ["dingtalk"]
  
  custom:
    git_operation:
      name: "Git Operation Detection"
      priority: "normal"
      enabled: true
      triggers:
        - type: "pattern"
          pattern: "git\\s+(commit|push)"
          field: "tool_input"
```

### Advanced Configuration

```yaml
# Notification settings
notifications:
  rate_limiting:
    enabled: true
    max_per_minute: 10
  
  time_windows:
    enabled: true
    quiet_hours:
      start: "22:00"
      end: "08:00"
      timezone: "Asia/Shanghai"

# Templates
templates:
  default_template: "default"
  user_templates_dir: "~/.claude-notifier/templates"
```

## 🔧 Custom Development

### Add a New Channel

1. Inherit from `BaseChannel`
2. Implement required methods:
   - `send_notification()`
   - `validate_config()`
   - `supports_actions()`
   - `get_max_content_length()`

```python
from src.channels.base import BaseChannel

class MyChannel(BaseChannel):
    def send_notification(self, template_data, event_type='generic'):
        # Implement sending logic
        pass
    
    def validate_config(self):
        # Validate configuration
        return True
```

### Add a Custom Event

```python
from src.events.base import BaseEvent, EventType, EventPriority

class MyEvent(BaseEvent):
    def __init__(self):
        super().__init__('my_event', EventType.CUSTOM, EventPriority.NORMAL)
    
    def should_trigger(self, context):
        # Decide whether to trigger
        return True
    
    def extract_data(self, context):
        # Extract event data
        return {'key': 'value'}
```

### Custom Templates

```yaml
# templates/my_template.yaml
title: "${title}"
content: |
  **Project**: ${project}
  **User**: ${user}
  **Time**: ${timestamp}
color: "blue"
buttons:
  - text: "View Details"
    url: "https://example.com"
    primary: true
```

## 🔍 Troubleshooting

### Common Issues

1. Invalid configuration format
   ```bash
   # Validate configuration
   python3 -c "from src.config_manager import ConfigManager; cm = ConfigManager(); print(cm.validate_config())"
   ```

2. Notification failed
   - Check network connectivity
   - Verify webhook URL and secrets
   - Inspect logs

3. Event not triggered
   - Check if the event is enabled
   - Verify trigger conditions
   - Review event statistics

### Debug Mode

```bash
# Enable verbose logs
export CLAUDE_NOTIFIER_DEBUG=1
python3 your_script.py
```

### Log Inspection

```bash
# System logs
tail -f ~/.claude-notifier/logs/notifier.log

# Error logs
tail -f ~/.claude-notifier/logs/error.log
```

## 📊 Monitoring and Maintenance

### Performance Monitoring

```python
from src.managers.event_manager import EventManager

# Get event statistics
manager = EventManager(config)
stats = manager.get_event_stats()
print(f"Total: {stats['total_events']}")
print(f"Triggered: {stats['triggered_events']}")
```

### Config Backups

```bash
# Backup configuration
python3 -c "from src.config_manager import ConfigManager; ConfigManager().backup_config()"

# Restore configuration
python3 -c "from src.config_manager import ConfigManager; ConfigManager().restore_config('backup_file.yaml')"
```

### Routine Maintenance

1. Clean up logs
   ```bash
   find ~/.claude-notifier/logs -name "*.log" -mtime +30 -delete
   ```

2. Update configuration
   ```bash
   python3 scripts/quick_setup.py
   ```

3. Run health checks
   ```bash
   python3 scripts/run_tests.py
   ```

## 🔒 Security Recommendations

1. Protect sensitive information
   - Use environment variables for secrets
   - Rotate webhook secrets regularly
   - Restrict permissions of config files

2. Network security
   - Use HTTPS webhooks
   - Enable signature verification
   - Configure firewall rules

3. Access control
   ```bash
   chmod 600 config/config.yaml
   chmod 700 ~/.claude-notifier/
   ```

## 📈 Extensions and Integrations

### CI/CD Integration

```yaml
# .github/workflows/notify.yml
- name: Send Notification
  run: |
    python3 -c "
    from src.managers.event_manager import EventManager
    from src.config_manager import ConfigManager
    
    config = ConfigManager().get_config()
    manager = EventManager(config)
    
    context = {
        'tool_input': 'CI/CD pipeline completed',
        'project': '${{ github.repository }}',
        'status': 'completed'
    }
    
    events = manager.process_context(context)
    print(f'Triggered {len(events)} events')
    "
```

### API Integration

```python
# Create a REST API endpoint
from flask import Flask, request, jsonify
from src.managers.event_manager import EventManager

app = Flask(__name__)

@app.route('/notify', methods=['POST'])
def notify():
    context = request.json
    events = event_manager.process_context(context)
    return jsonify({'triggered_events': len(events)})
```

## 📞 Support and Contributions

### Getting Help

1. Read the docs: `docs/advanced-usage_en.md`
2. Run examples: `python3 examples/usage_examples.py`
3. Browse tests: `python3 tests/test_events.py`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request

### Reporting Issues

Please file issues on GitHub with:
- Description of the problem
- Steps to reproduce
- System environment
- Configuration (with sensitive data removed)

---

🎉 Congratulations! You have successfully deployed Claude Code Notifier. Enjoy the productivity boost from smart notifications!

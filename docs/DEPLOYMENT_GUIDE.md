# Claude Code Notifier 部署指南

## 📋 项目概述

Claude Code Notifier 是一个功能完整的通知系统，支持多种事件类型、自定义配置、多渠道通知和模板系统。

### 🎯 核心功能

- **内置事件系统**: 敏感操作检测、任务完成、限流通知、错误处理、会话管理
- **自定义事件**: 支持模式匹配、条件判断、函数触发等多种触发方式
- **多渠道支持**: 钉钉、飞书、Telegram、邮箱等多种通知渠道
- **模板系统**: 可自定义通知卡片样式和内容
- **配置管理**: 完整的配置验证、备份、恢复功能
- **事件开关**: 灵活的事件启用/禁用控制

## 🚀 快速部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd claude-code-notifier

# 安装依赖
pip install -r requirements.txt

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. 快速配置

```bash
# 运行快速配置脚本
python3 scripts/quick_setup.py
```

快速配置将引导您：
- 配置通知渠道（钉钉、飞书等）
- 选择要启用的事件
- 添加自定义事件
- 设置高级选项

### 3. 手动配置

```bash
# 复制配置模板
cp config/enhanced_config.yaml.template config/config.yaml

# 编辑配置文件
vim config/config.yaml
```

### 4. 测试部署

```bash
# 运行系统测试
python3 scripts/run_tests.py

# 运行特定测试
python3 tests/test_events.py

# 测试通知渠道
./scripts/test.sh
```

## 📁 项目结构

```
claude-code-notifier/
├── src/                    # 源代码
│   ├── channels/          # 通知渠道实现
│   │   ├── base.py       # 渠道基类
│   │   ├── dingtalk.py   # 钉钉渠道
│   │   ├── feishu.py     # 飞书渠道
│   │   └── ...
│   ├── events/           # 事件系统
│   │   ├── base.py       # 事件基类
│   │   ├── builtin.py    # 内置事件
│   │   └── custom.py     # 自定义事件
│   ├── managers/         # 管理器
│   │   └── event_manager.py
│   ├── templates/        # 模板系统
│   │   └── template_engine.py
│   └── config_manager.py # 配置管理
├── config/               # 配置文件
├── templates/            # 通知模板
├── scripts/              # 脚本工具
├── tests/                # 测试文件
├── docs/                 # 文档
└── examples/             # 使用示例
```

## ⚙️ 配置说明

### 基础配置

```yaml
# 通知渠道配置
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: "your-secret"
  
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    secret: "your-secret"

# 事件配置
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
      name: "Git操作检测"
      priority: "normal"
      enabled: true
      triggers:
        - type: "pattern"
          pattern: "git\\s+(commit|push)"
          field: "tool_input"
```

### 高级配置

```yaml
# 通知设置
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

# 模板配置
templates:
  default_template: "default"
  user_templates_dir: "~/.claude-notifier/templates"
```

## 🔧 自定义开发

### 添加新的通知渠道

1. 继承 `BaseChannel` 类
2. 实现必要的方法：
   - `send_notification()`
   - `validate_config()`
   - `supports_actions()`
   - `get_max_content_length()`

```python
from src.channels.base import BaseChannel

class MyChannel(BaseChannel):
    def send_notification(self, template_data, event_type='generic'):
        # 实现通知发送逻辑
        pass
    
    def validate_config(self):
        # 验证配置
        return True
```

### 添加自定义事件

```python
from src.events.base import BaseEvent, EventType, EventPriority

class MyEvent(BaseEvent):
    def __init__(self):
        super().__init__('my_event', EventType.CUSTOM, EventPriority.NORMAL)
    
    def should_trigger(self, context):
        # 判断是否应该触发
        return True
    
    def extract_data(self, context):
        # 提取事件数据
        return {'key': 'value'}
```

### 自定义模板

```yaml
# templates/my_template.yaml
title: "${title}"
content: |
  **项目**: ${project}
  **用户**: ${user}
  **时间**: ${timestamp}
color: "blue"
buttons:
  - text: "查看详情"
    url: "https://example.com"
    primary: true
```

## 🔍 故障排除

### 常见问题

1. **配置文件格式错误**
   ```bash
   # 验证配置
   python3 -c "from src.config_manager import ConfigManager; cm = ConfigManager(); print(cm.validate_config())"
   ```

2. **通知发送失败**
   - 检查网络连接
   - 验证 webhook URL 和密钥
   - 查看日志文件

3. **事件未触发**
   - 检查事件是否启用
   - 验证触发条件
   - 查看事件统计

### 调试模式

```bash
# 启用详细日志
export CLAUDE_NOTIFIER_DEBUG=1
python3 your_script.py
```

### 日志查看

```bash
# 查看系统日志
tail -f ~/.claude-notifier/logs/notifier.log

# 查看错误日志
tail -f ~/.claude-notifier/logs/error.log
```

## 📊 监控和维护

### 性能监控

```python
from src.managers.event_manager import EventManager

# 获取事件统计
manager = EventManager(config)
stats = manager.get_event_stats()
print(f"处理事件数: {stats['total_events']}")
print(f"触发事件数: {stats['triggered_events']}")
```

### 配置备份

```bash
# 自动备份配置
python3 -c "from src.config_manager import ConfigManager; ConfigManager().backup_config()"

# 恢复配置
python3 -c "from src.config_manager import ConfigManager; ConfigManager().restore_config('backup_file.yaml')"
```

### 定期维护

1. **清理日志文件**
   ```bash
   find ~/.claude-notifier/logs -name "*.log" -mtime +30 -delete
   ```

2. **更新配置**
   ```bash
   python3 scripts/quick_setup.py
   ```

3. **运行健康检查**
   ```bash
   python3 scripts/run_tests.py
   ```

## 🔒 安全建议

1. **保护敏感信息**
   - 使用环境变量存储密钥
   - 定期轮换 webhook 密钥
   - 限制配置文件访问权限

2. **网络安全**
   - 使用 HTTPS webhook
   - 启用消息签名验证
   - 配置防火墙规则

3. **访问控制**
   ```bash
   chmod 600 config/config.yaml
   chmod 700 ~/.claude-notifier/
   ```

## 📈 扩展和集成

### 与 CI/CD 集成

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

### API 集成

```python
# 创建 REST API 端点
from flask import Flask, request, jsonify
from src.managers.event_manager import EventManager

app = Flask(__name__)

@app.route('/notify', methods=['POST'])
def notify():
    context = request.json
    events = event_manager.process_context(context)
    return jsonify({'triggered_events': len(events)})
```

## 📞 支持和贡献

### 获取帮助

1. 查看文档: `docs/advanced_usage.md`
2. 运行示例: `python3 examples/usage_examples.py`
3. 查看测试: `python3 tests/test_events.py`

### 贡献代码

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 报告问题

请在 GitHub Issues 中报告问题，包含：
- 错误描述
- 复现步骤
- 系统环境
- 配置信息（去除敏感数据）

---

🎉 **恭喜！** 您已成功部署 Claude Code Notifier 系统。享受智能通知带来的便利吧！

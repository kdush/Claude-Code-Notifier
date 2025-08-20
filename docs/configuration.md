# ⚙️ 配置指南

## 配置文件结构

Claude Code Notifier 使用 YAML 配置文件，主配置文件位于：
- `~/.claude-notifier/config.yaml` (全局配置)
- `./config.yaml` (项目级配置，可覆盖全局配置)

## 完整配置示例

```yaml
# 通知渠道配置
channels:
  dingtalk:
    enabled: true
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    secret: "YOUR_SECRET"  # 可选：签名验证密钥
    
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

# 事件配置
events:
  # 权限确认事件
  sensitive_operation:
    enabled: true
    channels: ["dingtalk", "feishu"]  # 使用的通知渠道
    template: "permission_request"    # 消息模板
    priority: "high"                  # 优先级：high/normal/low
    
  # 任务完成事件
  task_completion:
    enabled: true
    channels: ["dingtalk"]
    template: "task_completion"
    priority: "normal"
    delay: 3  # 延迟发送（秒）
    
  # 错误事件
  error:
    enabled: true
    channels: ["dingtalk", "telegram"]
    template: "error_notification"
    priority: "high"
    
  # 会话开始/结束
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

# 智能限制配置（可选）
intelligence:
  # 操作门控
  operation_gate:
    enabled: true
    # 阻止的操作模式
    blocked_patterns:
      - "sudo rm -rf"
      - "DROP TABLE"
      - "DELETE FROM"
      - "> /dev/null"
    # 高风险项目路径
    protected_paths:
      - "/etc"
      - "/usr/bin"
      - "/System"
    
  # 通知限流
  notification_throttle:
    enabled: true
    max_per_minute: 10        # 每分钟最大通知数
    max_per_hour: 60          # 每小时最大通知数
    cooldown_period: 300      # 冷却时间（秒）
    
  # 消息分组
  message_grouper:
    enabled: true
    group_window: 60          # 分组时间窗口（秒）
    similarity_threshold: 0.8  # 相似度阈值
    max_group_size: 5         # 最大分组大小

# 监控配置
monitoring:
  # 统计收集
  statistics:
    enabled: true
    retention_days: 30        # 统计数据保留天数
    
  # 健康检查
  health_check:
    enabled: true
    check_interval: 300       # 检查间隔（秒）
    
  # 性能监控
  performance:
    enabled: true
    sample_rate: 0.1          # 采样率

# 检测规则
detection:
  # 敏感操作模式
  sensitive_patterns:
    # 系统管理
    - "sudo"
    - "su -"
    - "chmod [0-9]+"
    - "chown"
    
    # 文件操作
    - "rm -rf"
    - "rmdir"
    - "> /dev/null"
    
    # 网络操作
    - "curl.*|.*sh"
    - "wget.*|.*sh"
    
    # 版本控制
    - "git push.*force"
    - "git reset.*hard"
    
    # 包管理
    - "npm publish"
    - "pip install.*--force"
    - "brew install"
    
    # 容器/部署
    - "docker"
    - "kubectl"
    - "helm"
    
    # 数据库
    - "DROP"
    - "DELETE.*FROM"
    - "TRUNCATE"
    
  # 排除模式（不视为敏感操作）
  safe_patterns:
    - "ls"
    - "cat"
    - "echo"
    - "pwd"
    - "cd"
    - "mkdir"
    - "touch"

# 模板配置
templates:
  # 自定义模板目录
  custom_templates_dir: "~/.claude-notifier/templates"
  
  # 模板变量
  variables:
    user_name: "开发者"
    project_emoji: "🚀"
    completion_emoji: "🎉"

# 高级设置
advanced:
  # 日志配置
  logging:
    level: "INFO"            # DEBUG/INFO/WARNING/ERROR
    file: "~/.claude-notifier/logs/notifier.log"
    max_size: "10MB"
    backup_count: 3
    
  # 网络配置
  network:
    timeout: 30              # 请求超时（秒）
    retry_attempts: 3        # 重试次数
    retry_delay: 1           # 重试延迟（秒）
    
  # 安全设置
  security:
    validate_ssl: true       # SSL证书验证
    max_message_size: 4096   # 最大消息大小（字节）
    
  # 性能设置
  performance:
    async_send: true         # 异步发送
    cache_templates: true    # 缓存模板
    batch_notifications: false  # 批量发送
```

## 配置验证

### 验证配置文件
```bash
# 检查配置文件语法和有效性
claude-notifier config validate

# 测试通知渠道连接
claude-notifier config test --channel dingtalk
```

### 常见配置错误

1. **YAML 语法错误**
   ```
   错误：缩进不一致
   解决：确保使用空格而非制表符，保持一致的缩进
   ```

2. **渠道配置错误**
   ```
   错误：webhook URL 无效
   解决：检查 URL 格式和访问权限
   ```

3. **事件配置错误**
   ```
   错误：引用了不存在的渠道
   解决：确保 channels 列表中的渠道都已启用
   ```

## 环境变量配置

可以通过环境变量覆盖部分配置：

```bash
# 钉钉配置
export CLAUDE_NOTIFIER_DINGTALK_WEBHOOK="your_webhook"
export CLAUDE_NOTIFIER_DINGTALK_SECRET="your_secret"

# 飞书配置
export CLAUDE_NOTIFIER_FEISHU_WEBHOOK="your_webhook"

# Telegram 配置
export CLAUDE_NOTIFIER_TELEGRAM_TOKEN="your_bot_token"
export CLAUDE_NOTIFIER_TELEGRAM_CHAT_ID="your_chat_id"

# 启用调试模式
export CLAUDE_NOTIFIER_DEBUG=1
```

## 多环境配置

### 开发环境
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
    - "rm -rf"  # 仅监控高风险操作
```

### 生产环境
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

## 配置最佳实践

1. **安全性**
   - 使用环境变量存储敏感信息
   - 定期更新 API 密钥和令牌
   - 启用 SSL 验证

2. **性能**
   - 合理设置通知频率限制
   - 启用消息分组减少噪音
   - 使用异步发送提高响应速度

3. **可维护性**
   - 使用清晰的配置文件结构
   - 添加注释说明特殊配置
   - 分环境管理配置文件

4. **监控**
   - 启用统计收集
   - 定期检查健康状态
   - 监控通知发送成功率
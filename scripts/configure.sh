#!/bin/bash

CONFIG_FILE="$HOME/.claude-notifier/config.yaml"

echo "⚙️  Claude Code Notifier 配置向导"
echo "================================="
echo ""

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在，请先运行安装脚本"
    exit 1
fi

# 备份现有配置
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%s)"
    echo "✅ 已备份现有配置文件"
fi

echo "📱 支持的通知渠道:"
echo "   1. 钉钉机器人"
echo "   2. 飞书机器人"
echo "   3. 企业微信机器人"
echo "   4. Telegram Bot"
echo "   5. 邮箱 SMTP"
echo "   6. Server酱"
echo "   7. 跳过配置"
echo ""

# 初始化配置变量
DINGTALK_ENABLED=false
FEISHU_ENABLED=false
WECHAT_WORK_ENABLED=false
TELEGRAM_ENABLED=false
EMAIL_ENABLED=false
SERVERCHAN_ENABLED=false

DINGTALK_WEBHOOK=""
DINGTALK_SECRET=""
FEISHU_WEBHOOK=""
FEISHU_SECRET=""
WECHAT_WORK_WEBHOOK=""
TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""
EMAIL_SMTP_SERVER=""
EMAIL_SMTP_PORT=""
EMAIL_USERNAME=""
EMAIL_PASSWORD=""
EMAIL_TO=""
SERVERCHAN_SENDKEY=""

while true; do
    echo "请选择要配置的通知渠道 (输入数字，多个选择用空格分隔):"
    read -p "选择: " choices
    
    if [[ " $choices " == *" 7 "* ]]; then
        echo "跳过配置，使用现有配置"
        break
    fi
    
    # 钉钉机器人配置
    if [[ " $choices " == *" 1 "* ]]; then
        echo ""
        echo "🔔 配置钉钉机器人"
        echo "--------------------"
        read -p "请输入钉钉机器人 Webhook URL: " DINGTALK_WEBHOOK
        read -p "请输入钉钉机器人密钥 (可选): " DINGTALK_SECRET
        
        if [ -n "$DINGTALK_WEBHOOK" ]; then
            DINGTALK_ENABLED=true
            echo "✅ 钉钉机器人配置完成"
        fi
    fi
    
    # 飞书机器人配置
    if [[ " $choices " == *" 2 "* ]]; then
        echo ""
        echo "🚀 配置飞书机器人"
        echo "--------------------"
        read -p "请输入飞书机器人 Webhook URL: " FEISHU_WEBHOOK
        read -p "请输入飞书机器人密钥 (可选): " FEISHU_SECRET
        
        if [ -n "$FEISHU_WEBHOOK" ]; then
            FEISHU_ENABLED=true
            echo "✅ 飞书机器人配置完成"
        fi
    fi
    
    # 企业微信机器人配置
    if [[ " $choices " == *" 3 "* ]]; then
        echo ""
        echo "💼 配置企业微信机器人"
        echo "----------------------"
        read -p "请输入企业微信机器人 Webhook URL: " WECHAT_WORK_WEBHOOK
        
        if [ -n "$WECHAT_WORK_WEBHOOK" ]; then
            WECHAT_WORK_ENABLED=true
            echo "✅ 企业微信机器人配置完成"
        fi
    fi
    
    # Telegram Bot 配置
    if [[ " $choices " == *" 4 "* ]]; then
        echo ""
        echo "🤖 配置 Telegram Bot"
        echo "---------------------"
        read -p "请输入 Telegram Bot Token: " TELEGRAM_BOT_TOKEN
        read -p "请输入 Telegram Chat ID: " TELEGRAM_CHAT_ID
        
        if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
            TELEGRAM_ENABLED=true
            echo "✅ Telegram Bot 配置完成"
        fi
    fi
    
    # 邮箱 SMTP 配置
    if [[ " $choices " == *" 5 "* ]]; then
        echo ""
        echo "📮 配置邮箱 SMTP"
        echo "------------------"
        read -p "请输入 SMTP 服务器 (如 smtp.gmail.com): " EMAIL_SMTP_SERVER
        read -p "请输入 SMTP 端口 (如 587): " EMAIL_SMTP_PORT
        read -p "请输入邮箱用户名: " EMAIL_USERNAME
        read -s -p "请输入邮箱密码: " EMAIL_PASSWORD
        echo ""
        read -p "请输入接收邮箱: " EMAIL_TO
        
        if [ -n "$EMAIL_SMTP_SERVER" ] && [ -n "$EMAIL_USERNAME" ] && [ -n "$EMAIL_TO" ]; then
            EMAIL_ENABLED=true
            echo "✅ 邮箱 SMTP 配置完成"
        fi
    fi
    
    # Server酱配置
    if [[ " $choices " == *" 6 "* ]]; then
        echo ""
        echo "📧 配置 Server酱"
        echo "------------------"
        read -p "请输入 Server酱 SendKey: " SERVERCHAN_SENDKEY
        
        if [ -n "$SERVERCHAN_SENDKEY" ]; then
            SERVERCHAN_ENABLED=true
            echo "✅ Server酱配置完成"
        fi
    fi
    
    break
done

# 生成配置文件
echo ""
echo "📝 生成配置文件..."

cat > "$CONFIG_FILE" << CONFIG_EOF
# Claude Code Notifier 配置文件
# 生成时间: $(date)

# 通知渠道配置
channels:
  # 钉钉机器人
  dingtalk:
    enabled: $DINGTALK_ENABLED
    webhook: "$DINGTALK_WEBHOOK"
    secret: "$DINGTALK_SECRET"
    
  # 飞书机器人
  feishu:
    enabled: $FEISHU_ENABLED
    webhook: "$FEISHU_WEBHOOK"
    secret: "$FEISHU_SECRET"
    
  # 企业微信机器人
  wechat_work:
    enabled: $WECHAT_WORK_ENABLED
    webhook: "$WECHAT_WORK_WEBHOOK"
    
  # Telegram Bot
  telegram:
    enabled: $TELEGRAM_ENABLED
    bot_token: "$TELEGRAM_BOT_TOKEN"
    chat_id: "$TELEGRAM_CHAT_ID"
    
  # 邮箱 SMTP
  email:
    enabled: $EMAIL_ENABLED
    smtp_server: "$EMAIL_SMTP_SERVER"
    smtp_port: $EMAIL_SMTP_PORT
    username: "$EMAIL_USERNAME"
    password: "$EMAIL_PASSWORD"
    to_email: "$EMAIL_TO"
    
  # Server酱
  serverchan:
    enabled: $SERVERCHAN_ENABLED
    sendkey: "$SERVERCHAN_SENDKEY"

# 通知设置
notifications:
  # 权限确认通知
  permission:
    enabled: true
    channels: []  # 空数组表示使用所有启用的渠道
    format: "actioncard"
    
  # 任务完成通知
  completion:
    enabled: true
    channels: []
    format: "markdown"
    delay: 3
    
  # 测试通知
  test:
    enabled: true
    channels: []
    format: "markdown"

# 检测规则
detection:
  # 需要权限确认的操作模式
  permission_patterns:
    - "sudo"
    - "rm -"
    - "chmod"
    - "chown"
    - "mv.*\\.env"
    - "cp.*\\.env"
    - "git push"
    - "npm publish"
    - "docker"
    - "kubectl"
    - "terraform"
    
  # 项目名称过滤
  project_filters:
    exclude:
      - "/"
      - "."
      - "tmp"
      - "temp"

# 高级设置
advanced:
  # 日志设置
  logging:
    enabled: true
    level: "info"
    file: "~/.claude-notifier/logs/notifier.log"
    
  # 重试设置
  retry:
    enabled: true
    max_attempts: 3
    delay: 1
    
  # 限流设置
  rate_limit:
    enabled: true
    max_per_minute: 10
CONFIG_EOF

echo "✅ 配置文件已生成: $CONFIG_FILE"
echo ""
echo "🎯 配置总结:"
[ "$DINGTALK_ENABLED" = true ] && echo "   ✅ 钉钉机器人"
[ "$FEISHU_ENABLED" = true ] && echo "   ✅ 飞书机器人"
[ "$WECHAT_WORK_ENABLED" = true ] && echo "   ✅ 企业微信机器人"
[ "$TELEGRAM_ENABLED" = true ] && echo "   ✅ Telegram Bot"
[ "$EMAIL_ENABLED" = true ] && echo "   ✅ 邮箱 SMTP"
[ "$SERVERCHAN_ENABLED" = true ] && echo "   ✅ Server酱"

echo ""
echo "🧪 接下来可以运行测试:"
echo "   $HOME/.claude-notifier/test.sh"
echo ""
echo "🎉 配置完成！现在可以在 Claude Code 中享受智能通知了！"

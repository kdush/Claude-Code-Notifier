#!/bin/bash

# Claude Code Notifier Hook 安装脚本
# 将钩子集成到 Claude Code 配置中

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/claude_hook.py"
CLAUDE_CONFIG_DIR="$HOME/.config/claude"
CLAUDE_HOOKS_FILE="$CLAUDE_CONFIG_DIR/hooks.json"

echo "🔧 Claude Code Notifier Hook 安装程序"
echo "======================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 创建 Claude 配置目录
mkdir -p "$CLAUDE_CONFIG_DIR"

# 创建或更新 hooks.json
if [ -f "$CLAUDE_HOOKS_FILE" ]; then
    echo "📄 发现现有 hooks.json，将进行备份..."
    cp "$CLAUDE_HOOKS_FILE" "$CLAUDE_HOOKS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 生成 hooks.json 配置
cat > "$CLAUDE_HOOKS_FILE" << EOF
{
  "hooks": {
    "on_session_start": {
      "command": "python3 $HOOK_SCRIPT session_start",
      "enabled": true,
      "description": "Claude Code 会话开始时触发"
    },
    "on_command_execute": {
      "command": "python3 $HOOK_SCRIPT command_execute '{\"command\": \"\$COMMAND\", \"tool\": \"\$TOOL\"}'",
      "enabled": true,
      "description": "执行命令时触发"
    },
    "on_task_complete": {
      "command": "python3 $HOOK_SCRIPT task_complete '{\"status\": \"\$STATUS\"}'",
      "enabled": true,
      "description": "任务完成时触发"
    },
    "on_error": {
      "command": "python3 $HOOK_SCRIPT error '{\"error_type\": \"\$ERROR_TYPE\", \"error_message\": \"\$ERROR_MESSAGE\"}'",
      "enabled": true,
      "description": "发生错误时触发"
    },
    "on_confirmation_required": {
      "command": "python3 $HOOK_SCRIPT confirmation_required '{\"message\": \"\$MESSAGE\"}'",
      "enabled": true,
      "description": "需要确认时触发"
    }
  },
  "settings": {
    "log_level": "info",
    "timeout": 5000
  }
}
EOF

echo "✅ hooks.json 已创建/更新"

# 创建 Claude 环境变量文件
CLAUDE_ENV_FILE="$HOME/.claude_env"
cat > "$CLAUDE_ENV_FILE" << EOF
# Claude Code Notifier 环境变量
export CLAUDE_NOTIFIER_ENABLED=true
export CLAUDE_NOTIFIER_CONFIG="$HOME/.claude-notifier/config.yaml"
export CLAUDE_PROJECT_DIR="\$(pwd)"
EOF

echo "✅ 环境变量文件已创建"

# 添加到 shell 配置文件
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
    # 检查是否已经添加
    if ! grep -q "claude_env" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Claude Code Notifier" >> "$SHELL_RC"
        echo "[ -f $HOME/.claude_env ] && source $HOME/.claude_env" >> "$SHELL_RC"
        echo "✅ 已添加到 $SHELL_RC"
    else
        echo "ℹ️  $SHELL_RC 中已存在配置"
    fi
fi

# 创建定时检查脚本（用于空闲检测）
CRON_SCRIPT="$SCRIPT_DIR/check_idle.sh"
cat > "$CRON_SCRIPT" << 'EOF'
#!/bin/bash
# 检查 Claude Code 空闲状态
python3 $HOOK_SCRIPT check_idle
EOF
chmod +x "$CRON_SCRIPT"

# 添加 crontab 任务（每5分钟检查一次）
(crontab -l 2>/dev/null | grep -v "claude_hook.py check_idle"; echo "*/5 * * * * $CRON_SCRIPT") | crontab -

echo "✅ 定时任务已设置"

# 设置权限
chmod +x "$HOOK_SCRIPT"
chmod 644 "$CLAUDE_HOOKS_FILE"

echo ""
echo "🎉 安装完成！"
echo ""
echo "请执行以下命令使配置生效："
echo "  source $HOME/.claude_env"
echo ""
echo "或重新打开终端窗口"
echo ""
echo "配置文件位置："
echo "  - Hooks: $CLAUDE_HOOKS_FILE"
echo "  - 环境变量: $HOME/.claude_env"
echo ""
echo "测试钩子："
echo "  python3 $HOOK_SCRIPT session_start"
echo ""
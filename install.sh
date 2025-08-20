#!/bin/bash

set -e

echo "🔔 Claude Code Notifier 安装程序"
echo "================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.6+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ 检测到 Python $PYTHON_VERSION"

# 检查 Claude Code 是否安装
if ! command -v claude &> /dev/null; then
    echo "⚠️  警告: Claude Code 未安装或不在 PATH 中"
    echo "   请确保已安装 Claude Code: npm install -g @anthropic-ai/claude-code"
    read -p "是否继续安装? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建配置目录
CONFIG_DIR="$HOME/.claude-notifier"
echo "📁 创建配置目录: $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"/{logs,hooks,session_states,templates,plugins}
mkdir -p "$CONFIG_DIR/data"/{cache,metrics,stats}

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user -r requirements.txt
else
    python3 -m pip install --user requests pyyaml pytz
fi

# 检查额外的可选依赖
echo "🔍 检查可选依赖..."
if ! python3 -c "import smtplib" 2>/dev/null; then
    echo "⚠️  警告: 邮件功能可能需要额外配置"
fi

# 复制源代码
echo "📋 复制程序文件..."
INSTALL_DIR="$CONFIG_DIR/src"
rm -rf "$INSTALL_DIR"
cp -r src "$INSTALL_DIR"

# 创建可执行脚本
echo "🔧 创建可执行脚本..."
cat > "$CONFIG_DIR/notifier" << 'SCRIPT_EOF'
#!/bin/bash
cd "$HOME/.claude-notifier/src"
python3 notifier.py "$@"
SCRIPT_EOF

chmod +x "$CONFIG_DIR/notifier"

# 复制配置文件模板
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "⚙️  创建配置文件模板..."
    if [ -f "config/enhanced_config.yaml.template" ]; then
        cp "config/enhanced_config.yaml.template" "$CONFIG_DIR/config.yaml"
        echo "   已安装增强配置模板: $CONFIG_DIR/config.yaml"
    elif [ -f "config/config.yaml.template" ]; then
        cp "config/config.yaml.template" "$CONFIG_DIR/config.yaml"
        echo "   已安装基础配置模板: $CONFIG_DIR/config.yaml"
    else
        echo "❌ 未找到配置模板文件"
        exit 1
    fi
fi

# 复制模板文件
echo "📄 复制消息模板..."
if [ -d "templates" ]; then
    cp -r templates/* "$CONFIG_DIR/templates/"
    echo "   模板文件已复制到: $CONFIG_DIR/templates/"
fi

# 复制脚本
echo "📜 复制管理脚本..."
if [ -d "scripts" ]; then
    cp -r scripts/* "$CONFIG_DIR/"
    chmod +x "$CONFIG_DIR"/*.sh
fi

# 创建 Claude Code 钩子
echo "🪝 配置 Claude Code 钩子..."

# 创建全局钩子配置
CLAUDE_CONFIG_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_CONFIG_DIR"

# 备份现有配置
if [ -f "$CLAUDE_CONFIG_DIR/settings.json" ]; then
    echo "   备份现有 Claude Code 配置..."
    cp "$CLAUDE_CONFIG_DIR/settings.json" "$CLAUDE_CONFIG_DIR/settings.json.backup.$(date +%s)"
fi

# 创建钩子脚本
cat > "$CONFIG_DIR/hooks/permission_check.sh" << 'HOOK_EOF'
#!/bin/bash
# Claude Code 权限检查钩子

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# 需要权限的操作模式
PERMISSION_PATTERNS=(
    "sudo"
    "rm -"
    "chmod"
    "chown"
    "git push"
    "npm publish"
    "docker"
    "kubectl"
)

# 检查是否需要权限
for pattern in "${PERMISSION_PATTERNS[@]}"; do
    if echo "$TOOL_INPUT" | grep -qi "$pattern"; then
        # 提取操作描述
        OPERATION_DESC=$(echo "$TOOL_INPUT" | grep -o '"command":"[^"]*"' | sed 's/"command":"//' | sed 's/"//' | head -1)
        
        if [ -z "$OPERATION_DESC" ]; then
            OPERATION_DESC=$(echo "$TOOL_INPUT" | head -1 | cut -c1-80)
        fi
        
        # 发送权限通知
        "$HOME/.claude-notifier/notifier" permission "检测到 $pattern 操作: $OPERATION_DESC"
        
        echo "⚠️ Claude Code 检测到敏感操作，已发送通知" >&2
        exit 2
    fi
done

exit 0
HOOK_EOF

cat > "$CONFIG_DIR/hooks/completion_check.sh" << 'HOOK_EOF'
#!/bin/bash
# Claude Code 任务完成钩子

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)}"

# 获取项目名
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
    PROJECT_NAME="$(basename "$CLAUDE_PROJECT_DIR")"
elif [ "$(pwd)" != "/" ] && [ "$(pwd)" != "$HOME" ]; then
    PROJECT_NAME="$(basename "$(pwd)")"
else
    PROJECT_NAME="claude-code"
fi

# 避免显示无效项目名
if [ -z "$PROJECT_NAME" ] || [ "$PROJECT_NAME" = "." ] || [ "$PROJECT_NAME" = "/" ]; then
    PROJECT_NAME="claude-code"
fi

# 创建状态目录
STATE_DIR="$HOME/.claude-notifier/session_states"
mkdir -p "$STATE_DIR"

SESSION_STATE_FILE="$STATE_DIR/${SESSION_ID}.completed"

# 避免重复通知
if [ -f "$SESSION_STATE_FILE" ]; then
    exit 0
fi

# 等待3秒确保任务真正完成
sleep 3

# 标记已完成并发送通知
touch "$SESSION_STATE_FILE"

# 发送完成通知
"$HOME/.claude-notifier/notifier" completion "$PROJECT_NAME 项目的 Claude Code 任务执行完成"

# 清理旧状态文件
find "$STATE_DIR" -name "*.completed" -mtime +1 -delete 2>/dev/null || true

exit 0
HOOK_EOF

chmod +x "$CONFIG_DIR/hooks"/*.sh

# 创建 Claude Code 钩子配置
cat > "$CLAUDE_CONFIG_DIR/settings.json" << 'CLAUDE_EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude-notifier/hooks/permission_check.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude-notifier/hooks/completion_check.sh &",
            "timeout": 1
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "*"
    ]
  }
}
CLAUDE_EOF

# 添加到 PATH (可选)
echo "🔗 创建符号链接..."
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$CONFIG_DIR/notifier" "$HOME/.local/bin/claude-notifier"
    echo "   已创建符号链接: ~/.local/bin/claude-notifier"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$CONFIG_DIR/notifier" "/usr/local/bin/claude-notifier"
    echo "   已创建符号链接: /usr/local/bin/claude-notifier"
fi

echo ""
# 初始化智能限流系统数据
echo "🧠 初始化智能限流系统..."
python3 -c "
import sys
sys.path.insert(0, '$CONFIG_DIR/src')
try:
    from utils.time_utils import RateLimitTracker
    from utils.cooldown_manager import CooldownManager
    
    # 创建初始配置验证
    print('✅ 智能限流组件验证通过')
except ImportError as e:
    print(f'⚠️  警告: 智能限流组件加载失败: {e}')
except Exception as e:
    print(f'⚠️  警告: 系统初始化异常: {e}')
"

echo ""
echo "🎉 Claude Code Notifier 安装完成！"
echo ""
echo "🧠 新功能特性:"
echo "   ✅ 智能操作阻止机制"
echo "   ✅ 通知频率自动控制"
echo "   ✅ 消息智能分组合并"
echo "   ✅ 多层级冷却管理"
echo "   ✅ 实时监控和统计"
echo ""
echo "📋 接下来的步骤:"
echo "   1. 配置通知渠道: $CONFIG_DIR/configure.sh"
echo "   2. 测试通知功能: $CONFIG_DIR/test.sh"
echo "   3. 编辑配置文件: nano $CONFIG_DIR/config.yaml"
echo "   4. 查看监控状态: $CONFIG_DIR/notifier status"
echo ""
echo "🚀 现在可以在任何项目中使用 Claude Code，享受智能通知体验！"
echo ""
echo "📊 配置目录结构:"
echo "   $CONFIG_DIR/"
echo "   ├── src/           # 程序源码"
echo "   ├── hooks/         # Claude Code 钩子"
echo "   ├── templates/     # 消息模板"
echo "   ├── data/          # 数据和缓存"
echo "   └── logs/          # 日志文件"
echo ""
echo "📖 查看文档: https://github.com/kdush/Claude-Code-Notifier"

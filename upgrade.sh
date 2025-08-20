#!/bin/bash

set -e

echo "🔄 Claude Code Notifier 升级程序"
echo "================================="

CONFIG_DIR="$HOME/.claude-notifier"

# 检查是否已安装
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ 未检测到现有安装，请运行 install.sh 进行全新安装"
    exit 1
fi

echo "✅ 检测到现有安装: $CONFIG_DIR"

# 备份现有配置
BACKUP_DIR="$CONFIG_DIR/backup/$(date +%Y%m%d_%H%M%S)"
echo "📦 备份现有配置到: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 备份重要文件
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    cp "$CONFIG_DIR/config.yaml" "$BACKUP_DIR/"
fi

if [ -d "$CONFIG_DIR/logs" ]; then
    cp -r "$CONFIG_DIR/logs" "$BACKUP_DIR/" 2>/dev/null || true
fi

if [ -d "$CONFIG_DIR/data" ]; then
    cp -r "$CONFIG_DIR/data" "$BACKUP_DIR/" 2>/dev/null || true
fi

# 检查 Python 依赖
echo "🔍 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION"

# 更新 Python 依赖
echo "📦 更新 Python 依赖..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user --upgrade -r requirements.txt
else
    python3 -m pip install --user --upgrade requests pyyaml pytz
fi

# 创建新目录结构
echo "🏗️  更新目录结构..."
mkdir -p "$CONFIG_DIR"/{session_states,templates,plugins}
mkdir -p "$CONFIG_DIR/data"/{cache,metrics,stats}

# 更新源代码
echo "🔄 更新程序文件..."
INSTALL_DIR="$CONFIG_DIR/src"
rm -rf "$INSTALL_DIR"
cp -r src "$INSTALL_DIR"

# 检查配置文件版本
echo "⚙️  检查配置文件..."
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    # 检查是否为旧版本配置
    if ! grep -q "intelligent_limiting" "$CONFIG_DIR/config.yaml" 2>/dev/null; then
        echo "📈 检测到旧版配置，升级到增强版本..."
        
        # 备份旧配置
        cp "$CONFIG_DIR/config.yaml" "$CONFIG_DIR/config.yaml.v1.backup"
        
        # 创建新配置文件
        if [ -f "config/enhanced_config.yaml.template" ]; then
            cp "config/enhanced_config.yaml.template" "$CONFIG_DIR/config.yaml.new"
            echo "   新配置模板已创建: $CONFIG_DIR/config.yaml.new"
            echo "   请手动合并配置: 旧配置备份在 $CONFIG_DIR/config.yaml.v1.backup"
            echo "   ⚠️  注意: 需要手动启用智能限流功能"
        fi
    else
        echo "✅ 配置文件已是最新版本"
    fi
fi

# 复制新模板
echo "📄 更新消息模板..."
if [ -d "templates" ]; then
    cp -r templates/* "$CONFIG_DIR/templates/" 2>/dev/null || true
fi

# 更新脚本
echo "📜 更新管理脚本..."
if [ -d "scripts" ]; then
    cp -r scripts/* "$CONFIG_DIR/" 2>/dev/null || true
    chmod +x "$CONFIG_DIR"/*.sh 2>/dev/null || true
fi

# 更新钩子
echo "🪝 更新 Claude Code 钩子..."
if [ -f "src/hooks/install_hooks.sh" ]; then
    bash "src/hooks/install_hooks.sh" --upgrade 2>/dev/null || true
fi

# 验证智能限流系统
echo "🧠 验证智能限流系统..."
python3 -c "
import sys
sys.path.insert(0, '$CONFIG_DIR/src')
try:
    from utils.operation_gate import OperationGate
    from utils.notification_throttle import NotificationThrottle
    from utils.message_grouper import MessageGrouper
    from utils.cooldown_manager import CooldownManager
    print('✅ 所有智能限流组件验证通过')
except ImportError as e:
    print(f'⚠️  警告: 部分组件加载失败: {e}')
except Exception as e:
    print(f'⚠️  警告: 验证异常: {e}')
"

# 数据迁移检查
echo "🔄 检查数据迁移..."
if [ -f "$CONFIG_DIR/data/stats.json" ]; then
    echo "   发现统计数据，无需迁移"
else
    echo "   初始化新的数据结构..."
    touch "$CONFIG_DIR/data/stats.json"
    echo '{"version": "1.2.0", "initialized": true}' > "$CONFIG_DIR/data/stats.json"
fi

# 权限检查
echo "🔒 检查文件权限..."
chmod +x "$CONFIG_DIR/notifier" 2>/dev/null || true
chmod +x "$CONFIG_DIR/hooks"/*.sh 2>/dev/null || true

# 符号链接更新
echo "🔗 更新符号链接..."
if [ -L "$HOME/.local/bin/claude-notifier" ]; then
    ln -sf "$CONFIG_DIR/notifier" "$HOME/.local/bin/claude-notifier"
    echo "   已更新符号链接: ~/.local/bin/claude-notifier"
elif [ -L "/usr/local/bin/claude-notifier" ]; then
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$CONFIG_DIR/notifier" "/usr/local/bin/claude-notifier"
        echo "   已更新符号链接: /usr/local/bin/claude-notifier"
    fi
fi

echo ""
echo "🎉 升级完成！"
echo ""
echo "📊 版本信息:"
python3 "$CONFIG_DIR/src/__version__.py" || echo "   Claude Code Notifier v1.2.0 (Intelligent Griffin)"
echo ""
echo "🆕 新增功能:"
echo "   🧠 智能操作阻止机制"
echo "   📊 通知频率自动控制"
echo "   🔄 消息智能分组合并"
echo "   ❄️ 多层级冷却管理"
echo "   📈 实时监控和统计"
echo ""
echo "⚠️  重要提醒:"
echo "   1. 配置文件可能需要手动更新"
echo "   2. 新功能默认禁用，需要手动启用"
echo "   3. 备份文件位置: $BACKUP_DIR"
echo ""
echo "📋 下一步操作:"
echo "   1. 检查配置文件: nano $CONFIG_DIR/config.yaml"
echo "   2. 测试新功能: $CONFIG_DIR/test.sh"
echo "   3. 查看状态: $CONFIG_DIR/notifier status"
echo ""
echo "🚀 享受智能通知体验！"
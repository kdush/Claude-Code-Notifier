#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$HOME/.claude-notifier/config.yaml"
PYTHON_NOTIFIER="$PROJECT_DIR/examples/usage_examples.py"

echo "🧪 Claude Code Notifier 测试工具"
echo "==============================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在，请先运行快速配置："
    echo "   python3 $PROJECT_DIR/scripts/quick_setup.py"
    exit 1
fi

# 检查项目文件
if [ ! -f "$PYTHON_NOTIFIER" ]; then
    echo "❌ 测试程序不存在: $PYTHON_NOTIFIER"
    exit 1
fi

# 解析命令行参数
CHANNEL=""
NOTIFICATION_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --channel|-c)
            CHANNEL="$2"
            shift 2
            ;;
        --type|-t)
            NOTIFICATION_TYPE="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -c, --channel CHANNEL    测试指定渠道 (dingtalk, feishu, wechat_work, telegram)"
            echo "  -t, --type TYPE          测试指定类型 (permission, completion, test)"
            echo "  -h, --help               显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                       测试所有启用的渠道"
            echo "  $0 -c dingtalk           测试钉钉渠道"
            echo "  $0 -t permission         测试权限通知"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 $0 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo ""

# 测试功能
if [ -n "$NOTIFICATION_TYPE" ]; then
    # 测试指定类型的通知
    case "$NOTIFICATION_TYPE" in
        "permission")
            echo "🔐 测试权限确认通知..."
            python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_permission_notification
test_permission_notification()
"
            ;;
        "completion")
            echo "✅ 测试任务完成通知..."
            python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_completion_notification
test_completion_notification()
"
            ;;
        "test")
            echo "🧪 测试基础通知..."
            python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_basic_notification
test_basic_notification('$CHANNEL')
"
            ;;
        *)
            echo "❌ 不支持的通知类型: $NOTIFICATION_TYPE"
            echo "支持的类型: permission, completion, test"
            exit 1
            ;;
    esac
elif [ -n "$CHANNEL" ]; then
    # 测试指定渠道
    echo "🎯 测试 $CHANNEL 渠道的所有通知类型..."
    echo ""
    
    echo "1️⃣ 测试基础通知..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_basic_notification
test_basic_notification('$CHANNEL')
"
    sleep 2
    
    echo "2️⃣ 测试权限确认通知..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_permission_notification
test_permission_notification()
"
    sleep 2
    
    echo "3️⃣ 测试任务完成通知..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_completion_notification
test_completion_notification()
"
    
else
    # 测试所有功能
    echo "📱 测试所有启用的通知渠道..."
    echo ""
    
    echo "1️⃣ 测试基础通知 (test)..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_basic_notification
test_basic_notification()
"
    sleep 3
    
    echo "2️⃣ 测试权限确认通知 (permission)..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_permission_notification
test_permission_notification()
"
    sleep 3
    
    echo "3️⃣ 测试任务完成通知 (completion)..."
    python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from examples.usage_examples import test_completion_notification
test_completion_notification()
"
    
fi

echo ""
echo "🎊 测试完成！"
echo ""
echo "📱 请检查你的通知设备，确认是否收到了测试消息"
echo ""
echo "🔧 如果没有收到通知，请检查:"
echo "   1. 配置文件: $CONFIG_FILE"
echo "   2. 日志文件: ~/.claude-notifier/logs/notifier.log"
echo "   3. 网络连接和渠道配置"
echo ""
echo "📖 获取帮助: https://github.com/your-username/claude-code-notifier"

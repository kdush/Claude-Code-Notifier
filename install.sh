#!/bin/bash

# Claude Code Notifier 智能安装脚本 v2.0
# 解决维护负担、用户混淆和更新困难问题

set -e

# ==================== 配置 ====================
REPO_URL="https://github.com/kdush/Claude-Code-Notifier.git"
PYPI_PACKAGE="claude-code-notifier"
CONFIG_DIR="$HOME/.claude-notifier"
INSTALL_LOG="$CONFIG_DIR/install.log"
VERSION_FILE="$CONFIG_DIR/version.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==================== 核心功能 ====================

# 1. 智能安装模式选择
select_installation_mode() {
    echo -e "${BLUE}🎯 Claude Code Notifier 智能安装系统${NC}"
    echo "================================================="
    
    # 检测现有安装
    if [ -f "$VERSION_FILE" ]; then
        current_version=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['version'])")
        current_type=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['type'])")
        echo -e "${YELLOW}检测到现有安装:${NC}"
        echo "  版本: $current_version"
        echo "  类型: $current_type"
        echo ""
    fi
    
    # 自动检测最佳模式
    if command -v pip3 &> /dev/null && ping -c 1 pypi.org &> /dev/null; then
        # PyPI可用 - 推荐标准安装
        recommended="pypi"
        echo -e "${GREEN}✅ 推荐: PyPI 标准安装（稳定、自动更新）${NC}"
    elif command -v git &> /dev/null; then
        # 只有Git可用 - 推荐Git安装
        recommended="git"
        echo -e "${YELLOW}⚠️ 推荐: Git 安装（PyPI不可用）${NC}"
    else
        recommended="manual"
        echo -e "${RED}❌ 需要手动安装依赖${NC}"
    fi
    
    echo ""
    echo "请选择安装方式:"
    echo "  1) PyPI 安装 [推荐] - 稳定版本，自动更新"
    echo "  2) Git 开发版 - 最新功能，手动更新"
    echo "  3) 混合模式 - PyPI核心 + Git扩展"
    echo "  4) 自动选择 - 根据环境自动决定"
    echo ""
    
    read -p "选择 (1-4，默认4): " choice
    choice=${choice:-4}
    
    case $choice in
        1) install_mode="pypi" ;;
        2) install_mode="git" ;;
        3) install_mode="hybrid" ;;
        4) install_mode="$recommended" ;;
        *) install_mode="$recommended" ;;
    esac
    
    echo -e "${GREEN}已选择: $install_mode 模式${NC}"
}

# 2. PyPI安装（解决维护负担）
install_pypi_mode() {
    echo -e "${BLUE}📦 执行 PyPI 安装...${NC}"
    
    # 安装最新版本
    pip3 install --upgrade $PYPI_PACKAGE
    
    # 记录安装信息
    version=$(pip3 show $PYPI_PACKAGE | grep Version | cut -d' ' -f2)
    
    # 保存版本信息
    cat > "$VERSION_FILE" <<EOF
{
    "type": "pypi",
    "version": "$version",
    "installed_at": "$(date -Iseconds)",
    "auto_update": true,
    "update_channel": "stable"
}
EOF
    
    # 设置自动更新
    setup_auto_update_pypi
    
    echo -e "${GREEN}✅ PyPI 安装完成，版本: $version${NC}"
}

# 3. Git安装（保留开发者功能）
install_git_mode() {
    echo -e "${BLUE}🔧 执行 Git 开发版安装...${NC}"
    
    # 克隆或更新仓库
    if [ -d "$HOME/Claude-Code-Notifier" ]; then
        cd "$HOME/Claude-Code-Notifier"
        echo -e "${YELLOW}🔄 更新现有仓库...${NC}"
        git fetch --all
        git checkout dev
        git pull origin dev
    else
        echo -e "${YELLOW}📥 克隆开发仓库...${NC}"
        git clone -b dev $REPO_URL "$HOME/Claude-Code-Notifier"
        cd "$HOME/Claude-Code-Notifier"
    fi
    
    # 验证项目文件存在
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ 错误: pyproject.toml 文件未找到${NC}"
        echo -e "${YELLOW}📋 当前分支: $(git branch --show-current)${NC}"
        echo -e "${YELLOW}📂 项目文件: $(ls -la | head -5)${NC}"
        exit 1
    fi
    
    # 获取版本信息
    version=$(git describe --tags --always)
    echo -e "${GREEN}📦 项目版本: $version${NC}"
    
    # 安装依赖
    echo -e "${YELLOW}📦 安装Python依赖...${NC}"
    pip3 install -e .
    
    # 保存版本信息
    cat > "$VERSION_FILE" <<EOF
{
    "type": "git",
    "version": "$version",
    "installed_at": "$(date -Iseconds)",
    "auto_update": false,
    "repo_path": "$HOME/Claude-Code-Notifier",
    "branch": "$(git branch --show-current)"
}
EOF
    
    # 设置更新提醒
    setup_update_reminder_git
    
    echo -e "${GREEN}✅ Git 开发版安装完成${NC}"
}

# 4. 混合模式（最佳体验）
install_hybrid_mode() {
    echo -e "${BLUE}🔀 执行混合模式安装...${NC}"
    
    # 安装PyPI核心包
    pip3 install --upgrade $PYPI_PACKAGE
    
    # 克隆配置和扩展
    if [ ! -d "$CONFIG_DIR/extensions" ]; then
        git clone --depth 1 $REPO_URL "$CONFIG_DIR/extensions"
    fi
    
    # 链接扩展功能
    ln -sf "$CONFIG_DIR/extensions/scripts" "$CONFIG_DIR/scripts"
    ln -sf "$CONFIG_DIR/extensions/hooks" "$CONFIG_DIR/hooks"
    
    # 保存版本信息
    pypi_version=$(pip3 show $PYPI_PACKAGE | grep Version | cut -d' ' -f2)
    cat > "$VERSION_FILE" <<EOF
{
    "type": "hybrid",
    "pypi_version": "$pypi_version",
    "extensions_version": "$(cd $CONFIG_DIR/extensions && git describe --tags --always)",
    "installed_at": "$(date -Iseconds)",
    "auto_update": true
}
EOF
    
    echo -e "${GREEN}✅ 混合模式安装完成${NC}"
}

# 5. 自动更新机制（解决更新困难）
setup_auto_update_pypi() {
    echo -e "${BLUE}⚙️ 设置自动更新...${NC}"
    
    # 创建更新检查脚本
    cat > "$CONFIG_DIR/check_update.sh" <<'SCRIPT'
#!/bin/bash
# 自动更新检查脚本

CONFIG_DIR="$HOME/.claude-notifier"
VERSION_FILE="$CONFIG_DIR/version.json"
UPDATE_LOG="$CONFIG_DIR/update.log"

# 检查更新（每天一次）
last_check_file="$CONFIG_DIR/.last_update_check"
if [ -f "$last_check_file" ]; then
    last_check=$(cat "$last_check_file")
    current_time=$(date +%s)
    time_diff=$((current_time - last_check))
    # 86400秒 = 24小时
    if [ $time_diff -lt 86400 ]; then
        exit 0
    fi
fi

# 检查PyPI新版本
current_version=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['version'])" 2>/dev/null || echo "0.0.0")
latest_version=$(pip3 index versions claude-code-notifier 2>/dev/null | grep "claude-code-notifier" | head -1 | cut -d'(' -f2 | cut -d')' -f1 || echo "$current_version")

if [ "$latest_version" != "$current_version" ]; then
    echo "[$(date)] 发现新版本: $latest_version (当前: $current_version)" >> "$UPDATE_LOG"
    
    # 自动更新或提示
    if [ "$(python3 -c "import json; print(json.load(open('$VERSION_FILE')).get('auto_update', False))")" = "True" ]; then
        pip3 install --upgrade claude-code-notifier >> "$UPDATE_LOG" 2>&1
        echo "[$(date)] 自动更新到版本 $latest_version" >> "$UPDATE_LOG"
        
        # 更新版本文件
        python3 -c "
import json
with open('$VERSION_FILE', 'r+') as f:
    data = json.load(f)
    data['version'] = '$latest_version'
    data['last_update'] = '$(date -Iseconds)'
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
"
    else
        echo "🔔 Claude Notifier 有新版本可用: $latest_version"
        echo "   运行 'pip3 install --upgrade claude-code-notifier' 更新"
    fi
fi

# 记录检查时间
date +%s > "$last_check_file"
SCRIPT
    
    chmod +x "$CONFIG_DIR/check_update.sh"
    
    # 添加到shell启动
    for rc in ~/.bashrc ~/.zshrc; do
        if [ -f "$rc" ]; then
            if ! grep -q "claude-notifier/check_update.sh" "$rc"; then
                echo "" >> "$rc"
                echo "# Claude Notifier 自动更新检查" >> "$rc"
                echo "[ -f $CONFIG_DIR/check_update.sh ] && $CONFIG_DIR/check_update.sh &" >> "$rc"
            fi
        fi
    done
    
    echo -e "${GREEN}✅ 自动更新已启用${NC}"
}

# 6. Git更新提醒
setup_update_reminder_git() {
    echo -e "${BLUE}📢 设置更新提醒...${NC}"
    
    cat > "$CONFIG_DIR/git_update_check.sh" <<'SCRIPT'
#!/bin/bash
# Git版本更新提醒

REPO_PATH="$HOME/Claude-Code-Notifier"
CONFIG_DIR="$HOME/.claude-notifier"

if [ -d "$REPO_PATH" ]; then
    cd "$REPO_PATH"
    
    # 获取远程更新
    git fetch --quiet
    
    # 检查是否有更新
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "🔔 Claude Notifier Git版本有更新可用"
        echo "   运行以下命令更新:"
        echo "   cd $REPO_PATH && git pull && pip3 install -e ."
    fi
fi
SCRIPT
    
    chmod +x "$CONFIG_DIR/git_update_check.sh"
    
    # 添加到crontab（每天检查）
    (crontab -l 2>/dev/null | grep -v "git_update_check.sh"; echo "0 10 * * * $CONFIG_DIR/git_update_check.sh") | crontab -
    
    echo -e "${GREEN}✅ 更新提醒已设置${NC}"
}

# 7. 统一命令接口（解决用户混淆）
setup_unified_interface() {
    echo -e "${BLUE}🔗 创建统一接口...${NC}"
    
    # 创建智能命令包装器
    cat > "$CONFIG_DIR/cn" <<'WRAPPER'
#!/bin/bash
# 统一命令接口 - 自动选择正确的执行方式

CONFIG_DIR="$HOME/.claude-notifier"
VERSION_FILE="$CONFIG_DIR/version.json"

if [ -f "$VERSION_FILE" ]; then
    install_type=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['type'])" 2>/dev/null)
    
    case "$install_type" in
        "pypi"|"hybrid")
            # 使用PyPI安装的命令
            if command -v claude-notifier &> /dev/null; then
                claude-notifier "$@"
            else
                echo "错误: claude-notifier 命令未找到"
                echo "请运行: pip3 install claude-code-notifier"
                exit 1
            fi
            ;;
        "git")
            # 使用Git安装的命令
            REPO_PATH=$(python3 -c "import json; print(json.load(open('$VERSION_FILE')).get('repo_path', ''))" 2>/dev/null)
            if [ -d "$REPO_PATH" ]; then
                python3 "$REPO_PATH/src/claude_notifier/cli/main.py" "$@"
            else
                echo "错误: Git仓库未找到"
                echo "请重新运行安装脚本"
                exit 1
            fi
            ;;
        *)
            echo "错误: 未知的安装类型"
            exit 1
            ;;
    esac
else
    echo "Claude Notifier 未安装"
    echo "请运行安装脚本: curl -sSL https://install.claude-notifier.io | bash"
    exit 1
fi
WRAPPER
    
    chmod +x "$CONFIG_DIR/cn"
    
    # 创建符号链接
    sudo ln -sf "$CONFIG_DIR/cn" /usr/local/bin/cn 2>/dev/null || \
        echo "alias cn='$CONFIG_DIR/cn'" >> ~/.bashrc
    
    echo -e "${GREEN}✅ 统一接口已创建，使用 'cn' 命令${NC}"
}

# 8. 迁移旧版本配置
migrate_old_installation() {
    echo -e "${BLUE}🔄 检查旧版本...${NC}"
    
    # 检查旧的安装目录
    old_locations=(
        "$HOME/Claude-Code-Notifier"
        "$HOME/.claude-notifier-old"
        "/opt/claude-notifier"
    )
    
    for loc in "${old_locations[@]}"; do
        if [ -d "$loc" ]; then
            echo "发现旧版本: $loc"
            
            # 备份配置
            if [ -f "$loc/config/config.yaml" ]; then
                cp -r "$loc/config" "$CONFIG_DIR/config.backup.$(date +%Y%m%d)"
                echo "配置已备份"
            fi
            
            # 询问是否删除旧版本
            read -p "是否删除旧版本? [y/N]: " remove_old
            if [ "$remove_old" = "y" ]; then
                rm -rf "$loc"
                echo "旧版本已删除"
            fi
        fi
    done
}

# 9. 验证安装
verify_installation() {
    echo -e "${BLUE}🔍 验证安装...${NC}"
    
    errors=0
    
    # 检查命令可用性
    if command -v claude-notifier &> /dev/null || command -v cn &> /dev/null; then
        echo -e "${GREEN}✅ 命令已安装${NC}"
    else
        echo -e "${RED}❌ 命令未找到${NC}"
        errors=$((errors + 1))
    fi
    
    # 检查配置目录
    if [ -d "$CONFIG_DIR" ]; then
        echo -e "${GREEN}✅ 配置目录已创建${NC}"
    else
        echo -e "${RED}❌ 配置目录未创建${NC}"
        errors=$((errors + 1))
    fi
    
    # 检查版本文件
    if [ -f "$VERSION_FILE" ]; then
        echo -e "${GREEN}✅ 版本信息已记录${NC}"
        cat "$VERSION_FILE" | python3 -m json.tool
    else
        echo -e "${RED}❌ 版本信息未记录${NC}"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ 安装验证成功！${NC}"
        return 0
    else
        echo -e "${RED}❌ 发现 $errors 个问题${NC}"
        return 1
    fi
}

# ==================== 主流程 ====================

main() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Claude Code Notifier 智能安装 v2.0   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    # 创建配置目录
    mkdir -p "$CONFIG_DIR"
    
    # 记录安装日志
    exec 2> >(tee -a "$INSTALL_LOG" >&2)
    
    # 1. 迁移旧版本
    migrate_old_installation
    
    # 2. 选择安装模式
    select_installation_mode
    
    # 3. 执行安装
    case "$install_mode" in
        "pypi")
            install_pypi_mode
            ;;
        "git")
            install_git_mode
            ;;
        "hybrid")
            install_hybrid_mode
            ;;
        *)
            echo -e "${RED}未知的安装模式: $install_mode${NC}"
            exit 1
            ;;
    esac
    
    # 4. 设置统一接口
    setup_unified_interface
    
    # 5. 验证安装
    verify_installation
    
    # 6. 显示后续步骤
    echo ""
    echo -e "${GREEN}🎉 安装完成！${NC}"
    echo ""
    echo "后续步骤:"
    echo "  1. 配置通知渠道: cn init"
    echo "  2. 测试通知: cn test"
    echo "  3. 查看状态: cn status"
    echo ""
    echo "更多帮助: cn --help"
    echo ""
    
    # 提示重新加载shell
    echo -e "${YELLOW}请运行以下命令或重新打开终端:${NC}"
    echo "  source ~/.bashrc"
}

# 运行主程序
main "$@"
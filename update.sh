#!/usr/bin/env bash
# Termux IP 优选工具 - 更新脚本
# 从 GitHub 拉取最新代码，保留配置数据

echo ""
echo "================================"
echo "  Termux IP 优选工具 - 更新"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 检查是否为 git 仓库
if [ ! -d ".git" ]; then
    echo "  ✗ 不是 git 仓库，无法更新"
    echo "  请重新 clone: git clone https://github.com/chengege666/ipcs"
    exit 1
fi

# 备份配置
CONFIG_BACKUP=""
CONFIG_DIR="$HOME/.ip_optimizer"
if [ -d "$CONFIG_DIR" ]; then
    CONFIG_BACKUP=$(mktemp -d)
    cp -r "$CONFIG_DIR" "$CONFIG_BACKUP/"
    echo "  ✓ 已备份配置数据"
fi

# 拉取最新代码
echo "  ～ 正在拉取更新..."
GIT_OUTPUT=$(git pull 2>&1)
GIT_EXIT=$?

if [ $GIT_EXIT -ne 0 ]; then
    echo "  ✗ 更新失败:"
    echo "    $GIT_OUTPUT"
    # 恢复配置
    if [ -n "$CONFIG_BACKUP" ] && [ -d "$CONFIG_BACKUP/.ip_optimizer" ]; then
        rm -rf "$CONFIG_DIR"
        mv "$CONFIG_BACKUP/.ip_optimizer" "$CONFIG_DIR"
        echo "  ✓ 已恢复配置数据"
    fi
    exit 1
fi

# 恢复配置
if [ -n "$CONFIG_BACKUP" ]; then
    rm -rf "$CONFIG_BACKUP"
fi

if echo "$GIT_OUTPUT" | grep -q "Already up to date"; then
    echo "  ✓ 已是最新版本"
else
    echo "  ✓ 更新完成"
    echo "  $GIT_OUTPUT"
fi

echo ""
echo "================================"
echo "  运行 python main.py 启动"
echo "================================"
echo ""

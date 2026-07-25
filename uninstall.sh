#!/usr/bin/env bash
# Termux IP 优选工具 - 卸载脚本
# 删除项目文件、配置数据、快捷命令

echo ""
echo "================================"
echo "  Termux IP 优选工具 - 卸载"
echo "================================"
echo ""

# 确认卸载
read -p "  确定要卸载吗? [y/N]: " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" && "$confirm" != "yes" ]]; then
    echo ""
    echo "  已取消"
    exit 0
fi

# 1. 删除快捷命令
SHORTCUT="/data/data/com.termux/files/usr/bin/ipcs"
if [ -f "$SHORTCUT" ]; then
    rm -f "$SHORTCUT"
    echo "  ✓ 已删除快捷命令: ipcs"
else
    echo "  - 快捷命令不存在，跳过"
fi

# 2. 删除配置数据目录
CONFIG_DIR="$HOME/.ip_optimizer"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    echo "  ✓ 已删除配置数据: $CONFIG_DIR"
else
    echo "  - 配置数据不存在，跳过"
fi

# 3. 删除项目文件（uninstall.sh 所在目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR" ]; then
    cd "$HOME"
    rm -rf "$SCRIPT_DIR"
    echo "  ✓ 已删除项目文件: $SCRIPT_DIR"
else
    echo "  - 项目文件不存在，跳过"
fi

echo ""
echo "================================"
echo "  卸载完成"
echo "================================"
echo ""

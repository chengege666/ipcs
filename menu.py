"""交互菜单模块"""

import os
import sys
from typing import Optional

from utils import (
    print_banner, green, yellow, red, cyan, bold
)


def show_main_menu() -> Optional[str]:
    """显示主菜单，返回选项"""
    print_banner()
    print()
    print("  " + cyan("1. 域名 IP 优选"))
    print("  " + cyan("2. Cloudflare IP 优选"))
    print("  " + cyan("3. CDN 节点测速"))
    print("  " + cyan("4. 下载速度测试"))
    print("  " + cyan("5. DNS 解析测试"))
    print("  " + cyan("6. 历史记录"))
    print("  " + cyan("7. 配置管理"))
    print("  " + cyan("8. 地区管理"))
    print("  " + cyan("9. 配置快捷启动"))
    print()
    print("  " + red("0. 退出"))
    print()
    print(cyan("-" * 40))
    print()

    try:
        choice = input("  " + bold("请选择: ")).strip()
        return choice
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def setup_shortcut():
    """配置 Termux 快捷启动命令"""
    shortcut_path = "/data/data/com.termux/files/usr/bin/ipcs"
    project_dir = os.path.dirname(os.path.abspath(__file__))

    print()
    print(cyan("=" * 40))
    print(cyan("  配置快捷启动"))
    print(cyan("=" * 40))
    print()

    # 检测是否在 Termux 环境
    if not os.path.exists("/data/data/com.termux"):
        print(f"  {yellow('非 Termux 环境，跳过配置')}")
        print(f"  {yellow('可手动创建别名: alias ipcs=\"python {project_dir}/main.py\"')}")
        return

    # 检查是否已配置
    if os.path.exists(shortcut_path):
        print(f"  {green('✓ 快捷启动已配置')}")
        print(f"  命令: {yellow('ipcs')}")
        print()
        try:
            choice = input(f"  {bold('是否重新创建?')} [y/N]: ").strip().lower()
            if choice not in ("y", "yes"):
                return
        except EOFError:
            return

    try:
        with open(shortcut_path, "w") as f:
            f.write(f'cd {project_dir} && exec python main.py "$@"\n')
        os.chmod(shortcut_path, 0o755)
        print(f"\n  {green('✓ 快捷启动已创建!')}")
        print(f"  以后在 Termux 直接输入: {yellow('ipcs')}")
        print()
        print(f"  {yellow('提示: 如果别名不生效，执行 \"hash -r\" 或重启 Termux')}")
    except PermissionError:
        print(f"\n  {red('✗ 权限不足，请手动创建:')}")
        print(f"    echo 'cd {project_dir} && python main.py' > {shortcut_path}")
        print(f"    chmod +x {shortcut_path}")
    except Exception as e:
        print(f"\n  {red(f'✗ 创建失败: {e}')}")


def show_config_menu(config):
    """配置管理菜单"""
    while True:
        print()
        print(cyan("=" * 40))
        print(cyan("     配置管理"))
        print(cyan("=" * 40))
        print()
        print(f"  1. Ping 次数      ({config.get('ping_count', 20)})")
        print(f"  2. 超时时间(s)    ({config.get('timeout', 5)})")
        print(f"  3. TCP 端口       ({config.get('tcp_port', 443)})")
        print(f"  4. 下载测试大小   ({config.get('download_size', '50MB')})")
        print(f"  5. 并发线程数     ({config.get('threads', 8)})")
        print(f"  6. 稳定性测试时长 ({config.get('stable_test_time', 30)}s)")
        print(f"  7. 最大测试IP数   ({config.get('ip_test_limit', 100)})")
        print(f"  8. 恢复默认设置")
        print()
        print("  0. 返回")
        print()

        try:
            choice = input("  请选择: ").strip()
        except EOFError:
            return

        if choice == "0":
            return

        config_map = {
            "1": ("ping_count", "Ping 次数", int),
            "2": ("timeout", "超时时间(秒)", float),
            "3": ("tcp_port", "TCP 端口", int),
            "4": ("download_size", "下载测试大小", str),
            "5": ("threads", "并发线程数", int),
            "6": ("stable_test_time", "稳定性测试时长(秒)", int),
            "7": ("ip_test_limit", "最大测试IP数", int),
        }

        if choice == "8":
            try:
                from config import save_config, DEFAULT_CONFIG
                save_config(DEFAULT_CONFIG)
                print(f"  {green('已恢复默认设置')}")
                return
            except Exception as e:
                print(f"  {red(f'恢复失败: {e}')}")
                return

        if choice in config_map:
            key, name, cast_type = config_map[choice]
            try:
                val = input(f"  输入{name} (当前: {config.get(key, '')}): ").strip()
                if val:
                    if cast_type == int:
                        val = int(val)
                    elif cast_type == float:
                        val = float(val)
                    from config import update_config
                    update_config(key, val)
                    config[key] = val
                    print(f"  {green(f'✓ {name} 已更新为 {val}')}")
            except (ValueError, EOFError):
                print(f"  {yellow('输入无效')}")
        else:
            print(f"  {yellow('无效选择')}")

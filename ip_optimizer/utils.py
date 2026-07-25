"""工具函数模块"""

import os
import sys
import time
import subprocess
from datetime import datetime


def color_text(text, color_code):
    """终端颜色输出"""
    return f"\033[{color_code}m{text}\033[0m"


def red(text):
    return color_text(text, "91")


def green(text):
    return color_text(text, "92")


def yellow(text):
    return color_text(text, "93")


def blue(text):
    return color_text(text, "94")


def magenta(text):
    return color_text(text, "95")


def cyan(text):
    return color_text(text, "96")


def bold(text):
    return color_text(text, "1")


def print_banner():
    """打印启动横幅"""
    banner = f"""
{cyan('=' * 48)}
{cyan('  Termux IP 优选工具 v1.0')}
{cyan('  Termux-IP-Optimizer')}
{cyan('=' * 48)}
"""
    print(banner)


def print_step(step, total, message):
    """打印进度步骤"""
    print(f"{cyan('[')}{green(f'{step}/{total}')}{cyan(']')} {message}")


def print_progress(current, total, prefix="", bar_length=30):
    """打印进度条"""
    ratio = current / total if total > 0 else 0
    filled = int(bar_length * ratio)
    bar = f"{'█' * filled}{'░' * (bar_length - filled)}"
    percent = f"{ratio * 100:.1f}%"
    print(f"\r{prefix} |{cyan(bar)}| {green(percent)}", end="")
    if current >= total:
        print()


def format_speed(bytes_per_sec):
    """格式化速度显示"""
    if bytes_per_sec >= 1024 ** 3:
        return f"{bytes_per_sec / (1024 ** 3):.1f}GB/s"
    elif bytes_per_sec >= 1024 ** 2:
        return f"{bytes_per_sec / (1024 ** 2):.1f}MB/s"
    elif bytes_per_sec >= 1024:
        return f"{bytes_per_sec / 1024:.1f}KB/s"
    return f"{bytes_per_sec:.0f}B/s"


def format_latency(ms):
    """格式化延迟显示"""
    if ms < 1:
        return f"{ms * 1000:.1f}μs"
    return f"{ms:.1f}ms"


def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}m{s:.0f}s"


def get_timestamp():
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_date():
    """获取当前日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def run_command(cmd, timeout=10):
    """安全运行系统命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -2, "", "Command not found"
    except Exception as e:
        return -3, "", str(e)


def check_dependencies():
    """检查必要依赖是否安装"""
    missing = []
    # 检查Python包
    packages = ["requests", "dns.resolver", "ping3", "rich"]
    for pkg in packages:
        try:
            __import__(pkg.replace(".", ".").split(".")[0])
        except ImportError:
            missing.append(pkg)

    # 检查系统命令
    commands = ["curl", "wget", "jq"]
    for cmd in commands:
        code, _, _ = run_command(f"which {cmd} 2>/dev/null || command -v {cmd} 2>/dev/null")
        if code != 0:
            missing.append(cmd)

    return missing


def safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

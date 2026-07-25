"""下载速度测试模块"""

import time
import subprocess
import re
from typing import Dict, List, Optional

from utils import format_speed, green, yellow, red


# Cloudflare 下载测速地址
CF_SPEED_URLS = [
    "https://speed.cloudflare.com/__down?bytes=50000000",
    "https://speed.cloudflare.com/__down?bytes=104857600",
]

# 通用测速地址（备用，不用 IP 绑定）
FALLBACK_URLS = {
    "50MB": [
        "https://proof.ovh.net/files/50Mb.dat",
    ],
    "100MB": [
        "https://proof.ovh.net/files/100Mb.dat",
    ]
}


def get_cf_test_url(size: str = "50MB") -> str:
    """获取 Cloudflare 下载测速 URL"""
    if size == "100MB":
        return "https://speed.cloudflare.com/__down?bytes=104857600"
    return "https://speed.cloudflare.com/__down?bytes=50000000"


def speed_test(ip: str, size: str = "50MB", threads: int = 8,
               timeout: float = 30.0) -> Dict:
    """对指定IP进行下载速度测试（使用 curl --resolve 绑定域名到IP）"""
    url = get_cf_test_url(size)

    # 用 curl --resolve 把 speed.cloudflare.com 绑定到指定 IP
    domain = "speed.cloudflare.com"
    resolve_arg = f"{domain}:443:{ip}"

    result = {
        "ip": ip,
        "avg_speed": 0,
        "peak_speed": 0,
        "downloaded": 0,
        "time": 0,
        "speeds": [],
        "size": size
    }

    # 先测试 curl 是否可用
    try:
        subprocess.run(["curl", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        result["error"] = "未安装 curl，请执行: pkg install curl"
        return result

    # 构造 curl 命令
    # --resolve 绑定域名到IP
    # -o /dev/null 不保存文件
    # -s 静默模式
    # -w 输出速度信息
    # --connect-timeout 连接超时
    # --max-time 总超时
    cmd = [
        "curl",
        "--resolve", resolve_arg,
        "-o", "/dev/null",
        "-s",
        "-w", "%{speed_download}\n%{time_total}\n%{size_download}\n%{http_code}",
        "--connect-timeout", "10",
        "--max-time", str(timeout),
        url
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)

        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            if "resolve" in stderr.lower() or "could not resolve" in stderr.lower():
                result["error"] = f"DNS 解析失败"
            elif "timeout" in stderr.lower():
                result["error"] = f"连接超时"
            elif "connection refused" in stderr.lower():
                result["error"] = f"连接被拒绝"
            else:
                result["error"] = stderr[:100] if stderr else f"curl 错误({proc.returncode})"
            return result

        # 解析 curl 输出
        lines = proc.stdout.strip().split("\n")
        if len(lines) >= 4:
            try:
                speed_bps = float(lines[0])  # bytes per second
                total_time = float(lines[1])
                downloaded = float(lines[2])
                http_code = lines[3].strip()

                if http_code not in ("200", "206"):
                    result["error"] = f"HTTP {http_code}"
                    return result

                # speed_download 是字节/秒，转换为 MB/s
                speed_bps = float(lines[0])
                result["avg_speed"] = speed_bps
                result["downloaded"] = downloaded
                result["time"] = total_time
                result["peak_speed"] = speed_bps

            except (ValueError, IndexError) as e:
                result["error"] = f"解析结果失败: {e}"

    except subprocess.TimeoutExpired:
        result["error"] = "测速超时"
    except Exception as e:
        result["error"] = str(e)

    return result


def print_speed_result(result: Dict):
    """打印测速结果"""
    if result.get("error"):
        print(f"  {red('测速失败:')} {result['error']}")
        return

    speed_mb = result['avg_speed'] / (1024 * 1024)

    print(f"  下载速度: {green(f'{speed_mb:.2f} MB/s')}")
    print(f"  耗时: {result['time']:.1f}s")
    if result.get("downloaded", 0) > 0:
        size_mb = result['downloaded'] / (1024 * 1024)
        print(f"  下载大小: {size_mb:.1f} MB")

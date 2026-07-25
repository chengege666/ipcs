"""IP扫描模块"""

import os
import ipaddress
from typing import List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import green, yellow, print_progress
from config import IP_POOL_DIR


def load_ip_pool(region: str = None) -> List[str]:
    """从IP池文件加载IP列表"""
    ips = []

    # 如果指定了地区，加载对应文件
    if region:
        region_file = os.path.join(IP_POOL_DIR, f"{region}.txt")
        if os.path.exists(region_file):
            with open(region_file, "r") as f:
                ips.extend([line.strip() for line in f if line.strip()])

    # 加载通用IP池
    common_file = os.path.join(IP_POOL_DIR, "common.txt")
    if os.path.exists(common_file):
        with open(common_file, "r") as f:
            ips.extend([line.strip() for line in f if line.strip()])

    return ips


def load_cloudflare_ips() -> List[str]:
    """加载Cloudflare IP段"""
    cf_ranges = [
        "104.16.0.0/13",
        "104.24.0.0/14",
        "172.64.0.0/13",
        "103.21.244.0/22",
        "103.22.200.0/22",
        "103.31.4.0/22",
        "141.101.64.0/18",
        "108.162.192.0/18",
        "190.93.240.0/20",
        "188.114.96.0/20",
        "197.234.240.0/22",
        "198.41.128.0/17",
        "162.158.0.0/15",
        "173.245.48.0/20"
    ]
    ips = []
    for cidr in cf_ranges:
        try:
            network = ipaddress.ip_network(cidr)
            ips.extend([str(ip) for ip in network.hosts()])
        except ValueError:
            pass
    return ips


def merge_ip_sources(dns_ips: List[str] = None,
                     pool_ips: List[str] = None,
                     user_ips: List[str] = None,
                     max_ips: int = 100) -> List[str]:
    """合并多个来源的IP，去重并限制数量"""
    ip_set: Set[str] = set()

    # DNS解析结果优先
    if dns_ips:
        for ip in dns_ips:
            if is_valid_ip(ip):
                ip_set.add(ip.strip())

    # IP池
    if pool_ips:
        for ip in pool_ips:
            if is_valid_ip(ip):
                ip_set.add(ip.strip())

    # 用户输入
    if user_ips:
        for ip in user_ips:
            if is_valid_ip(ip):
                ip_set.add(ip.strip())

    result = list(ip_set)
    if len(result) > max_ips:
        result = result[:max_ips]

    return result


def is_valid_ip(ip: str) -> bool:
    """验证IP地址格式"""
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def scan_ip(ip: str, timeout: int = 2) -> bool:
    """扫描单个IP是否可达（使用ping快速检测）"""
    import subprocess
    try:
        # 使用系统ping
        if os.name == "nt":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except Exception:
        return False


def scan_ips(ip_list: List[str], max_workers: int = 30,
             timeout: int = 2, callback=None) -> List[str]:
    """并发扫描IP列表，返回可达的IP"""
    reachable = []
    total = len(ip_list)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_ip, ip, timeout): ip for ip in ip_list}
        completed = 0
        for future in as_completed(futures):
            ip = futures[future]
            completed += 1
            try:
                if future.result():
                    reachable.append(ip)
            except Exception:
                pass

            if callback:
                callback(completed, total, ip)

            print_progress(completed, total, f"扫描IP ({len(reachable)}可达)")

    return reachable

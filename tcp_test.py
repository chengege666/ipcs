"""TCP连接测试模块"""

import time
import socket
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import format_latency, green, red, print_progress


def tcp_connect(ip: str, port: int, timeout: float = 3.0) -> Optional[float]:
    """TCP连接测试，返回握手时间(ms)"""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        elapsed = (time.time() - start) * 1000
        sock.close()
        if result == 0:
            return elapsed
    except Exception:
        pass
    return None


def tls_connect(ip: str, port: int = 443, timeout: float = 5.0) -> Optional[float]:
    """TLS连接测试，返回TLS握手时间(ms)"""
    try:
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        tls_sock = context.wrap_socket(sock, server_hostname=ip)
        elapsed = (time.time() - start) * 1000
        tls_sock.close()
        sock.close()
        return elapsed
    except Exception:
        return None


def test_tcp(ip: str, ports: List[int] = None,
             timeout: float = 3.0, test_tls: bool = True) -> Dict:
    """全面TCP测试"""
    if ports is None:
        ports = [80, 443, 8080, 8443]

    result = {
        "ip": ip,
        "tcp_results": {},
        "tls_time": None,
        "best_time": None,
        "best_port": None
    }

    # TCP握手测试
    for port in ports:
        rtt = tcp_connect(ip, port, timeout)
        if rtt is not None:
            result["tcp_results"][str(port)] = rtt
            if result["best_time"] is None or rtt < result["best_time"]:
                result["best_time"] = rtt
                result["best_port"] = port

    # TLS连接测试（443端口）
    if test_tls and 443 in ports:
        tls_time = tls_connect(ip, 443, timeout + 2)
        result["tls_time"] = tls_time

    return result


def batch_test_tcp(ip_list: List[str], ports: List[int] = None,
                   max_workers: int = 20, timeout: float = 3.0) -> Dict[str, Dict]:
    """批量TCP测试"""
    if ports is None:
        ports = [80, 443]

    results = {}
    total = len(ip_list)

    def worker(ip):
        for port in ports:
            rtt = tcp_connect(ip, port, timeout)
            if rtt is not None:
                return ip, port, rtt
        return ip, None, None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, ip) for ip in ip_list]
        for i, future in enumerate(as_completed(futures)):
            ip, port, rtt = future.result()
            results[ip] = {
                "ip": ip,
                "best_port": port,
                "best_time": rtt
            }
            print_progress(i + 1, total, f"TCP测试 ({len(results)}完成)")

    return results


def print_tcp_result(result: Dict):
    """打印TCP测试结果"""
    print(f"  IP: {result['ip']}")

    for port_str, rtt in result["tcp_results"].items():
        status = green(f"{format_latency(rtt)}")
        print(f"  TCP端口 {port_str}: {status}")

    if result.get("tls_time"):
        print(f"  TLS握手: {green(format_latency(result['tls_time']))}")

    if result.get("best_port"):
        print(f"  最佳端口: {result['best_port']} "
              f"({format_latency(result['best_time'])})")

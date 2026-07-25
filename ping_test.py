"""Ping测速模块"""

import time
import statistics
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import format_latency, print_progress


def ping_once(ip: str, timeout: float = 2.0, interval: float = 0.2) -> Optional[float]:
    """单次Ping测试，返回延迟(ms)"""
    try:
        import ping3
        rtt = ping3.ping(ip, timeout=timeout, unit='ms')
        if rtt is not None and rtt > 0:
            time.sleep(interval)
            return rtt
    except Exception:
        pass
    return None


def ping_test(ip: str, count: int = 20, timeout: float = 2.0,
              interval: float = 0.2) -> Dict:
    """执行多次Ping测试，返回统计结果"""
    rtts = []

    for i in range(count):
        rtt = ping_once(ip, timeout, interval)
        if rtt is not None:
            rtts.append(rtt)
        print_progress(i + 1, count, f"Ping测试 {ip}")

    result = {
        "ip": ip,
        "sent": count,
        "received": len(rtts),
        "loss": 100 - (len(rtts) / count * 100) if count > 0 else 100,
        "rtts": rtts
    }

    if rtts:
        result["min"] = min(rtts)
        result["max"] = max(rtts)
        result["avg"] = statistics.mean(rtts)
        result["median"] = statistics.median(rtts)
        result["stddev"] = statistics.stdev(rtts) if len(rtts) > 1 else 0
        result["jitter"] = result["stddev"]
    else:
        result["min"] = 0
        result["max"] = 0
        result["avg"] = 0
        result["median"] = 0
        result["stddev"] = 0
        result["jitter"] = 0

    return result


def ping_batch(ip_list: List[str], count: int = 5, timeout: float = 2.0,
               max_workers: int = 30) -> Dict[str, Dict]:
    """批量Ping多个IP"""
    results = {}
    total = len(ip_list)

    def ping_worker(ip):
        rtts = []
        for _ in range(count):
            rtt = ping_once(ip, timeout)
            if rtt is not None:
                rtts.append(rtt)
        return ip, rtts

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(ping_worker, ip) for ip in ip_list]
        completed = 0
        for future in as_completed(futures):
            completed += 1
            ip, rtts = future.result()
            result = {
                "ip": ip,
                "sent": count,
                "received": len(rtts),
                "loss": 100 - (len(rtts) / count * 100) if count > 0 else 100,
                "rtts": rtts
            }
            if rtts:
                result["avg"] = statistics.mean(rtts)
                result["min"] = min(rtts)
                result["max"] = max(rtts)
                result["jitter"] = statistics.stdev(rtts) if len(rtts) > 1 else 0
            else:
                result["avg"] = 9999
                result["min"] = 0
                result["max"] = 0
                result["jitter"] = 0
            results[ip] = result
            print_progress(completed, total, f"批量Ping ({len(results)}完成)")

    return results


def print_ping_result(result: Dict):
    """打印Ping测试结果"""
    if result["received"] == 0:
        print(f"  {result['ip']}: {format_latency(9999)} (超时)")
        return

    print(f"  IP: {result['ip']}")
    print(f"  发送: {result['sent']}, 接收: {result['received']}, "
          f"丢包: {result['loss']:.1f}%")
    print(f"  延迟: 最小={format_latency(result['min'])}, "
          f"最大={format_latency(result['max'])}, "
          f"平均={format_latency(result['avg'])}")
    print(f"  抖动: {format_latency(result['jitter'])}")

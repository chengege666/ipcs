"""丢包检测模块"""

import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import format_latency, green, yellow, red, print_progress


def get_loss_grade(loss_percent: float) -> tuple:
    """根据丢包率返回等级和颜色"""
    if loss_percent == 0:
        return "优秀", green
    elif loss_percent <= 2:
        return "良好", green
    elif loss_percent <= 5:
        return "一般", yellow
    elif loss_percent <= 10:
        return "较差", yellow
    else:
        return "淘汰", red


def detect_packet_loss(ip: str, count: int = 20, timeout: float = 2.0,
                       interval: float = 0.1) -> Dict:
    """检测丢包率"""
    sent = 0
    received = 0
    rtts = []

    for i in range(count):
        try:
            import ping3
            rtt = ping3.ping(ip, timeout=timeout, unit='ms')
            sent += 1
            if rtt is not None and rtt > 0:
                received += 1
                rtts.append(rtt)
            time.sleep(interval)
        except Exception:
            sent += 1

        print_progress(i + 1, count, f"丢包检测 {ip}")

    loss_percent = 0
    if sent > 0:
        loss_percent = ((sent - received) / sent) * 100

    grade, color = get_loss_grade(loss_percent)

    result = {
        "ip": ip,
        "sent": sent,
        "received": received,
        "lost": sent - received,
        "loss_percent": loss_percent,
        "grade": grade,
        "rtts": rtts
    }

    if rtts:
        result["avg_rtt"] = sum(rtts) / len(rtts)
    else:
        result["avg_rtt"] = 0

    return result


def batch_detect_loss(ip_list: List[str], count: int = 10,
                      max_workers: int = 20) -> Dict[str, Dict]:
    """批量检测多个IP的丢包率"""
    results = {}
    total = len(ip_list)

    def worker(ip):
        sent = 0
        received = 0
        for _ in range(count):
            try:
                import ping3
                rtt = ping3.ping(ip, timeout=2.0, unit='ms')
                sent += 1
                if rtt is not None and rtt > 0:
                    received += 1
            except Exception:
                sent += 1
        return ip, sent, received

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, ip) for ip in ip_list]
        for i, future in enumerate(as_completed(futures)):
            ip, sent, received = future.result()
            loss_pct = ((sent - received) / sent * 100) if sent > 0 else 100
            grade, color = get_loss_grade(loss_pct)
            results[ip] = {
                "ip": ip,
                "sent": sent,
                "received": received,
                "lost": sent - received,
                "loss_percent": loss_pct,
                "grade": grade
            }
            print_progress(i + 1, total, f"批量丢包检测 ({len(results)}完成)")

    return results


def print_loss_result(result: Dict):
    """打印丢包检测结果"""
    grade, color = get_loss_grade(result["loss_percent"])

    print(f"  IP: {result['ip']}")
    print(f"  发送: {result['sent']}, 接收: {result['received']}, "
          f"丢失: {result['lost']}")
    loss_str = f"{result['loss_percent']:.1f}%"
    print(f"  丢包率: {color(loss_str)}")
    print(f"  评级: {color(grade)}")

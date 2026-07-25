"""网络稳定性分析模块"""

import time
import statistics
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import format_speed, format_latency, green, yellow, red, print_progress


def speed_stability_test(ip: str, duration: int = 30,
                         interval: float = 1.0) -> Dict:
    """速度稳定性测试，持续一段时间记录速度变化"""
    import requests

    speeds = []
    timestamps = []
    start = time.time()
    end = start + duration

    # 使用轻量级测试
    test_url = f"http://{ip}"
    downloaded = 0
    last_check = start

    print(f"\n  稳定性测试 ({duration}秒)...")

    try:
        resp = requests.get(test_url, stream=True, timeout=duration + 5)
        for chunk in resp.iter_content(chunk_size=65536):
            now = time.time()
            if now > end:
                break
            if chunk:
                downloaded += len(chunk)
                elapsed = now - last_check
                if elapsed >= interval:
                    speed = downloaded / elapsed
                    speeds.append(speed)
                    timestamps.append(now)
                    downloaded = 0
                    last_check = now
                    remaining = int(end - now)
                    if remaining > 0:
                        print(f"    剩余 {remaining}s ... 当前速度: {format_speed(speed)}")
    except Exception:
        pass

    total_time = time.time() - start

    result = {"ip": ip, "speeds": speeds, "duration": total_time}

    if speeds:
        result["avg_speed"] = statistics.mean(speeds)
        result["max_speed"] = max(speeds)
        result["min_speed"] = min(speeds)
        result["stddev"] = statistics.stdev(speeds) if len(speeds) > 1 else 0

        # 稳定性评分（波动越小越稳定）
        avg = result["avg_speed"]
        if avg > 0:
            result["stability_score"] = max(0, 100 - (result["stddev"] / avg * 100))
            result["stability_score"] = min(100, result["stability_score"])
        else:
            result["stability_score"] = 0

        # 波动率
        result["volatility"] = (result["stddev"] / avg * 100) if avg > 0 else 100
    else:
        result["avg_speed"] = 0
        result["max_speed"] = 0
        result["min_speed"] = 0
        result["stddev"] = 0
        result["stability_score"] = 0
        result["volatility"] = 100

    return result


def latency_stability(ping_results: Dict) -> Dict:
    """延迟稳定性分析"""
    rtts = ping_results.get("rtts", [])
    result = {
        "jitter": ping_results.get("jitter", 0),
        "stddev": ping_results.get("stddev", 0)
    }

    if len(rtts) > 1:
        # 计算抖动率
        avg = statistics.mean(rtts)
        if avg > 0:
            result["jitter_ratio"] = result["jitter"] / avg
        else:
            result["jitter_ratio"] = 0

        # 稳定性评分
        result["latency_stability"] = max(0, 100 - (result["jitter_ratio"] * 100))
        result["latency_stability"] = min(100, result["latency_stability"])

        # 检测是否有大幅波动
        sorted_rtts = sorted(rtts)
        if len(sorted_rtts) >= 4:
            q1 = sorted_rtts[len(sorted_rtts) // 4]
            q3 = sorted_rtts[3 * len(sorted_rtts) // 4]
            result["iqr"] = q3 - q1
            result["spike_count"] = sum(1 for r in rtts if r > q3 + 1.5 * (q3 - q1))
        else:
            result["iqr"] = 0
            result["spike_count"] = 0
    else:
        result["jitter_ratio"] = 0
        result["latency_stability"] = 50
        result["iqr"] = 0
        result["spike_count"] = 0

    return result


def print_stability_result(result: Dict):
    """打印稳定性结果"""
    print(f"  稳定性结果 ({result.get('duration', 0):.1f}s)")

    if result.get("speeds"):
        print(f"  平均速度: {green(format_speed(result['avg_speed']))}")
        print(f"  峰值速度: {green(format_speed(result['max_speed']))}")
        print(f"  最低速度: {yellow(format_speed(result['min_speed']))}")

        score = result.get("stability_score", 0)
        if score >= 90:
            color = green
        elif score >= 70:
            color = yellow
        else:
            color = red
        print(f"  稳定性评分: {color(f'{score:.1f}/100')}")
        print(f"  波动率: {result.get('volatility', 0):.1f}%")

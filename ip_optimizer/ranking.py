"""综合评分系统模块"""

from typing import Dict, List, Any
from utils import green, yellow, red, cyan, bold, format_latency, format_speed


def calculate_score(ip_data: Dict, weights: Dict = None) -> float:
    """计算单个IP的综合评分（0-100）"""
    if weights is None:
        weights = {
            "download_speed": 0.35,
            "latency": 0.25,
            "packet_loss": 0.15,
            "region_match": 0.15,
            "stability": 0.10
        }

    scores = {}

    # 1. 下载速度评分 (35%)
    speed = ip_data.get("download_speed", 0)
    if speed > 0:
        # 以 100MB/s 为满分
        scores["download_speed"] = min(100, speed / (100 * 1024 * 1024) * 100)
    else:
        speed = ip_data.get("avg_speed", 0)
        if speed > 0:
            scores["download_speed"] = min(100, speed / (100 * 1024 * 1024) * 100)
        else:
            scores["download_speed"] = 0

    # 2. 延迟评分 (25%)
    latency = ip_data.get("ping_avg", ip_data.get("avg", 9999))
    if latency <= 0 or latency >= 9999:
        scores["latency"] = 0
    elif latency <= 10:
        scores["latency"] = 100
    elif latency <= 30:
        scores["latency"] = 90
    elif latency <= 50:
        scores["latency"] = 80
    elif latency <= 80:
        scores["latency"] = 65
    elif latency <= 120:
        scores["latency"] = 50
    elif latency <= 200:
        scores["latency"] = 30
    elif latency <= 500:
        scores["latency"] = 10
    else:
        scores["latency"] = 0

    # 3. 丢包率评分 (15%)
    loss = ip_data.get("loss_percent", ip_data.get("loss", 100))
    if loss == 0:
        scores["packet_loss"] = 100
    elif loss <= 1:
        scores["packet_loss"] = 95
    elif loss <= 2:
        scores["packet_loss"] = 85
    elif loss <= 5:
        scores["packet_loss"] = 65
    elif loss <= 10:
        scores["packet_loss"] = 40
    else:
        scores["packet_loss"] = 0

    # 4. 地区匹配评分 (15%)
    region_match = ip_data.get("region_match", ip_data.get("region_score", 0))
    scores["region_match"] = min(100, max(0, region_match))

    # 5. 稳定性评分 (10%)
    stability = ip_data.get("stability_score", 50)
    scores["stability"] = min(100, max(0, stability))

    # 计算总分
    total = 0
    for key, weight in weights.items():
        score = scores.get(key, 0)
        total += score * weight

    total = min(100, max(0, total))
    ip_data["score"] = round(total, 1)
    ip_data["score_details"] = scores

    return total


def rank_ips(ip_list: List[Dict], weights: Dict = None,
              top_n: int = 10) -> List[Dict]:
    """对IP列表进行综合评分并排序"""
    if weights is None:
        weights = {
            "download_speed": 0.35,
            "latency": 0.25,
            "packet_loss": 0.15,
            "region_match": 0.15,
            "stability": 0.10
        }

    for ip_data in ip_list:
        calculate_score(ip_data, weights)

    # 排序：总分 > 下载速度 > 丢包率 > 延迟
    ranked = sorted(
        ip_list,
        key=lambda x: (
            x.get("score", 0),
            x.get("download_speed", x.get("avg_speed", 0)),
            -x.get("loss_percent", x.get("loss", 100)),
            -x.get("ping_avg", x.get("avg", 9999))
        ),
        reverse=True
    )

    return ranked[:top_n]


def get_score_color(score: float) -> Any:
    """根据分数返回对应颜色函数"""
    if score >= 90:
        return green
    elif score >= 75:
        return green
    elif score >= 60:
        return yellow
    elif score >= 40:
        return yellow
    else:
        return red


def print_ranking(ranked_ips: List[Dict], region_name: str = ""):
    """打印排名结果"""
    print()
    print(cyan("=" * 56))
    print(cyan(f"          IP 优选结果"))
    if region_name:
        print(cyan(f"     目标地区: {region_name}"))
    print(cyan("=" * 56))
    print()

    # 表头
    header = f"{'排名':<6} {'IP':<18} {'地区':<6} {'延迟':<10} {'丢包':<8} {'下载':<12} {'得分':<6}"
    print(bold(header))
    print("-" * 66)

    for idx, ip_data in enumerate(ranked_ips, 1):
        ip = ip_data.get("ip", "Unknown")
        region = ip_data.get("region", ip_data.get("country_code", "??"))

        ping = ip_data.get("ping_avg", ip_data.get("avg", 0))
        latency_str = format_latency(ping) if ping and ping < 9999 else f"{red('超时')}"

        loss = ip_data.get("loss_percent", ip_data.get("loss", 0))
        loss_str = f"{loss:.1f}%" if loss >= 0 else "N/A"

        speed = ip_data.get("download_speed", ip_data.get("avg_speed", 0))
        speed_str = format_speed(speed) if speed > 0 else f"{red('N/A')}"

        score = ip_data.get("score", 0)
        score_color = get_score_color(score)
        score_str = score_color(f"{score:.0f}")

        line = f"{idx:<6} {ip:<18} {region:<6} {latency_str:<10} {loss_str:<8} {speed_str:<12} {score_str:<6}"
        print(line)

    print("-" * 66)
    print()

    if ranked_ips:
        best = ranked_ips[0]
        print(cyan("=" * 56))
        print(f"  {bold('推荐IP:')} {green(best['ip'])}")
        print(f"  {bold('综合评分:')} {get_score_color(best['score'])(f\"{best['score']:.1f}/100\")}")
        print()
        print(f"  {bold('优势分析:')}")
        details = best.get("score_details", {})

        if details.get("packet_loss", 0) >= 85:
            print(f"    ✓ 低丢包")
        if details.get("latency", 0) >= 80:
            print(f"    ✓ 低延迟")
        if details.get("download_speed", 0) >= 70:
            print(f"    ✓ 高下载速度")
        if details.get("region_match", 0) >= 80:
            print(f"    ✓ 地区匹配")
        if details.get("stability", 0) >= 80:
            print(f"    ✓ 高稳定性")

        print(cyan("=" * 56))

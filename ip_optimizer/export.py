"""结果导出模块"""

import os
import json
import csv
from typing import Dict, List
from datetime import datetime

from config import RESULT_DIR, ensure_dirs
from utils import green, yellow, red, cyan, bold


def export_txt(results: List[Dict], filename: str = None) -> str:
    """导出为TXT格式"""
    ensure_dirs()
    if not filename:
        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    filepath = os.path.join(RESULT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=" * 56 + "\n")
        f.write("  Termux IP 优选工具 - 测试结果\n")
        f.write(f"  导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 56 + "\n\n")

        f.write(f"{'排名':<6} {'IP':<18} {'地区':<6} {'延迟(ms)':<10} {'丢包(%)':<8} {'速度':<12} {'得分':<6}\n")
        f.write("-" * 66 + "\n")

        for idx, r in enumerate(results, 1):
            ip = r.get("ip", "Unknown")
            region = r.get("region", r.get("country_code", "??"))
            ping = r.get("ping_avg", r.get("avg", 0))
            loss = r.get("loss_percent", r.get("loss", 0))
            speed = r.get("download_speed", r.get("avg_speed", 0))
            score = r.get("score", 0)

            ping_str = f"{ping:.1f}" if ping and ping < 9999 else "超时"
            loss_str = f"{loss:.1f}"
            speed_str = f"{speed/(1024*1024):.1f}MB/s" if speed > 0 else "N/A"

            f.write(f"{idx:<6} {ip:<18} {region:<6} {ping_str:<10} {loss_str:<8} {speed_str:<12} {score:<6.1f}\n")

        # 推荐IP
        if results:
            f.write("\n" + "=" * 56 + "\n")
            best = results[0]
            f.write(f"推荐IP: {best.get('ip', 'N/A')}\n")
            f.write(f"综合评分: {best.get('score', 0):.1f}/100\n")
            f.write("=" * 56 + "\n")

    return filepath


def export_json(results: List[Dict], filename: str = None) -> str:
    """导出为JSON格式"""
    ensure_dirs()
    if not filename:
        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    filepath = os.path.join(RESULT_DIR, filename)
    export_data = {
        "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total": len(results),
        "results": results
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return filepath


def export_csv(results: List[Dict], filename: str = None) -> str:
    """导出为CSV格式"""
    ensure_dirs()
    if not filename:
        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    filepath = os.path.join(RESULT_DIR, filename)

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["排名", "IP", "地区", "延迟(ms)", "丢包(%)",
                         "下载速度(B/s)", "综合得分"])

        for idx, r in enumerate(results, 1):
            writer.writerow([
                idx,
                r.get("ip", "Unknown"),
                r.get("region", r.get("country_code", "??")),
                r.get("ping_avg", r.get("avg", 0)),
                r.get("loss_percent", r.get("loss", 0)),
                r.get("download_speed", r.get("avg_speed", 0)),
                r.get("score", 0)
            ])

    return filepath


def show_export_menu(results: List[Dict]):
    """导出菜单"""
    if not results:
        print(f"\n  {yellow('没有可导出的数据')}")
        return

    print()
    print(cyan("=" * 40))
    print(cyan("     结果导出"))
    print(cyan("=" * 40))
    print()
    print("  1. 导出为 TXT")
    print("  2. 导出为 JSON")
    print("  3. 导出为 CSV")
    print("  0. 返回")
    print()

    try:
        choice = input("  请选择: ").strip()
    except EOFError:
        return

    exporters = {
        "1": ("TXT", export_txt),
        "2": ("JSON", export_json),
        "3": ("CSV", export_csv)
    }

    if choice in exporters:
        fmt, exporter = exporters[choice]
        try:
            filepath = exporter(results)
            print(f"\n  {green(f'✓ 已导出为 {fmt} 格式')}")
            print(f"  文件: {yellow(filepath)}")
        except Exception as e:
            print(f"\n  {red(f'导出失败: {e}')}")
    elif choice == "0":
        return
    else:
        print(f"  {yellow('无效选择')}")

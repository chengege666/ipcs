"""历史记录模块"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from config import HISTORY_FILE, ensure_dirs
from utils import green, yellow, red, cyan, bold, get_timestamp


def save_history(record: Dict) -> bool:
    """保存一条历史记录"""
    ensure_dirs()

    records = load_history()

    record["time"] = get_timestamp()

    records.insert(0, record)

    # 保留最近100条
    if len(records) > 100:
        records = records[:100]

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def load_history() -> List[Dict]:
    """加载历史记录"""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []


def clear_history() -> bool:
    """清空历史记录"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except IOError:
        return False


def show_history(limit: int = 20):
    """显示历史记录"""
    records = load_history()

    if not records:
        print(f"\n  {yellow('暂无历史记录')}")
        return

    print()
    print(cyan("=" * 64))
    print(cyan("          历史记录"))
    print(cyan("=" * 64))

    header = f"{'序号':<6} {'时间':<18} {'域名':<20} {'IP':<18} {'地区':<6} {'得分':<6}"
    print(f"\n{bold(header)}")
    print("-" * 74)

    for idx, record in enumerate(records[:limit], 1):
        time_str = record.get("time", "")[-16:]
        domain = record.get("domain", "-")[:18]
        ip = record.get("ip", "-")[:16]
        region = record.get("region", "??")
        score = record.get("score", 0)

        score_str = f"{score:.0f}" if isinstance(score, (int, float)) else str(score)
        print(f"{idx:<6} {time_str:<18} {domain:<20} {ip:<18} {region:<6} {score_str:<6}")

    print("-" * 74)
    print(f"\n 共 {len(records)} 条记录 (显示前 {min(limit, len(records))} 条)")

    return records


def show_history_menu():
    """历史记录菜单"""
    while True:
        records = show_history()
        if not records:
            return

        print()
        print("  1. 查看详情")
        print("  2. 清空历史")
        print("  0. 返回")
        print()

        try:
            choice = input("  请选择: ").strip()
        except EOFError:
            return

        if choice == "0":
            return
        elif choice == "2":
            if clear_history():
                print(f"  {green('历史记录已清空')}")
            else:
                print(f"  {red('清空失败')}")
        elif choice == "1":
            try:
                n = input("  输入序号: ").strip()
                idx = int(n) - 1
                if 0 <= idx < len(records):
                    record = records[idx]
                    print()
                    print(cyan("-" * 40))
                    for k, v in record.items():
                        print(f"  {k}: {v}")
                    print(cyan("-" * 40))
                    input(f"\n  {green('按回车继续...')}")
                else:
                    print(f"  {yellow('无效序号')}")
            except (ValueError, EOFError):
                pass

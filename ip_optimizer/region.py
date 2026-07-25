"""地区选择模块"""

import json
import os
from typing import Optional, Dict, List

from utils import green, yellow, cyan, bold, print_banner


def get_regions() -> List[Dict]:
    """获取地区列表"""
    regions = [
        {"id": "auto", "name": "自动选择", "name_en": "Auto", "flag": "🌍"},
        {"id": "cn", "name": "中国大陆", "name_en": "China", "flag": "🇨🇳"},
        {"id": "hk", "name": "香港", "name_en": "Hong Kong", "flag": "🇭🇰"},
        {"id": "tw", "name": "台湾", "name_en": "Taiwan", "flag": "🇹🇼"},
        {"id": "jp", "name": "日本", "name_en": "Japan", "flag": "🇯🇵"},
        {"id": "kr", "name": "韩国", "name_en": "South Korea", "flag": "🇰🇷"},
        {"id": "sg", "name": "新加坡", "name_en": "Singapore", "flag": "🇸🇬"},
        {"id": "us", "name": "美国", "name_en": "United States", "flag": "🇺🇸"},
        {"id": "eu", "name": "欧洲", "name_en": "Europe", "flag": "🇪🇺"},
        {"id": "global", "name": "全球模式", "name_en": "Global", "flag": "🌐"}
    ]

    # 尝试从数据文件加载自定义地区
    data_file = os.path.join(os.path.dirname(__file__), "data", "regions.json")
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "regions" in data:
                    return data["regions"]
        except (json.JSONDecodeError, IOError):
            pass

    return regions


def show_region_menu() -> Optional[str]:
    """显示地区选择菜单，返回地区ID"""
    regions = get_regions()

    print()
    print(cyan("=" * 40))
    print(cyan("     请选择目标地区"))
    print(cyan("=" * 40))
    print()

    for i, region in enumerate(regions, 1):
        flag = region.get("flag", "")
        name = region["name"]
        name_en = region.get("name_en", "")
        print(f"  {i}. {flag} {name} ({name_en})")

    print()
    print("  0. 返回上级菜单")
    print()

    try:
        choice = input(f"  {bold('请选择')} [1-{len(regions)}]: ").strip()
        if choice == "0":
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(regions):
            return regions[idx]["id"]
        else:
            print(f"  {yellow('无效选择，使用默认: 自动选择')}")
            return "auto"
    except (ValueError, EOFError):
        return "auto"


def auto_detect_region() -> Optional[Dict]:
    """自动检测地区"""
    try:
        from geoip import detect_region, get_self_ip, get_geo_info

        self_ip = get_self_ip()
        if not self_ip:
            print(f"  {yellow('无法获取当前网络位置')}")
            return None

        geo = get_geo_info(self_ip)
        country = geo.get("country", "Unknown")
        country_code = geo.get("country_code", "XX")
        region_id = detect_region()

        if not region_id:
            return None

        regions = get_regions()
        region_name = country
        for r in regions:
            if r["id"] == region_id:
                region_name = r["name"]
                break

        print(f"\n  {green('检测当前位置:')}")
        print(f"    IP: {self_ip}")
        print(f"    国家: {country} ({country_code})")
        print(f"    推荐地区: {green(region_name)}")

        return {
            "region_id": region_id,
            "region_name": region_name,
            "country": country,
            "country_code": country_code,
            "ip": self_ip
        }
    except Exception as e:
        print(f"  {yellow(f'地区检测失败: {e}')}")
        return None


def confirm_region(region_info: Dict) -> Optional[str]:
    """确认是否使用检测到的地区"""
    print()
    try:
        choice = input(f"  {bold('是否使用推荐地区?')} [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            return region_info["region_id"]
        return None
    except EOFError:
        return region_info["region_id"]


def get_region_name(region_id: str) -> str:
    """根据地区ID获取显示名称"""
    regions = get_regions()
    for r in regions:
        if r["id"] == region_id:
            flag = r.get("flag", "")
            return f"{flag} {r['name']}"
    return region_id.upper()

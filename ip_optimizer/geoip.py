"""IP地理信息模块"""

import json
import os
from typing import Dict, Optional
from utils import run_command, yellow


# 简易IP地理位置缓存
_geo_cache: Dict[str, Dict] = {}


def get_geo_info(ip: str) -> Dict:
    """获取IP地理位置信息"""
    if ip in _geo_cache:
        return _geo_cache[ip]

    info = {
        "ip": ip,
        "country": "Unknown",
        "country_code": "XX",
        "city": "Unknown",
        "isp": "Unknown",
        "region": None
    }

    # 优先使用 ip-api.com (免费, 不需要API key)
    result = _query_ip_api(ip)
    if result and result.get("status") == "success":
        info["country"] = result.get("country", "Unknown")
        info["country_code"] = result.get("countryCode", "XX")
        info["city"] = result.get("city", "Unknown")
        info["isp"] = result.get("isp", "Unknown")
        info["region"] = result.get("regionName", "")
    else:
        # 备选: ipinfo.io
        result = _query_ipinfo(ip)
        if result:
            info["country"] = result.get("country", "Unknown")
            info["country_code"] = result.get("country", "XX")
            info["city"] = result.get("city", "Unknown")
            info["isp"] = result.get("org", "Unknown")

    _geo_cache[ip] = info
    return info


def _query_ip_api(ip: str) -> Optional[Dict]:
    """通过 ip-api.com 查询"""
    try:
        import requests
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,countryCode,city,isp,regionName"},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _query_ipinfo(ip: str) -> Optional[Dict]:
    """通过 ipinfo.io 查询"""
    try:
        import requests
        resp = requests.get(
            f"https://ipinfo.io/{ip}/json",
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_self_ip() -> Optional[str]:
    """获取当前出口IP"""
    services = [
        "https://api.ipify.org",
        "https://ipv4.icanhazip.com",
        "https://checkip.amazonaws.com"
    ]
    for service in services:
        try:
            import requests
            resp = requests.get(service, timeout=5)
            if resp.status_code == 200:
                ip = resp.text.strip()
                return ip
        except Exception:
            continue
    return None


def detect_region() -> Optional[str]:
    """自动检测当前网络所在地"""
    self_ip = get_self_ip()
    if not self_ip:
        return None

    geo = get_geo_info(self_ip)
    country_code = geo.get("country_code", "").upper()

    # 映射国家代码到地区ID
    mapping = {
        "CN": "cn", "HK": "hk", "TW": "tw",
        "JP": "jp", "KR": "kr",
        "SG": "sg", "MY": "sg", "ID": "sg",
        "US": "us", "CA": "us",
        "GB": "eu", "DE": "eu", "FR": "eu",
        "NL": "eu", "FI": "eu", "SE": "eu",
        "NO": "eu", "DK": "eu", "IT": "eu",
        "ES": "eu", "CH": "eu", "AT": "eu",
        "BE": "eu", "IE": "eu", "PL": "eu",
        "RU": "eu", "UA": "eu"
    }

    return mapping.get(country_code)


def print_geo_info(ip: str):
    """打印IP地理信息"""
    info = get_geo_info(ip)
    flag_map = {
        "CN": "🇨🇳", "HK": "🇭🇰", "TW": "🇹🇼",
        "JP": "🇯🇵", "KR": "🇰🇷",
        "SG": "🇸🇬", "US": "🇺🇸"
    }
    flag = flag_map.get(info["country_code"], "🌍")

    print(f"  IP: {ip}")
    print(f"  国家: {flag} {info['country']} ({info['country_code']})")
    print(f"  城市: {info['city']}")
    print(f"  运营商: {info['isp']}")

"""DNS解析模块"""

import socket
import re
from typing import List, Dict, Optional, Tuple

from utils import yellow, red, green, cyan


def is_valid_domain(domain: str) -> bool:
    """验证域名格式"""
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain.strip()))


def resolve_dns(domain: str, timeout: int = 5) -> Dict:
    """DNS解析，返回A/AAAA/CNAME记录"""
    result = {
        "domain": domain,
        "cname": None,
        "ipv4": [],
        "ipv6": [],
        "error": None
    }

    try:
        # 尝试用 dnspython 解析
        try:
            import dns.resolver
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout

            # 查询 A 记录
            try:
                answers = resolver.resolve(domain, 'A')
                result["ipv4"] = [str(r) for r in answers]
            except Exception:
                pass

            # 查询 AAAA 记录
            try:
                answers = resolver.resolve(domain, 'AAAA')
                result["ipv6"] = [str(r) for r in answers]
            except Exception:
                pass

            # 查询 CNAME
            try:
                answers = resolver.resolve(domain, 'CNAME')
                result["cname"] = str(answers[0])
            except Exception:
                pass

        except ImportError:
            # 回退到 socket 解析
            ips = socket.gethostbyname_ex(domain)
            result["ipv4"] = ips[2] if len(ips) > 2 else []

        if not result["ipv4"] and not result["ipv6"]:
            result["error"] = "DNS解析无结果"

    except socket.gaierror:
        result["error"] = "域名解析失败"
    except Exception as e:
        result["error"] = f"DNS解析异常: {str(e)}"

    return result


def resolve_dns_simple(domain: str) -> List[str]:
    """简单DNS解析，仅返回IPv4地址列表"""
    result = resolve_dns(domain)
    return result.get("ipv4", [])


def print_dns_result(result: Dict):
    """打印DNS解析结果"""
    print(f"\n{cyan('DNS解析结果')}")
    print(f"{'=' * 40}")
    print(f"  域名: {result['domain']}")

    if result.get("cname"):
        print(f"  CNAME: {yellow(result['cname'])}")

    if result.get("ipv4"):
        print(f"  IPv4 ({len(result['ipv4'])}):")
        for ip in result["ipv4"][:10]:
            print(f"    {green(ip)}")
        if len(result["ipv4"]) > 10:
            print(f"    ... 还有 {len(result['ipv4']) - 10} 个")

    if result.get("ipv6"):
        print(f"  IPv6 ({len(result['ipv6'])}):")
        for ip in result["ipv6"][:5]:
            print(f"    {green(ip)}")
        if len(result["ipv6"]) > 5:
            print(f"    ... 还有 {len(result['ipv6']) - 5} 个")

    if result.get("error"):
        print(f"  错误: {red(result['error'])}")

    print(f"{'=' * 40}")

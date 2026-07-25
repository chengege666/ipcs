#!/usr/bin/env python3
"""
Termux IP 优选工具 v1.0（cg）
Termux-IP-Optimizer
基于多维度指标（延迟、丢包、速度、稳定性、地区）的智能 IP 优选系统
"""

import sys
import os
import json
import time
from typing import List, Dict, Optional

# 确保可在项目目录外执行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    print_banner, red, green, yellow, cyan, bold,
    print_step, format_latency, format_speed, get_timestamp,
    check_dependencies
)
from config import load_config, save_config, update_config
from menu import show_main_menu, show_config_menu, setup_shortcut, uninstall
from region import (
    show_region_menu, auto_detect_region, confirm_region,
    get_region_name, get_regions
)
from dns import resolve_dns, print_dns_result, is_valid_domain
from ip_scan import (
    merge_ip_sources, scan_ips, load_ip_pool,
    load_cloudflare_ips
)
from ping_test import ping_batch
from packet_loss import batch_detect_loss, get_loss_grade
from tcp_test import batch_test_tcp
from speedtest import speed_test, print_speed_result
from stability import speed_stability_test
from geoip import get_geo_info, print_geo_info, detect_region
from ranking import rank_ips, print_ranking
from export import show_export_menu
from history import save_history, show_history_menu


def load_domain_pool() -> Dict[str, List[str]]:
    """加载域名池"""
    pool_file = os.path.join(os.path.dirname(__file__), "data", "domain_pool.json")
    if not os.path.exists(pool_file):
        return {}
    try:
        with open(pool_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError):
        return {}


def show_domain_pool_menu() -> Optional[str]:
    """显示域名池菜单，返回选中域名"""
    pool = load_domain_pool()
    if not pool:
        return None

    categories = pool.get("categories", [])
    if not categories:
        return None

    print()
    print(cyan("=" * 40))
    print(cyan("  域名池 - 选择常用域名"))
    print(cyan("=" * 40))
    print()

    # 展平所有域名并编号
    flat_domains = []
    start_idx = 1
    for cat in categories:
        cat_name = cat.get("name", "其他")
        domains = cat.get("domains", [])
        if not domains:
            continue
        print(f"  {bold(cat_name)}:")
        for d in domains:
            print(f"    {start_idx}. {green(d)}")
            flat_domains.append((cat_name, d))
            start_idx += 1
        print()

    print(f"  {bold('0.')} {yellow('手动输入域名')}")
    print()

    try:
        choice = input(f"  {bold('请选择')} [0-{len(flat_domains)}]: ").strip()
        if choice == "0" or not choice:
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(flat_domains):
            return flat_domains[idx][1]
        else:
            print(f"  {yellow('无效选择，切换手动输入')}")
            return None
    except (ValueError, EOFError):
        return None


def run_domain_optimize():
    """域名 IP 优选主流程"""
    print()
    print(cyan("=" * 40))
    print(cyan("  域名 IP 优选"))
    print(cyan("=" * 40))
    print()

    # 1. 域名池选择 > 手动输入
    domain = show_domain_pool_menu()
    if not domain:
        domain = input("  请输入目标域名: ").strip()
        if not domain:
            print(f"  {red('域名不能为空')}")
            return

    if not is_valid_domain(domain):
        # 尝试添加 https:// 或 http:// 前缀
        if domain.startswith("http://") or domain.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.hostname
        else:
            print(f"  {red('域名格式无效')}")
            return

    # 2. 选择地区
    region_id = show_region_menu()
    if region_id is None:
        return

    if region_id == "auto":
        region_info = auto_detect_region()
        if region_info:
            region_id = confirm_region(region_info)
            if region_id is None:
                region_id = show_region_menu()

    region_name = get_region_name(region_id or "auto")
    print(f"\n  {green(f'目标地区: {region_name}')}")
    print()

    # 3. DNS解析
    print_step(1, 6, "DNS解析")
    dns_result = resolve_dns(domain)
    print_dns_result(dns_result)

    if dns_result.get("error") and not dns_result.get("ipv4"):
        print(f"  {red('DNS解析失败，无法继续')}")
        return

    # 4. 获取IP列表
    print_step(2, 6, "构建IP池")
    dns_ips = dns_result.get("ipv4", [])
    pool_ips = load_ip_pool(region_id)

    config = load_config()
    max_ips = config.get("ip_test_limit", 100)

    ip_list = merge_ip_sources(
        dns_ips=dns_ips,
        pool_ips=pool_ips,
        max_ips=max_ips
    )

    if not ip_list:
        print(f"  {red('没有可测试的IP地址')}")
        return

    print(f"  {green(f'共 {len(ip_list)} 个待测IP')}")
    print()

    # 5. 批量Ping测试
    print_step(3, 6, "延迟测试 (Ping)")
    ping_count = config.get("ping_count", 5)
    concurrent = config.get("concurrent_ping", 30)
    ping_results = ping_batch(ip_list, count=ping_count, max_workers=concurrent)

    # 过滤可达IP
    reachable_ips = [ip for ip, r in ping_results.items() if r["received"] > 0]
    print(f"  {green(f'可达IP: {len(reachable_ips)}/{len(ip_list)}')}")

    if not reachable_ips:
        print(f"  {red('没有可达的IP')}")
        return

    # 限制测试数量
    if len(reachable_ips) > max_ips:
        reachable_ips = reachable_ips[:max_ips]

    # 6. 丢包检测
    print_step(4, 6, "丢包检测")
    loss_results = batch_detect_loss(reachable_ips, count=ping_count)

    # 7. TCP连接测试
    print_step(5, 6, "TCP连接测试")
    tcp_results = batch_test_tcp(reachable_ips)

    # 8. 下载测速（对排名靠前的IP）
    print_step(6, 6, "下载速度测试")
    ranked = rank_ips_simple(ping_results, loss_results, tcp_results, region_id)

    top_n = min(5, len(ranked))
    speed_results = {}
    for ip_data in ranked[:top_n]:
        ip = ip_data["ip"]
        print(f"\n  测速IP: {ip}")
        speed_result = speed_test(
            ip,
            size=config.get("download_size", "50MB"),
            threads=config.get("threads", 8)
        )
        speed_results[ip] = speed_result
        if not speed_result.get("error"):
            print_speed_result(speed_result)
        print()

    # 9. 综合评分与排名
    all_results = []
    for ip in reachable_ips:
        pr = ping_results.get(ip, {})
        lr = loss_results.get(ip, {})
        tr = tcp_results.get(ip, {})

        geo = get_geo_info(ip)
        region_score = 0
        if region_id and region_id != "auto" and region_id != "global":
            target_code = get_target_code(region_id)
            if geo.get("country_code", "").upper() == target_code:
                region_score = 100
            else:
                region_score = 30

        entry = {
            "ip": ip,
            "region": geo.get("country_code", "XX"),
            "country_code": geo.get("country_code", "XX"),
            "ping_avg": pr.get("avg", 0),
            "avg": pr.get("avg", 0),
            "loss_percent": lr.get("loss_percent", 100),
            "loss": lr.get("loss_percent", 100),
            "tcp_time": tr.get("best_time"),
            "download_speed": 0,
            "avg_speed": 0,
            "region_match": region_score,
            "region_score": region_score,
            "stability_score": 50,
            "jitter": pr.get("jitter", 0)
        }

        # 补充测速结果
        if ip in speed_results:
            sr = speed_results[ip]
            entry["download_speed"] = sr.get("avg_speed", 0)
            entry["avg_speed"] = sr.get("avg_speed", 0)

        all_results.append(entry)

    final_ranked = rank_ips(all_results, top_n=10)
    print_ranking(final_ranked, region_name)

    # 10. 导出
    show_export_menu(final_ranked)

    # 11. 保存历史
    if final_ranked:
        best = final_ranked[0]
        save_history({
            "domain": domain,
            "region": region_id,
            "ip": best["ip"],
            "ping": best.get("avg", 0),
            "loss": best.get("loss_percent", 0),
            "download": best.get("download_speed", 0),
            "score": best.get("score", 0)
        })

    input(f"\n  {green('按回车键返回主菜单...')}")


def run_cloudflare_optimize():
    """Cloudflare IP 优选"""
    print()
    print(cyan("=" * 40))
    print(cyan("  Cloudflare IP 优选"))
    print(cyan("=" * 40))
    print()

    region_id = show_region_menu()
    if region_id is None:
        return

    region_name = get_region_name(region_id or "auto")
    print(f"\n  {green(f'目标地区: {region_name}')}")

    config = load_config()
    max_ips = config.get("ip_test_limit", 100)

    print(f"\n  {cyan('正在加载Cloudflare IP池...')}")
    all_ips = load_cloudflare_ips()
    import random
    sampled_ips = random.sample(all_ips, min(max_ips, len(all_ips)))
    print(f"  {green(f'共 {len(sampled_ips)} 个待测IP (从 {len(all_ips)} 个中采样)')}")

    # 继续使用通用优选流程
    _run_common_optimize(sampled_ips, region_id, region_name)


def run_cdn_test():
    """CDN 节点测速"""
    print()
    print(cyan("=" * 40))
    print(cyan("  CDN 节点测速"))
    print(cyan("=" * 40))
    print()

    domain = input("  请输入CDN域名: ").strip()
    if not domain:
        print(f"  {red('域名不能为空')}")
        return

    if not is_valid_domain(domain):
        print(f"  {red('域名格式无效')}")
        return

    print(f"\n  {cyan('正在解析CNAME...')}")
    dns_result = resolve_dns(domain)

    # 获取CNAME指向
    cname = dns_result.get("cname")
    if cname:
        print(f"  CNAME: {yellow(cname)}")
        cname_result = resolve_dns(cname)
        ips = cname_result.get("ipv4", [])
    else:
        ips = dns_result.get("ipv4", [])

    if not ips:
        print(f"  {red('未找到CDN节点IP')}")
        return

    print(f"  {green(f'发现 {len(ips)} 个CDN节点')}")

    region_id = show_region_menu()
    region_name = get_region_name(region_id or "auto")

    _run_common_optimize(ips, region_id, region_name)


def run_download_test():
    """下载速度测试"""
    print()
    print(cyan("=" * 40))
    print(cyan("  下载速度测试"))
    print(cyan("=" * 40))
    print()

    target = input("  输入IP或域名: ").strip()
    if not target:
        print(f"  {red('输入不能为空')}")
        return

    config = load_config()
    result = speed_test(
        target,
        size=config.get("download_size", "50MB"),
        threads=config.get("threads", 8)
    )
    print("\n" + cyan("=" * 40))
    print_speed_result(result)
    print(cyan("=" * 40))

    input(f"\n  {green('按回车键返回主菜单...')}")


def run_dns_test():
    """DNS 解析测试"""
    print()
    print(cyan("=" * 40))
    print(cyan("  DNS 解析测试"))
    print(cyan("=" * 40))
    print()

    domain = input("  输入域名: ").strip()
    if not domain:
        print(f"  {red('域名不能为空')}")
        return

    if not is_valid_domain(domain):
        print(f"  {red('域名格式无效')}")
        return

    result = resolve_dns(domain)
    print_dns_result(result)

    input(f"\n  {green('按回车键返回主菜单...')}")


def _run_common_optimize(ip_list: List[str], region_id: str, region_name: str):
    """通用IP优选流程"""
    if not ip_list:
        print(f"  {red('没有可测试的IP')}")
        return

    config = load_config()
    max_ips = config.get("ip_test_limit", 100)

    if len(ip_list) > max_ips:
        import random
        ip_list = random.sample(ip_list, max_ips)

    # 1. 批量Ping
    print(f"\n  {cyan('[1/4] 延迟测试...')}")
    ping_count = config.get("ping_count", 5)
    ping_results = ping_batch(ip_list, count=min(ping_count, 5), max_workers=config.get("concurrent_ping", 30))

    reachable = [ip for ip, r in ping_results.items() if r["received"] > 0]
    print(f"  {green(f'可达IP: {len(reachable)}/{len(ip_list)}')}")

    if not reachable:
        print(f"  {red('没有可达IP')}")
        return

    # 2. 丢包检测
    print(f"\n  {cyan('[2/4] 丢包检测...')}")
    loss_results = batch_detect_loss(reachable, count=min(ping_count, 5))

    # 3. TCP测试
    print(f"\n  {cyan('[3/4] TCP连接测试...')}")
    tcp_results = batch_test_tcp(reachable)

    # 4. 评分与排序
    print(f"\n  {cyan('[4/4] 综合评分...')}")
    all_results = []
    for ip in reachable:
        pr = ping_results.get(ip, {})
        lr = loss_results.get(ip, {})

        geo = get_geo_info(ip)
        region_score = 0
        if region_id and region_id != "auto" and region_id != "global":
            target = get_target_code(region_id)
            if geo.get("country_code", "").upper() == target:
                region_score = 100
            else:
                region_score = 30

        entry = {
            "ip": ip,
            "region": geo.get("country_code", "XX"),
            "country_code": geo.get("country_code", "XX"),
            "ping_avg": pr.get("avg", 0),
            "avg": pr.get("avg", 0),
            "loss_percent": lr.get("loss_percent", 100),
            "loss": lr.get("loss_percent", 100),
            "region_match": region_score,
            "region_score": region_score,
            "stability_score": 50,
            "jitter": pr.get("jitter", 0)
        }
        all_results.append(entry)

    final = rank_ips(all_results, top_n=10)
    print_ranking(final, region_name)

    show_export_menu(final)

    if final:
        best = final[0]
        save_history({
            "domain": "cdn/cloudflare",
            "region": region_id,
            "ip": best["ip"],
            "ping": best.get("avg", 0),
            "loss": best.get("loss_percent", 0),
            "download": 0,
            "score": best.get("score", 0)
        })

    input(f"\n  {green('按回车键返回主菜单...')}")


def rank_ips_simple(ping_results, loss_results, tcp_results, region_id):
    """简单排名（用于选择测速目标）"""
    entries = []
    for ip, pr in ping_results.items():
        if pr.get("received", 0) == 0:
            continue

        lr = loss_results.get(ip, {})
        geo = get_geo_info(ip)

        region_score = 0
        if region_id and region_id not in ("auto", "global"):
            target = get_target_code(region_id)
            if geo.get("country_code", "").upper() == target:
                region_score = 100

        loss = lr.get("loss_percent", 100)
        ping = pr.get("avg", 9999)

        # 简单打分
        score = 0
        if ping < 50:
            score += 40
        elif ping < 100:
            score += 30
        elif ping < 200:
            score += 15

        if loss == 0:
            score += 30
        elif loss <= 2:
            score += 25
        elif loss <= 5:
            score += 15
        elif loss <= 10:
            score += 5

        score += region_score * 0.3

        entries.append({
            "ip": ip,
            "ping_avg": ping,
            "avg": ping,
            "loss_percent": loss,
            "loss": loss,
            "score": score,
            "region": geo.get("country_code", "XX"),
            "country_code": geo.get("country_code", "XX"),
            "region_match": region_score,
            "region_score": region_score,
            "stability_score": 50,
            "download_speed": 0,
            "avg_speed": 0,
            "jitter": pr.get("jitter", 0)
        })

    entries.sort(key=lambda x: x["score"], reverse=True)
    return entries[:10]


def run_region_management():
    """地区管理"""
    print()
    print(cyan("=" * 40))
    print(cyan("  地区管理"))
    print(cyan("=" * 40))
    print()

    region_info = auto_detect_region()
    if region_info:
        print(f"\n  {green('✓ 已检测到当前位置')}")
    else:
        print(f"\n  {yellow('无法自动检测')}")

    print(f"\n  {cyan('支持的地区列表:')}")
    regions = get_regions()
    for r in regions:
        flag = r.get("flag", "")
        print(f"    {flag} {r['name']} ({r.get('name_en', '')}) [{r['id']}]")

    print()
    print(f"  {yellow('提示: 可在 data/ip_pool/ 目录下添加IP池文件')}")
    print(f"  {yellow('文件名格式: {地区id}.txt')}")

    input(f"\n  {green('按回车键返回主菜单...')}")


def run_update():
    """检查更新"""
    print()
    print(cyan("=" * 40))
    print(cyan("  检查更新"))
    print(cyan("=" * 40))
    print()

    import subprocess
    import os

    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    if not os.path.exists(os.path.join(project_dir, ".git")):
        print(f"  {yellow('不是 git 仓库，无法更新')}")
        print(f"  请重新 clone: git clone https://github.com/chengege666/ipcs")
        input(f"\n  {green('按回车键返回主菜单...')}")
        return

    print(f"  {cyan('正在检查更新...')}")
    print()

    try:
        # 备份配置
        config_dir = os.path.expanduser("~/.ip_optimizer")
        config_backup = None
        if os.path.exists(config_dir):
            import shutil, tempfile
            config_backup = tempfile.mkdtemp()
            shutil.copytree(config_dir, os.path.join(config_backup, ".ip_optimizer"))

        result = subprocess.run(["git", "pull"], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"  {red('更新失败:')}")
            print(f"  {result.stderr}")
            # 恢复配置
            if config_backup:
                backup_path = os.path.join(config_backup, ".ip_optimizer")
                if os.path.exists(backup_path):
                    if os.path.exists(config_dir):
                        shutil.rmtree(config_dir)
                    shutil.move(backup_path, config_dir)
                shutil.rmtree(config_backup, ignore_errors=True)
        else:
            if "Already up to date" in result.stdout:
                print(f"  {green('✓ 已是最新版本')}")
            else:
                print(f"  {green('✓ 更新完成')}")
                print(f"  {result.stdout}")

            # 清理备份
            if config_backup:
                shutil.rmtree(config_backup, ignore_errors=True)

    except subprocess.TimeoutExpired:
        print(f"  {red('更新超时，请检查网络')}")
    except FileNotFoundError:
        print(f"  {red('未找到 git 命令，请安装: pkg install git')}")
    except Exception as e:
        print(f"  {red(f'更新失败: {e}')}")

    input(f"\n  {green('按回车键返回主菜单...')}")


def get_target_code(region_id: str) -> str:
    """获取地区ID对应的国家代码"""
    mapping = {
        "cn": "CN", "hk": "HK", "tw": "TW",
        "jp": "JP", "kr": "KR",
        "sg": "SG", "us": "US",
        "eu": "EU", "global": "XX"
    }
    return mapping.get(region_id, "XX")


def main():
    """主入口"""
    # 检查依赖
    missing = check_dependencies()
    if missing:
        print(f"\n  {yellow('缺少以下依赖:')}")
        for m in missing:
            print(f"    - {m}")
        print(f"\n  {yellow('请运行:')}")
        print(f"    pip install requests dnspython aiohttp ping3 rich geoip2")
        print(f"    pkg install dnsutils jq")
        print()

    # 命令行快捷模式
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        if is_valid_domain(domain):
            sys.argv = sys.argv[:1]
            _run_domain_quick(domain)
            return

    # 交互模式
    while True:
        try:
            choice = show_main_menu()
            if choice is None:
                continue
            elif choice == "0":
                print(f"\n  {green('感谢使用!')}")
                break
            elif choice == "1":
                run_domain_optimize()
            elif choice == "2":
                run_cloudflare_optimize()
            elif choice == "3":
                run_cdn_test()
            elif choice == "4":
                run_download_test()
            elif choice == "5":
                run_dns_test()
            elif choice == "6":
                show_history_menu()
            elif choice == "7":
                config = load_config()
                show_config_menu(config)
            elif choice == "8":
                run_region_management()
            elif choice == "9":
                setup_shortcut()
            elif choice.lower() == "u":
                run_update()
            elif choice.lower() == "x":
                uninstall()
            else:
                print(f"\n  {yellow('无效选择，请重新输入')}")
        except KeyboardInterrupt:
            print(f"\n\n  {green('感谢使用!')}")
            break
        except EOFError:
            print(f"\n\n  {green('感谢使用!')}")
            break


def _run_domain_quick(domain: str):
    """快速模式"""
    print()
    print(cyan("=" * 48))
    print(cyan("  Termux IP 优选工具 - 快速模式"))
    print(cyan("=" * 48))
    print(f"\n  域名: {yellow(domain)}")

    # 自动检测地区
    region_id = None
    region_info = auto_detect_region()
    if region_info:
        region_id = region_info["region_id"]

    if not region_id:
        region_id = "auto"

    region_name = get_region_name(region_id)

    # DNS解析
    print(f"\n  {cyan('[1/4] DNS解析...')}")
    dns_result = resolve_dns(domain)
    ips = dns_result.get("ipv4", [])
    if not ips:
        print(f"  {red('DNS解析失败')}")
        return
    print(f"  {green(f'获取到 {len(ips)} 个IP')}")

    # Ping测试
    print(f"\n  {cyan('[2/4] 延迟测试...')}")
    config = load_config()
    ping_results = ping_batch(ips, count=min(config.get("ping_count", 5), 5),
                              max_workers=config.get("concurrent_ping", 30))

    reachable = [ip for ip, r in ping_results.items() if r["received"] > 0]
    if not reachable:
        print(f"  {red('没有可达IP')}")
        return

    # 丢包检测
    print(f"\n  {cyan('[3/4] 丢包检测...')}")
    loss_results = batch_detect_loss(reachable, count=min(config.get("ping_count", 5), 5))

    # 评分
    print(f"\n  {cyan('[4/4] 综合评分...')}")
    all_results = []
    for ip in reachable:
        pr = ping_results.get(ip, {})
        lr = loss_results.get(ip, {})
        geo = get_geo_info(ip)

        region_score = 0
        if region_id and region_id not in ("auto", "global"):
            target = get_target_code(region_id)
            if geo.get("country_code", "").upper() == target:
                region_score = 100

        entry = {
            "ip": ip,
            "region": geo.get("country_code", "XX"),
            "country_code": geo.get("country_code", "XX"),
            "ping_avg": pr.get("avg", 0),
            "avg": pr.get("avg", 0),
            "loss_percent": lr.get("loss_percent", 100),
            "loss": lr.get("loss_percent", 100),
            "region_match": region_score,
            "region_score": region_score,
            "stability_score": 50,
            "jitter": pr.get("jitter", 0)
        }
        all_results.append(entry)

    final = rank_ips(all_results, top_n=10)
    print_ranking(final, region_name)

    if final:
        save_history({
            "domain": domain,
            "region": region_id,
            "ip": final[0]["ip"],
            "ping": final[0].get("avg", 0),
            "loss": final[0].get("loss_percent", 0),
            "download": 0,
            "score": final[0].get("score", 0)
        })


if __name__ == "__main__":
    main()

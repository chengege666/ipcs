"""配置管理模块"""

import os
import json

CONFIG_DIR = os.path.expanduser("~/.ip_optimizer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
REGIONS_FILE = os.path.join(CONFIG_DIR, "regions.json")
IP_POOL_DIR = os.path.join(CONFIG_DIR, "ip_pool")
RESULT_DIR = os.path.join(CONFIG_DIR, "result")

DEFAULT_CONFIG = {
    "ping_count": 20,
    "ping_interval": 0.2,
    "timeout": 5,
    "tcp_port": 443,
    "tcp_ports": [80, 443, 8080, 8443],
    "download_test": True,
    "download_size": "50MB",
    "download_sizes": ["10MB", "50MB", "100MB"],
    "threads": 8,
    "max_threads": 30,
    "stable_test_time": 30,
    "ip_test_limit": 100,
    "concurrent_ping": 30,
    "score_weights": {
        "download_speed": 0.35,
        "latency": 0.25,
        "packet_loss": 0.15,
        "region_match": 0.15,
        "stability": 0.10
    }
}


def ensure_dirs():
    """确保配置目录存在"""
    for d in [CONFIG_DIR, IP_POOL_DIR, RESULT_DIR]:
        os.makedirs(d, exist_ok=True)


def load_config():
    """加载配置文件"""
    ensure_dirs()
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 合并默认值，确保新字段存在
        merged = dict(DEFAULT_CONFIG)
        merged.update(cfg)
        return merged
    except (json.JSONDecodeError, IOError):
        return dict(DEFAULT_CONFIG)


def save_config(config):
    """保存配置文件"""
    ensure_dirs()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def update_config(key, value):
    """更新单个配置项"""
    config = load_config()
    keys = key.split(".")
    target = config
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    target[keys[-1]] = value
    return save_config(config)


def get_config_path():
    """获取配置目录路径"""
    return CONFIG_DIR

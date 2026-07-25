"""下载速度测试模块"""

import time
import threading
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import format_speed, print_progress, green, yellow, red


# 测试用URL列表（可公开访问的大文件）
TEST_URLS = {
    "10MB": [
        "http://speedtest.tele2.net/10MB.zip",
        "https://proof.ovh.net/files/10Mb.dat",
        "http://speedtest.ftp.otenet.gr/files/test10Mb.db"
    ],
    "50MB": [
        "http://speedtest.tele2.net/50MB.zip",
        "https://proof.ovh.net/files/50Mb.dat"
    ],
    "100MB": [
        "http://speedtest.tele2.net/100MB.zip",
        "https://proof.ovh.net/files/100Mb.dat"
    ]
}


def get_test_url(size: str) -> Optional[str]:
    """获取可用的测试URL"""
    urls = TEST_URLS.get(size, TEST_URLS["50MB"])
    # 直接返回第一个URL，跳过HEAD检查（Termux网络环境可能受限）
    return urls[0] if urls else None


def download_speed(url: str, timeout: float = 30.0) -> Dict:
    """单线程下载测速"""
    start = time.time()
    downloaded = 0
    speeds = []

    try:
        import requests
        resp = requests.get(url, stream=True, timeout=timeout)
        resp.raise_for_status()

        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                downloaded += len(chunk)
                elapsed = time.time() - start
                if elapsed > 0:
                    current_speed = downloaded / elapsed
                    speeds.append(current_speed)

    except Exception:
        pass

    elapsed = time.time() - start
    avg_speed = downloaded / elapsed if elapsed > 0 else 0

    return {
        "downloaded": downloaded,
        "time": elapsed,
        "avg_speed": avg_speed,
        "speeds": speeds
    }


def multi_thread_download(url: str, threads: int = 8,
                          timeout: float = 30.0) -> Dict:
    """多线程下载测速"""
    # 先获取文件大小
    file_size = 0
    try:
        import requests
        resp = requests.head(url, timeout=5)
        file_size = int(resp.headers.get("content-length", 0))
    except Exception:
        pass

    if file_size == 0:
        return download_speed(url, timeout)

    chunk_size = file_size // threads
    results = []
    lock = threading.Lock()
    start_time = time.time()
    stop_event = threading.Event()

    def download_chunk(start_byte, end_byte):
        downloaded = 0
        try:
            import requests
            headers = {"Range": f"bytes={start_byte}-{end_byte}"}
            resp = requests.get(url, headers=headers, stream=True,
                                timeout=timeout)
            for chunk in resp.iter_content(chunk_size=65536):
                if stop_event.is_set():
                    break
                if chunk:
                    downloaded += len(chunk)
                    with lock:
                        results.append(len(chunk))
        except Exception:
            pass
        return downloaded

    thread_pool = []
    for i in range(threads):
        s = i * chunk_size
        e = s + chunk_size - 1 if i < threads - 1 else file_size - 1
        t = threading.Thread(target=download_chunk, args=(s, e))
        thread_pool.append(t)
        t.start()

    for t in thread_pool:
        t.join()

    elapsed = time.time() - start_time
    total_downloaded = sum(results)
    avg_speed = total_downloaded / elapsed if elapsed > 0 else 0

    return {
        "downloaded": total_downloaded,
        "time": elapsed,
        "avg_speed": avg_speed,
        "file_size": file_size,
        "threads": threads
    }


def speed_test(ip: str, size: str = "50MB", threads: int = 8,
               timeout: float = 30.0) -> Dict:
    """对指定IP进行下载速度测试（整体带宽测试）"""
    url = get_test_url(size)
    if not url:
        return {
            "ip": ip,
            "error": "无可用测试源",
            "avg_speed": 0,
            "peak_speed": 0,
            "time": 0
        }

    result = _http_speed_download(url, threads=threads, timeout=timeout)

    result["ip"] = ip
    result["peak_speed"] = max(result.get("speeds", [result.get("avg_speed", 0)])) if result.get("speeds") else result.get("avg_speed", 0)
    result["size"] = size
    result["threads"] = threads if threads > 1 else 1

    return result


def _http_speed_download(url: str, headers: dict = None, threads: int = 8,
                          timeout: float = 30.0) -> Dict:
    """HTTP下载测速（仅首次测速显示进度）"""
    import requests

    if headers is None:
        headers = {}

    result = {"downloaded": 0, "time": 0, "avg_speed": 0, "speeds": []}

    try:
        start = time.time()
        resp = requests.get(url, headers=headers,
                            stream=True, timeout=timeout,
                            allow_redirects=True)
        resp.raise_for_status()

        downloaded = 0
        speeds = []
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                downloaded += len(chunk)
                elapsed = time.time() - start
                if elapsed > 0:
                    speeds.append(downloaded / elapsed)

        total_time = time.time() - start
        result["downloaded"] = downloaded
        result["time"] = total_time
        result["avg_speed"] = downloaded / total_time if total_time > 0 else 0
        result["speeds"] = speeds

    except Exception as e:
        result["error"] = str(e)

    return result


def print_speed_result(result: Dict):
    """打印测速结果"""
    if result.get("error"):
        print(f"  {red('测速失败:')} {result['error']}")
        return

    print(f"  下载大小: {result.get('size', '50MB')}")
    print(f"  下载速度: {green(format_speed(result['avg_speed']))}")
    print(f"  峰值速度: {green(format_speed(result['peak_speed']))}")
    print(f"  耗时: {result['time']:.1f}s")
    if result.get("threads"):
        print(f"  线程数: {result['threads']}")

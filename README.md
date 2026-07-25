# Termux IP 优选工具 v1.0

> 一个运行于 Android Termux 环境的命令行网络优化工具  
> 基于多维度指标智能选择访问体验最佳的 IP 节点

---

## 目录

- [项目定位](#项目定位)
- [解决的问题](#解决的问题)
- [运行环境](#运行环境)
- [快速开始](#快速开始)
- [功能模块](#功能模块)
- [使用指南](#使用指南)
- [评分系统](#评分系统)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [后续规划](#后续规划)

---

## 项目定位

Termux-IP-Optimizer = 一个支持全球地区选择、CDN 识别、延迟检测、丢包分析、真实下载测速的智能 IP 优选系统。

**核心选择标准：** 地区正确 + 延迟低 + 0 丢包 + 下载快 + 长时间稳定。

---

## 解决的问题

传统 IP 优选工具只依赖 Ping 延迟判断节点质量，但实际网络环境中：

| 情况 | 说明 |
|------|------|
| 低 Ping ≠ 高速度 | ICMP 优先级高，不代表 TCP 下载快 |
| 低 Ping ≠ 低丢包 | 延迟低但可能频繁丢包 |
| 低 Ping ≠ 高稳定 | 延迟波动大，实际体验差 |

**本项目的解决方案：** 5 维度综合评分体系，全面评估节点质量。

---

## 运行环境

| 项目 | 要求 |
|------|------|
| 系统 | Android |
| 运行环境 | Termux |
| Python | 3.10+ |
| 权限 | 普通用户（无需 Root） |

---

下载termux-app
https://github.com/termux/termux-app/releases

## 快速开始

### 一键命令

```bash
pkg update && pkg install -y python git curl wget dnsutils jq && pip install requests dnspython aiohttp ping3 rich geoip2 && git clone https://github.com/chengege666/ipcs && cd ipcs && python main.py
```
### 国内环境

## 一键命令
```bash
pkg update && pkg install -y python git curl wget dnsutils jq && pip install requests dnspython aiohttp ping3 rich geoip2 && git clone https://gitee.com/chengege666/ipcs && cd ipcs && python main.py
```
### 分步安装

```bash
# 1. 安装 Termux 依赖
pkg update
pkg install python git curl wget dnsutils jq

# 2. 安装 Python 库
pip install requests dnspython aiohttp ping3 rich geoip2

# 3. 下载项目
git clone https://github.com/chengege666/ipcs
cd ipcs
```
# 4. 删除旧代码残留
```bash
cd ~/ipcs
git pull
python main.py
```
### 运行

```bash
# 交互模式
python main.py

# 快捷模式（自动完成优选）
python main.py example.com
```

---

## 功能模块

| 编号 | 模块 | 说明 |
|------|------|------|
| M01 | 交互菜单 | 终端操作界面，8 大功能入口 |
| M02 | 地区选择 | 10 个地区选项 + 自动检测当前网络位置 |
| M03 | DNS 解析 | A 记录 / AAAA 记录 / CNAME 解析 |
| M04 | IP 扫描 | DNS 结果 + IP 池 + 用户输入多源合并 |
| M05 | Ping 测速 | 并发批量延迟测试，统计均值/抖动 |
| M06 | 丢包检测 | 丢包率计算 + 5 级评级 |
| M07 | TCP 测试 | 多端口 TCP 握手 + TLS 连接时间 |
| M08 | 下载测速 | HTTP/HTTPS 多线程测速（默认 8 线程） |
| M09 | 评分系统 | 5 维度加权综合评分 |
| M10 | 历史记录 | 本地 JSON 持久化，最多保留 100 条 |
| M11 | 结果导出 | TXT / JSON / CSV 三种格式 |
| M12 | 配置管理 | 交互式参数调整 |

---

## 使用指南

### 主菜单

```
================================

  Termux IP 优选工具 v1.0

================================

 1. 域名 IP 优选      ← 输入域名，多地节点综合优选
 2. Cloudflare IP 优选 ← 专项扫描 CF IP 段
 3. CDN 节点测速       ← 追踪 CNAME 后测速
 4. 下载速度测试       ← 单点下载测速
 5. DNS 解析测试       ← 查看域名解析结果
 6. 历史记录           ← 查看历史优选记录
 7. 配置管理           ← 调整各项参数
 8. 地区管理           ← 查看/管理可用地区

 0. 退出
```

### 域名优选流程

1. **选择域名** — 从域名池选择常用域名，或手动输入
2. **选择地区** — 选择目标地区（支持自动检测）
3. **DNS 解析** — 解析域名获取 IP 列表 + CNAME
4. **Ping 测速** — 批量并发延迟测试
5. **丢包检测** — 分析各节点丢包率
6. **TCP 连接测试** — 测试握手 + TLS 连接时间
7. **下载测速** — 对排名靠前的节点进行真实下载测试
8. **综合评分** — 输出排名结果 + 推荐节点
9. **导出结果** — TXT / JSON / CSV 可选

### 地区选择

支持以下目标地区：

| 编号 | 地区 | 代码 |
|------|------|------|
| 1 | 自动选择 | auto |
| 2 | 中国大陆 | cn |
| 3 | 香港 | hk |
| 4 | 台湾 | tw |
| 5 | 日本 | jp |
| 6 | 韩国 | kr |
| 7 | 新加坡 | sg |
| 8 | 美国 | us |
| 9 | 欧洲 | eu |
| 10 | 全球模式 | global |

自动检测模式下，工具会根据当前出口 IP 的地理位置推荐目标地区。

### 域名池

内置常用域名分组，涵盖：
- Cloudflare 系列
- 国际 CDN 加速
- Google 服务
- 微软 / Azure
- GitHub
- 流媒体（Netflix, Disney+ 等）
- 社交网络
- AI / 开发工具

可编辑 `data/domain_pool.json` 自定义域名列表。

---

## 评分系统

### 评分权重

| 维度 | 权重 | 说明 |
|------|------|------|
| 下载速度 | 35% | 真实 HTTP 多线程下载速度 |
| 延迟 | 25% | ICMP Ping 平均延迟 |
| 丢包率 | 15% | ICMP 丢包百分比 |
| 地区匹配 | 15% | IP 地理位置与目标地区匹配度 |
| 稳定性 | 10% | 延迟抖动 / 速度波动率 |

### 丢包评级

| 丢包率 | 评级 |
|--------|------|
| 0% | 优秀 |
| 1-2% | 良好 |
| 3-5% | 一般 |
| 5-10% | 较差 |
| >10% | 淘汰 |

### 排序规则

1. 综合评分（降序）
2. 下载速度（降序）
3. 丢包率（升序）
4. 延迟（升序）

---

## 配置说明

配置文件位于 `~/.ip_optimizer/config.json`，支持以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| ping_count | 20 | 每个 IP 的 Ping 次数 |
| timeout | 5 | 网络请求超时时间（秒） |
| tcp_port | 443 | TCP 测试默认端口 |
| download_size | 50MB | 下载测试文件大小 |
| threads | 8 | 下载测速并发线程数 |
| stable_test_time | 30 | 稳定性测试时长（秒） |
| ip_test_limit | 100 | 最大测试 IP 数 |
| concurrent_ping | 30 | 并发 Ping 数 |

可通过主菜单 **第 7 项 - 配置管理** 交互式调整。

---

## 项目结构

```
ip_optimizer/
├── main.py               # 主入口 / 命令行处理
├── menu.py               # 交互菜单
├── config.py             # 配置管理
├── region.py             # 地区选择 / 自动检测
├── dns.py                # DNS 解析
├── ip_scan.py            # IP 扫描 / 多源合并
├── ping_test.py          # Ping 测速
├── packet_loss.py        # 丢包检测
├── tcp_test.py           # TCP 连接测试
├── speedtest.py          # 下载速度测试
├── stability.py          # 网络稳定性分析
├── geoip.py              # IP 地理信息
├── ranking.py            # 综合评分系统
├── history.py            # 历史记录
├── export.py             # 结果导出
├── utils.py              # 工具函数
├── README.md             # 本文档
└── data/
    ├── regions.json      # 地区数据库
    ├── domain_pool.json  # 域名池
    └── ip_pool/          # IP 池文件
        ├── cn.txt        # 中国大陆
        ├── hk.txt        # 香港
        ├── jp.txt        # 日本
        ├── kr.txt        # 韩国
        ├── sg.txt        # 新加坡
        ├── us.txt        # 美国
        └── eu.txt        # 欧洲
```

---

## 性能指标

| 指标 | 目标 |
|------|------|
| 100 个 IP 完成时间 | < 5 分钟 |
| 并发线程数 | 默认 30 |
| 内存占用 | < 100 MB |
| 历史记录上限 | 100 条 |

---

## 异常处理

| 情况 | 处理方式 |
|------|----------|
| 无网络 | 提示用户检查连接 |
| DNS 解析失败 | 自动重试 |
| IP 不可达 | 跳过，继续测试 |
| 测速超时 | 记录超时 |
| 权限不足 | 提示用户 |
| Termux 后台关闭 | 提醒用户保持前台运行 |

---

## 安全说明

- 无需 Root 权限
- 不会修改系统网络配置
- 所有数据本地保存，不上传
- 不会在后台隐藏运行

---

## 后续规划

### v2.0

- IPv6 优选
- 上传速度测试
- Clash 配置生成
- Sing-box 配置生成

### v3.0

- Web 管理界面
- 自动定时优选
- Telegram 机器人通知
- 云端 IP 数据库

---

## 许可证

MIT License

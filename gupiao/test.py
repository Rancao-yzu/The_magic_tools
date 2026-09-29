#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债持仓实时涨跌 + 加权值计算（只输出统计 + 指数）
数据源：腾讯财经（qt.gtimg.cn）
功能：每 10 分钟自动运行一次，结果追加写入同目录 CSV
"""

import os
import re
import csv
import sys
import time
import urllib.request

# ============================ 持仓数据 ============================
HOLDINGS_TEXT = """
1 113052 兴业转债 116,929,046.14 0.49；
2 118034 晶能转债 85,895,034.25 0.36；
3 110086 精工转债 75,519,905.13 0.32；
4 113054 绿动转债 53,863,444.82 0.23；
5 127108 太能转债 50,148,748.42 0.21；
6 127082 亚科转债 49,841,775.81 0.21；
7 123176 精测转 2 48,838,552.77 0.21；
8 118022 锂科转债 48,485,946.84 0.20；
9 123216 科顺转债 47,806,928.07 0.20；
10 118031 天 23 转债 46,216,005.81 0.19；
11 110073 国投转债 45,553,029.83 0.19；
12 123225 翔丰转债 45,246,343.56 0.19；
13 123257 安克转债 45,155,971.87 0.19；
14 123253 永贵转债 43,666,313.27 0.18；
15 123252 银邦转债 41,397,193.45 0.17；
16 118060 瑞可转债 40,705,006.53 0.17；
17 118058 微导转债 35,930,859.48 0.15；
18 113696 伯 25 转债 35,118,200.00 0.15；
19 113058 友发转债 33,326,612.34 0.14；
20 127056 中特转债 33,167,049.50 0.14；
21 118050 航宇转债 30,703,528.77 0.13；
22 118030 睿创转债 29,552,255.34 0.12；
23 113652 伟 22 转债 29,510,339.16 0.12；
24 127110 广核转债 28,973,228.49 0.12；
25 110090 爱迪转债 28,936,101.99 0.12；
26 123255 鼎龙转债 27,916,945.21 0.12；
27 113666 爱玛转债 27,304,186.88 0.11；
28 113661 福 22 转债 25,838,449.33 0.11；
29 110087 天业转债 25,197,477.05 0.11；
30 113688 国检转债 23,470,472.37 0.10；
31 113694 清源转债 22,114,937.85 0.09；
32 118024 冠宇转债 21,636,829.91 0.09；
33 127046 百润转债 21,522,272.33 0.09；
34 113692 保隆转债 21,403,708.56 0.09；
35 123150 九强转债 20,944,801.02 0.09；
36 118035 国力转债 20,249,784.22 0.09；
37 127105 龙星转债 19,400,497.48 0.08；
38 123258 胜蓝转 02 19,338,796.78 0.08；
39 113678 中贝转债 18,840,817.15 0.08；
40 113691 和邦转债 17,901,418.14 0.08；
41 127068 顺博转债 17,501,410.18 0.07；
42 127102 浙建转债 17,340,327.80 0.07；
43 113056 重银转债 16,810,444.21 0.07；
44 113699 金 25 转债 16,400,093.15 0.07；
45 113655 欧 22 转债 16,277,667.41 0.07；
46 118056 路维转债 16,044,312.12 0.07；
47 113648 巨星转债 15,362,271.88 0.06；
48 111018 华康转债 14,810,199.97 0.06；
49 127103 东南转债 14,033,111.45 0.06；
50 123107 温氏转债 13,812,253.84 0.06；
"""

# ============================ 配置 ============================
INTERVAL = 60                                  # 运行间隔（秒），600 = 10 分钟
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cb_monitor.csv')

INDEX_SYMBOLS = [
    ('sh000001', '上证指数'),
    ('sz399006', '创业板'),
    ('sh000300', '沪深300'),
    ('sh000688', '科创50'),
]

CSV_HEADER = [
    '时间', '上涨', '下跌', '平盘',
    '权重合计%', '加权平均涨跌幅%', '贡献%',
    '上证指数', '上证涨跌幅%',
    '创业板', '创业板涨跌幅%',
    '沪深300', '沪深300涨跌幅%',
    '科创50', '科创50涨跌幅%',
]

ROW_RE = re.compile(r'(\d{6})\s+(.+?)\s+([\d,]+\.\d+)\s+([\d.]+)')


# ============================ 工具函数 ============================
def now_str():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def parse_holdings(text):
    rows = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        m = ROW_RE.search(line)
        if not m:
            print(f'[警告] 无法解析：{line}', file=sys.stderr)
            continue
        code, name, amount, weight = m.groups()
        rows.append({
            'code': code,
            'name': name.replace(' ', ''),
            'amount': float(amount.replace(',', '')),
            'weight': float(weight),
        })
    return rows


def to_symbol(code):
    """110/111/113/118 -> 上交所 sh；123/127/128 -> 深交所 sz"""
    if code[:3] in ('110', '111', '113', '118'):
        return 'sh' + code
    if code[:3] in ('123', '127', '128'):
        return 'sz' + code
    return None


def fetch_quotes(symbols, batch=60, timeout=15, retry=2, tag='行情'):
    """传入如 ['sh113052', 'sz123176', 'sh000001']，返回行情字典"""
    quotes = {}
    total = len(symbols)
    if total == 0:
        return quotes

    batch_cnt = (total + batch - 1) // batch

    for i in range(0, total, batch):
        chunk = symbols[i:i + batch]
        batch_no = i // batch + 1
        url = 'https://qt.gtimg.cn/q=' + ','.join(chunk)

        t0 = time.time()
        raw = None
        for attempt in range(retry + 1):
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Referer': 'https://gu.qq.com/',
                })
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode('gbk', errors='ignore')
                break
            except Exception as e:
                if attempt == retry:
                    print(f'[错误] {now_str()} 行情请求失败：{e}', file=sys.stderr)
                else:
                    time.sleep(1)

        if not raw:
            print(f'【获取】{now_str()} {tag} 第{batch_no}/{batch_cnt}批 请求失败 '
                  f'耗时 {time.time() - t0:.2f}s', file=sys.stderr)
            continue

        before = len(quotes)
        for sym, payload in re.findall(r'v_([a-z]{2}\d{6})="([^"]*)"', raw):
            f = payload.split('~')
            if len(f) < 6:
                continue
            try:
                price = float(f[3])
                prev = float(f[4])
            except ValueError:
                continue
            if price <= 0 or prev <= 0:
                continue
            chg = price - prev
            quotes[sym] = {
                'name': f[1],
                'price': price,
                'prev': prev,
                'chg': chg,
                'pct': chg / prev * 100.0,
            }

        elapsed = time.time() - t0
        got = len(quotes) - before


    return quotes


# ============================ 单次运行 ============================
def run_once():
    """执行一次抓取+统计+打印，返回结果字典（供 CSV 使用）"""
    t_start = time.time()
    run_time = now_str()
    print(f'\n{run_time}')

    rows = parse_holdings(HOLDINGS_TEXT)
    cb_symbols = [s for s in (to_symbol(r['code']) for r in rows) if s]
    quotes = fetch_quotes(cb_symbols, tag='转债')

    total_w = 0.0
    weighted_sum = 0.0
    up = down = flat = 0

    for r in rows:
        sym = to_symbol(r['code'])
        q = quotes.get(sym) if sym else None
        if q is None:
            continue

        pct = q['pct']
        w = r['weight']
        total_w += w
        weighted_sum += w * pct

        if pct > 0:
            up += 1
        elif pct < 0:
            down += 1
        else:
            flat += 1

    avg_pct = None
    contrib = None
    if total_w > 0:
        avg_pct = weighted_sum / total_w
        contrib = weighted_sum / 100.0
        print(f'【统计】上涨 {up} 只 / 下跌 {down} 只 / 平盘 {flat} 只')
        print(f'【权重】覆盖占比合计：{total_w:.2f}%')
        print(f'【加权平均涨跌幅】（按占比归一）：{avg_pct:+.3f}%')
        print(f'【对组合净值的贡献】          ：{contrib:+.4f}%')
    else:
        print('未获取到有效转债行情')

    # 指数行情
    idx_quotes = fetch_quotes([s for s, _ in INDEX_SYMBOLS], tag='指数')
    idx_result = {}
    for sym, label in INDEX_SYMBOLS:
        q = idx_quotes.get(sym)
        if q:
            print(f'{label:6s} {q["price"]:>10.2f}  {q["pct"]:+.2f}%')
            idx_result[label] = (q['price'], q['pct'])
        else:
            print(f'{label:6s} {"--":>10s}  {"--":>6s}')
            idx_result[label] = (None, None)


    return {
        'time': run_time,
        'up': up, 'down': down, 'flat': flat,
        'total_w': total_w,
        'avg_pct': avg_pct,
        'contrib': contrib,
        'indexes': idx_result,
    }


# ============================ CSV ============================
def save_csv(result):
    """把单次结果追加到 CSV；文件不存在则先写表头"""
    file_exists = os.path.exists(CSV_FILE)
    idx = result['indexes']

    def fmt(v, digits=4):
        return '' if v is None else f'{v:.{digits}f}'

    row = [
        result['time'],
        result['up'], result['down'], result['flat'],
        fmt(result['total_w'], 2),
        fmt(result['avg_pct'], 3),
        fmt(result['contrib'], 4),
    ]
    for label in ('上证指数', '创业板', '沪深300', '科创50'):
        price, pct = idx.get(label, (None, None))
        row.append(fmt(price, 2))
        row.append(fmt(pct, 2))

    # utf-8-sig 让 Excel 打开不乱码
    with open(CSV_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)



# ============================ 主循环 ============================
def main():

    try:
        while True:
            cycle_start = time.time()
            try:
                result = run_once()
                save_csv(result)
            except Exception as e:
                print(f'[错误] {now_str()} 本轮运行失败：{e}', file=sys.stderr)

            # 按周期对齐：从本轮开始算起每 INTERVAL 秒跑一次
            elapsed = time.time() - cycle_start
            wait = max(0.0, INTERVAL - elapsed)
            next_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(time.time() + wait))
            print(f'【等待】下次运行：{next_time}  (Ctrl+C 退出)\n')

            try:
                time.sleep(wait)
            except KeyboardInterrupt:
                raise
    except KeyboardInterrupt:
        print('\n【退出】用户中断，已停止定时任务。')


if __name__ == '__main__':
    main()

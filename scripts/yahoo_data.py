# -*- coding: utf-8 -*-
"""Yahoo Finance 数据抓取共享模块（仅 Python 标准库，无第三方依赖）。

本模块封装法国股市（Euronext Paris）行情与基本面数据获取，供其他脚本复用。

两个核心接口：
  1. fetch_chart()        -- OHLCV 历史行情（行情/技术面用），公开接口，无需认证
  2. fetch_quote_summary()-- 估值/基本面指标（PE/PB/股息率/市值/分析师目标价等），需 crumb 认证

Yahoo 代码规则（Euronext Paris）：
  - 法国个股：交易所代码 + ".PA"，如 Airbus=AIR.PA, LVMH=MC.PA
  - 指数：^FCHI(CAC 40), ^SBF120(SBF 120), ^CN20(CAC Next 20)

更多说明见 ../references/data-sources.md
"""
import http.cookiejar
import json
import ssl
import time
import urllib.parse
import urllib.request

BASE = 'https://query1.finance.yahoo.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'}

_opener = None


def _get_opener():
    """带 CookieJar 的 opener（cookie 用于通过 Yahoo 访问风控）。"""
    global _opener
    if _opener is None:
        jar = http.cookiejar.CookieJar()
        _opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return _opener


def _get(url, timeout=20, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with _get_opener().open(req, timeout=timeout) as resp:
                return resp.read().decode('utf-8')
        except Exception as exc:  # noqa: BLE001 - 网络层统一重试
            last = exc
            time.sleep(1)
    raise RuntimeError(f'请求失败 {url}: {last}')


def fetch_crumb():
    """获取 Yahoo Finance 的 crumb 令牌（估值接口必需）。

    流程：先访问 fc.yahoo.com 种下 cookie（页面本身返回 404 属正常），
    再请求 /v1/test/getcrumb。缺少 cookie 时该接口可能返回 401。
    """
    try:
        _get('https://fc.yahoo.com')
    except Exception:  # noqa: BLE001 - 404 等均正常，cookie 已种下即可
        pass
    crumb = _get(f'{BASE}/v1/test/getcrumb').strip()
    if not crumb:
        raise RuntimeError('获取 crumb 失败')
    return crumb


def fetch_chart(ticker, rng='1y', interval='1d'):
    """拉取 OHLCV 历史行情。

    参数:
        ticker: Yahoo 代码，如 'AIR.PA' / '^FCHI'
        rng:   时间范围，'1d'/'5d'/'1mo'/'3mo'/'6mo'/'1y'/'2y'/'5y'/'max'
        interval: 周期，'1d'/'1wk'/'1mo'

    返回:
        dict: {ticker, meta, timestamps, open, high, low, close, volume}
    """
    url = (f'{BASE}/v8/finance/chart/{urllib.parse.quote(ticker)}'
           f'?range={rng}&interval={interval}')
    data = json.loads(_get(url))
    res = data['chart']['result'][0]
    quote = res['indicators']['quote'][0]
    return {
        'ticker': ticker,
        'meta': res.get('meta', {}),
        'timestamps': res.get('timestamp', []),
        'open': quote.get('open', []),
        'high': quote.get('high', []),
        'low': quote.get('low', []),
        'close': quote.get('close', []),
        'volume': quote.get('volume', []),
    }


def fetch_quote_summary(ticker, modules=None, crumb=None):
    """拉取估值/基本面数据（需要 crumb）。

    参数:
        ticker: Yahoo 代码
        modules: 需要的模块名列表，默认覆盖估值与基本面核心字段
        crumb: 可复用已获取的 crumb（批量抓取时传入以省去重复认证请求）

    返回:
        dict: quoteSummary 的 result[0]，字段均为 {raw, fmt} 结构
    """
    if modules is None:
        modules = ['summaryDetail', 'defaultKeyStatistics', 'financialData',
                   'price', 'summaryProfile', 'earningsTrend', 'calendarEvents']
    if crumb is None:
        crumb = fetch_crumb()
    url = (f'{BASE}/v10/finance/quoteSummary/{urllib.parse.quote(ticker)}'
           f'?modules={",".join(modules)}&crumb={urllib.parse.quote(crumb)}')
    data = json.loads(_get(url))
    err = data.get('error')
    if err:
        raise RuntimeError(f'quoteSummary 返回错误: {err}')
    return data['quoteSummary']['result'][0]


def deep_get(obj, *keys):
    """按路径逐层取字段；遇到 {raw:...} 结构返回 raw。取不到或值为空返回 None。"""
    cur = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    if isinstance(cur, dict):
        return cur.get('raw') if 'raw' in cur else None
    return cur


def format_money(value):
    """把数值格式化为人类可读的金额/市值字符串。"""
    if value is None:
        return 'N/A'
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 'N/A'
    if abs(value) >= 1e12:
        return f'{value / 1e12:.2f}T'
    if abs(value) >= 1e9:
        return f'{value / 1e9:.2f}B'
    if abs(value) >= 1e6:
        return f'{value / 1e6:.2f}M'
    return f'{value:,.0f}'


def format_pct(value, scale=100):
    """把小数(如 0.0157)转为百分比字符串；Yahoo 的股息率/利润率常为小数。"""
    if value is None:
        return 'N/A'
    try:
        return f'{float(value) * scale:.2f}%'
    except (TypeError, ValueError):
        return 'N/A'

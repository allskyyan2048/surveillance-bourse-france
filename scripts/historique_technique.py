# -*- coding: utf-8 -*-
"""Historique et indicateurs techniques (indices & actions françaises).

Fonctions :
  - Performances par période (1j / 1sem / 1mois / 3mois / 6mois / 1an / YTD) et plus haut/bas 52 sem.
  - Indicateurs techniques : MA20/50/200, RSI(14), MACD (DIF/DEA/histogramme), supports/résistances
  - Signal de tendance global (haussière / baissière / neutre)

Usage :
  python historique_technique.py AIR.PA
  python historique_technique.py AIR.PA --range 1y --json
  python historique_technique.py ^FCHI

Code de retour : 0 = succès ; 1 = échec.
"""
import argparse
import json
import math  # noqa: F401
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yahoo_data as yd


def sma(values, n):
    out = [None] * len(values)
    s = 0.0
    for i, x in enumerate(values):
        s += x
        if i >= n:
            s -= values[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(values, n):
    k = 2.0 / (n + 1)
    out = []
    prev = None
    for x in values:
        prev = x if prev is None else x * k + prev * (1 - k)
        out.append(prev)
    return out


def rsi(values, n=14):
    out = [None] * len(values)
    if len(values) <= n:
        return out
    gains, losses = [], []
    for i in range(len(values)):
        if i == 0:
            gains.append(0.0)
            losses.append(0.0)
        else:
            ch = values[i] - values[i - 1]
            gains.append(max(ch, 0.0))
            losses.append(max(-ch, 0.0))
    ag = sum(gains[1:n + 1]) / n
    al = sum(losses[1:n + 1]) / n
    out[n] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    for i in range(n + 1, len(values)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


def macd(values, fast=12, slow=26, signal=9):
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    dif = [a - b for a, b in zip(ema_fast, ema_slow)]
    dea = ema(dif, signal)
    hist = [a - b for a, b in zip(dif, dea)]
    return dif, dea, hist


def ts_to_date(ts):
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
    except (ValueError, OSError, OverflowError):
        return '?'


def perf_signal(dif, dea, hist, rsi_val, price, ma20, ma200):
    """Signal technique : retourne (label, raisons)."""
    reasons = []
    if price is None:
        return 'données insuffisantes', reasons
    if ma20 and ma200:
        if price > ma20 > ma200:
            reasons.append('Prix > MA20 > MA200 (alignement haussier)')
        elif price < ma20 < ma200:
            reasons.append('Prix < MA20 < MA200 (alignement baissier)')
        else:
            reasons.append('Moyennes mobiles entremêlées')
    if rsi_val is not None:
        if rsi_val >= 70:
            reasons.append(f'RSI {rsi_val:.0f} (surachat)')
        elif rsi_val <= 30:
            reasons.append(f'RSI {rsi_val:.0f} (survente)')
        else:
            reasons.append(f'RSI {rsi_val:.0f} (neutre)')
    if hist is not None and dif is not None and dea is not None:
        if dif > dea and hist > 0:
            reasons.append('MACD croix haussière')
        elif dif < dea and hist < 0:
            reasons.append('MACD croix baissière')
        else:
            reasons.append('MACD plat')
    bullish = sum(1 for r in reasons if 'haussi' in r or 'survente' in r)
    bearish = sum(1 for r in reasons if 'baissi' in r or 'surachat' in r)
    if bullish > bearish:
        return 'haussière', reasons
    if bearish > bullish:
        return 'baissière', reasons
    return 'neutre', reasons


def _setup_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:  # noqa: BLE001
            pass


def _f(x, nd=2):
    return f'{x:.{nd}f}' if x is not None else 'N/A'


def main():
    _setup_stdout()
    ap = argparse.ArgumentParser(description='Historique et indicateurs techniques (France)')
    ap.add_argument('ticker', help='Code Yahoo, ex. AIR.PA / ^FCHI')
    ap.add_argument('--range', default='1y', help='Plage historique, défaut 1y')
    ap.add_argument('--json', action='store_true', help='Sortie JSON')
    args = ap.parse_args()

    try:
        c = yd.fetch_chart(args.ticker, rng=args.range, interval='1d')
    except Exception as e:  # noqa: BLE001
        print(f'Échec de récupération {args.ticker} : {e}', file=sys.stderr)
        return 1

    meta = c['meta']
    ts = c['timestamps']
    closes = c['close']
    highs = [h for h in c['high'] if h is not None]
    lows = [lo for lo in c['low'] if lo is not None]

    valid = [(t, px) for t, px in zip(ts, closes) if px is not None]
    if not valid:
        print(f'{args.ticker} : aucune donnée de cours valide', file=sys.stderr)
        return 1
    dates = [ts_to_date(t) for t, _ in valid]
    px = [p for _, p in valid]

    price = px[-1] if px else None
    prev = px[-2] if len(px) >= 2 else None
    change = (price - prev) if (price is not None and prev) else None
    chg_pct = (change / prev * 100) if change is not None and prev else None

    def ret_n(n):
        return (price / px[-1 - n] - 1) * 100 if len(px) > n and price else None

    ytd_base = None
    cur_year = dates[-1][:4] if dates else None
    for i, d in enumerate(dates):
        if d[:4] == cur_year:
            ytd_base = px[i]
            break
    ytd = (price / ytd_base - 1) * 100 if price and ytd_base else None

    ma20 = sma(px, 20)
    ma50 = sma(px, 50)
    ma200 = sma(px, 200)
    rsi_vals = rsi(px, 14)
    dif, dea, hist = macd(px)

    high52 = max(highs[-252:]) if highs else None
    low52 = min(lows[-252:]) if lows else None
    high3m = max(highs[-63:]) if highs else None
    low3m = min(lows[-63:]) if lows else None

    signal, reasons = perf_signal(dif[-1], dea[-1], hist[-1], rsi_vals[-1], price, ma20[-1], ma200[-1])

    result = {
        'ticker': args.ticker,
        'name': meta.get('shortName') or meta.get('longName') or args.ticker,
        'currency': meta.get('currency'),
        'as_of': dates[-1] if dates else None,
        'price': price, 'change': change, 'change_pct': chg_pct,
        'performance_pct': {
            '1d': change / prev * 100 if (change is not None and prev) else None,
            '1w': ret_n(5), '1m': ret_n(21), '3m': ret_n(63), '6m': ret_n(126),
            '1y': ret_n(252) if len(px) > 252 else (price / px[0] - 1) * 100 if px else None,
            'ytd': ytd,
        },
        'technical': {
            'ma20': ma20[-1], 'ma50': ma50[-1], 'ma200': ma200[-1],
            'rsi14': rsi_vals[-1],
            'macd_dif': dif[-1], 'macd_dea': dea[-1], 'macd_hist': hist[-1],
            'high52': high52, 'low52': low52,
            'support_3m': low3m, 'resistance_3m': high3m,
            'signal': signal, 'reasons': reasons,
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'\n=== {result["name"]} ({args.ticker}) — données au {result["as_of"]} ===')
        print(f'Dernier cours : {_f(price, 2)} {meta.get("currency")}   Variation : {_f(change, 3)} ({_f(chg_pct, 2)} %)')
        p = result['performance_pct']
        print('\nPerformances par période :')
        print(f'  1j {_f(p["1d"], 2)} % | 1 sem. {_f(p["1w"], 2)} % | 1 mois {_f(p["1m"], 2)} % | 3 mois {_f(p["3m"], 2)} % '
              f'| 6 mois {_f(p["6m"], 2)} % | 1 an {_f(p["1y"], 2)} % | YTD {_f(p["ytd"], 2)} %')
        t = result['technical']
        print('\nIndicateurs techniques :')
        print(f'  MA20 {_f(t["ma20"], 2)} | MA50 {_f(t["ma50"], 2)} | MA200 {_f(t["ma200"], 2)}')
        print(f'  RSI14 {_f(t["rsi14"], 1)} | MACD DIF {_f(t["macd_dif"], 2)} / DEA {_f(t["macd_dea"], 2)} / Hist. {_f(t["macd_hist"], 2)}')
        print(f'  Haut 52 sem. {_f(t["high52"], 2)} / bas {_f(t["low52"], 2)} | Support 3 mois {_f(t["support_3m"], 2)} / résistance {_f(t["resistance_3m"], 2)}')
        print(f'\nSignal : {t["signal"]}')
        for r in t['reasons']:
            print(f'  - {r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

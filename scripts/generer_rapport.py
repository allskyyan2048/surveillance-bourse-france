# -*- coding: utf-8 -*-
"""Générateur de rapport boursier français en HTML (autonome, portable).

Point d'entrée principal du skill « surveillance-bourse-france ».
Il récupère les données de marché (indices, historique du CAC 40, valeurs,
univers de croissance), calcule les indicateurs techniques, les rendements
annualisés attendus (dividende + objectif de cours), puis génère un rapport
HTML **auto-contenu** (ECharts embarqué) au format du modèle fourni.

Portable : Python 3.8+ standard uniquement, aucune dépendance tierce,
fonctionne sous Windows / macOS / Linux, depuis n'importe quel répertoire.

Usage :
  python generer_rapport.py --sortie rapport.html                  # rapport complet par défaut
  python generer_rapport.py --tickers AIR.PA,MC.PA,TTE.PA          # valeurs personnalisées
  python generer_rapport.py --news actualites.json                 # injecter des actualités
  python generer_rapport.py --sans-portefeuille                    # désactiver module portefeuille
  python generer_rapport.py --donnees donnees.json                 # réutiliser un cache de données
  python generer_rapport.py --sortie-json donnees.json             # ne sauvegarder que les données

Code de retour : 0 = succès ; 1 = erreur.
"""
import argparse
import json
import math  # noqa: F401
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import yahoo_data as yd
from apercu_marche import build_index_row, build_stock_row, DEFAULT_INDICES, DEFAULT_WATCHLIST, NOMS_FR as NOMS_APERCU  # noqa: F401
from historique_technique import sma, rsi, macd, ts_to_date, perf_signal  # noqa: F401
from univers_croissance import build as build_univers, CANDIDATES, NOMS_FR as NOMS_UNIVERS  # noqa: F401

TEMPLATE = os.path.join(SKILL, 'templates', 'rapport_modele.html')
LIB_ECHARTS = os.path.join(SKILL, 'lib', 'echarts.min.js')


def _safe(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def _r(x, nd=2):
    return round(x, nd) if x is not None else None


def fetch_cac40_serie():
    """Historique 1 an du CAC 40 (clôtures + MA20/50/200) pour le graphique principal."""
    c = yd.fetch_chart('^FCHI', rng='1y', interval='1d')
    ts, closes = c['timestamps'], c['close']
    dates, px = [], []
    for t, p in zip(ts, closes):
        if p is None:
            continue
        dates.append(ts_to_date(t))
        px.append(p)
    if not px:
        raise RuntimeError('CAC 40 : aucune donnée de cours')
    ma20 = sma(px, 20)
    ma50 = sma(px, 50)
    ma200 = sma(px, 200)
    return {
        'dates': dates,
        'close': [_r(x) for x in px],
        'ma20': [_r(x) if x is not None else None for x in ma20],
        'ma50': [_r(x) if x is not None else None for x in ma50],
        'ma200': [_r(x) if x is not None else None for x in ma200],
    }


def fetch_indices():
    rows = []
    for t in DEFAULT_INDICES:
        try:
            rows.append(build_index_row(t))
        except Exception:  # noqa: BLE001
            pass
    return rows


def fetch_stocks(tickers):
    rows = []
    for t in tickers:
        try:
            rows.append(build_stock_row(t))
        except Exception:  # noqa: BLE001
            pass
    return rows


def fetch_technical():
    """Indicateurs techniques du CAC 40 + performances par période."""
    c = yd.fetch_chart('^FCHI', rng='1y', interval='1d')
    ts, closes, highs, lows = c['timestamps'], c['close'], c['high'], c['low']
    valid = [(t, p) for t, p in zip(ts, closes) if p is not None]
    dates = [ts_to_date(t) for t, _ in valid]
    px = [p for _, p in valid]
    price = px[-1]
    prev = px[-2]
    def ret_n(n):
        return (price / px[-1 - n] - 1) * 100 if len(px) > n else None
    ytd_base = None
    cur_year = dates[-1][:4]
    for i, d in enumerate(dates):
        if d[:4] == cur_year:
            ytd_base = px[i]
            break
    ytd = (price / ytd_base - 1) * 100 if ytd_base else None
    m20, m50, m200 = sma(px, 20), sma(px, 50), sma(px, 200)
    rsi14 = rsi(px, 14)
    dif, dea, hist = macd(px)
    h52 = max(x for x in highs if x is not None)
    l52 = min(x for x in lows if x is not None)
    h3m = max(x for x in highs[-63:] if x is not None)
    l3m = min(x for x in lows[-63:] if x is not None)
    signal, reasons = perf_signal(dif[-1], dea[-1], hist[-1], rsi14[-1], price, m20[-1], m200[-1])
    return {
        'price': _r(price), 'change_pct': _r((price / prev - 1) * 100, 2),
        'perf': {'1w': _r(ret_n(5)), '1m': _r(ret_n(21)), '3m': _r(ret_n(63)),
                 '6m': _r(ret_n(126)), '1y': _r(ret_n(252)), 'ytd': _r(ytd)},
        'tech': {'ma20': _r(m20[-1]), 'ma50': _r(m50[-1]), 'ma200': _r(m200[-1]),
                 'rsi': _r(rsi14[-1], 1), 'macd_dif': _r(dif[-1]), 'macd_dea': _r(dea[-1]),
                 'macd_hist': _r(hist[-1]), 'high52': _r(h52), 'low52': _r(l52),
                 'support': _r(l3m), 'resistance': _r(h3m), 'signal': signal, 'reasons': reasons},
    }


def fetch_univers(tickers=None):
    """Univers de croissance : rendements annualisés attendus en trois scénarios."""
    if tickers:
        candidates = [(t.strip().upper(), 'inconnu') for t in tickers.split(',') if t.strip()]
    else:
        candidates = CANDIDATES
    crumb = yd.fetch_crumb()
    rows = []
    for t, sector in candidates:
        try:
            rows.append(build_univers(t, sector, crumb))
        except Exception:  # noqa: BLE001
            pass
    return rows


def auto_these(x):
    """Génère une thèse (positionnement / arguments / risques) en français à partir des données."""
    dy = (x.get('div_yield') or 0) * 100
    eps = (x.get('eps_growth') or 0) * 100
    price = x.get('price')
    tm = x.get('target_mean')
    up = ((tm - price) / price * 100) if (price and tm) else None
    na = x.get('analyst_count')
    pef = x.get('pe_forward')

    if dy >= 4.5 and eps >= 8:
        pos = 'Défensif & rendement + croissance'
    elif dy >= 4.5:
        pos = 'Défensif à haut rendement'
    elif eps >= 10:
        pos = 'Croissance & revalorisation'
    elif eps >= 0:
        pos = 'Valeur & rendement'
    else:
        pos = 'Élastique (retournement)'

    args = (f'Cours {price:.2f} €, rendement {dy:.2f} %, PE prévisionnel '
            f'{pef:.1f} (si dispo), croissance du BPA {eps:+.1f} %.')
    if up is not None:
        args += f' Potentiel vs objectif moyen {up:+.1f} %'
        if na:
            args += f' (consensus {na} analystes)'
        args += '.'
    risques = 'Divergence possible des objectifs selon les analystes.'
    if x.get('exp_pessimistic') is not None and x.get('exp_pessimistic') < 0:
        risques += ' Scénario pessimiste négatif : forte volatilité à prévoir.'
    if x.get('sector') == 'Automobile' or x.get('sector') == 'Acier' or x.get('sector') == 'Semi-conducteurs':
        risques += ' Secteur cyclique : les bénéfices sont sensibles au cycle.'
    return {'position': pos, 'these': args, 'risques': risques}


def build_recommandations(univers):
    """Top 5 par rendement annualisé attendu (scénario de base), avec qualité/diversification."""
    ok = [x for x in univers if x.get('exp_base') is not None and x.get('price')]
    ok.sort(key=lambda x: x['exp_base'], reverse=True)
    rec = []
    seen_sectors = set()
    for x in ok:
        if len(rec) >= 5:
            break
        rec.append(x)
    top5 = rec[:5]
    data = []
    for x in top5:
        th = auto_these(x)
        data.append({
            'ticker': x['ticker'], 'name': x['name'], 'sector': x['sector'],
            'price': _r(x['price']), 'dy': _r((x.get('div_yield') or 0) * 100),
            'pe_f': _r(x.get('pe_forward')), 'eps_g': _r((x.get('eps_growth') or 0) * 100),
            'exp_p': _r(x.get('exp_pessimistic') * 100), 'exp_b': _r(x.get('exp_base') * 100),
            'exp_o': _r(x.get('exp_optimistic') * 100),
            'position': th['position'], 'these': th['these'], 'risques': th['risques'],
        })
    return data


def build_portefeuille(rec5):
    """Portefeuille équipondéré (20 % x 5) et rendements annualisés attendus en trois scénarios."""
    if not rec5:
        return None
    n = len(rec5)
    return {
        'names': [x['name'] for x in rec5],
        'weight': round(100.0 / n, 1),
        'exp_p': _r(sum(x['exp_p'] for x in rec5) / n),
        'exp_b': _r(sum(x['exp_b'] for x in rec5) / n),
        'exp_o': _r(sum(x['exp_o'] for x in rec5) / n),
    }


def build_scenarios(tech):
    """Trois scénarios de marché (fourchettes cibles du CAC 40) à partir des niveaux techniques."""
    price = tech['price']
    sup = tech['tech']['support']
    res = tech['tech']['resistance']
    h52 = tech['tech']['high52']
    m200 = tech['tech']['ma200']
    base_lo = round(min(price * 0.98, sup) if sup else price * 0.98)
    base_hi = round(max(price * 1.02, res) if res else price * 1.02)
    opt_hi = round(max(res, h52) * 1.01) if (res or h52) else round(price * 1.06)
    opt_lo = round(base_hi)
    pes_lo = round(min(sup, m200) * 0.99) if (sup and m200) else round(price * 0.95)
    pes_hi = round(base_lo)
    return {
        'base': f'{base_lo} – {base_hi}',
        'optimiste': f'{opt_lo} – {opt_hi}',
        'pessimiste': f'{pes_lo} – {pes_hi}',
    }


def load_news(path):
    """Charge un fichier JSON d'actualités : [{titre, tag, description, source}]."""
    if not path:
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get('actualites') or data.get('news') or []
    return data


def _setup_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:  # noqa: BLE001
            pass


def main():
    _setup_stdout()
    ap = argparse.ArgumentParser(description='Génère un rapport boursier français en HTML')
    ap.add_argument('--tickers', default=None, help='Valeurs personnalisées (virgules)')
    ap.add_argument('--news', default=None, help='Fichier JSON d\'actualités à injecter')
    ap.add_argument('--sortie', default='rapport_bourse_france.html', help='Fichier HTML de sortie')
    ap.add_argument('--sortie-json', default=None, help='Ne sauvegarder que les données JSON')
    ap.add_argument('--donnees', default=None, help='Réutiliser un cache de données JSON')
    ap.add_argument('--sans-portefeuille', action='store_true', help='Désactiver le module portefeuille')
    args = ap.parse_args()

    if args.donnees and os.path.exists(args.donnees):
        with open(args.donnees, encoding='utf-8') as f:
            DATA = json.load(f)
        print(f'Données chargées depuis {args.donnees}')
    else:
        print('Récupération des données de marché (Yahoo Finance)…')
        tickers = args.tickers.split(',') if args.tickers else None
        DATA = {
            'as_of': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'indices': fetch_indices(),
            'cac40': fetch_cac40_serie(),
            'tech_info': fetch_technical(),
            'stocks': fetch_stocks(tickers if tickers else DEFAULT_WATCHLIST),
            'univers': fetch_univers(tickers),
        }
        # Dérivés : recommandations + portefeuille
        rec5 = build_recommandations(DATA['univers'])
        DATA['rec5'] = rec5
        DATA['portfolio'] = None if args.sans_portefeuille else build_portefeuille(rec5)
        DATA['scenarios'] = build_scenarios(DATA['tech_info'])

    if args.sortie_json:
        with open(args.sortie_json, 'w', encoding='utf-8') as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
        print(f'Données sauvegardées : {os.path.abspath(args.sortie_json)}')
        return 0

    # Injecter les actualités éventuelles
    DATA['news'] = load_news(args.news)

    # Lire le modèle HTML
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()

    # Remplacer les marqueurs
    data_json = json.dumps(DATA, ensure_ascii=False)
    html = html.replace('__DONNEES__', data_json)
    if os.path.exists(LIB_ECHARTS):
        with open(LIB_ECHARTS, encoding='utf-8') as f:
            html = html.replace('__ECHARTS_LIB__', f.read())
    else:
        html = html.replace('__ECHARTS_LIB__', '/* ECharts introuvable : les graphiques ne seront pas rendus */')

    out_path = os.path.abspath(args.sortie)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Rapport généré : {out_path}')
    print(f'Indices: {len(DATA["indices"])} | Valeurs: {len(DATA["stocks"])} | Recommandations: {len(DATA["rec5"])}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

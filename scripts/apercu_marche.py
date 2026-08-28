# -*- coding: utf-8 -*-
"""Aperçu du marché français (Euronext Paris) : indices + actions.

Fonctions :
  - Indices : CAC 40 / SBF 120 / CAC Next 20 — dernier cours, variation, plus haut/bas 52 semaines
  - Actions : dernier cours, variation, PE (trailing/forward), PB, rendement du dividende,
    capitalisation, objectif de cours moyen et recommandation des analystes

Usage :
  python apercu_marche.py                            # indices + liste de suivi par défaut
  python apercu_marche.py --tickers AIR.PA,MC.PA     # actions personnalisées
  python apercu_marche.py --indices-only             # indices uniquement
  python apercu_marche.py --json                     # sortie JSON (pour parsing)

Code de retour : 0 = succès ; 1 = échec complet ; 2 = échec partiel.
"""
import argparse
import json
import os
import sys

# Import du module de données local (fonctionne depuis n'importe quel répertoire)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yahoo_data as yd

DEFAULT_INDICES = ['^FCHI', '^SBF120', '^CN20']
DEFAULT_WATCHLIST = [
    'AIR.PA', 'MC.PA', 'OR.PA', 'TTE.PA', 'SAN.PA', 'SAF.PA',
    'SU.PA', 'AI.PA', 'BNP.PA', 'CS.PA', 'DG.PA', 'RI.PA',
]

NOMS_FR = {
    '^FCHI': 'CAC 40', '^SBF120': 'SBF 120', '^CN20': 'CAC Next 20',
    'AIR.PA': 'Airbus', 'MC.PA': 'LVMH', 'OR.PA': 'L\'Oréal', 'TTE.PA': 'TotalEnergies',
    'SAN.PA': 'Sanofi', 'SAF.PA': 'Safran', 'SU.PA': 'Schneider Electric', 'AI.PA': 'Air Liquide',
    'BNP.PA': 'BNP Paribas', 'CS.PA': 'AXA', 'DG.PA': 'Vinci', 'RI.PA': 'Pernod Ricard',
    'KER.PA': 'Kering', 'EL.PA': 'EssilorLuxottica', 'RMS.PA': 'Hermès', 'GLE.PA': 'Société Générale',
    'ACA.PA': 'Crédit Agricole', 'BN.PA': 'Danone', 'CA.PA': 'Carrefour', 'ORA.PA': 'Orange',
    'EN.PA': 'Bouygues', 'ENGI.PA': 'Engie', 'VIE.PA': 'Veolia Environnement', 'STLAP.PA': 'Stellantis',
    'CAP.PA': 'Capgemini', 'DSY.PA': 'Dassault Systèmes', 'STMPA.PA': 'STMicroelectronics',
    'ML.PA': 'Michelin', 'RNO.PA': 'Renault', 'AM.PA': 'Dassault Aviation', 'HO.PA': 'Thales',
    'PUB.PA': 'Publicis', 'SGO.PA': 'Saint-Gobain', 'LR.PA': 'Legrand', 'URW.PA': 'Unibail-Rodamco-Westfield',
    'AC.PA': 'Accor', 'GET.PA': 'Getlink', 'VIV.PA': 'Vivendi', 'BB.PA': 'BNP Paribas (ex)',
}


def _safe_float(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def build_index_row(ticker):
    """Ligne d'indice : interface chart uniquement (rapide, sans crumb)."""
    c = yd.fetch_chart(ticker, rng='1y', interval='1d')
    meta = c['meta']
    closes = [x for x in c['close'] if x is not None]
    price = closes[-1] if closes else _safe_float(meta.get('regularMarketPrice'))
    prev = closes[-2] if len(closes) >= 2 else None
    change = (price - prev) if (price is not None and prev) else None
    chg_pct = (change / prev * 100) if change is not None and prev else None
    return {
        'ticker': ticker,
        'name': NOMS_FR.get(ticker, meta.get('shortName') or meta.get('longName') or ticker),
        'currency': meta.get('currency'),
        'price': price, 'change': change, 'change_pct': chg_pct,
        'high52': _safe_float(meta.get('fiftyTwoWeekHigh')),
        'low52': _safe_float(meta.get('fiftyTwoWeekLow')),
    }


def build_stock_row(ticker):
    """Ligne d'action : chart (cours) + quoteSummary (valorisation)."""
    c = yd.fetch_chart(ticker, rng='1y', interval='1d')
    meta = c['meta']
    closes = [x for x in c['close'] if x is not None]
    price = closes[-1] if closes else _safe_float(meta.get('regularMarketPrice'))
    prev = closes[-2] if len(closes) >= 2 else None
    change = (price - prev) if (price is not None and prev) else None
    chg_pct = (change / prev * 100) if change is not None and prev else None

    q = yd.fetch_quote_summary(ticker)
    sd, dks, fd, pd = q.get('summaryDetail', {}), q.get('defaultKeyStatistics', {}), q.get('financialData', {}), q.get('price', {})
    return {
        'ticker': ticker,
        'name': NOMS_FR.get(ticker, meta.get('shortName') or meta.get('longName') or ticker),
        'currency': meta.get('currency'),
        'price': price, 'change': change, 'change_pct': chg_pct,
        'high52': _safe_float(yd.deep_get(sd, 'fiftyTwoWeekHigh')) or _safe_float(meta.get('fiftyTwoWeekHigh')),
        'low52': _safe_float(yd.deep_get(sd, 'fiftyTwoWeekLow')) or _safe_float(meta.get('fiftyTwoWeekLow')),
        'market_cap': yd.deep_get(pd, 'marketCap') or yd.deep_get(dks, 'marketCap'),
        'pe_trailing': yd.deep_get(sd, 'trailingPE'),
        'pe_forward': yd.deep_get(sd, 'forwardPE'),
        'pb': yd.deep_get(sd, 'priceToBook') or yd.deep_get(dks, 'priceToBook'),
        'div_yield': yd.deep_get(sd, 'dividendYield') or yd.deep_get(dks, 'dividendYield'),
        'beta': yd.deep_get(sd, 'beta'),
        'target_mean': yd.deep_get(fd, 'targetMeanPrice'),
        'target_high': yd.deep_get(fd, 'targetHighPrice'),
        'target_low': yd.deep_get(fd, 'targetLowPrice'),
        'recommendation': yd.deep_get(fd, 'recommendationKey'),
        'analyst_count': yd.deep_get(fd, 'numberOfAnalystOpinions'),
        'free_cashflow': yd.deep_get(fd, 'freeCashflow'),
        'revenue_growth': yd.deep_get(fd, 'revenueGrowth'),
        'earnings_growth': yd.deep_get(fd, 'earningsGrowth'),
    }


def _fmt(x, nd=2, suffix=''):
    return f'{x:.{nd}f}{suffix}' if x is not None else 'N/A'


def _fmt_big(x):
    return yd.format_money(x)


def print_index_table(rows):
    print('\n=== Indices de la Bourse de Paris ===')
    print(f'{"Indice":<16}{"Cours":>10}{"Var.":>10}{"Var. %":>9}{"Haut 52s":>11}{"Bas 52s":>11}')
    for r in rows:
        print(f'{r["name"]:<16}{_fmt(r["price"]):>10}{_fmt(r["change"],3):>10}{_fmt(r["change_pct"],2,"%"):>9}'
              f'{_fmt(r["high52"]):>11}{_fmt(r["low52"]):>11}')


def print_stock_table(rows):
    print('\n=== Cours et valorisation des actions ===')
    print(f'{"Action":<18}{"Cours":>9}{"Var.%":>8}{"PE(tr)":>8}{"PE(fwd)":>8}{"PB":>7}{"Rend.":>8}'
          f'{"Cap.":>10}{"Obj. moy":>9}{"Note":>10}')
    for r in rows:
        rec = r['recommendation'] or 'N/A'
        print(f'{r["name"]:<18}{_fmt(r["price"]):>9}{_fmt(r["change_pct"],2,"%"):>8}'
              f'{_fmt(r["pe_trailing"]):>8}{_fmt(r["pe_forward"]):>8}{_fmt(r["pb"]):>7}'
              f'{yd.format_pct(r["div_yield"]):>8}{_fmt_big(r["market_cap"]):>10}'
              f'{_fmt(r["target_mean"]):>9}{rec:>10}')


def _setup_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:  # noqa: BLE001
            pass


def main():
    _setup_stdout()
    ap = argparse.ArgumentParser(description='Aperçu du marché boursier français')
    ap.add_argument('--tickers', help='Codes Yahoo séparés par des virgules (remplace la liste par défaut)')
    ap.add_argument('--indices-only', action='store_true', help='Indices uniquement')
    ap.add_argument('--stocks-only', action='store_true', help='Actions uniquement')
    ap.add_argument('--json', action='store_true', help='Sortie JSON')
    args = ap.parse_args()

    indices = [] if args.stocks_only else DEFAULT_INDICES
    stocks = [] if args.indices_only else (args.tickers.split(',') if args.tickers else DEFAULT_WATCHLIST)

    out = {'indices': [], 'stocks': []}
    errors = []
    for t in indices:
        try:
            out['indices'].append(build_index_row(t))
        except Exception as e:  # noqa: BLE001
            errors.append(f'{t}: {e}')
    for t in stocks:
        try:
            out['stocks'].append(build_stock_row(t))
        except Exception as e:  # noqa: BLE001
            errors.append(f'{t}: {e}')

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if out['indices']:
            print_index_table(out['indices'])
        if out['stocks']:
            print_stock_table(out['stocks'])
        for e in errors:
            print(f'[Échec] {e}', file=sys.stderr)

    if len(errors) == (len(indices) + len(stocks)) and (indices or stocks):
        return 1
    if errors:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())

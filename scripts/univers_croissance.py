# -*- coding: utf-8 -*-
"""Univers de croissance : données de croissance/valorisation pour la sélection à haut rendement.

Pour chaque action candidate, récupère : croissance du BPA, croissance du CA, ROE, marge,
objectif de cours / recommandation des analystes, rendement du dividende, PE, etc.
Puis calcule le **rendement annualisé attendu en trois scénarios**
( = rendement du dividende + potentiel vs objectif de cours des analystes) :
  - exp_pessimistic (pessimiste)  = rendement + (objectif bas  − cours)/cours
  - exp_base (base)               = rendement + (objectif moyen − cours)/cours
  - exp_optimistic (optimiste)    = rendement + (objectif haut  − cours)/cours

Sortie : univers_croissance.json (par défaut dans le répertoire courant ; --out pour personnaliser).

Usage (portable : Python 3.8+ standard, aucune dépendance tierce) :
  python univers_croissance.py                              # univers par défaut → univers_croissance.json
  python univers_croissance.py --out /tmp/u.json            # chemin de sortie
  python univers_croissance.py --tickers AIR.PA,MC.PA       # univers personnalisé
  python univers_croissance.py --print                      # impression des 10 premiers

Code de retour : 0 = tout OK ; 1 = échec partiel ; 2 = échec complet.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yahoo_data as yd

# Univers par défaut : grandes valeurs du CAC 40 par secteur (le secteur sert à la diversification)
CANDIDATES = [
    ('AIR.PA', 'Aéronautique'), ('SAF.PA', 'Aéronautique'), ('MC.PA', 'Luxe'), ('OR.PA', 'Luxe'),
    ('RMS.PA', 'Luxe'), ('KER.PA', 'Luxe'), ('SU.PA', 'Électricité'), ('LR.PA', 'Électricité'),
    ('AI.PA', 'Gaz industriels'), ('DG.PA', 'Infrastructures'), ('SGO.PA', 'Matériaux'), ('BNP.PA', 'Banques'),
    ('GLE.PA', 'Banques'), ('ACA.PA', 'Banques'), ('CS.PA', 'Assurances'), ('TTE.PA', 'Énergie'),
    ('ENGI.PA', 'Utilities'), ('VIE.PA', 'Utilities'), ('EN.PA', 'Construction'), ('SAN.PA', 'Pharmacie'),
    ('RI.PA', 'Spiritueux'), ('CA.PA', 'Distribution'), ('ML.PA', 'Équip. auto'), ('STMPA.PA', 'Semi-conducteurs'),
    ('CAP.PA', 'Conseil'), ('DSY.PA', 'Logiciels'), ('EL.PA', 'Optique'), ('ORA.PA', 'Télécoms'),
    ('RNO.PA', 'Automobile'), ('MT.PA', 'Acier'), ('BN.PA', 'Agroalimentaire'), ('ENX.PA', 'Bourse'),
]

NOMS_FR = {
    'AIR.PA': 'Airbus', 'SAF.PA': 'Safran', 'MC.PA': 'LVMH', 'OR.PA': "L'Oréal",
    'RMS.PA': 'Hermès', 'KER.PA': 'Kering', 'SU.PA': 'Schneider Electric', 'LR.PA': 'Legrand',
    'AI.PA': 'Air Liquide', 'DG.PA': 'Vinci', 'SGO.PA': 'Saint-Gobain', 'BNP.PA': 'BNP Paribas',
    'GLE.PA': 'Société Générale', 'ACA.PA': 'Crédit Agricole', 'CS.PA': 'AXA', 'TTE.PA': 'TotalEnergies',
    'ENGI.PA': 'Engie', 'VIE.PA': 'Veolia', 'EN.PA': 'Bouygues', 'SAN.PA': 'Sanofi',
    'RI.PA': 'Pernod Ricard', 'CA.PA': 'Carrefour', 'ML.PA': 'Michelin', 'STMPA.PA': 'STMicroelectronics',
    'CAP.PA': 'Capgemini', 'DSY.PA': 'Dassault Systèmes', 'EL.PA': 'EssilorLuxottica', 'ORA.PA': 'Orange',
    'RNO.PA': 'Renault', 'MT.PA': 'ArcelorMittal', 'BN.PA': 'Danone', 'ENX.PA': 'Euronext',
}


def _setup_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:  # noqa: BLE001
            pass


def build(ticker, sector, crumb):
    c = yd.fetch_chart(ticker, rng='1y', interval='1d')
    meta = c['meta']
    closes = [x for x in c['close'] if x is not None]
    price = closes[-1] if closes else None
    prev = closes[-2] if len(closes) >= 2 else None
    chg = (price - prev) / prev * 100 if (price is not None and prev) else None
    chg1y = (price / closes[0] - 1) * 100 if price and closes else None

    q = yd.fetch_quote_summary(ticker, crumb=crumb)
    sd, dks, fd, pd = (q.get('summaryDetail', {}), q.get('defaultKeyStatistics', {}),
                       q.get('financialData', {}), q.get('price', {}))
    div_yield = yd.deep_get(sd, 'dividendYield') or yd.deep_get(dks, 'dividendYield')
    target_mean = yd.deep_get(fd, 'targetMeanPrice')
    target_high = yd.deep_get(fd, 'targetHighPrice')
    target_low = yd.deep_get(fd, 'targetLowPrice')

    def _exp(tgt):
        if div_yield is None or tgt is None or price is None or price <= 0:
            return None
        return div_yield + (tgt - price) / price

    return {
        'ticker': ticker, 'name': NOMS_FR.get(ticker, meta.get('shortName') or ticker), 'sector': sector,
        'price': price, 'change_pct': chg, 'chg_1y': chg1y,
        'div_yield': div_yield,
        'pe_trailing': yd.deep_get(sd, 'trailingPE'),
        'pe_forward': yd.deep_get(sd, 'forwardPE'),
        'pb': yd.deep_get(sd, 'priceToBook'),
        'eps_growth': yd.deep_get(fd, 'earningsGrowth'),
        'rev_growth': yd.deep_get(fd, 'revenueGrowth'),
        'roe': yd.deep_get(dks, 'returnOnEquity'),
        'profit_margin': yd.deep_get(fd, 'profitMargins'),
        'fcf': yd.deep_get(fd, 'freeCashflow'),
        'target_mean': target_mean,
        'target_high': target_high,
        'target_low': target_low,
        'exp_pessimistic': _exp(target_low),
        'exp_base': _exp(target_mean),
        'exp_optimistic': _exp(target_high),
        'recommendation': yd.deep_get(fd, 'recommendationKey'),
        'analyst_count': yd.deep_get(fd, 'numberOfAnalystOpinions'),
        'market_cap': yd.deep_get(pd, 'marketCap'),
    }


def main():
    _setup_stdout()
    ap = argparse.ArgumentParser(description='Univers de croissance (sélection & portefeuille)')
    ap.add_argument('--out', default='univers_croissance.json', help='Chemin JSON de sortie')
    ap.add_argument('--tickers', default=None,
                    help='Univers personnalisé, codes séparés par des virgules (secteur = inconnu)')
    ap.add_argument('--print', action='store_true', help='Imprime un aperçu dans le terminal')
    args = ap.parse_args()

    if args.tickers:
        candidates = [(t.strip().upper(), 'inconnu') for t in args.tickers.split(',') if t.strip()]
    else:
        candidates = CANDIDATES

    crumb = yd.fetch_crumb()
    rows, errors = [], []
    for t, sector in candidates:
        try:
            rows.append(build(t, sector, crumb))
        except Exception as e:  # noqa: BLE001
            errors.append(f'{t}: {e}')

    out_path = os.path.abspath(args.out)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'rows': rows, 'errors': errors}, f, ensure_ascii=False, indent=2)

    print(f'OK {len(rows)}/{len(candidates)} -> {out_path}')
    for e in errors:
        print('ERR', e)

    if args.print:
        print('\n--- Aperçu (trié par rendement annualisé attendu — scénario de base) ---')
        for r in sorted(rows, key=lambda x: (x.get('exp_base') or -1), reverse=True)[:10]:
            f3 = lambda v: f'{v * 100:5.1f} %' if v is not None else '  N/A'  # noqa: E731
            print(f"{r['ticker']:<10} {r['name']:<20} Pessimiste={f3(r.get('exp_pessimistic'))} "
                  f"Base={f3(r.get('exp_base'))} Optimiste={f3(r.get('exp_optimistic'))} "
                  f"Rendement={(r.get('div_yield') or 0) * 100:5.2f} %")

    sys.exit(2 if not rows else (1 if errors else 0))


if __name__ == '__main__':
    main()

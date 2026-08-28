# Sources de données

Les données de marché et de valorisation proviennent de l'interface publique de
**Yahoo Finance** (sans clé API) ; les actualités et fondamentaux sont complétés par la
recherche web. Ce document décrit chaque canal.

---

## 1. Marché & valorisation : Yahoo Finance

### 1.1 Règles de codes (Euronext Paris)

- **Valeurs françaises** : code société + `.PA`, ex. Airbus → `AIR.PA`, LVMH → `MC.PA`,
  TotalEnergies → `TTE.PA`, Sanofi → `SAN.PA`.
- **Indices** : CAC 40 → `^FCHI`, SBF 120 → `^SBF120`, CAC Next 20 → `^CN20`.
- Liste complète : `univers-actions.md`.

### 1.2 Deux interfaces

| Interface | Usage | Authentification |
|---|---|---|
| `v8/finance/chart/{ticker}` | OHLCV historique, cours temps réel, plus haut/bas 52 sem. (meta) | non |
| `v10/finance/quoteSummary/{ticker}` | PE/PB/rendement/cap./objectifs & notes des analystes/cash-flow | crumb |

Le flux crumb est encapsulé dans `scripts/yahoo_data.py::fetch_crumb()` :
visiter `fc.yahoo.com` (le 404 est normal), puis `/v1/test/getcrumb`. En cas de 401,
attendre 2 à 5 secondes et réessayer (le script gère déjà les tentatives).

### 1.3 Champs de valorisation (quoteSummary)

| Indicateur | Module / champ | Remarque |
|---|---|---|
| PE (trailing) | summaryDetail.trailingPE | EPS réalisés |
| PE (prévisionnel) | summaryDetail.forwardPE | année suivante |
| PB | summaryDetail.priceToBook | |
| Rendement du dividende | summaryDetail.dividendYield | **décimal** : 0.0157 = 1.57 % |
| Capitalisation | price.marketCap / defaultKeyStatistics.marketCap | |
| Beta | summaryDetail.beta | |
| Objectif de cours | financialData.targetMeanPrice / targetHighPrice / targetLowPrice | |
| Note analystes | financialData.recommendationKey (buy / strong_buy / hold…) | |
| Nombre d'analystes | financialData.numberOfAnalystOpinions | |
| Cash-flow libre | financialData.freeCashflow | |
| Croissance CA / BPA | financialData.revenueGrowth / earningsGrowth | décimal |
| ROE | defaultKeyStatistics.returnOnEquity | décimal |

Champs `{raw, fmt}` gérés par `yahoo_data.deep_get()`. Certains champs peuvent être vides
(notamment ROE) : signaler N/A plutôt que d'inventer.

### 1.4 Univers de croissance (univers_croissance.py)

L'outil récupère pour chaque valeur du candidat (32 par défaut) les données `financialData`
(croissance BPA/CA, marges, cash-flow, objectifs, notes) et les multiples, puis écrit
`univers_croissance.json`.

**Modèle de rendement annualisé attendu (trois scénarios)** :

```
rendement annualisé attendu = rendement du dividende + (objectif de cours − cours)/cours
```

- **Pessimiste** `exp_pessimistic` : rendement + (objectif bas − cours)/cours
- **Base** `exp_base` : rendement + (objectif moyen − cours)/cours
- **Optimiste** `exp_optimistic` : rendement + (objectif haut − cours)/cours

Les objectifs sont les consensus des analystes (Yahoo). Valeurs avec couverture faible
(`analyst_count` réduit ou objectifs manquants) : pondérer à la baisse ou exclure.

---

## 2. Historique & indicateurs techniques

`historique_technique.py` récupère 1 an de données quotidiennes et calcule :
- Performances : 1j/1sem/1mois/3mois/6mois/1an/YTD
- MA20/MA50/MA200, RSI14, MACD (12/26/9)
- Plus haut/bas 52 sem., supports/résistances 3 mois, signal technique (haussière/baissière/neutre)

⚠️ Précisions :
- `close` = cours de clôture **non ajusté** ; `adjclose` = ajusté des dividendes (rendement total).
- `chartPreviousClose` n'est pas fiable : la veille = avant-dernier élément de la série de clôtures.
- `^SBF120` : historique Yahoo très clairsemé (souvent 1 bougie) ; variation souvent N/A —
  utiliser CAC 40 / CAC Next 20 ou expliquer la limite.

---

## 3. Actualités financières

### 3.1 Médias français de référence (par priorité)

| Média | URL | Positionnement |
|---|---|---|
| Les Échos | lesechos.fr | premier quotidien économique français |
| Le Figaro Économie | lefigaro.fr/economie | économie & politique |
| Boursier.com | boursier.com | cours / flashs / commentaires |
| Zonebourse | zonebourse.com | données & consensus analystes |
| Boursorama | boursorama.com | portail boursier |
| Investing.com FR | fr.investing.com | monde + France |
| La Tribune | latribune.fr | entreprises / industrie / énergie |
| Challenges | challenges.fr | entreprises |
| BFMTV Bourse | bfmtv.com/bourse | flash |
| Le Monde Économie | lemonde.fr/economie | analyses |
| ABC Bourse | abcbourse.com | valeurs & dividendes |
| Yahoo Finance France | fr.finance.yahoo.com | agrégateur |

### 3.2 Stratégie de collecte (recommandée)

**Ne pas** scraper chaque site (structure variable, blocages) ; utiliser la recherche web en
parallèle :
- Mots-clés français : `CAC 40 aujourd'hui` / `Bourse de Paris` / `{Société} résultats` /
  `{Société} dividende 2026` / `{Société} analystes objectif de cours`
- Filtrer 1 à 3 jours, privilégier les communiqués (résultats) et les événements macro
  (BCE, inflation, OAT, politique/notation)
- Après identification, lire l'article (`web_fetch`) puis produire un **résumé français**
  avec URL de source et date.

---

## 4. Autres canaux de fondamentaux

- **Résultats financiers** : page Relations Investisseurs du site officiel (PDF) ;
  quoteSummary fournit EPS/cash-flow/croissance.
- **Macro** : décisions de la BCE, IPC/PMI français, rendement OAT, EUR/USD — recherche web.
- **Croisement de valorisation** : comparer les multiples du skill avec Zonebourse /
  Investing.com FR pour écarter une dérive de source unique.

## 5. Fraîcheur des données

- Les cours reflètent la clôture du dernier jour ouvré (Paris 9h00–17h30, UTC+1/UTC+2).
- Le rapport doit indiquer la **date des données** pour éviter de traiter des cours périmés.
- Après un long week-end, les données peuvent encore être celles de la veille de fermeture.

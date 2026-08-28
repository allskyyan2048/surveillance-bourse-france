# Surveillance Bourse France

**Système portable de surveillance du marché boursier français (Euronext Paris)**
avec génération automatique de **rapport HTML auto-contenu** (graphiques ECharts embarqués,
aucun fichier externe nécessaire pour l'ouvrir).

- 📈 Suivi des indices : **CAC 40 / SBF 120 / CAC Next 20**
- 📊 Analyse technique du CAC 40 (MA/RSI/MACD, supports/résistances, signaux)
- 📰 Collecte d'actualités financières françaises (à injecter au format JSON)
- 💎 Analyse & valorisation de valeurs françaises (Airbus, LVMH, TotalEnergies, Sanofi…)
- 🏆 Sélection de **5 valeurs à haut rendement** (rendement annualisé attendu en 3 scénarios)
- 💼 **Portefeuille à rendement maximal** (5 valeurs, 3 scénarios, ≥ 4 secteurs)
- 🔮 Perspectives avec trois scénarios (base / optimiste / pessimiste) et fourchettes cibles

## ⚙️ Portabilité

- **Python 3.8+ standard library uniquement** — aucune dépendance tierce à installer
- Fonctionne sous **Windows / macOS / Linux**, depuis n'importe quel répertoire
  (les scripts se localisent automatiquement)
- Données : **Yahoo Finance** (interface publique, sans clé API)
- Le rapport HTML final est **auto-contenu** : la bibliothèque de graphiques ECharts est
  embarquée dans le fichier → il s'ouvre dans n'importe quel navigateur, **même hors ligne**

## 📁 Structure

```
surveillance-bourse-france/
├── SKILL.md                    # Définition du skill (français)
├── README.md                   # Ce document
├── scripts/
│   ├── yahoo_data.py           # Couche d'accès aux données (Yahoo Finance)
│   ├── apercu_marche.py        # Indices + valeurs (cours, PE/PB, rendement, objectifs)
│   ├── historique_technique.py # Historique + indicateurs techniques
│   ├── univers_croissance.py   # Univers de croissance (rendements annualisés, 3 scénarios)
│   └── generer_rapport.py      # ⭐ Générateur principal du rapport HTML
├── templates/
│   └── rapport_modele.html     # Modèle HTML du rapport
├── lib/
│   └── echarts.min.js          # Bibliothèque de graphiques (embarquée dans le HTML)
└── references/
    ├── sources-de-donnees.md   # Sources, champs, médias, stratégie de recherche
    ├── univers-actions.md      # Codes indices/valeurs par secteur
    └── methodes-valorisation.md # Méthodes de valorisation, technique, perspectives
```

## 🚀 Utilisation rapide

```bash
# Rapport HTML complet (par défaut : CAC 40 + 12 valeurs + haut rendement + portefeuille)
python scripts/generer_rapport.py --sortie rapport.html

# Valeurs personnalisées
python scripts/generer_rapport.py --tickers AIR.PA,MC.PA,TTE.PA --sortie rapport.html

# Avec actualités (voir format ci-dessous)
python scripts/generer_rapport.py --news actualites.json --sortie rapport.html

# Réutiliser un cache de données (pas de re-téléchargement)
python scripts/generer_rapport.py --sortie-json donnees.json
python scripts/generer_rapport.py --donnees donnees.json --sortie rapport.html
```

### Format du fichier d'actualités (`--news`)

```json
[
  {"titre": "Fitch confirme la note A+ de la France",
   "tag": "MAJOR",
   "description": "Résumé de l'actualité en une ou deux phrases.",
   "source": "Les Échos (28/08/2026)"}
]
```

Tags disponibles : `MAJOR` · `BUDGET` · `SOCIÉTÉ` · `MACRO` · `GLOBAL`.

### Scripts autonomes

```bash
python scripts/apercu_marche.py                     # indices + valeurs (tableau)
python scripts/apercu_marche.py --json              # sortie JSON
python scripts/historique_technique.py ^FCHI        # technique du CAC 40
python scripts/historique_technique.py AIR.PA       # technique d'une valeur
python scripts/univers_croissance.py --print        # classement haut rendement
```

## 📄 Contenu du rapport HTML

1. **Aperçu des indices** — cartes CAC 40 / SBF 120 / CAC Next 20, graphique d'évolution du
   CAC 40 (1 an, MA50/MA200) et performances par période
2. **Analyse technique** — MA/RSI/MACD, supports/résistances, signal de tendance
3. **Actualités** — injectées via `--news` (résumé + sources)
4. **Zoom valeurs** — rendements des dividendes, potentiel vs objectif de cours, PE
5. **Recommandations à haut rendement** — top 5 avec thèse, risques et 3 scénarios
6. **Portefeuille** — équipondéré, rendements annualisés attendus (3 scénarios)
7. **Perspectives** — trois scénarios avec fourchettes cibles (pré-remplies depuis les
   niveaux techniques)

## ⚠️ Avertissement

Les données proviennent de Yahoo Finance (clôtures de la dernière séance) ; les rendements
annualisés attendus sont des **estimations de modèle** (dividende + objectif de cours des
analystes), pas des engagements de performance. **Information à titre indicatif — ne
constitue pas un conseil en investissement.** Tout investissement comporte un risque de
perte en capital.

## 📄 Licence

MIT — voir le fichier `LICENSE`.

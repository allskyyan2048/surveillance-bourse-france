---
name: surveillance-bourse-france
description: Système de surveillance et d'analyse du marché boursier français (Euronext Paris) avec génération automatique de rapport HTML autonome. Suivi des indices CAC 40 / SBF 120 / CAC Next 20, collecte d'actualités financières, analyse fondamentale et valorisation de valeurs françaises (Airbus, LVMH, TotalEnergies, Sanofi, Schneider, etc.), calcul du rendement annualisé attendu (dividende + objectif de cours), sélection de valeurs à haut rendement, construction d'un portefeuille à rendement maximal et perspectives de marché. Le rapport final est toujours généré au format HTML (auto-contenu, ECharts embarqué), prêt à être ouvert dans n'importe quel navigateur. Convient pour : cours du CAC 40, Bourse de Paris, actualités financières françaises, analyse de valeurs françaises, valeurs à fort dividende, construction de portefeuille, perspectives du marché français.
---

# Surveillance Bourse France — Rapport HTML automatique

Système **tout-en-un** de surveillance du marché boursier français. Il récupère les données
de marché (Yahoo Finance, sans clé API), calcule les indicateurs techniques et les
rendements annualisés attendus, puis génère un **rapport HTML auto-contenu** (ECharts
embarqué, aucun fichier externe requis) à partir du modèle fourni.

**Portabilité** : scripts en Python 3.8+ **standard library uniquement** (aucune
installation tierce), fonctionnent sous Windows / macOS / Linux, depuis n'importe quel
répertoire (les scripts se localisent automatiquement). Une fois le skill installé sur
n'importe quelle machine (répertoire de skills), il fonctionne directement.

---

## 0. Vue d'ensemble du flux de travail

1. Identifier le(s) module(s) demandé(s) par l'utilisateur :
   - Cours des indices / du marché → module 1
   - Actualités financières françaises → module 2
   - Analyse / valorisation de valeurs → module 3
   - Valeurs à haut rendement / portefeuille → module 4
   - Perspectives / tendances → module 5 (nécessite généralement modules 1 + 3)
2. **Toujours** lancer les scripts pour les données de marché — ne jamais inventer de chiffres.
3. Pour les actualités, utiliser la recherche web avec des mots-clés français
   (voir `references/sources-de-donnees.md` §3).
4. Générer le rapport **en HTML** avec `generer_rapport.py` (ou reconstruire un rapport
   personnalisé à partir des données JSON).
5. Respecter la « discipline de sortie » en fin de document.

## 1. Lancement rapide

```bash
# Générer un rapport HTML complet (indices + valeurs + haut rendement + portefeuille + perspectives)
python <skill>/scripts/generer_rapport.py --sortie rapport.html

# Valeurs personnalisées
python <skill>/scripts/generer_rapport.py --tickers AIR.PA,MC.PA,TTE.PA --sortie rapport.html

# Injecter des actualités (fichier JSON) et générer le rapport
python <skill>/scripts/generer_rapport.py --news actualites.json --sortie rapport.html

# Ne récupérer que les données (cache JSON)
python <skill>/scripts/generer_rapport.py --sortie-json donnees.json

# Réutiliser un cache de données existant
python <skill>/scripts/generer_rapport.py --donnees donnees.json --sortie rapport.html

# Désactiver le module portefeuille
python <skill>/scripts/generer_rapport.py --sans-portefeuille --sortie rapport.html
```

### Scripts autonomes (données / diagnostic)

```bash
# Aperçu du marché : indices + valeurs (cours, PE/PB, rendement, objectifs)
python <skill>/scripts/apercu_marche.py                 # indices + liste par défaut
python <skill>/scripts/apercu_marche.py --tickers AIR.PA,MC.PA
python <skill>/scripts/apercu_marche.py --indices-only
python <skill>/scripts/apercu_marche.py --json

# Historique + indicateurs techniques d'une valeur ou d'un indice
python <skill>/scripts/historique_technique.py ^FCHI
python <skill>/scripts/historique_technique.py AIR.PA --json

# Univers de croissance : rendements annualisés attendus en trois scénarios
python <skill>/scripts/univers_croissance.py --print        # 32 valeurs par défaut
python <skill>/scripts/univers_croissance.py --tickers AIR.PA,MC.PA --print
```

- `<skill>` = répertoire de ce skill ; les scripts se localisent automatiquement, pas besoin de `cd`.
- Tous les scripts acceptent `--json` pour une sortie structurée.
- En cas d'échec de récupération : réessayer une fois ; si l'échec persiste, croiser avec la
  recherche web et mentionner la cause dans le rapport.

## 2. Module 1 — Surveillance des indices

1. `python apercu_marche.py --indices-only` → CAC 40 / SBF 120 / CAC Next 20 : cours, variation, plus haut/bas 52 sem.
2. `python historique_technique.py ^FCHI` → indicateurs techniques du CAC 40 (MA/RSI/MACD/52 sem./performances).
3. Contenu : points des trois indices, variations du jour, plus hauts/bas 52 sem., performances par
   période et signal technique, synthèse d'une phrase (avec les actualités).

Note : `^SBF120` a un historique Yahoo très clairsemé ; sa variation peut être N/A (limite de la source).

## 3. Module 2 — Actualités financières

1. Recherche web parallèle avec mots-clés français :
   - `CAC 40 aujourd'hui` / `Bourse de Paris` + jour/semaine
   - `site:lesechos.fr` ou autres médias (`references/sources-de-donnees.md` §3.1)
   - `{Société} résultats` / `{Société} dividende` / `{Société} objectif de cours`
   - Macro : `BCE taux` / `inflation zone euro` / `OAT France`
2. Filtrer sur 1 à 3 jours (résultats, M&A, macro, politique, mouvements d'indices).
3. Lire les articles clés (`web_fetch`) et produire un **résumé français** avec source et date.
4. Construire le fichier `actualites.json` puis l'injecter avec `--news` :
   ```json
   [
     {"titre": "Titre", "tag": "MAJOR", "description": "Résumé en une ou deux phrases.", "source": "Média (date)"}
   ]
   ```
   Tags possibles : `MAJOR`, `BUDGET`, `SOCIÉTÉ`, `MACRO`, `GLOBAL`.

## 4. Module 3 — Analyse et valorisation de valeurs

1. Valorisation : `apercu_marche.py --tickers CODE` → PE(trailing/forward), PB, rendement, cap., objectif moyen, note.
2. Technique : `historique_technique.py CODE` → performances et signaux.
3. Fondamentaux : recherche web (derniers résultats, activité sectorielle) ; si besoin `web_fetch`.
4. Valorisation : méthode de `references/methodes-valorisation.md` — donner un intervalle
   reproductible (valorisation relative + DCF/DDM si adapté), avec hypothèses clés.
5. Rapport individuel — gabarit :

```
### [Nom français] (CODE) — données au AAAA-MM-JJ
- Cours / variation du jour / intervalle 52 sem. / capitalisation
- Valorisation : PE(trailing) x / PE(forward) x / PB x / rendement x % (vs historique et pairs)
- Fondamentaux : croissance / qualité / rendement actionnaire / risques (2 à 4 points)
- Intervalle de valorisation : bas – base – haut (€), potentiel vs cours
- Technique : signal + supports/résistances clés
- Conclusion : sous-évalué / correctement évalué / surévalué + justification + avertissements
```

## 5. Module 4 — Valeurs à haut rendement & portefeuille

1. `python univers_croissance.py --print` → univers par défaut (32 valeurs, tous secteurs) ;
   ou `--tickers` pour un univers personnalisé.
2. **Rendement annualisé attendu (trois scénarios)** :
   `rendement annualisé = rendement du dividende + (objectif de cours − cours)/cours`
   - **Pessimiste** : rendement + (objectif bas − cours)/cours
   - **Base** : rendement + (objectif moyen − cours)/cours
   - **Optimiste** : rendement + (objectif haut − cours)/cours
3. Filtrage : classement par rendement annualisé attendu (base) + croisement avec la croissance
   des bénéfices + diversification sectorielle + qualité (ROE/marge). Éviter un secteur unique ;
   pour les valeurs cycliques, privilégier le potentiel vs objectif comme critère de classement.
4. `generer_rapport.py` sélectionne automatiquement le top 5, génère les cartes de
   recommandation (thèse/risques en français) et le portefeuille équipondéré (3 scénarios).
5. Sortie : pour chaque valeur, recommandation motivée + 3 scénarios ; portefeuille max. 5 valeurs,
   ≥ 4 secteurs, avec rendements annualisés attendus agrégés (pessimiste/base/optimiste).

## 6. Module 5 — Perspectives

Suivre « macro → flux/émotions → structure → scénarios » (voir `references/methodes-valorisation.md` §5) :
1. Macro : politique de la BCE, inflation, finances publiques françaises (budget, notation), taux OAT, EUR/USD.
2. Marché : tendance technique du CAC 40, rotation sectorielle, actualités, volatilité.
3. Opportunités structurelles : secteurs/valeurs bénéficiant du contexte macro.
4. **Toujours donner trois scénarios** (base / optimiste / pessimiste) avec conditions de
   déclenchement, fourchettes cibles et signaux de confirmation/infirmation.
   `generer_rapport.py` pré-remplit les fourchettes à partir des niveaux techniques (section 7).

## 7. Gabarit de rapport global (module 7 du HTML)

Le rapport HTML généré contient 7 sections :
1. Aperçu des indices  2. Analyse technique  3. Actualités  4. Zoom valeurs
5. Recommandations à haut rendement  6. Portefeuille  7. Perspectives
Chaque section est autonome ; les actualités, recommandations et scénarios sont injectés
automatiquement (fichiers JSON / données calculées).

## 8. Discipline de sortie

- **Données sourcées** : cours issus des scripts, actualités issues de la recherche web ; chaque
  chiffre indique sa source et sa date.
- **Distinguer faits et jugements** : les données sont objectives, les conclusions sont signalées comme « jugement ».
- **Valorisation reproductible** : hypothèses listées (WACC, croissance, multiples, dividende).
- **Ne pas inventer** : champ indisponible → N/A ou explication.
- **Rendement annualisé attendu = estimation de modèle** (dividende + potentiel vs objectif),
  pas un engagement de performance ; les objectifs évoluent avec les fondamentaux et le macro.
  Toujours accompagner d'« information à titre indicatif, ne constitue pas un conseil en investissement ».

## 9. Fichiers de référence

- `references/sources-de-donnees.md` — interfaces, champs, médias, stratégie de recherche
- `references/univers-actions.md` — codes indices/valeurs, groupes sectoriels
- `references/methodes-valorisation.md` — méthodologie de valorisation, technique, perspectives

# Méthodes de valorisation et d'analyse

Méthodologie unifiée pour l'analyse des valeurs et les perspectives. Objectif : des
conclusions appuyées sur des données, des intervalles de valorisation reproductibles,
des risques transparents.

---

## 1. Indicateurs de valorisation (mémo)

### 1.1 Valorisation relative (multiples)

| Indicateur | Formule | Usage |
|---|---|---|
| PE | cours / BPA 12 mois | secteurs stables ; PE faussé en cas de perte ou de bas de cycle |
| PE (prévisionnel) | cours / BPA attendu | reflète le prix de la croissance ; écart avec PE trailing = changement d'attente |
| PB | cours / actif net par action | banques/assurances/cycles ; ROE élevé justifie un PB élevé |
| Rendement du dividende | dividende annualisé / cours | **clé en France** (culture du dividende) ; vérifier la soutenabilité |
| PEG | PE / croissance BPA % | < 1 sous-évalué, > 2 surévalué ; non pertinent si croissance négative |
| EV/EBITDA | VE / EBITDA | secteurs lourds, structures de capital complexes |
| P/S | capitalisation / CA | croissance ou pertes |

**Trois angles de comparaison :**
1. Propre historique (percentile 5 ans du PE actuel)
2. Pairs sectoriels (ex. luxe : LVMH/Hermès/Richemont)
3. Indice global (CAC 40 : PE forward ~13–15x de référence)

### 1.2 Valorisation absolue (DCF)

Pour les sociétés matures à cash-flow stable. Points clés :
- FCFF : `financialData.freeCashflow` ou rapports ; moyenne sur 3 ans pour lisser
- WACC ≈ 6–9 % (grandes valeurs françaises matures : 7–8 % ; croissance/beta élevé : au-dessus)
- Croissance terminale g : prudent, 0–2,5 %
- Sortie : trois scénarios (optimiste/base/pessimiste) ; comparer au cours.

### 1.3 Dividendes actualisés (DDM)

Pour les valeurs à haut dividende (banques, énergie, utilities) :
- Valeur ≈ dividende attendu × (1+g) / (r − g)
- Vérifier l'écart du rendement vs son historique (méfiance envers le « piège à rendement » :
  bénéfices en baisse → dividende non soutenable).

### 1.4 Format de conclusion de valorisation

```
Intervalle de valorisation (12 mois) : [bas] – [base] – [haut]  (€)
Jugement : sous-évalué / correctement évalué / surévalué (potentiel ±xx %)
Hypothèses clés : WACC, croissance, multiples, dividende (listées pour reproductibilité)
```

---

## 2. Cadre technique

Utiliser `historique_technique.py` pour aider au timing (pas un signal d'achat/vente isolé) :

| Indicateur | Usage |
|---|---|
| MA20/50/200 | alignement haussier (cours > MA20 > MA50 > MA200) ; perte de la MA200 = affaiblissement |
| RSI14 | > 70 surachat, < 30 survente ; à confronter à la tendance |
| MACD | croix haussière/baissière, expansion du histogramme |
| Supports/résistances | plus hauts/bas 3 mois + 52 sem. ; franchissement en volume = signal |
| Performances | excès vs CAC 40 pour juger de la force relative |

Le script fournit un signal « haussière/baissière/neutre » ; le croiser avec les
fondamentaux dans le rapport.

---

## 3. Dimensions fondamentales (valeurs)

1. **Modèle & fossé** : pouvoir de fixation des prix, marque/technologie, position (luxe, industrie, énergie)
2. **Croissance** : revenueGrowth / earningsGrowth ; carnet de commandes (aéro/défense),
   demande structurelle (électrification, IA)
3. **Qualité** : ROE, marges, cash-flow libre positif couvrant le dividende
4. **Solidité financière** : endettement net/EBITDA ; banques → ratio CET1
5. **Rendement actionnaire** : dividende + rachats (les groupes français versent souvent 40–60 %)
6. **Risques** : changes (luxe/Asie, énergie/USD), réglementation, géopolitique, taux

---

## 4. Sélection à haut rendement & construction de portefeuille

### 4.1 Rendement annualisé attendu (trois scénarios)

```
rendement annualisé attendu = rendement du dividende + (objectif de cours − cours)/cours
```

- `dividendYield` (décimal) : summaryDetail.dividendYield (annualisé)
- Objectifs : consensus trois niveaux (bas/moyen/haut des analystes)
  | Scénario | Champ | Définition |
  |---|---|---|
  | Pessimiste | `exp_pessimistic` | rendement + (objectif bas − cours)/cours |
  | Base | `exp_base` | rendement + (objectif moyen − cours)/cours |
  | Optimiste | `exp_optimistic` | rendement + (objectif haut − cours)/cours |

Interprétation : **rendement du dividende + rendement de cours implicite du consensus**,
trois scénarios pour refléter la dispersion des objectifs.

Limites : couverture faible ou objectifs manquants → peu fiable (pondérer ou exclure).

### 4.2 Règles de filtrage et de classement

1. Tri principal : rendement annualisé attendu (décroissant)
2. Croisement : croissance BPA, ROE, marge — dégrader les croissances négatives / ROE faible
3. Cycliques (auto, acier, semi-conducteurs) : croissance faussée → **classer par potentiel vs objectif**
4. Diversification : 1–2 valeurs max par secteur, ≥ 4 secteurs au total
5. Qualité : privilégier freeCashflow > 0 (dividende soutenu, anti « piège à rendement »)

### 4.3 Construction du portefeuille

- Équipondéré par défaut (20 % × 5) ; pondération possible selon le risque
- Rendement attendu du portefeuille = moyenne pondérée des rendements (trois scénarios) ;
  la largeur de l'intervalle reflète la dispersion des objectifs
- Substitut prudent : remplacer une valeur très élastique par un actif à rendement stable
  (banque/assurance) — intervalle plus étroit, scénario pessimiste moins profond
- **Obligation de divulgation** : estimation de modèle, pas un engagement de performance ;
  les objectifs évoluent avec les fondamentaux et le macro.

---

## 5. Spécificités du marché français (à connaître pour le rapport)

- **Pondération CAC 40** : luxe (LVMH/L'Oréal/Hermès/Kering), industrie (Airbus/Safran/Schneider),
  énergie (TotalEnergies), pharma (Sanofi), banques/assurances ; peu de grandes valeurs tech pures.
- **Culture du dividende** : rendement global du CAC 40 souvent 2,5–3,5 % ; banques/énergie 5 %+.
- **Sensibilités macro** : trajectoire de la BCE, EUR/USD, rendement OAT et événements
  politique/fiscal (budget, notation souveraine) affectent fortement le risque.
- **Valorisation** : PE forward CAC 40 ~13–15x de longue date ; leaders de croissance
  (Schneider, Safran, Hermès) nettement au-dessus, c'est normal.
- **Horaires** : 9h00–17h30 Paris (UTC+1 / UTC+2).

---

## 6. Cadre des perspectives

En quatre étapes « macro → flux → structure → scénarios » :

1. **Macro & politique** : décisions BCE, inflation, croissance, géopolitique et finances
   publiques (France/zone euro)
2. **Flux & sentiment** : tendance de l'indice (technique ^FCHI), volatilité, rotation, actualités
3. **Opportunités structurelles** : secteurs/valeurs gagnants (ex. baisse des taux → dividendes
   & mid-caps ; électrification/IA → chaîne électrique)
4. **Scénarios (obligatoires)** :
   - Base : hypothèses neutres → fourchette de cours
   - Optimiste : conditions haussières
   - Pessimiste : conditions baissières + niveaux de sortie
   - Chaque scénario avec **signaux observables de confirmation/infirmation**

**Discipline de sortie** : chiffres sourcés ; faits vs jugements ; valorisation reproductible ;
information à titre indicatif, ne constitue pas un conseil en investissement.

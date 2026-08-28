# Univers des actions françaises

Codes Yahoo des principaux instruments d'Euronext Paris, par secteur. **La composition du
CAC 40 évolue régulièrement** : vérifier la liste la plus récente (ex. « liste CAC 40 »)
si nécessaire. Codes au format `xxx.PA`.

## 1. Indices

| Indice | Code Yahoo | Note |
|---|---|---|
| CAC 40 | `^FCHI` | 40 plus fortes capitalisations de Paris |
| SBF 120 | `^SBF120` | plus large (120) — historique Yahoo très clairsemé |
| CAC Next 20 | `^CN20` | 20 valeurs en dessous du CAC 40 |

## 2. Liste de suivi par défaut (apercu_marche.py / rapport)

Couvre les leaders de chaque secteur ; utilisable avec `--tickers` :

| Valeur | Code | Secteur | Note |
|---|---|---|---|
| Airbus | `AIR.PA` | Aéronautique | leader européen aéro/défense |
| LVMH | `MC.PA` | Luxe | 1er groupe de luxe mondial |
| L'Oréal | `OR.PA` | Beauté | leader mondial |
| TotalEnergies | `TTE.PA` | Énergie | énergie + renouvelables |
| Sanofi | `SAN.PA` | Pharmacie | vaccins / maladies rares |
| Safran | `SAF.PA` | Aéronautique | moteurs d'avion |
| Schneider Electric | `SU.PA` | Électricité | électrification / IA |
| Air Liquide | `AI.PA` | Gaz industriels | défensif |
| BNP Paribas | `BNP.PA` | Banques | banque systémique |
| AXA | `CS.PA` | Assurances | leader mondial |
| Vinci | `DG.PA` | Infrastructures | concessions |
| Pernod Ricard | `RI.PA` | Spiritueux | haut dividende |

## 3. Principales valeurs du CAC 40 (par secteur)

### Luxe / Consommation
LVMH `MC.PA`, L'Oréal `OR.PA`, Hermès `RMS.PA`, Kering `KER.PA`, EssilorLuxottica `EL.PA`,
Pernod Ricard `RI.PA`, Danone `BN.PA`, Carrefour `CA.PA`

### Industrie / Aéro / Infrastructures
Airbus `AIR.PA`, Safran `SAF.PA`, Schneider Electric `SU.PA`, Vinci `DG.PA`, Bouygues `EN.PA`,
Saint-Gobain `SGO.PA`, Legrand `LR.PA`, Alstom `ALO.PA`, Michelin `ML.PA`

### Énergie / Utilities
TotalEnergies `TTE.PA`, Engie `ENGI.PA`, Veolia Environnement `VIE.PA`

### Finance
BNP Paribas `BNP.PA`, Crédit Agricole `ACA.PA`, Société Générale `GLE.PA`, AXA `CS.PA`

### Technologie / Logiciels / Conseil
Capgemini `CAP.PA`, Dassault Systèmes `DSY.PA`, Publicis `PUB.PA`

### Télécoms / Médias
Orange `ORA.PA`, Vivendi `VIV.PA`

### Automobile / Mobilité
Stellantis `STLAP.PA` (Paris ; Milan `STLAM.MI` ; NY `STLA`), Renault `RNO.PA`

### Immobilier
Unibail-Rodamco-Westfield `URW.PA`

## 4. Valeurs supplémentaires (hors CAC 40 mais représentatives)

- Dassault Aviation `AM.PA` (défense), Thales `HO.PA` (électronique de défense),
  Accor `AC.PA` (hôtellerie), STMicroelectronics `STMPA.PA` (semi-conducteurs)
- Moyennes : Bureau Veritas `BVI.PA`, Eiffage `FGR.PA`, Getlink `GET.PA`, Edenred `EDEN.PA`

## 5. Conseils d'utilisation

- Code incertain ? Vérifier d'abord :
  `python apercu_marche.py --tickers CODE_PROPOSE` (affiche cours et nom si valide).
- Les noms français sont intégrés dans `apercu_marche.py` / `univers_croissance.py`
  (table `NOMS_FR`) ; ajouter de nouvelles valeurs si nécessaire.

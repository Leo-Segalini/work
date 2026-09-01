# Décision de transmission M4 — Brief 2 M3

**Date :** 2026-08-31  
**Décision :** transmission **sous conditions**  
**Jeu transmis :** `output/brief2/transmission_m4/sensor_readings_m4.csv`

---

## 1. Capacité du jeu (avant fabrication)

| Indicateur | Valeur |
|---|---|
| Équipements totaux | 411 |
| Équipements instrumentés | 35 (8,5 %) |
| SITE-OUEST instrumenté | 0 / 16 |
| Ratio sévérité max/min (événements) | 2,93 |
| Rapprochement critical (fenêtre −48h/+24h) | 12,7 % |

**Segmentation KMeans (k=4)** sur âge, puissance, criticité, site et type : les segments 0 et 3 restent les moins couverts (~5–6 %), ce que les comptages par site ne montraient pas (mélange de sites à faible instrumentation).

### Trois questions non traitables

1. **Modéliser SITE-OUEST par capteurs** — 0 équipement instrumenté sur 16.
2. **Détecter les événements critical** — taux de rapprochement 12,7 % seulement.
3. **Inférer une tendance inter-capteurs sur tout le parc** — couverture 8,5 %, grain inadapté.

---

## 2. Augmentation (2 techniques)

| Procédé | Préserve | Détruit | Usage admissible |
|---|---|---|---|
| `AUG-NOISE-001` | ordre de grandeur, unité, pas | valeurs exactes, corrélation fine avec événements | tests de robustesse |
| `AUG-SHIFT-001` | distribution des valeurs | alignement temporel avec `events.csv` | stress-test fenêtres |

Sorties : `output/brief2/augmented_noise.csv`, `augmented_shift.csv`.

---

## 3. Génération SITE-OUEST

**Périmètre :** 3 équipements non instrumentés (`EQ-COMP-140`, `EQ-COMP-149`, `EQ-COMP-189`).

| Méthode | Lignes | Procédé |
|---|---|---|
| Tirage marginal | 84 | `GEN-MARG-001` |
| SMOTE manuel | 120 | `GEN-SMOTE-001` |

**Marges :** moyenne réelle 192,2 vs synthétique 145,5 ; écart-type 455,5 vs 374,6.  
**Relations :** le tirage marginal détruit les corrélations inter-capteurs ; SMOTE les partiellement (écart-type inter-capteurs 630 vs 669).

**Catégories en SMOTE :** `sensor_name` encodé en one-hot ; interpolation sur `[valeur, one-hot capteur]` ; le capteur résultant = argmax des composantes one-hot interpolées.

---

## 4. Confrontation au détecteur de référence

| Étape | Hypothèse | Lignes signalées |
|---|---|---|
| v1 (générateur brut) | premier générateur SITE-OUEST | 8 (`R-KEY` — doublons logiques) |
| v2 (clip plages) | correction après analyse R-RANGE | 8 (inchangé — cause = clés, pas plages) |

**Interprétation :** l'absence de signalement sur R-RANGE/UNIT ne prouve pas la fidélité : le détecteur signale explicitement qu'il ne contrôle pas la cohérence multi-source (`events.csv`). Les 8 doublons de clé logique restent à corriger si on transmet l'intégralité du synthétique.

Journal : `output/brief2/detector_journal.json`.

---

## 5. Détection sur `control_batch.csv`

| Verdict | Lignes |
|---|---|
| réelle | 4 978 |
| fabriquée | 752 |
| indécidable | 270 |

| Règle | Occurrences |
|---|---|
| D-OK | 4 978 |
| D-FORMAT | 270 |
| D-FK | 210 |
| D-RANGE | 212 |
| D-UNIT | 180 |
| D-PRECISION | 150 |

**Multi-source :** règle `D-MS-EVT` (mesure calme pendant événement critical/high).  
**Règles brief 1 réévaluées :** `D-FORMAT` seul → `indécidable` (calibré sur `control_sample`) ; `D-FK`/`D-UNIT`/`D-RANGE` → `fabriquée`.

Fichier : `output/brief2/verdicts_control_batch.csv`.

---

## 6. Laplace — agrégat SITE-OUEST

Comptage brut : 16 équipements SITE-OUEST (trop faible pour publication directe).

| ε | Publié | Erreur relative |
|---|---|---|
| 0,1 | 23,94 | 49,6 % |
| 1,0 | 16,79 | 5,0 % |
| 10,0 | 16,08 | 0,5 % |

- **ε < 0,5 :** protection forte mais chiffre inexploitable pour pilotage.
- **ε > 5 :** utilité acceptable, protection faible pour un effectif de 16.

---

## 7. Biais et risques résiduels

| Biais | Chiffre | Atténuation | Résiduel | Amplifié par génération ? |
|---|---|---|---|---|
| Couverture instrumentale | 8,5 % du parc | génération SITE-OUEST | sélection persistante | non |
| Sévérité événements | ratio 2,93 | sur-échantillonnage (non retenu) | rares sous-représentés | oui |
| Historique maintenance | quarantaine M2 | documenter périmètre | activité passée biaisée | non |

---

## 8. Décision finale

**Transmis à M4 :**

- 48 860 lignes **réelles** (`provenance=réelle`)
- 200 lignes **synthétiques** SITE-OUEST (`provenance=synthétique`, procédés documentés)

**Conditions :**

1. Provenance obligatoire sur chaque ligne.
2. Synthétique limité à SITE-OUEST, échantillon borné (pas l'intégralité des 204 lignes générées).
3. Aucune conclusion sur le parc entier ni sur les corrélations inter-sources.
4. Retrait du synthétique si le modèle M4 est sensible aux relations temporelles ou multi-sources.

**Interdit de conclure :**

- performance prédictive sur SITE-OUEST comme si mesuré ;
- causalité capteur ↔ événement sur données synthétiques ;
- représentativité du parc global.

**Rejeu :**

```bash
cd work/M3 && source .venv/bin/activate
PYTHONPATH=. python scripts/brief2_run.py
```

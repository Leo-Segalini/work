# Jour J — Procédure game day M5

Checklist opérationnelle. Garder ce fichier ouvert + `timeline.md` + Prometheus.

---

## 0. Avant l’arrivée du formateur (15–20 min)

```bash
cd work/M5
source .venv/bin/activate

# Stack
docker compose -f deploy/compose.yaml up --build -d
docker compose -f deploy/compose.yaml ps   # api = healthy

# Preuves de départ
python3 -m pytest -q
./pipelines/ci_local.sh
curl -s http://127.0.0.1:8000/health/ready
curl -s http://127.0.0.1:8000/version
```

Ouvrir **3 fenêtres** :

| Fenêtre | URL / fichier |
|---------|----------------|
| A | http://127.0.0.1:8000/docs ou terminal `curl` |
| B | http://127.0.0.1:9090 → Graph → `diagops_index_valid` + `diagops_ready` · **Last 15 minutes** |
| C | `game_day/timeline.md` (à remplir en UTC) |

Vérifier **Status → Targets** : `diagops-api` = **UP**.

Optionnel — s’entraîner 2 min :

```bash
./pipelines/run_gameday_drill.sh
```

---

## 1. Briefing rôles (2 min)

| Rôle | Toi (solo) | Action |
|------|------------|--------|
| Incident commander | toi | décide rollback / continue, chronomètre |
| Observabilité | toi | Prometheus + ready |
| Exécutant | toi | commandes runbook |
| Scribe | toi | une ligne timeline par événement |
| Injecteur | formateur | **ne touche pas** sauf consignes |

Annoncer les objectifs : détection &lt; 2 min · décision &lt; 5 min · restauration &lt; 10 min · 0 perte data.

---

## 2. Pendant l’injection (4 h max — souvent beaucoup moins)

### Dès que le formateur dit « c’est injecté » (ou que tu vois un signal)

1. **Noter T0** UTC dans `timeline.md`.
2. **Tester tout de suite** (ne pas attendre l’animateur) :

```bash
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8000/health/live
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8000/health/ready
curl -s http://127.0.0.1:8000/metrics | grep diagops_
```

3. **Prometheus** (fenêtre B) — requêtes une par une :

```text
diagops_index_valid
diagops_ready
diagops_dependency_up
```

4. Classer le scénario (voir `game_day/plan.md` tableau signaux).

### Décider (&lt; 5 min)

| Signal | Action typique |
|--------|----------------|
| ready 503 + `index_valid=0` | clear fault **ou** rollback release saine |
| gate failed / candidat pourri | **ne pas** promote ; rollback si déjà promu |
| `dependency_up=0` | qualifier panne gen ; rollback si lié à promo |
| Target Prometheus DOWN | relancer `docker compose … up -d` ; investiguer API |

### Restaurer (&lt; 10 min)

```bash
# Cas A — faute labo faults.json
docker compose -f deploy/compose.yaml exec -T api python -c \
  "from pathlib import Path; Path('artifacts/runtime/faults.json').unlink(missing_ok=True)"

# Cas B — mauvaise release promue
python3 pipelines/rollback_release.py diagops-m4-reference-r1 \
  --current artifacts/current.json \
  --history artifacts/history

# Cas C — index candidat à reconstruire
./pipelines/ci_local.sh
```

### Vérifier

```bash
curl -s http://127.0.0.1:8000/health/ready    # 200
python3 -m pytest -q
./pipelines/ci_local.sh                       # gate passed
```

**Ne pas effacer** history, timeline, ni logs pendant l’exercice.

---

## 3. Après l’incident (remédiation 4 h)

1. Finir `game_day/timeline.md` (tous les horodatages).
2. Remplir `game_day/post_incident.md` (cause ≠ symptômes, sans blâme).
3. Cocher / compléter `game_day/remediation.md` + **rejouer** le scénario une fois.
4. Préparer la défense avec `game_day/defense.md`.

---

## 4. Pourquoi ta courbe est une ligne droite

Causes fréquentes :

1. **Tu regardes après coup** — tout est revenu à `1` → ligne plate.  
   → Relance `./pipelines/run_gameday_drill.sh` **avec le graph déjà ouvert**.
2. **Mauvaise plage de temps** — mets **Last 5 minutes** ou **Last 15 minutes**, pas « Last 2 days ».
3. **Mauvaise métrique** — utilise `diagops_index_valid` (passe à 0), pas seulement `diagops_ready` (reste souvent à 1 pendant une faute index).
4. **Pas de refresh** — reclique **Execute** pendant l’incident ; le scrape est toutes les **15 s** (créneau visible, pas une sinusoïde).

Aspect attendu : **créneau** (1 → 0 → 1), pas une belle courbe lisse.

---

## 5. Commandes « poche » jour J

```bash
# Santé
curl -s http://127.0.0.1:8000/health/ready ; echo

# Métriques brutes
curl -s http://127.0.0.1:8000/metrics | grep diagops_

# Drill entraînement
./pipelines/run_gameday_drill.sh

# Rollback sain
python3 pipelines/rollback_release.py diagops-m4-reference-r1 \
  --current artifacts/current.json --history artifacts/history
```

Runbook complet : `docs/runbook.md`.

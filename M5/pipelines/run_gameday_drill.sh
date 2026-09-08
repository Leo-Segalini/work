#!/usr/bin/env bash
# Drill incident labo M5 — ~2 min — pour voir l'évolution dans Prometheus.
# Usage (Compose déjà up) :
#   cd work/M5 && ./pipelines/run_gameday_drill.sh
set -euo pipefail
cd "$(dirname "$0")/.."

BASE="${BASE_URL:-http://127.0.0.1:8000}"
HOLD_SEC="${HOLD_SEC:-90}"

echo "=== 1) Ouvre Prometheus AVANT de continuer ==="
echo "    http://127.0.0.1:9090"
echo "    Graph → Last 5 minutes → query: diagops_index_valid"
echo "    clique Execute, laisse le graphe ouvert (auto-refresh si dispo)"
echo ""
read -r -p "Prometheus ouvert ? Entrée pour injecter la faute… " _

echo "=== 2) Baseline ==="
curl -s -w "\nHTTP %{http_code}\n" "$BASE/health/ready"
date -u +"%Y-%m-%dT%H:%M:%SZ baseline"

echo "=== 3) Injection index_valid=false ==="
docker compose -f deploy/compose.yaml exec -T api python -c \
  "from pathlib import Path; Path('artifacts/runtime').mkdir(parents=True, exist_ok=True); Path('artifacts/runtime/faults.json').write_text('{\"index_valid\": false}')"
date -u +"%Y-%m-%dT%H:%M:%SZ fault_on"
echo "Attendue: curl ready → 503 ; Prometheus diagops_index_valid → 0 (sous 15-20 s)"
curl -s -w "\nHTTP %{http_code}\n" "$BASE/health/ready" || true

echo "=== 4) Maintien incident ${HOLD_SEC}s — REGARDE LE GRAPH ==="
for ((i=15; i<=HOLD_SEC; i+=15)); do
  sleep 15
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health/ready" || echo 000)
  date -u +"%Y-%m-%dT%H:%M:%SZ hold_${i}s ready=${code}"
done

echo "=== 5) Clear faute ==="
docker compose -f deploy/compose.yaml exec -T api python -c \
  "from pathlib import Path; Path('artifacts/runtime/faults.json').unlink(missing_ok=True)"
date -u +"%Y-%m-%dT%H:%M:%SZ fault_off"
curl -s -w "\nHTTP %{http_code}\n" "$BASE/health/ready"

echo "=== 6) Attente scrape recovery (~20 s) ==="
sleep 20
curl -s -w "\nHTTP %{http_code}\n" "$BASE/health/ready"
date -u +"%Y-%m-%dT%H:%M:%SZ done"
echo ""
echo "Sur le graph: tu dois voir un CRÉNEAU à 0 puis retour à 1."
echo "Si ligne plate à 1: tu regardes APRÈS l'exercice → rejoue avec le graph OUVERT."

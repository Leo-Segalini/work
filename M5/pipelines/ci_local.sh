#!/usr/bin/env bash
# CI locale M5 — tests + index candidat + gate (pas de promotion auto).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CANDIDATE="${CANDIDATE:-artifacts/candidates/local}"
MANIFEST="${MANIFEST:-../../data_pack/2026-S1/knowledge/manifest.csv}"
DOCUMENTS="${DOCUMENTS:-../../data_pack/2026-S1/knowledge/documents}"
METRICS="${METRICS:-../../data_pack/2026-S1/reference_runs/m4_for_m5/evaluation/metrics_calibration.json}"
GATES="${GATES:-configs/gates.json}"

echo "== pytest =="
python3 -m pytest -q

echo "== build_index =="
mkdir -p "$CANDIDATE"
python3 pipelines/build_index.py \
  --manifest "$MANIFEST" \
  --documents "$DOCUMENTS" \
  --output "$CANDIDATE/index.json"

echo "== evaluate_release =="
python3 pipelines/evaluate_release.py \
  --index "$CANDIDATE/index.json" \
  --metrics "$METRICS" \
  --gates "$GATES" \
  --output "$CANDIDATE/gate_report.json"

STATUS="$(python3 -c "import json; print(json.load(open('$CANDIDATE/gate_report.json'))['status'])")"
echo "Gate status: $STATUS"
if [[ "$STATUS" != "passed" ]]; then
  echo "CI REFUSÉE — aucune promotion."
  exit 1
fi
echo "CI OK — promotion manuelle uniquement (promote_release.py)."

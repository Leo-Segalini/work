#!/usr/bin/env python3
"""Mini-audit des relevés capteurs — avant toute intégration dans processed/.

Objectif : détecter et documenter ce qui ne doit PAS être intégré tel quel :
- valeurs impossibles / sentinelles / hors plages physiques plausibles ;
- incohérences sensor_name ↔ unit (données « inventées » ou mal typées) ;
- doublons de clé avec valeurs divergentes ;
- équipements inconnus ;
- horodatages illisibles / hors période ;
- indices de données sensibles dans les champs texte (rare sur capteurs).

Ne modifie jamais data_pack/. Écrit uniquement sous output/audit/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

# Plages physiques plausibles (bornes pédagogiques, à justifier dans le registre).
# Hors plage = candidat à quarantaine, pas suppression silencieuse.
PLAUSIBLE_RANGES: dict[str, tuple[float, float]] = {
    "vibration_mm_s": (0.0, 80.0),
    "temperature_c": (-40.0, 200.0),
    "pressure_bar": (-1.0, 100.0),
    "current_a": (0.0, 500.0),
    "rpm": (0.0, 10000.0),
}

EXPECTED_UNITS = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}

SENTINELS = {-9999.0, -999.0, 9999.0, 99999.0}

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}")
PERSON_RE = re.compile(
    r"\b(?:Mme|M\.|Mr|Prénom|appeler|rappeler)\b.*?\b[A-ZÀÂÄÉÈÊËÎÏÔÙÛÜ][a-zàâäéèêëîïôùûü]+",
    re.I,
)

KEY = ["equipment_id", "timestamp", "sensor_name"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def row_id(row: pd.Series) -> str:
    """Identifiant rejouable sans PK fournie."""
    return f"{row['equipment_id']}|{row['timestamp']}|{row['sensor_name']}"


def find_data_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    roots = [Path.cwd().resolve(), *Path.cwd().resolve().parents]
    for root in roots:
        candidate = root / "data_pack" / "2026-S1"
        if (candidate / "sensors" / "sensor_readings.csv").is_file():
            return candidate
    raise FileNotFoundError("data_pack/2026-S1 introuvable — passer --data-dir")


def scan_pii_in_strings(frame: pd.DataFrame) -> list[dict]:
    hits: list[dict] = []
    text_cols = [c for c in frame.columns if frame[c].dtype == object]
    for col in text_cols:
        for idx, val in frame[col].dropna().astype(str).items():
            rules = []
            if EMAIL_RE.search(val):
                rules.append("PII-EMAIL")
            if PHONE_RE.search(val):
                rules.append("PII-PHONE")
            if PERSON_RE.search(val):
                rules.append("PII-PERSON")
            for rule in rules:
                hits.append(
                    {
                        "source_file": "sensor_readings.csv",
                        "row_identifier": row_id(frame.loc[idx]),
                        "rule_id": rule,
                        "column": col,
                        "observed_value": val[:120],
                        "reason": "indice de donnée personnelle dans un champ texte",
                        "decision": "quarantine",
                    }
                )
    return hits


def audit(data_dir: Path, out_dir: Path) -> dict:
    sensors_path = data_dir / "sensors" / "sensor_readings.csv"
    equipment_path = data_dir / "equipment" / "equipment.csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    sensors = pd.read_csv(sensors_path)
    equipment = pd.read_csv(equipment_path)
    known_eq = set(equipment["equipment_id"].astype(str))

    findings: list[dict] = []

    # --- schéma minimal ---
    required = ["equipment_id", "timestamp", "sensor_name", "value", "unit", "period"]
    missing_cols = [c for c in required if c not in sensors.columns]
    if missing_cols:
        findings.append(
            {
                "source_file": "sensor_readings.csv",
                "row_identifier": "*",
                "rule_id": "SNS-SCHEMA",
                "column": ",".join(missing_cols),
                "observed_value": "",
                "reason": "colonnes obligatoires absentes",
                "decision": "block",
            }
        )

    # --- parsing valeurs / temps ---
    sensors = sensors.copy()
    sensors["_value"] = pd.to_numeric(sensors["value"], errors="coerce")
    sensors["_ts"] = pd.to_datetime(sensors["timestamp"], errors="coerce", utc=True, format="mixed")
    sensors["_row_id"] = sensors.apply(row_id, axis=1)

    bad_value = sensors["_value"].isna() & sensors["value"].notna()
    for _, row in sensors.loc[bad_value].iterrows():
        findings.append(
            {
                "source_file": "sensor_readings.csv",
                "row_identifier": row["_row_id"],
                "rule_id": "SNS-VALUE-NAN",
                "column": "value",
                "observed_value": str(row["value"]),
                "reason": "valeur non numérique (illisible ou inventée)",
                "decision": "quarantine",
            }
        )

    bad_ts = sensors["_ts"].isna() & sensors["timestamp"].notna()
    for _, row in sensors.loc[bad_ts].iterrows():
        findings.append(
            {
                "source_file": "sensor_readings.csv",
                "row_identifier": row["_row_id"],
                "rule_id": "SNS-TS-PARSE",
                "column": "timestamp",
                "observed_value": str(row["timestamp"]),
                "reason": "horodatage illisible",
                "decision": "quarantine",
            }
        )

    # --- unité ↔ nom de capteur ---
    for _, row in sensors.iterrows():
        expected = EXPECTED_UNITS.get(str(row["sensor_name"]))
        if expected is None:
            findings.append(
                {
                    "source_file": "sensor_readings.csv",
                    "row_identifier": row["_row_id"],
                    "rule_id": "SNS-UNKNOWN-SENSOR",
                    "column": "sensor_name",
                    "observed_value": str(row["sensor_name"]),
                    "reason": "nom de capteur hors contrat connu",
                    "decision": "quarantine",
                }
            )
        elif str(row["unit"]) != expected:
            findings.append(
                {
                    "source_file": "sensor_readings.csv",
                    "row_identifier": row["_row_id"],
                    "rule_id": "SNS-UNIT-MISMATCH",
                    "column": "unit",
                    "observed_value": f"{row['sensor_name']}={row['unit']}",
                    "reason": f"unité attendue {expected}",
                    "decision": "quarantine",
                }
            )

    # --- sentinelles & plages ---
    for _, row in sensors.dropna(subset=["_value"]).iterrows():
        val = float(row["_value"])
        if val in SENTINELS:
            findings.append(
                {
                    "source_file": "sensor_readings.csv",
                    "row_identifier": row["_row_id"],
                    "rule_id": "SNS-SENTINEL",
                    "column": "value",
                    "observed_value": str(val),
                    "reason": "valeur sentinelle suspecte",
                    "decision": "quarantine",
                }
            )
            continue
        bounds = PLAUSIBLE_RANGES.get(str(row["sensor_name"]))
        if bounds is not None and not (bounds[0] <= val <= bounds[1]):
            findings.append(
                {
                    "source_file": "sensor_readings.csv",
                    "row_identifier": row["_row_id"],
                    "rule_id": "SNS-RANGE",
                    "column": "value",
                    "observed_value": str(val),
                    "reason": f"hors plage plausible {bounds}",
                    "decision": "hold_for_review",
                }
            )

    # --- équipement inconnu ---
    unknown = ~sensors["equipment_id"].astype(str).isin(known_eq)
    for _, row in sensors.loc[unknown].iterrows():
        findings.append(
            {
                "source_file": "sensor_readings.csv",
                "row_identifier": row["_row_id"],
                "rule_id": "SNS-FK-EQ",
                "column": "equipment_id",
                "observed_value": str(row["equipment_id"]),
                "reason": "équipement absent de equipment.csv",
                "decision": "quarantine",
            }
        )

    # --- doublons de clé ---
    dup_mask = sensors.duplicated(subset=KEY, keep=False)
    dups = sensors.loc[dup_mask].copy()
    if not dups.empty:
        for key, group in dups.groupby(KEY, dropna=False):
            values = group["_value"].dropna().unique()
            if len(values) <= 1:
                rule, reason, decision = (
                    "SNS-DUP-STRICT",
                    "doublon strict (même valeur)",
                    "hold_for_review",
                )
            else:
                rule, reason, decision = (
                    "SNS-DUP-CONFLICT",
                    f"doublon de clé avec valeurs divergentes: {sorted(map(float, values))}",
                    "quarantine",
                )
            for _, row in group.iterrows():
                findings.append(
                    {
                        "source_file": "sensor_readings.csv",
                        "row_identifier": row["_row_id"],
                        "rule_id": rule,
                        "column": "value",
                        "observed_value": str(row.get("value")),
                        "reason": reason,
                        "decision": decision,
                    }
                )

    # --- période / fuseau ---
    ts_text = sensors["timestamp"].astype("string")
    naive = ~ts_text.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False) & ts_text.notna()
    for _, row in sensors.loc[naive].head(200).iterrows():  # plafond pour lisibilité
        findings.append(
            {
                "source_file": "sensor_readings.csv",
                "row_identifier": row["_row_id"],
                "rule_id": "SNS-TS-NAIVE",
                "column": "timestamp",
                "observed_value": str(row["timestamp"]),
                "reason": "horodatage sans fuseau (hypothèse UTC à documenter)",
                "decision": "info",
            }
        )

    # --- PII ---
    findings.extend(scan_pii_in_strings(sensors.drop(columns=["_value", "_ts", "_row_id"], errors="ignore")))

    findings_df = pd.DataFrame(findings)
    if findings_df.empty:
        findings_df = pd.DataFrame(
            columns=[
                "source_file",
                "row_identifier",
                "rule_id",
                "column",
                "observed_value",
                "reason",
                "decision",
            ]
        )

    # Lignes à ne pas intégrer (décisions bloquantes / quarantaine)
    block_decisions = {"quarantine", "block"}
    blocked_ids = set(
        findings_df.loc[findings_df["decision"].isin(block_decisions), "row_identifier"].astype(str)
    )
    # hold_for_review = ne pas intégrer sans avis
    hold_ids = set(
        findings_df.loc[findings_df["decision"] == "hold_for_review", "row_identifier"].astype(str)
    )
    exclude_ids = blocked_ids | hold_ids

    sensors["_exclude"] = sensors["_row_id"].isin(exclude_ids)
    candidates_ok = sensors.loc[~sensors["_exclude"]].drop(
        columns=["_value", "_ts", "_row_id", "_exclude"], errors="ignore"
    )
    candidates_hold = sensors.loc[sensors["_row_id"].isin(exclude_ids)].drop(
        columns=["_value", "_ts", "_row_id", "_exclude"], errors="ignore"
    )

    # --- overview ---
    overview = {
        "source": str(sensors_path),
        "sha256": sha256_file(sensors_path),
        "rows_total": int(len(sensors)),
        "equipment_instrumented": int(sensors["equipment_id"].nunique()),
        "equipment_known": int(len(known_eq)),
        "coverage_rate": round(sensors["equipment_id"].astype(str).isin(known_eq).mean(), 4),
        "sensor_names": sensors["sensor_name"].value_counts().to_dict(),
        "units": sensors["unit"].value_counts().to_dict(),
        "period_min": str(sensors["_ts"].min()),
        "period_max": str(sensors["_ts"].max()),
        "findings_total": int(len(findings_df)),
        "by_rule": findings_df["rule_id"].value_counts().to_dict() if len(findings_df) else {},
        "by_decision": findings_df["decision"].value_counts().to_dict() if len(findings_df) else {},
        "rows_ok_for_integration": int(len(candidates_ok)),
        "rows_excluded_pending_review": int(len(candidates_hold)),
        "integration_policy": (
            "Ne pas écrire dans output/processed/ tant que les lignes "
            "quarantine/block/hold_for_review n'ont pas été arbitrées."
        ),
        "plausible_ranges_used": {k: list(v) for k, v in PLAUSIBLE_RANGES.items()},
    }

    findings_df.to_csv(out_dir / "sensor_findings.csv", index=False)
    candidates_hold.to_csv(out_dir / "sensor_rows_to_exclude.csv", index=False)
    # Intentionnel : pas de processed/ — seulement un inventaire des lignes saines
    candidates_ok.to_csv(out_dir / "sensor_rows_ok_candidate.csv", index=False)
    (out_dir / "sensor_audit_summary.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = [
        "# Audit capteurs M3 — avant intégration",
        "",
        f"- Fichier : `{sensors_path}`",
        f"- SHA-256 : `{overview['sha256'][:16]}…`",
        f"- Lignes totales : **{overview['rows_total']}**",
        f"- Équipements instrumentés : **{overview['equipment_instrumented']}** / {overview['equipment_known']}",
        f"- Période observée : {overview['period_min']} → {overview['period_max']}",
        f"- Findings : **{overview['findings_total']}**",
        f"- OK candidats : **{overview['rows_ok_for_integration']}**",
        f"- À exclure / revoir : **{overview['rows_excluded_pending_review']}**",
        "",
        "## Décisions",
        "",
        "| decision | count |",
        "|---|---:|",
    ]
    for k, v in sorted(overview["by_decision"].items(), key=lambda x: (-x[1], x[0])):
        md_lines.append(f"| {k} | {v} |")
    md_lines += [
        "",
        "## Règles déclenchées",
        "",
        "| rule_id | count |",
        "|---|---:|",
    ]
    for k, v in sorted(overview["by_rule"].items(), key=lambda x: (-x[1], x[0])):
        md_lines.append(f"| {k} | {v} |")
    md_lines += [
        "",
        "## Politique",
        "",
        overview["integration_policy"],
        "",
        "Fichiers : `sensor_findings.csv`, `sensor_rows_to_exclude.csv`, "
        "`sensor_rows_ok_candidate.csv`, `sensor_audit_summary.json`.",
        "",
        "**Aucune écriture dans `output/processed/`.**",
    ]
    (out_dir / "sensor_audit_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return overview


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit des relevés capteurs avant intégration")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/audit"),
        help="dossier de sortie (défaut: output/audit)",
    )
    args = parser.parse_args()
    data_dir = find_data_dir(args.data_dir)
    overview = audit(data_dir, args.output.resolve())
    print(json.dumps({k: overview[k] for k in (
        "rows_total",
        "findings_total",
        "rows_ok_for_integration",
        "rows_excluded_pending_review",
        "by_rule",
        "by_decision",
    )}, ensure_ascii=False, indent=2))
    print(f"\n→ rapport : {args.output.resolve() / 'sensor_audit_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

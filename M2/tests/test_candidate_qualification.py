from pathlib import Path

import pytest

from src.candidate_qualification import qualify_candidate, verify_checksums

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "../../data_pack/2026-S1"
CANDIDATE = DATA / "m2_candidate_release"


@pytest.mark.skipif(not CANDIDATE.is_dir(), reason="data_pack candidate absent")
def test_candidate_checksums_valid():
    results = verify_checksums(CANDIDATE.resolve())
    assert results
    assert all(r["ok"] for r in results)


@pytest.mark.skipif(not CANDIDATE.is_dir(), reason="data_pack candidate absent")
def test_candidate_release_is_rejected(tmp_path):
    summary = qualify_candidate(
        DATA.resolve(),
        CANDIDATE.resolve(),
        tmp_path / "out",
    )
    assert summary["decision"] == "REJECTED"
    assert summary["blocking"] >= 10
    assert summary["counts"]["events_new"] == 80
    assert (tmp_path / "out/candidate_findings.csv").is_file()
    assert (tmp_path / "out/decision_candidate.md").is_file()

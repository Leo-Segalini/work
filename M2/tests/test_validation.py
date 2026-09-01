import pandas as pd

from src.data_pipeline.pii import mask_pii, scan_notes_for_pii
from src.data_pipeline.validation import missing_required_columns


def test_valid_frame_has_no_missing_required_column():
    frame = pd.DataFrame([{"equipment_id": "EQ-001", "site_id": "SITE-A"}])
    assert missing_required_columns(frame, ["equipment_id", "site_id"]) == []


def test_invalid_frame_reports_missing_required_column():
    frame = pd.DataFrame([{"equipment_id": "EQ-001"}])
    assert missing_required_columns(frame, ["equipment_id", "site_id"]) == ["site_id"]


def test_mask_pii_email_and_phone():
    text = "Appeler Nadia B. au 06 12 34 56 78 ou leo.martin@example.test"
    masked, kinds = mask_pii(text)
    assert "email" in kinds
    assert "telephone" in kinds
    assert "personne" in kinds
    assert "@" not in masked
    assert "06 12 34 56 78" not in masked
    assert "[EMAIL_MASQUE]" in masked
    assert "[TEL_MASQUE]" in masked


def test_scan_notes_creates_quarantine_records():
    frame = pd.DataFrame(
        [
            {
                "maintenance_id": "MNT-1",
                "work_order_note": "Compte rendu à leo.martin@example.test",
            }
        ]
    )
    out, records = scan_notes_for_pii(
        frame,
        source_file="maintenance_history.csv",
        id_col="maintenance_id",
    )
    assert any(r["rule_id"] == "PII-EMAIL" for r in records)
    assert "[EMAIL_MASQUE]" in out.loc[0, "work_order_note"]

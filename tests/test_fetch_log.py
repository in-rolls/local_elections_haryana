"""Source receipts must survive consolidation into the fetch log."""

import json

import pytest

from local_elections_haryana.build import fetch_log


def test_source_receipt_provenance_and_tampering(tmp_path, monkeypatch):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"source document")
    receipt = {
        "sha256": fetch_log.digest(path),
        "bytes": path.stat().st_size,
        "url": "https://example.org/report.pdf",
        "retrieved_at": "2026-11-10T03:00:00+00:00",
    }
    path.with_name(path.name + ".receipt.json").write_text(json.dumps(receipt))
    monkeypatch.setattr(fetch_log, "ROOT", tmp_path)
    monkeypatch.setattr(fetch_log, "LOG", tmp_path / "fetch_log.csv")
    monkeypatch.setattr(fetch_log, "urls", lambda: {})
    monkeypatch.setattr(fetch_log, "tracked", lambda: ["report.pdf"])
    row = fetch_log.rows()[0]
    assert row["url"] == receipt["url"]
    assert row["fetched_at_utc"] == receipt["retrieved_at"]
    assert row["method"] == "live"
    path.write_bytes(b"changed document")
    with pytest.raises(ValueError, match="source receipt"):
        fetch_log.rows()

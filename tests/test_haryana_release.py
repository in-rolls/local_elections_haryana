"""Haryana historical release: every observation is accounted for."""

from pathlib import Path

import pyarrow.parquet as pq

from local_elections_haryana import build_release


def test_historical_release_reconciles_every_row(tmp_path: Path):
    receipt = build_release.build(tmp_path)
    assert receipt["release_ready"] is True
    historical = receipt["historical"]
    assert (
        historical["included_source_reviewed_occurrences"]
        + historical["reviewed_unresolved_quarantine"]
        + historical["provisional_or_nonseat_preserved_outside_release"]
        == historical["input_observations"]
        == 70592
    )
    assert historical["missing_heading_quarantine"] == 32
    assert pq.read_table(tmp_path / "historical_quarantine.parquet").num_rows == 61


def test_release_inputs_live_in_this_repository():
    for path in build_release.EXPECTED:
        assert path.is_relative_to(build_release.ROOT)

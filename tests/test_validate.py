"""Ensure a derived-data check cannot silently validate the published files."""

import subprocess
import sys
from pathlib import Path


def test_missing_derived_input_fails(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/validate.py"
    result = subprocess.run(
        [sys.executable, str(script), "--year", "2016", "--input-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert str(tmp_path / "gp_reservation.csv") in result.stderr

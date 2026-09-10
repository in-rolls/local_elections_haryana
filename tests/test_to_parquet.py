"""Test preservation of observation identity and missing source values."""

import csv

import pyarrow.parquet as pq
import pytest
from to_parquet import read_snapshot, schema, write_atomic


def snapshot(tmp_path, *, flag="", width=None):
    path = tmp_path / "ward.csv"
    fields = schema("ward").names[1:]
    row = dict.fromkeys(fields, "")
    row.update(
        district="Example district",
        block="Example block",
        sr_no="001",
        gram_panchayat="Example GP",
        ward_no="",
        printings_agree=flag,
        woman_reserved="1",
        unopposed="0",
        vacant="0",
    )
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        values = [row[name] for name in fields]
        writer.writerow(values if width is None else values[:width])
        writer.writerow(values)
    return path


def test_roundtrip_preserves_duplicates_identifiers_and_missing_values(tmp_path):
    table = read_snapshot(snapshot(tmp_path), 2016, "ward")
    output = tmp_path / "ward.parquet"
    write_atomic(output, table)
    restored = pq.read_table(output)
    assert restored.equals(table, check_metadata=True)
    assert restored.num_rows == 2
    row = restored.to_pylist()[0]
    assert row["sr_no"] == "001"
    assert row["ward_no"] is None
    assert row["printings_agree"] is None
    assert row["woman_reserved"] is True
    assert row["unopposed"] is False
    assert row["year"] == 2016


@pytest.mark.parametrize("flag", ["yes", "2", "false"])
def test_invalid_flags_rejected(tmp_path, flag):
    with pytest.raises(ValueError, match="invalid printings_agree"):
        read_snapshot(snapshot(tmp_path, flag=flag), 2016, "ward")


def test_ragged_csv_rejected(tmp_path):
    with pytest.raises(ValueError, match="column count"):
        read_snapshot(snapshot(tmp_path, width=3), 2016, "ward")


def test_failed_write_preserves_existing_output(tmp_path, monkeypatch):
    output = tmp_path / "snapshot.parquet"
    output.write_bytes(b"previous")

    def fail(_table, path, **_kwargs):
        path.write_bytes(b"incomplete")
        raise OSError("interrupted")

    monkeypatch.setattr(pq, "write_table", fail)
    with pytest.raises(OSError, match="interrupted"):
        write_atomic(output, read_snapshot(snapshot(tmp_path), 2016, "ward"))
    assert output.read_bytes() == b"previous"
    assert not output.with_suffix(".parquet.part").exists()

"""Export the published CSV snapshots without changing their observation units."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from local_elections_haryana.paths import SEAT_TABLES

DATA = Path(__file__).resolve().parents[3] / "data"
YEARS = (2000, 2005, 2010, 2016, 2022)
FLAGS = {"reserved_woman", "unopposed", "vacant", "printings_agree"}
GP_COLUMNS = (
    "district",
    "block",
    "sr_no",
    "gram_panchayat",
    "reserved_label",
    "reserved_caste",
    "reserved_woman",
    "winner",
    "father_husband",
    "unopposed",
    "vacant",
    "reserved_raw",
    "script",
    "printings_agree",
    "notification",
    "source_pdf",
)


def schema(kind):
    """Keep source identifiers as strings, including any leading zeroes."""
    columns = list(GP_COLUMNS)
    if kind == "ward":
        columns.insert(4, "ward_no")
    elif kind != "gp":
        raise ValueError(f"Unknown seat kind: {kind}")
    return pa.schema(
        [pa.field("year", pa.int16(), nullable=False)]
        + [
            pa.field(name, pa.bool_() if name in FLAGS else pa.string())
            for name in columns
        ]
    )


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_snapshot(path, year, kind):
    """Validate CSV structure and flags, retaining row order and duplicates."""
    contract = schema(kind)
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != contract.names[1:]:
            raise ValueError(f"{path}: unexpected columns: {reader.fieldnames}")
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{line}: inconsistent column count")
            record = {"year": year}
            for name, value in row.items():
                if name in FLAGS:
                    if value not in {"", "0", "1"}:
                        raise ValueError(f"{path}:{line}: invalid {name}: {value!r}")
                    record[name] = None if value == "" else value == "1"
                else:
                    record[name] = value if value != "" else None
            rows.append(record)
    if not rows:
        raise ValueError(f"{path}: no observations")
    return pa.Table.from_pylist(rows, schema=contract)


def write_atomic(path, table):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        pq.write_table(table, temporary, compression="zstd")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def export(data, check=False):
    """Build or verify the released seat tables and data/MANIFEST.json."""
    entries = []
    for year in YEARS:
        for kind in ("gp", "ward"):
            source = data / "extracted" / str(year) / f"{kind}_reservation.csv"
            target = data / "release" / str(year) / SEAT_TABLES[kind]
            table = read_snapshot(source, year, kind)
            if check:
                if not target.exists():
                    raise ValueError(f"Missing export: {target}")
                if not table.equals(pq.read_table(target), check_metadata=True):
                    raise ValueError(f"{target}: rows or schema differ from {source}")
            else:
                write_atomic(target, table)
            entries.append(
                {
                    "file": target.relative_to(data).as_posix(),
                    "source_csv": source.relative_to(data).as_posix(),
                    "source_sha256": sha256(source),
                    "sha256": sha256(target),
                    "rows": table.num_rows,
                    "year": year,
                    "seat_kind": kind,
                    "schema": [
                        {"name": f.name, "type": str(f.type), "nullable": f.nullable}
                        for f in table.schema
                    ],
                }
            )
            print(f"{target.relative_to(data)}: {table.num_rows:,} rows")
    manifest = {"format_version": 1, "files": entries}
    path = data / "MANIFEST.json"
    if check:
        if json.loads(path.read_text()) != manifest:
            raise ValueError(f"{path}: hashes or metadata differ from the files")
    else:
        temporary = path.with_suffix(".json.part")
        try:
            temporary.write_text(json.dumps(manifest, indent=2) + "\n")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return manifest


def verify_sources(data):
    """Verify downloaded PDF bytes against the retained acquisition manifests."""
    for year in YEARS:
        directory = data / "raw" / str(year)
        with (directory / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"{year}: empty source manifest")
        # 2000's scans (660 MB) stay in the git-ignored raw archive; its manifest
        # names them there, with public URLs, and they are verified when held.
        paths = [
            data / row["archive_path"]
            if row.get("archive_path")
            else directory / row["saved_as"]
            for row in rows
        ]
        if all(row.get("archive_path") for row in rows) and not any(
            p.exists() for p in paths
        ):
            print(f"{year}: {len(rows)} source PDFs not held (raw archive); skipped")
            continue
        for row, path in zip(rows, paths, strict=True):
            if (
                path.stat().st_size != int(row["bytes"])
                or sha256(path) != row["sha256"]
            ):
                raise ValueError(f"{path}: bytes differ from the source manifest")
        print(f"{year}: verified {len(rows)} source PDFs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        export(args.data, check=args.check)
        if args.check:
            verify_sources(args.data)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()

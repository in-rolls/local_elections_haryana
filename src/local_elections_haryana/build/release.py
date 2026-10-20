"""Verify source-to-release values and refresh the Parquet inventory."""

import argparse
import json
import re
import tempfile
from pathlib import Path

import pyarrow.parquet as pq

from local_elections_haryana.build.build_release import DEFAULT_OUT, build
from local_elections_haryana.parse.to_parquet import export, verify_sources
from local_elections_haryana.paths import ROOT, digest, inside

DATA = ROOT / "data"
UNITS = {
    "printing_reconciliation.parquet": "Archived comparison of printed occurrences",
    "modern_seats.parquet": "Archived modern seat record",
    "historical_reviewed_occurrences.parquet": "Reviewed 2000 printed occurrence",
    "historical_quarantine.parquet": "Reviewed 2000 occurrence with unresolved fields",
    "historical_provisional_observations.parquet": (
        "Provisional OCR or reviewed non-seat occurrence"
    ),
    "historical_reservation_occurrences.parquet": (
        "Archived historical reservation occurrence"
    ),
    "modern_quarantine.parquet": "Archived modern record requiring review",
    "seat_rows.parquet": "Archived OCR/review observation; not a unique seat",
}


def summary():
    lines = ["<!-- datasets:start -->", ""]
    published = sorted([*DATA.glob("fin/*.parquet"), *DEFAULT_OUT.glob("*.parquet")])
    snapshots = sorted(DATA.glob("release/observations/*/*.parquet"))
    for paths, archived in [(published, False), (snapshots, True)]:
        if archived:
            lines.extend(
                [
                    "",
                    "<details>",
                    "<summary>Retained observation snapshots</summary>",
                    "",
                ]
            )
        lines.extend(["| File | Rows | Each row represents |", "| --- | ---: | --- |"])
        for path in paths:
            name = path.relative_to(ROOT).as_posix()
            label = path.relative_to(DATA).as_posix()
            if archived:
                label = f"observations/{path.parent.name[:12]}/{path.name}"
            unit = (
                "GP head seat record"
                if path.name.startswith("gp_reservation_")
                else "GP ward seat record"
                if path.name.startswith("ward_reservation_")
                else UNITS[path.name]
            )
            rows = pq.ParquetFile(path).metadata.num_rows
            lines.append(f"| [{label}]({name}) | {rows:,} | {unit} |")
        if archived:
            lines.extend(["", "</details>"])
    lines.extend(["", "<!-- datasets:end -->"])
    readme = ROOT / "README.md"
    pattern = r"<!-- datasets:start -->.*?<!-- datasets:end -->"
    text = readme.read_text()
    if len(re.findall(pattern, text, flags=re.S)) != 1:
        raise ValueError("README must contain one dataset inventory block")
    readme.write_text(re.sub(pattern, lambda _: "\n".join(lines), text, flags=re.S))


def verify():
    export(DATA, DATA / "fin", check=True)
    verify_sources(DATA)
    for manifest in sorted((DATA / "release").rglob("SHA256SUMS")):
        for line in manifest.read_text().splitlines():
            expected, name = line.split(maxsplit=1)
            path = inside(manifest.parent, name)
            if digest(path) != expected:
                raise ValueError(f"Retained artifact changed: {path}")
    with tempfile.TemporaryDirectory(prefix="haryana-verify-") as temp:
        out = Path(temp)
        receipt = build(out)
        published = json.loads((DEFAULT_OUT / "release_receipt.json").read_text())
        if receipt["historical"] != published["historical"]:
            raise ValueError("Historical release counts differ from published records")
        for path in sorted(DEFAULT_OUT.glob("*.parquet")):
            expected, actual = pq.read_table(path), pq.read_table(out / path.name)
            if not expected.equals(actual):
                changed = [
                    name
                    for name in expected.column_names
                    if name not in actual.column_names
                    or not expected[name].equals(actual[name])
                ]
                raise ValueError(f"{path.name}: rebuilt fields differ: {changed}")
    print("Published modern and historical records reproduce from retained sources.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify", "summary"])
    args = parser.parse_args()
    {"verify": verify, "summary": summary}[args.command]()


if __name__ == "__main__":
    main()

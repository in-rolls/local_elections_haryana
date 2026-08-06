"""Download the Haryana SEC notification corpus for one election year.

Network stage of the pipeline. Downloads nothing but PDFs and writes a manifest;
it does not parse notification content - parse.py does that, offline.

Files are saved under a readable name built from the index (Rohtak__Meham.pdf,
not 2022120213-3.pdf) and recorded in manifest.csv with a SHA-256, so a later
run can prove it fetched the same bytes.
"""

import argparse
import concurrent.futures
import csv
import hashlib
import pathlib
import re
import sys
import urllib.request

import index_pdf

YEAR = "2022"

# Statewide index of the 30 November 2022 notifications, linked from
# https://secharyana.gov.in/orders-notifications-related-to-panchayat-elections-2021/
INDEX_URL = {
    "2022": "https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c"
            "/uploads/2022/12/2022121338.pdf",
}

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
MANIFEST_COLUMNS = ["district", "block", "saved_as", "sha256", "bytes",
                    "source_filename", "url"]


def fetch(url, dest, timeout=180):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    dest.write_bytes(payload)
    return payload


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(district, block, fallback):
    """Readable, collision-free filename stem for a notification."""
    parts = [re.sub(r"[^A-Za-z0-9]+", "-", p).strip("-") for p in (district, block) if p]
    return "__".join(parts) or pathlib.Path(fallback).stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default=YEAR)
    ap.add_argument("--refresh", action="store_true",
                    help="re-download files already present")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if args.year not in INDEX_URL:
        sys.exit(f"no index URL known for {args.year}")

    year_dir = DATA / args.year
    pdf_dir = year_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    index_path = year_dir / "index.pdf"

    if args.refresh or not index_path.exists():
        print(f"index -> {index_path}")
        fetch(INDEX_URL[args.year], index_path)

    entries = index_pdf.read(index_path)
    print(f"{len(entries)} notifications listed in the index")

    # a district/block pair can appear more than once; keep names unique
    used = {}
    for entry in entries:
        stem = slug(entry["district"], entry["block"], entry["filename"])
        used[stem] = used.get(stem, 0) + 1
        if used[stem] > 1:
            stem = f"{stem}-{used[stem]}"
        entry["saved_as"] = f"{stem}.pdf"

    todo = [e for e in entries
            if args.refresh or not (pdf_dir / e["saved_as"]).exists()]
    if todo:
        print(f"downloading {len(todo)} of {len(entries)}")
        failures = []
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            futures = {pool.submit(fetch, e["url"], pdf_dir / e["saved_as"]): e
                       for e in todo}
            for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
                entry = futures[future]
                try:
                    future.result()
                except Exception as exc:  # noqa: BLE001 - collect and report
                    failures.append((entry["saved_as"], exc))
                print(f"\r  {done}/{len(todo)}", end="", file=sys.stderr)
        print(file=sys.stderr)
        for name, exc in failures:
            print(f"FAILED {name}: {exc}", file=sys.stderr)
        if failures:
            sys.exit(1)
    else:
        print(f"all {len(entries)} already downloaded")

    for entry in entries:
        path = pdf_dir / entry["saved_as"]
        entry["sha256"] = digest(path)
        entry["bytes"] = path.stat().st_size
        entry["source_filename"] = entry.pop("filename")

    manifest = year_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(entries)

    total = sum(e["bytes"] for e in entries)
    print(f"wrote {manifest} ({len(entries)} rows, {total / 1e6:.0f} MB on disk)")


if __name__ == "__main__":
    main()

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
import html
import io
import json
import pathlib
import re
import sys
import urllib.request

import index_pdf
import pdfplumber

YEAR = "2022"

# How each election year publishes its notifications.
#
# 2022 is a single index PDF whose hyperlinks point at one PDF per block.
# 2016 is an HTML page linking one PDF per district, each containing every
# block in that district. The 2016 files are served from an NIC host that no
# longer answers, so they are fetched from the Internet Archive instead.
SOURCES = {
    "2022": {
        "style": "index-pdf",
        "url": "https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c"
        "/uploads/2022/12/2022121338.pdf",
    },
    "2016": {
        "style": "page-list",
        "url": "https://secharyana.gov.in/notifications-of-elected-candidates-of-"
        "panchayati-raj-institution-in-5th-general-elections-2016-in-the-"
        "state-of-haryana/",
        "prefer": "-e.pdf",  # the English printing; each district also has -H
        "via_wayback": True,
    },
}

CDX = (
    "https://web.archive.org/cdx/search/cdx?url={prefix}*&output=json"
    "&fl=timestamp,original,statuscode&collapse=urlkey&limit=500"
)

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
MANIFEST_COLUMNS = [
    "district",
    "block",
    "saved_as",
    "sha256",
    "bytes",
    "source_filename",
    "url",
]


def fetch(url, dest, timeout=180):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
        expected = response.headers.get("Content-Length")
        if expected is not None and len(payload) != int(expected):
            raise ValueError(f"Incomplete download: {url}")
    if not payload.lstrip().startswith(b"%PDF-"):
        raise ValueError(f"Response is not a PDF: {url}")
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        if not pdf.pages:
            raise ValueError(f"PDF has no pages: {url}")
    temporary = dest.with_suffix(dest.suffix + ".part")
    try:
        temporary.write_bytes(payload)
        temporary.replace(dest)
    finally:
        temporary.unlink(missing_ok=True)
    return payload


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wayback_urls(prefix):
    """Map original URL -> archived URL, for a host that no longer answers."""
    with urllib.request.urlopen(CDX.format(prefix=prefix), timeout=120) as response:
        rows = json.load(response)[1:]
    # "id_" asks the Archive for the original bytes, without its own banner
    return {
        url: f"https://web.archive.org/web/{ts}id_/{url}"
        for ts, url, status in rows
        if status == "200"
    }


def page_list(source):
    """Discover one PDF per district from the SEC's HTML listing page."""
    request = urllib.request.Request(
        source["url"], headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        page = response.read().decode("utf-8", "replace")

    entries = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S | re.I):
        cells = [
            re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)
        ]
        urls = re.findall(r'href="([^"]+\.pdf)"', row, re.I)
        wanted = [u for u in urls if u.lower().endswith(source["prefer"])]
        district = next((c for c in cells if c and not c.rstrip(".").isdigit()), "")
        if wanted and district:
            entries.append(
                {
                    "url": wanted[0],
                    "district": district.title(),
                    "block": "",
                    "filename": wanted[0].rsplit("/", 1)[-1],
                }
            )

    if not entries:
        raise ValueError("The listing page contained no matching PDF links")
    if source.get("via_wayback"):
        prefix = entries[0]["url"].split("//", 1)[1].rsplit("/", 1)[0]
        archived = wayback_urls(prefix)
        missing = [e["filename"] for e in entries if e["url"] not in archived]
        if missing:
            sys.exit(f"no Internet Archive snapshot for: {missing}")
        for entry in entries:
            entry["url"] = archived[entry["url"]]
    return entries


def slug(district, block, fallback):
    """Readable, collision-free filename stem for a notification."""
    parts = [
        re.sub(r"[^A-Za-z0-9]+", "-", p).strip("-") for p in (district, block) if p
    ]
    return "__".join(parts) or pathlib.Path(fallback).stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default=YEAR)
    ap.add_argument(
        "--refresh", action="store_true", help="re-download files already present"
    )
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if args.year not in SOURCES:
        sys.exit(f"no source known for {args.year}; have {sorted(SOURCES)}")
    source = SOURCES[args.year]

    year_dir = DATA / args.year
    pdf_dir = year_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    index_path = year_dir / "index.pdf"

    if source["style"] == "index-pdf":
        if args.refresh or not index_path.exists():
            print(f"index -> {index_path}")
            fetch(source["url"], index_path)
        entries = index_pdf.read(index_path)
    else:
        entries = page_list(source)
    print(f"{len(entries)} notifications listed for {args.year}")

    # a district/block pair can appear more than once; keep names unique
    used = {}
    for entry in entries:
        stem = slug(entry["district"], entry["block"], entry["filename"])
        used[stem] = used.get(stem, 0) + 1
        if used[stem] > 1:
            stem = f"{stem}-{used[stem]}"
        entry["saved_as"] = f"{stem}.pdf"

    todo = [
        e for e in entries if args.refresh or not (pdf_dir / e["saved_as"]).exists()
    ]
    if todo:
        print(f"downloading {len(todo)} of {len(entries)}")
        failures = []
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            futures = {
                pool.submit(fetch, e["url"], pdf_dir / e["saved_as"]): e for e in todo
            }
            for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
                entry = futures[future]
                try:
                    future.result()
                except Exception as exc:
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
        writer = csv.DictWriter(
            fh, fieldnames=MANIFEST_COLUMNS, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(entries)

    total = sum(e["bytes"] for e in entries)
    print(f"wrote {manifest} ({len(entries)} rows, {total / 1e6:.0f} MB on disk)")


if __name__ == "__main__":
    main()

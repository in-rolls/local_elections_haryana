"""Read the printed GP serial numbers from the 2000 gazette pages.

Each gram panchayat in the 2000 gazettes is headed by its serial within the
block and its name ("17 PINJOKHERA"). The hosted transcription kept the name and
dropped the serial, and the serial is what shows a block's roster is complete:
serials run 1..N, so a gap names the GPs that are missing and a repeat names a
page scanned twice.

This reads the left strip of every page holding sarpanch and panch rows with
local Tesseract and keeps each line that starts with a number followed by a
name. Tesseract misses some lines and misreads others, so its output is
evidence to be matched against the transcribed GP names, not an assignment; the
matching happens in parse_2000.

    uv run python -m local_elections_haryana.parse.serials_2000

It also reads each page's header, which prints the gazette's running page
number ("913(2434)"): a number skipped within a file is a gazette page the scan
does not hold. Writes data/manual/2000/serial_ocr.csv and page_numbers.csv.
Needs the raw archive and Tesseract.
"""

import csv
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from PIL import Image

from local_elections_haryana import paths
from local_elections_haryana.paths import ROOT

RAW = ROOT / "data/raw/gazette_archive/national/early_cycles"
OBSERVATIONS = (
    paths.RELEASE
    / "2000/gazette_occurrences/historical_provisional_observations.parquet"
)
OUT = ROOT / "data/manual/2000/serial_ocr.csv"
PAGES_OUT = ROOT / "data/manual/2000/page_numbers.csv"
# "913(2434) HARYANA GOVT GAZ." - issue page and running page of the gazette
HEADER = re.compile(r"(\d{3})\s*\(\s*(\d{3,4})\s*\)")
LINE = re.compile(r"^\W*(\d{1,3})\s*[.,)]?\s+([A-Za-z][A-Za-z .()/-]{2,})")
FIELDS = ["source_path", "source_page", "psm", "serial", "name_ocr", "line"]


def pages():
    d = pd.read_parquet(OBSERVATIONS, columns=["source_path", "source_page", "family"])
    d = d[d.family == "gp_head_and_ward"]
    return sorted(set(zip(d.source_path, d.source_page.astype(int), strict=True)))


def read_page(job):
    path, page = job
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "p"
        subprocess.run(
            ["pdftoppm", "-f", str(page), "-l", str(page), "-r", "300", "-gray",
             "-png", "-singlefile", str(RAW / path), str(prefix)],
            check=True, capture_output=True, timeout=120,
        )  # fmt: skip
        image = Image.open(prefix.with_suffix(".png"))
        width, height = image.size
        top = prefix.with_name("top.png")
        image.crop((0, 0, width, int(height * 0.07))).save(top)
        header = subprocess.run(
            ["tesseract", str(top), "-", "--psm", "6"],
            capture_output=True, text=True, timeout=120,
        ).stdout  # fmt: skip
        found = HEADER.search(header)
        out.append(
            {
                "source_path": path,
                "source_page": page,
                "psm": "header",
                "serial": int(found[2]) if found else "",
                "name_ocr": found[1] if found else "",
                "line": " ".join(header.split())[:120],
            }
        )
        # serial and GP name sit in the leftmost third, below the header rule
        strip = prefix.with_name("strip.png")
        image.crop((0, int(height * 0.06), int(width * 0.32), height)).save(strip)
        for psm in ("6", "4"):
            text = subprocess.run(
                ["tesseract", str(strip), "-", "--psm", psm],
                capture_output=True, text=True, timeout=120,
            ).stdout  # fmt: skip
            for line in text.splitlines():
                match = LINE.match(line.strip())
                if match:
                    out.append(
                        {
                            "source_path": path,
                            "source_page": page,
                            "psm": psm,
                            "serial": int(match[1]),
                            "name_ocr": match[2].strip(),
                            "line": line.strip(),
                        }
                    )
    return out


def main():
    jobs = pages()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = [r for found in pool.map(read_page, jobs) for r in found]
    headers = [r for r in rows if r["psm"] == "header"]
    rows = [r for r in rows if r["psm"] != "header"]
    rows.sort(key=lambda r: (r["source_path"], r["source_page"], r["psm"], r["line"]))
    with PAGES_OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "source_path",
                "source_page",
                "gazette_page",
                "issue",
                "header",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {"source_path": r["source_path"], "source_page": r["source_page"],
             "gazette_page": r["serial"], "issue": r["name_ocr"], "header": r["line"]}
            for r in sorted(headers, key=lambda r: (r["source_path"], r["source_page"]))
        )  # fmt: skip
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(jobs)} pages, {len(rows)} serial lines -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

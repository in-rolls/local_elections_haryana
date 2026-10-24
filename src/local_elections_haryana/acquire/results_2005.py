"""Bring the 2005 sarpanch and panch results out of the raw archive.

The State Election Commission published one results PDF per block under
`secharyana.nic.in/html/PCRESULTPDF/`. Those files survive only as Wayback
captures from 2007 to 2009, which the raw archive already holds with their
fetch receipts. This copies the 119 block files into `data/raw/2005/`, together
with the source-cell reviews made when they were first parsed, and writes
`data/raw/2005/manifest.csv`. After that the year rebuilds from tracked files alone.

The captures predate the July 2010 general election, and the winners repeat
2000's and 2010's no more often than any two elections do (about 1% of linked
panchayats against 0.1% for random pairs within a block), so the files are the
2005 general election rather than a reposted 2000 list.

District and block come from each file's printed heading. Two headings need a
decision. `MGARH.pdf` prints "BLOCK MAHENDERGARH" with no district. `SIWAN.pdf`
prints "BLOCK RAJOUND, KAITHAL", but 29 of its 43 panchayats are 2010 Siwan
panchayats and none are Rajound's, which has its own file. Both overrides are
recorded in the manifest's `heading_note`.
"""

import csv
import hashlib
import re
import shutil

from local_elections_haryana import paths
from local_elections_haryana.paths import ROOT

ARCHIVE = ROOT / "data/raw/gazette_archive/national/gap_recovery"
OUT = paths.raw(2005)
REVIEWS = paths.manual(2005) / "reviews"
REVIEWS = ("layout_reviews.csv", "section_reviews.csv", "reservation_reviews.csv")
# file name -> (district, block, why the printed heading is not used)
HEADING_OVERRIDES = {
    "MGARH.pdf": (
        "Mahendergarh",
        "Mahendergarh",
        "Prints BLOCK MAHENDERGARH with no district; the block is the district's "
        "headquarters block of the same name.",
    ),
    "SIWAN.pdf": (
        "Kaithal",
        "Siwan",
        "Prints BLOCK RAJOUND, KAITHAL; 29 of 43 GPs are 2010 Siwan GPs and none "
        "are Rajound's, which has its own file (RAJOUND.pdf).",
    ),
}
FIELDS = [
    "district",
    "block",
    "saved_as",
    "sha256",
    "bytes",
    "source_filename",
    "url",
    "title_raw",
    "heading_note",
]


def place(text):
    """Title-case a printed place name, keeping roman numerals upper case."""
    words = re.split(r"(\W+)", text.strip().lower())
    return "".join(
        w.upper() if re.fullmatch(r"i{1,3}|iv", w) else w.capitalize() for w in words
    )


def heading(title):
    match = re.fullmatch(r"\s*BLOCK\s+(.+?),\s*(.+?)\s*", title or "")
    if not match:
        raise ValueError(f"Unrecognized 2005 heading: {title!r}")
    return place(match.group(2)), place(match.group(1))


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    with (ARCHIVE / "parsed/documents.csv").open(encoding="utf-8") as fh:
        documents = [
            row for row in csv.DictReader(fh) if row["family"] == "gp_head_and_ward"
        ]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc in documents:
        name = doc["original_url"].rsplit("/", 1)[-1]
        source = ARCHIVE / doc["source_path"]
        if sha256(source) != doc["source_sha256"]:
            raise ValueError(f"Archive file changed: {source}")
        if name in HEADING_OVERRIDES:
            district, block, note = HEADING_OVERRIDES[name]
        else:
            district, block, note = (*heading(doc["title_raw"]), "")
        target = OUT / name
        if target.exists():
            raise ValueError(f"Two archived files are named {name}")
        shutil.copyfile(source, target)
        rows.append(
            {
                "district": district,
                "block": block,
                "saved_as": name,
                "sha256": doc["source_sha256"],
                "bytes": target.stat().st_size,
                "source_filename": name,
                "url": doc["source_url"],
                "title_raw": doc["title_raw"],
                "heading_note": note,
            }
        )
    rows.sort(key=lambda r: (r["district"], r["block"]))
    with (OUT / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    REVIEWS.mkdir(parents=True, exist_ok=True)
    for name in REVIEWS:
        shutil.copyfile(ARCHIVE / name, REVIEWS / name)
    print(f"{len(rows)} block files -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

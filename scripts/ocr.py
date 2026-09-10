"""Read the pages whose grid pdfplumber cannot see.

    python scripts/ocr.py --plan --year 2022        # which pages, and why
    uv run --no-project --with savitr==0.2.0 --with pillow==10.4.0 \
        python scripts/ocr.py --read --year 2022    # read them

Two steps because they cannot share an interpreter: savitr pins pillow<11 and
pdfplumber needs >=12.2. Deciding which pages are bad needs pdfplumber; reading
them needs savitr. The plan is written to a file, so what was read is a record
rather than a side effect, and a re-run reads only what is missing.

Most of these gazettes extract perfectly: the text layer is faithful Kruti Dev
and `find_tables` recovers the cells the page draws. On 67 pages of 1,606 it
does not - it returns one fully-ruled seven-column grid as two tables, the
right-hand one holding [father, office, reservation]. `split_row` anchors on
the office cell, so it parses every row happily while reading the father as the
winner with no ward at all, and the panchayat name goes the same way: it is
printed once per panchayat and blank beneath, so a panchayat whose column is
never read lets its wards inherit the previous one's.

Surya reads those pages as rows of seven, merges the wrapped cells, and returns
Unicode Devanagari rather than Kruti Dev. Five attempts to fix this inside
pdfplumber failed - three chose between readings on a quality proxy and let
something else move, one dropped the table finder and lost the wrapped content,
one passed the page's own rules and lost 447 rows elsewhere.

Only the bad pages are read, and the output is cached and committed, so a
re-parse never needs the model. Apple Silicon only.

**2016 is read but not used, and the cache is kept so the next attempt starts
from it.** Applying it there fixed 123 of the 164 wardless rows and cut ward
holes from 487 to 338 - and attached fourteen people to the wrong panchayat.
Theh Taranwali in Siwan had nine clean rows before and came out with fifteen,
its wards duplicated and one numbered 45.

The cause is the long-form layout, from the other side. A ward row leaves the
panchayat column blank, so it inherits the name carried forward - and where an
OCR'd page begins part-way through a panchayat, or its sarpanch row is not
read, the rows inherit the *previous* panchayat instead of their own. 2022 did
not show this because its bad pages happen to start at a panchayat boundary.

A wrong row misleads where a missing row only shrinks, so this is worse than
the 164 it would fix. The next attempt needs the panchayat identity established
for an OCR'd page independently - from the page's own first sarpanch row, or by
refusing the page when it has none - rather than inherited across a boundary
the OCR cannot see.
"""

import argparse
import csv
import pathlib
import subprocess
import sys
import tempfile

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
DPI = 200


def bad_pages(path):
    """(page number, why) for the pages pdfplumber lost the grid on."""
    # Imported here, not at the top: the reading half of this script runs under
    # savitr, which pins pillow<11 where pdfplumber needs >=12.2, so the two
    # halves cannot share an interpreter and must not share imports either.
    import pdfplumber
    from parse import clean, split_row

    out = []
    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            got = [
                split_row([clean(c) for c in raw])
                for table in page.find_tables()
                for raw in table.extract()
            ]
            panch = [g for g in got if g and g[0] == "panch"]
            wardless = sum(1 for g in panch if not g[3])
            if panch and wardless > len(panch) / 2:
                out.append(
                    (index, f"{wardless} of {len(panch)} panch rows carry no ward")
                )
    return out


def ocr_page(engine, pdf_path, page_no):
    with tempfile.TemporaryDirectory() as tmp:
        stem = pathlib.Path(tmp) / "p"
        subprocess.run(
            [
                "pdftoppm",
                "-f",
                str(page_no),
                "-l",
                str(page_no),
                "-r",
                str(DPI),
                "-png",
                str(pdf_path),
                str(stem),
            ],
            capture_output=True,
        )
        images = sorted(pathlib.Path(tmp).glob("p-*.png"))
        if not images:
            return None
        text, _ = engine.ocr_image(str(images[0]))
        return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--plan",
        action="store_true",
        help="list the pages that need reading, and write the plan",
    )
    ap.add_argument("--read", action="store_true", help="read the pages the plan names")
    ap.add_argument("--year", default="2022")
    ap.add_argument("--only", help="substring of a filename to limit to")
    args = ap.parse_args()

    year = DATA / args.year
    plan_path = year / "ocr_plan.csv"
    out = year / "ocr"

    if args.plan:
        pdfs = sorted((year / "pdfs").glob("*.pdf"))
        if args.only:
            pdfs = [p for p in pdfs if args.only.lower() in p.name.lower()]
        rows = []
        for path in pdfs:
            for page, why in bad_pages(path):
                rows.append({"document": path.name, "page": page, "why": why})
            print(f"\r  scanned {path.name:34s}", end="", file=sys.stderr)
        print(file=sys.stderr)
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with plan_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["document", "page", "why"], lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        docs = len({r["document"] for r in rows})
        print(
            f"  {len(rows)} page(s) across {docs} document(s) -> "
            f"{plan_path.relative_to(DATA.parent)}"
        )
        return 0

    if not args.read:
        ap.error("pass --plan or --read")
    if not plan_path.exists():
        sys.exit(f"no plan at {plan_path} - run --plan first")

    import os

    from savitr import MLXSuryaOCR

    engine = MLXSuryaOCR(
        os.environ.get(
            "SURYA_MLX_PATH",
            os.path.expanduser("~/Documents/GitHub/savitr/models/surya-mlx-4bit"),
        )
    )
    out.mkdir(parents=True, exist_ok=True)
    with plan_path.open(encoding="utf-8") as fh:
        plan = list(csv.DictReader(fh))
    if args.only:
        plan = [r for r in plan if args.only.lower() in r["document"].lower()]

    read = cached = 0
    for entry in plan:
        stem = pathlib.Path(entry["document"]).stem
        page = int(entry["page"])
        target = out / f"{stem}-{page:03d}.html"
        if target.exists():
            cached += 1
            continue
        text = ocr_page(engine, year / "pdfs" / entry["document"], page)
        if text is None:
            continue
        target.write_text(text, encoding="utf-8")
        read += 1
        print(
            f"\r  {stem[:28]:30s} p{page:<4} read={read} cached={cached}",
            end="",
            file=sys.stderr,
            flush=True,
        )
    print(file=sys.stderr)
    print(
        f"  {read} page(s) read, {cached} already cached -> "
        f"{out.relative_to(DATA.parent)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

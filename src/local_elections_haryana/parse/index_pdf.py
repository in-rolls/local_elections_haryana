"""Read the State Election Commission's index PDF.

The index is a District x Block table with a hyperlink on every block name, so
the position of a link tells us both which notification it points at and where
that notification belongs. That is more reliable than reading the preamble
inside each notification: one block (Machhrauli, Jhajjar) is published only in
Kruti Dev and has no English preamble to read at all.

Both harvest.py and parse.py read the index through here so that the download
manifest and the parsed rows agree on district and block by construction.
"""

import pathlib
import re

import pdfplumber

# Column x-ranges in the index table, in PDF points.
SERIAL_X = (82, 104)
DISTRICT_X = (120, 210)


def read(path):
    """Return a list of {url, filename, district, block}, in index order."""
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} - run harvest.py first")

    bands, links = [], []
    with pdfplumber.open(str(path)) as pdf:
        for page_no, page in enumerate(pdf.pages):
            words = page.extract_words()
            serials = sorted(
                (
                    w
                    for w in words
                    if SERIAL_X[0] <= w["x0"] <= SERIAL_X[1]
                    and re.fullmatch(r"\d+\.?", w["text"])
                ),
                key=lambda w: w["top"],
            )
            for i, w in enumerate(serials):
                end = (
                    serials[i + 1]["top"] - 2 if i + 1 < len(serials) else float("inf")
                )
                name = " ".join(
                    x["text"]
                    for x in sorted(
                        (
                            x
                            for x in words
                            if DISTRICT_X[0] <= x["x0"] <= DISTRICT_X[1]
                            and w["top"] - 3 <= x["top"] < end
                        ),
                        key=lambda x: (x["top"], x["x0"]),
                    )
                )
                bands.append((page_no, w["top"], name))

            for annot in page.annots or []:
                uri = annot.get("uri") or ""
                if not uri.endswith(".pdf"):
                    continue
                block = " ".join(
                    x["text"]
                    for x in words
                    if x["x0"] >= annot["x0"] - 2
                    and x["x1"] <= annot["x1"] + 2
                    and x["top"] >= annot["top"] - 3
                    and x["bottom"] <= annot["bottom"] + 3
                )
                links.append((page_no, annot["top"], uri, block.strip()))

    bands.sort()
    out, seen = [], set()
    for page_no, top, uri, block in links:
        # a district cell spans many block rows and can run past a page break,
        # so take the most recent non-empty district at or above this link
        above = [n for bp, bt, n in bands if (bp, bt) <= (page_no, top + 3) and n]
        filename = uri.rsplit("/", 1)[-1]
        if filename in seen:
            continue
        seen.add(filename)
        out.append(
            {
                "url": uri,
                "filename": filename,
                "district": above[-1] if above else "",
                "block": block,
            }
        )
    return out

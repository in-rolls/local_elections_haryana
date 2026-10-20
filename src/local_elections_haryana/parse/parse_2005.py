"""Parse the 2005 block results into the same seat tables as 2010, 2016 and 2022.

Each block file prints one row per office: the panchayat, "Sarpanch" or a ward
number, the winner, the father's or husband's name, and the seat's category. The
text layer is intact, so `parse_historical.parse_document` reads it with
pdfplumber; there is no OCR. The source-cell reviews made when the files were
first parsed are applied here and refuse to run if a reviewed cell has changed.

Three decisions shape the output:

- Samalkha's file appends Raipur Rani's whole roster after its own. The appended
  354 rows match Raipur Rani's own file row for row, so they are dropped from
  Samalkha rather than counted twice.
- The results list prints no serial, so `sr_no` is the panchayat's order of
  first appearance within its block file. It identifies a row within this
  release, not an official number.
- Many winners carry a leading `*`. No file says what it marks, so it is
  removed from `winner` and not read as unopposed; `unopposed` stays blank.
"""

import csv
import re
from collections import Counter

import pandas as pd

from local_elections_haryana.parse.parse_historical import (
    apply_reservation_reviews,
    parse_document,
    reconcile_sections,
)
from local_elections_haryana.parse.to_parquet import GP_COLUMNS
from local_elections_haryana.paths import ROOT

YEAR = "2005"
DATA = ROOT / "data" / YEAR
WARD_COLUMNS = (*GP_COLUMNS[:4], "ward_no", *GP_COLUMNS[4:])


def read_csv(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def label(caste, woman):
    if caste is None or pd.isna(caste) or woman is None or pd.isna(woman):
        return ""
    prefix = "" if caste == "NONE" else f"{caste} "
    return prefix + ("Woman" if woman else "Other than Woman")


def flag(value):
    return "" if value is None or pd.isna(value) else str(int(bool(value)))


def read_block(doc, layout):
    """One block file, read with the wrap direction its panchayat cells use.

    Wrapped panchayat names overflow below their row in some files and above it
    in others. Read the wrong way, every wrapped name splits into fragments
    that differ from row to row, so the direction giving fewer distinct names
    is the one the file uses. A file with no wrapped names reads the same
    both ways.
    """
    path = DATA / "pdfs" / doc["saved_as"]
    readings = {
        wrap: parse_document(path, "gp_head_and_ward", layout, wrap=wrap)[0]
        for wrap in ("below", "above")
    }
    names = {
        wrap: len({r["gram_panchayat_raw"] for r in rows})
        for wrap, rows in readings.items()
    }
    WRAP[doc["saved_as"]] = "above" if names["above"] < names["below"] else "below"
    return readings[WRAP[doc["saved_as"]]]


WRAP = {}


def parse():
    manifest = read_csv(DATA / "manifest.csv")
    layout = read_csv(DATA / "reviews/layout_reviews.csv")
    records = []
    for doc in manifest:
        rows = read_block(
            doc, [r for r in layout if r["source_sha256"] == doc["sha256"]]
        )
        for row in rows:
            row.update(
                source_sha256=doc["sha256"],
                source_pdf=doc["saved_as"],
                district=doc["district"],
                block=doc["block"],
            )
        records += rows
    frame = pd.DataFrame(records)
    frame = reconcile_sections(frame, read_csv(DATA / "reviews/section_reviews.csv"))
    # the reviews also cover the samiti and zila parishad files, not released here
    held = {doc["sha256"] for doc in manifest}
    reviews = read_csv(DATA / "reviews/reservation_reviews.csv")
    frame = apply_reservation_reviews(
        frame, [r for r in reviews if r["source_sha256"] in held]
    )
    repeated = frame.quality_flags.str.contains("cross_document_section_repeat")
    frame = frame[~repeated].reset_index(drop=True)
    return mend_page_breaks(frame), int(repeated.sum())


def office_step(previous, current):
    """True when `current` is the office printed straight after `previous`."""
    if previous.lower().startswith("sarpanc"):
        return current == "1"
    return previous.isdigit() and current == str(int(previous) + 1)


def mend_page_breaks(frame):
    """Give a name cut off at a page break the full name its neighbours print.

    A wrapped panchayat name loses its overflow line when its row is the last on
    a page, so Palwal's ward 20 reads "Palwal Rural Urf" while wards 1-19 read
    "Palwal Rural Urf Shamshabad". Within a run of consecutive offices in one
    file (Sarpanch, 1, 2, ...), names that are word-prefixes of one another are
    one name, and the longest is the one printed in full.
    """
    frame = frame.copy()
    names = frame.gram_panchayat_raw.tolist()
    run = [0]
    for i in range(1, len(frame) + 1):
        joined = i < len(frame) and (
            frame.source_pdf[i] == frame.source_pdf[i - 1]
            and office_step(
                frame.ward_or_office_raw[i - 1].strip(),
                frame.ward_or_office_raw[i].strip(),
            )
        )
        if joined:
            run.append(i)
            continue
        full = max((names[j] for j in run), key=lambda n: len(n.split()))
        for j in run:
            if names[j] != full and full.split()[: len(names[j].split())] == (
                names[j].split()
            ):
                frame.at[j, "gram_panchayat_raw"] = full
                frame.at[j, "quality_flags"] += ";gp_name_completed_from_run"
        run = [i]
    return frame


def tables(frame):
    order = {}
    for row in frame.itertuples():
        order.setdefault((row.source_pdf, row.gram_panchayat_raw), None)
    serial = Counter()
    numbers = {}
    for pdf, gp in order:
        serial[pdf] += 1
        numbers[(pdf, gp)] = str(serial[pdf])
    gp_rows, ward_rows = [], []
    for row in frame.itertuples():
        winner = re.sub(r"^\s*\*\s*", "", row.winner_name_raw).strip()
        record = {
            "district": row.district,
            "block": row.block,
            "sr_no": numbers[(row.source_pdf, row.gram_panchayat_raw)],
            "gram_panchayat": row.gram_panchayat_raw.strip(),
            "reserved_label": label(row.reserved_caste, row.reserved_woman),
            "reserved_caste": "" if pd.isna(row.reserved_caste) else row.reserved_caste,
            "reserved_woman": flag(row.reserved_woman),
            "winner": winner,
            "father_husband": row.relation_name_raw.strip(),
            "unopposed": "",
            "vacant": "0" if winner else "1",
            "reserved_raw": row.reserved_raw,
            "script": "latin",
            "printings_agree": "",
            "notification": "",
            "source_pdf": row.source_pdf,
        }
        if row.tier == "gp_head":
            gp_rows.append(record)
        else:
            ward_rows.append(record | {"ward_no": row.ward_or_office_raw.strip()})
    return gp_rows, ward_rows


def write(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    frame, dropped = parse()
    gp_rows, ward_rows = tables(frame)
    write(DATA / "gp_reservation.csv", GP_COLUMNS, gp_rows)
    write(DATA / "ward_reservation.csv", WARD_COLUMNS, ward_rows)
    print(
        f"2005: {len(gp_rows):,} sarpanch and {len(ward_rows):,} panch rows; "
        f"{dropped} repeated Raipur Rani rows dropped from Samalkha"
    )


if __name__ == "__main__":
    main()

"""Build the 2000 sarpanch and panch tables from the hosted transcription.

The 2000 gazettes are scanned images; Muse Spark transcribed every row
(`acquire/rollout_hosted.py`) into the tracked provisional table. That table is
close to the commission's own block totals but not a seat roster as it stands.
Root-causing the differences gave four problems this fixes, each recorded:

- **Repeated scans.** Kharkhoda's and Bapoli's PDFs carry the same gazette page
  twice (Kharkhoda pp. 7 and 8 are both printed page 913(1799)). A page whose
  rows repeat an earlier page of the same file is dropped.
- **Second printings.** Thirteen Faridabad and Sirsa notifications print every
  roster in Hindi and again in English. The English rows are kept; each Hindi
  row is paired with its English twin, and whether the two independent
  transcriptions agree on the category is kept in `printings_agree` (they
  agree on 98.4% of 6,571 pairs).
- **Spilled rows.** Elsewhere, Hindi rows on an English page are the tail of
  the notification printed before it, usually another block's. They are not
  this block's seats and are set aside in `reference/spilled_hindi_rows.csv`.
- **Missing pages.** A page's first ward that does not follow the last ward
  before it means a gazette page is missing between them (Hansi-I skips page
  2435); those rows open an unnamed GP rather than joining the wrong one.
- **Block names.** Nineteen blocks are spelled differently in the gazette index
  and in the commission's tables; `reference/block_names.csv` maps them, with
  the commission's table as the authority.
- **Serials.** Each GP is headed by its printed serial within the block, which
  the transcription dropped. Tesseract reads some of them
  (`parse/serials_2000.py`); since serials are consecutive within a page, one
  serial read and matched to its GP name fixes every heading on the page, and
  any further reads check it. A page with no read takes its numbering from the
  page before. `sr_no` is that printed serial, and gaps in a block's 1..N are
  the GPs the release does not hold.

`*` in the ward column is the gazette's own mark for a member returned
unopposed, defined in each page's footer.

    uv run python -m local_elections_haryana.parse.parse_2000
"""

import csv
import difflib
import re
from collections import Counter
from itertools import pairwise

import pandas as pd

from local_elections_haryana.parse.to_parquet import GP_COLUMNS
from local_elections_haryana.paths import ROOT

DATA = ROOT / "data" / "2000"
REFERENCE = DATA / "reference"
OBSERVATIONS = (
    ROOT / "data/release/historical/historical_provisional_observations.parquet"
)
WARD_COLUMNS = (*GP_COLUMNS[:4], "ward_no", *GP_COLUMNS[4:])
REPEAT_SHARE = 0.8
NAME_MATCH = 0.85
CONFIRM = 2
BILINGUAL = (0.4, 0.6)


def text(value):
    return value.strip() if isinstance(value, str) else ""


def fold(text):
    return re.sub(r"[^a-z]", "", str(text or "").lower())


def similar(a, b):
    return difflib.SequenceMatcher(None, fold(a), fold(b)).ratio()


def load():
    d = pd.read_parquet(OBSERVATIONS)
    d = d[(d.family == "gp_head_and_ward") & d.tier.isin(["gp_head", "gp_ward"])]
    d = d[d.is_seat_record.isna()].copy()
    d["source_page"] = d.source_page.astype(int)
    d["source_row_on_page"] = d.source_row_on_page.astype(int)
    names = pd.read_csv(REFERENCE / "block_names.csv")
    d = d.merge(names, on=["district_index", "block_index"], how="left", validate="m:1")
    if d.block_sec.isna().any():
        raise SystemExit("block missing from reference/block_names.csv")
    return d.sort_values(["source_path", "source_page", "source_row_on_page"])


def page_rows(g):
    return set(zip(g.winner_raw.fillna(""), g.relation_raw.fillna(""), strict=True))


def repeated_pages(d):
    """Pages that repeat another page, which are dropped.

    Two kinds: a page scanned twice into one file (Kharkhoda pp. 7 and 8), and
    a block's last page reprinted at the head of the next block's file (Odhan's
    file opens with Dabwali's GPs 45 and 46). Repeats are near-total - every
    flagged page shares at least 97% of its winner and relation names with the
    other, and no other page shares more than 10% - so the threshold is loose.
    """
    latin = d[d.script == "Latin"]
    pages = {
        key: page_rows(g) for key, g in latin.groupby(["source_path", "source_page"])
    }
    first = {path: min(p for q, p in pages if q == path) for path, _ in pages}
    found = []
    for (path, page), rows in sorted(pages.items()):
        if len(rows) <= 5:
            continue
        others = [
            key
            for key in pages
            if (key[0] == path and key[1] < page)
            or (key[0] != path and page == first[path])
        ]
        for key in others:
            if len(rows & pages[key]) >= REPEAT_SHARE * len(rows):
                found.append({"source_path": path, "source_page": page,
                              "repeats_path": key[0], "repeats_page": key[1],
                              "rows": len(rows)})  # fmt: skip
                break
    return pd.DataFrame(
        found,
        columns=["source_path", "source_page", "repeats_path", "repeats_page", "rows"],
    )


def pair_printings(d):
    """Pair each Hindi row with its English twin in the same notification.

    Both printings list the same offices in the same order, so the two office
    sequences are aligned (office, ward) by difflib; categories are compared on
    the aligned pairs. Returns English row index -> 1/0 agreement.
    """
    agree = {}
    for _path, f in d.groupby("source_path"):
        hindi, english = f[f.script == "Devanagari"], f[f.script == "Latin"]
        # Only notifications printed whole in both languages. Elsewhere the
        # Hindi rows are another notification's tail spilling onto the page,
        # and aligning them pairs different seats: they agree on 49% of
        # "pairs", against 98.4% in the bilingual files.
        if not BILINGUAL[0] <= len(hindi) / len(f) <= BILINGUAL[1]:
            continue

        def token(x):
            # tier, not the printed office: Hindi prints पंच where English
            # prints PANCH
            return list(zip(x.tier, x.ward.fillna(-1), strict=True))

        matcher = difflib.SequenceMatcher(
            None, token(english), token(hindi), autojunk=False
        )
        for block in matcher.get_matching_blocks():
            for k in range(block.size):
                e, h = english.iloc[block.a + k], hindi.iloc[block.b + k]
                same = (e.caste_reservation == h.caste_reservation) and (
                    e.woman_reserved == h.woman_reserved
                )
                agree[e.name] = int(bool(same))
    return agree


def gp_units(f):
    """Number the GPs of one file in printed order: each sarpanch row opens one.

    Ward rows belong to the GP above them, across page breaks - unless the
    first ward on a page does not follow the last ward before it. Then a page
    is missing between them (Hansi-I jumps from gazette page 2434 to 2436, and
    page 2436 opens at ward 6 of GP 41), and the rows open a GP whose heading
    and sarpanch row were on the missing page. A ward 1 that follows another
    ward opens a GP whose sarpanch row the gazette does not print (Dujana,
    Frain Khurd and Guwani in 2005 are such GPs).
    """
    unit, units, previous = -1, [], None
    for r in f.itertuples():
        page_start = previous is None or r.source_page != previous.source_page
        broken = (
            page_start
            and previous is not None
            and r.tier == "gp_ward"
            and not (
                (previous.tier == "gp_head" and r.ward == 1)
                or (previous.tier == "gp_ward" and r.ward == previous.ward + 1)
            )
        )
        if (
            r.tier == "gp_head"
            or broken
            or (r.ward == 1 and previous is not None and previous.tier == "gp_ward")
        ):
            unit += 1
        units.append(unit)
        previous = r
    return pd.Series(units, index=f.index)


def supports(k, serial, offset):
    """Whether a read fits the offset, allowing a dropped leading digit."""
    predicted = str(k + offset)
    return predicted == str(serial) or predicted.endswith(str(serial))


def segments(reads):
    """Offsets confirmed by consecutive reads, as (first_k, last_k, offset).

    Within one block file serials run on from heading to heading, so
    serial - position is constant except where GPs are missing (it steps up)
    or a page repeats (it steps down). Tesseract misreads digits too, and most
    often drops a leading one - 52 read as 2 - so a read whose digits end the
    predicted serial still supports the current offset. The offset changes
    only when two consecutive reads contradict it and agree on a new one.
    """
    out, current, start, last, pending = [], None, None, None, []
    for k, serial in reads:
        if current is not None and supports(k, serial, current):
            last, pending = k, []
            continue
        offset = serial - k
        pending = [p for p in pending if p[1] == offset] + [(k, offset)]
        if len(pending) >= CONFIRM:
            if current is not None:
                out.append((start, last, current))
            current, start, last, pending = offset, pending[0][0], k, []
    if current is not None:
        out.append((start, last, current))
    # A run whose offset differs from equal neighbours on both sides by a whole
    # multiple of ten is a run of the same digit misread (40s read as 30s, or
    # 34 read as 343), not GPs that vanished and reappeared.
    changed = True
    while changed:
        changed = False
        for i in range(1, len(out) - 1):
            a, b, c = out[i - 1], out[i], out[i + 1]
            if a[2] == c[2] and (b[2] - a[2]) % 10 == 0:
                out[i - 1 : i + 2] = [(a[0], c[1], a[2])]
                changed = True
                break
    return out


def assign_serials(d, ocr):
    """Printed serial and name evidence for every GP unit of every file.

    A unit inside a confirmed serial segment, or between two segments with the
    same offset, takes position + offset. Before the first read, after the last,
    or between differing segments GPs may be missing, so nothing is
    extrapolated there.
    """
    serial, basis, read_name, steps = {}, {}, {}, []
    for path, f in d.groupby("source_path"):
        heads = f[f.unit_start].sort_values(["source_page", "source_row_on_page"])
        names = list(
            zip(heads.unit, heads.source_page, heads.body_within_page, strict=True)
        )
        reads = []
        page_reads = ocr[ocr.source_path == path].drop_duplicates(
            ["source_page", "serial", "name_ocr"]
        )
        for r in page_reads.itertuples():
            on_page = [
                (similar(r.name_ocr, n), k) for k, p, n in names if p == r.source_page
            ]
            if on_page and max(on_page)[0] >= NAME_MATCH:
                reads.append((max(on_page)[1], r.serial))
        segs = segments(sorted(set(reads)))
        for k, page, _ in names:
            inside = [s for s in segs if s[0] <= k <= s[1]]
            before = [s for s in segs if s[1] < k]
            after = [s for s in segs if s[0] > k]
            if inside:
                offset, how = inside[0][2], "printed_serial_sequence"
            elif before and after and before[-1][2] == after[0][2]:
                offset, how = before[-1][2], "printed_serial_sequence"
            else:
                offset, how = (
                    None,
                    "outside_confirmed_serials" if segs else "no_serial_read",
                )
            serial[(path, k)] = k + offset if offset is not None else None
            basis[(path, k)] = how
            if offset is not None:
                hit = page_reads[
                    (page_reads.source_page == page) & (page_reads.serial == k + offset)
                ]
                if len(hit):
                    read_name[(path, k)] = hit.name_ocr.iloc[0]
        for a, b in pairwise(segs):
            steps.append(
                {
                    "source_path": path,
                    "after_position": a[1],
                    "before_position": b[0],
                    "offset_before": a[2],
                    "offset_after": b[2],
                    "serials_skipped": b[2] - a[2],
                }
            )
    return serial, basis, read_name, pd.DataFrame(steps)


def label(caste, woman):
    if caste is None or pd.isna(caste) or woman is None or pd.isna(woman):
        return ""
    return ("" if caste == "NONE" else f"{caste} ") + (
        "Woman" if woman else "Other than Woman"
    )


def flag(value):
    return "" if value is None or pd.isna(value) else str(int(bool(value)))


def gp_names(english, read_name):
    """The name of each GP unit, and how it was read.

    The heading the transcription carried onto the unit's first row, unless it
    is the same name as the unit before - a heading the model did not read, so
    the previous GP's name ran on (Kharkhoda prints "GORAR" five times). Those
    take the name Tesseract read beside the unit's printed serial, or none.
    """
    out = {}
    for path, f in english[english.unit_start].groupby("source_path"):
        previous = None
        for r in f.itertuples():
            body = text(r.body_within_page) or (
                text(r.incoming_body_candidate) if r.tier == "gp_head" else ""
            )
            if r.tier != "gp_head" and not text(r.body_within_page):
                out[(path, r.unit)] = ("", "heading_on_missing_page")
            elif body and body != previous:
                out[(path, r.unit)] = (body, "transcribed_heading")
            elif (path, r.unit) in read_name:
                out[(path, r.unit)] = (
                    read_name[(path, r.unit)],
                    "tesseract_serial_line",
                )
            else:
                out[(path, r.unit)] = ("", "heading_unread")
            previous = body
    return out


def build():
    d = load()
    repeats = repeated_pages(d)
    drop = set(zip(repeats.source_path, repeats.source_page, strict=True))
    keep = [
        (p, n) not in drop for p, n in zip(d.source_path, d.source_page, strict=True)
    ]
    d = d[keep]
    agree = pair_printings(d)
    share = d.groupby("source_path").script.apply(lambda s: (s == "Devanagari").mean())
    spilled = d[(d.script == "Devanagari") & d.source_path.map(share).lt(BILINGUAL[0])]
    SPILLED.append(spilled)
    english = d[d.script == "Latin"].copy()
    english["unit"] = english.groupby("source_path", group_keys=False).apply(gp_units)
    english["unit_start"] = ~english.duplicated(["source_path", "unit"])
    ocr = pd.read_csv(REFERENCE / "serial_ocr.csv")
    serial, basis, read_name, steps = assign_serials(english, ocr)
    names = gp_names(english, read_name)

    gp_rows, ward_rows = [], []
    for r in english.itertuples():
        key = (r.source_path, r.unit)
        sr = serial.get(key)
        name, name_basis = names.get(key, ("", "heading_unread"))
        winner = text(r.winner_raw)
        vacant = bool(re.fullmatch(r"(?i)vacant", winner))
        record = {
            "district": r.district_sec.title(),
            "block": r.block_sec.title(),
            "sr_no": "" if sr is None else str(sr),
            "gram_panchayat": name,
            "reservation": label(r.caste_reservation, r.woman_reserved),
            "caste_reservation": r.caste_reservation
            if isinstance(r.caste_reservation, str)
            else "",
            "woman_reserved": flag(r.woman_reserved),
            "winner": "" if vacant else winner,
            "father_husband": text(r.relation_raw),
            "unopposed": "1" if re.search(r"[*\u2022]", text(r.ward_raw)) else "0",
            "vacant": "1" if vacant or not winner else "0",
            "reservation_raw": text(r.category_raw),
            "script": "latin",
            "printings_agree": str(agree[r.Index]) if r.Index in agree else "",
            "notification": "",
            "source_pdf": r.source_path.split("/")[-1],
        }
        provenance = {
            "source_pdf": record["source_pdf"],
            "source_page": r.source_page,
            "source_row_on_page": r.source_row_on_page,
            "unit": r.unit,
            "serial_basis": basis.get(key, ""),
            "name_basis": name_basis,
            "quality_flags": text(r.quality_flags),
        }
        if r.tier == "gp_head":
            gp_rows.append(record)
            PROVENANCE.append(provenance | {"tier": "gp_head"})
        else:
            ward_rows.append(
                record | {"ward_no": "" if pd.isna(r.ward) else str(int(r.ward))}
            )
    blank_unreadable("gp_reservation.csv", gp_rows)
    blank_unreadable("ward_reservation.csv", ward_rows)
    return gp_rows, ward_rows, repeats, steps, basis


PROVENANCE = []
SPILLED = []


def continuity(gp_rows, steps, sec):
    """Per block: GPs held against the commission's count, and where the gap is.

    A step between confirmed serial segments locates GPs missing inside the
    roster. Whatever the steps do not account for lies before the first serial
    read or after the last one - a missing first or final page.
    """
    g = pd.DataFrame(gp_rows)
    file_block = g.drop_duplicates("source_pdf").set_index("source_pdf")[
        ["district", "block"]
    ]
    out = []
    for (district, block), x in g.groupby(["district", "block"]):
        files = set(x.source_pdf)
        st = (
            steps[steps.source_path.str.split("/").str[-1].isin(files)]
            if len(steps)
            else steps
        )
        interior = int(st.serials_skipped.clip(lower=0).sum()) if len(st) else 0
        repeated = int((-st.serials_skipped.clip(upper=0)).sum()) if len(st) else 0
        serials = sorted(int(v) for v in x.sr_no if v)
        want = sec.get((district.upper(), block.upper()))
        shortfall = (want - len(x)) if want is not None else None
        out.append(
            {
                "district": district,
                "block": block,
                "gps_held": len(x),
                "gps_sec": want,
                "shortfall": shortfall,
                "with_serial": len(serials),
                "first_serial": serials[0] if serials else "",
                "last_serial": serials[-1] if serials else "",
                "missing_inside": interior,
                "repeated_inside": repeated,
                "missing_at_ends": (shortfall - interior + repeated)
                if shortfall is not None
                else "",
                "interior_steps": "; ".join(
                    f"{int(r.offset_before + r.after_position)}"
                    f"->{int(r.offset_after + r.before_position)}"
                    for r in st.itertuples()
                )
                if len(st)
                else "",
            }
        )
    del file_block
    return pd.DataFrame(out)


# The hosted model returned a few Hindi cells with their Devanagari code points
# mangled into control characters (Safidon's सामान्य came back as "\x05b8\x05be..."),
# under a Latin script tag. They cannot be read back reliably, so the cell is left
# blank, the seat is kept, and the cell is listed in reference/unreadable_cells.csv.
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
UNREADABLE = []


def blank_unreadable(table, rows):
    for i, row in enumerate(rows):
        for column, value in row.items():
            if isinstance(value, str) and CONTROL.search(value):
                UNREADABLE.append(
                    {
                        "table": table,
                        "row": i + 1,
                        "district": row["district"],
                        "block": row["block"],
                        "source_pdf": row["source_pdf"],
                        "column": column,
                        "value_escaped": value.encode("unicode_escape").decode(),
                    }
                )
                row[column] = ""


def write(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    gp_rows, ward_rows, repeats, steps, basis = build()
    write(DATA / "gp_reservation.csv", GP_COLUMNS, gp_rows)
    write(DATA / "ward_reservation.csv", WARD_COLUMNS, ward_rows)
    repeats.to_csv(REFERENCE / "repeated_pages.csv", index=False)
    steps.to_csv(REFERENCE / "serial_steps.csv", index=False)
    pd.DataFrame(PROVENANCE).to_csv(REFERENCE / "sarpanch_provenance.csv", index=False)
    # Hindi rows on English pages: the tail of the notification printed before,
    # so not seats of the file's own block. Most repeat a GP printed in English
    # elsewhere; the rest await review against the neighbouring blocks' gaps.
    SPILLED[0][
        ["source_path", "source_page", "source_row_on_page", "district_sec",
         "block_sec", "tier", "body_within_page", "ward", "winner_raw",
         "relation_raw", "category_raw"]
    ].to_csv(REFERENCE / "spilled_hindi_rows.csv", index=False)  # fmt: skip
    sec = pd.read_csv(REFERENCE / "sec_panch_reservation_2000.csv").query(
        "level == 'block'"
    )
    sec_gps = {
        (r.district.upper(), r.block.upper()): int(r.gram_panchayats)
        for r in sec.itertuples()
    }
    continuity(gp_rows, steps, sec_gps).to_csv(
        REFERENCE / "serial_continuity.csv", index=False
    )
    pd.DataFrame(
        UNREADABLE,
        columns=["table", "row", "district", "block", "source_pdf", "column",
                 "value_escaped"],
    ).to_csv(REFERENCE / "unreadable_cells.csv", index=False)  # fmt: skip
    print(
        f"2000: {len(gp_rows):,} sarpanch and {len(ward_rows):,} panch rows; "
        f"{len(repeats)} repeated pages dropped; serial basis "
        f"{dict(Counter(basis.values()))}"
    )


if __name__ == "__main__":
    main()

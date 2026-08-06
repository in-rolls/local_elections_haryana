"""Parse the 2022 Haryana SEC notifications into GP-level reservation data.

Each block notification is a 7-column table:

    Sr. No. | Gram Panchayat | Ward No. | Name | Father's/Husband's Name |
    Office | Reservation

Rows where Office == Sarpanch are the gram-panchayat-level seats: one per GP,
and the Reservation cell on that row is the GP's reservation status. Rows where
Office == Panch are ward-level seats within the GP.

The tables are ruled, so pdfplumber's table finder recovers the cells exactly -
including reservation labels that wrap onto a second line, which defeats naive
whitespace-column splitting.

Most notifications are published twice, once with the table typeset in English
and once in legacy Kruti Dev Hindi. Where both exist we keep the English one,
because its gram panchayat names are readable without transliteration.
"""

import argparse
import collections
import csv
import pathlib
import re
import sys

import pdfplumber

from normalize import label, normalize_reservation, strip_unopposed

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
YEAR = "2022"

SARPANCH = {"sarpanch", "ljiap", "ljaip", "ljip", "lliap"}
PANCH = {"panch", "iap", "ipa"}

# "... Block-Narnaul, District-Mahendergarh during General Elections-2022"
RE_BLOCK_EN = re.compile(
    r"Block\s*[-–—]?\s*['‘\"]?\s*(?P<block>[A-Za-z][A-Za-z0-9 .&\-]{1,30}?)\s*['’\"]?\s*,?\s*"
    r"(?:and\s+)?District\s*[-–—:]?\s*['‘\"]?\s*(?P<district>[A-Za-z][A-Za-z .&\-]{1,25}?)"
    r"\s*(?:during|for|,|$)",
    re.I,
)
# Kruti Dev: [k.M&<block>] ftyk&<district>
RE_BLOCK_HI = re.compile(r"\[k\.M&\s*(?P<block>[^\]]{1,30}?)\]\s*ftyk&\s*(?P<district>\S{1,30}?)\s")

# The notification's own serial number, e.g. "No. SEC/4E-II/2022/7385.- In
# pursuance ..." or, in Kruti Dev, "...@4bZ&AA@2022@7385-& gfj;k.kk iapk;rh jkt".
#
# This is the join key that makes the corpus tractable: each notification is
# printed more than once in its PDF - typically once typeset in Kruti Dev Hindi
# and once or twice in English - and every copy carries the same number. The
# trailing s.161 phrase is required because the same number format also appears
# inside table cells, in footnotes citing *other* notifications.
RE_NOTIF = re.compile(
    r"2022\s*[@/]\s*(\d{3,5})\s*[.,\-–—&]{0,3}\s*"
    r"(?:In\s+pursuance|gfj;k\.kk\s+iapk;rh\s+jkt|,rn)",
    re.I,
)


def clean(cell):
    return re.sub(r"\s+", " ", (cell or "").replace("\n", " ")).strip()


def office_kind(cell):
    key = re.sub(r"[^a-z]", "", clean(cell).lower()) or re.sub(r"\s+", "", clean(cell))
    if key in SARPANCH:
        return "sarpanch"
    if key in PANCH:
        return "panch"
    return None


# The ward column of a Sarpanch row holds a placeholder rather than a number:
# some run of dashes or dots, or "&" where Kruti Dev renders the dash. The run
# length varies from one to at least four, so match the shape, not a literal.
RE_WARD_DASH = re.compile(r"[-–—&.·]+$")


def is_ward_dash(cell):
    return bool(RE_WARD_DASH.match(cell))


# Words a reservation label is built from, in both scripts. A table row made up
# of nothing but these is not a seat - it is the tail of the row above, whose
# reservation label wrapped onto a second line and was ruled as its own row.
#
# This is the trap in this corpus: "Scheduled Caste" with "Women" stranded on
# the next line reads as a perfectly plausible SC-but-not-woman seat, so the
# error is silent. Merging must happen before the label is interpreted.
CONTINUATION = {
    "other", "than", "women", "woman", "(women)", "(woman)", "caste", "class",
    "scheduled", "schedule", "schedulded", "backward", "tribe", "unreserved",
    "a", "'a'", "‘a’", "(a)",
    "ds", "d¢", "flok;", "vu;", "efgyk", "efgyk,a", "efgykvksa", "tkfr",
    "tutkfr", "vuqlwfpr", "oxz", "finmk", "finm+k", "finms", "¼,½", "d",
}


def _all_continuation_words(cell):
    words = cell.split()
    return bool(words) and all(w.lower().strip(",.") in CONTINUATION for w in words)


def is_continuation(cells):
    """True when a row is nothing but the tail of the reservation above it."""
    return bool([c for c in cells if c]) and all(
        _all_continuation_words(c) for c in cells if c
    )


def continuation_tail(cells):
    """The reservation fragment at the end of a non-seat row.

    A wrapped row often carries two different overflows at once - the tail of a
    long father's name and the tail of the reservation:

        ['Singh', 'other than Women']

    Requiring the whole row to look like a reservation misses these, and losing
    the "other than Women" turns the seat above into a plausible, wrong,
    woman-reserved seat. So take the trailing run of reservation-looking cells
    and leave the rest alone.
    """
    tail = []
    for cell in reversed([c for c in cells if c]):
        if not _all_continuation_words(cell):
            break
        tail.insert(0, cell)
    return " ".join(tail)


def split_row(cells):
    """Pull (kind, sr_no, gram_panchayat, ward_no, name, father, reservation,
    gp_column) out of one extracted table row.

    Columns are located by content rather than by index. Most notifications are
    a clean 7-column table, but some are shredded into 11-15 columns by spurious
    empty splits, so a fixed index would read the wrong field. The office cell
    (Sarpanch/Panch) is the anchor: everything right of it is the reservation,
    everything left is the identifying detail.

    ``gp_column`` is the cell index the gram panchayat name was read from. A long
    name wraps onto the following row at that same index, so the caller needs it
    to reattach the tail - without which "Bhaini Chanderpal", "Bhaini Maharajpur"
    and "Bhaini Surjan" all collapse to "Bhaini".
    """
    kind, office_index = None, -1
    for i, cell in enumerate(cells):
        kind = office_kind(cell)
        if kind:
            office_index = i
            break
    if not kind:
        return None

    reservation = " ".join(c for c in cells[office_index + 1:] if c)

    # Some notifications render every glyph run twice, so cells arrive doubled
    # ("4", "4", "*iqtk", "*iqtk"). Collapse the repeats before reading columns,
    # or the duplicated serial number gets read as the gram panchayat name.
    left = [(i, c) for i, c in enumerate(cells[:office_index]) if c]
    left = [x for k, x in enumerate(left) if k == 0 or x[1] != left[k - 1][1]]

    gp = gp_column = None
    if kind == "sarpanch":
        sr = left.pop(0)[1] if left and left[0][1].isdigit() else None
        # The "--" in the ward column separates the gram panchayat name from the
        # person's name. In heavily fragmented tables the GP name is spread over
        # several cells, so that dash is the only reliable boundary; without it
        # a two-word name like "Bahlba Panri" loses its second half.
        boundary = next((k for k, (_, c) in enumerate(left) if is_ward_dash(c)), None)
        # with the dash present the GP name is everything before it; without it,
        # fall back to a single cell
        head, rest = (left[:boundary], left[boundary + 1:]) if boundary is not None \
            else (left[:1], left[1:])
        gp = " ".join(c for _, c in head) or None
        gp_column = head[0][0] if head else None
        left = rest
        ward = ""
    else:
        left = [x for x in left if not is_ward_dash(x[1])]
        ward = left.pop(0)[1] if left and left[0][1].isdigit() else ""
        sr = None

    name = left[0][1] if left else ""
    father = left[1][1] if len(left) > 1 else ""
    return kind, sr, gp, ward, name, father, reservation, gp_column


def load_manifest(path):
    """Map saved PDF filename -> (district, block) from the harvest manifest.

    The manifest is written by harvest.py from the index PDF, so district and
    block agree with the download by construction. Reading it here rather than
    re-deriving from the index keeps parsing offline and reproducible.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return {r["saved_as"]: (r["district"], r["block"]) for r in csv.DictReader(fh)}


def find_place(text):
    """Return (block, district, script) for a notification preamble, or None."""
    m = RE_BLOCK_EN.search(text)
    if m:
        return clean(m.group("block")), clean(m.group("district")), "latin"
    m = RE_BLOCK_HI.search(text)
    if m:
        return clean(m.group("block")), clean(m.group("district")), "krutidev"
    return None


def parse_pdf(path):
    """Yield seat dicts for one notification PDF.

    Each PDF holds exactly one block's notification, printed two or three times:
    typeset in Kruti Dev Hindi, then in English, occasionally in English twice.
    Every printing renumbers its gram panchayats from 1, so a drop in the serial
    number marks the start of the next printing. Rows are tagged with a
    ``printing`` index and one printing is chosen per file downstream - the seat
    numbering is the only reliable boundary, because the Hindi printings
    sometimes render their preamble as doubled characters ("22002222") and defeat
    any text match.
    """
    ctx: dict[str, str | None] = {"notif": None, "block": None, "district": None}
    printing = 0
    last_sr = None
    sr = gp = None
    pending = None

    def finish(row):
        """Interpret a buffered row once no more continuation lines can arrive."""
        if not row:
            return
        res = normalize_reservation(row["reservation_raw"])
        if not res:
            return
        caste, woman, script = res
        row.update(
            reservation=label(caste, woman),
            caste_reservation=caste,
            woman_reserved=woman,
            script=script,
        )
        yield row

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = clean(page.extract_text() or "")
            match = RE_NOTIF.search(text)
            if match:
                ctx["notif"] = match.group(1)
            place = find_place(text)
            # an English preamble anywhere in the file names the block for all
            # of it; a Kruti Dev one is only a fallback
            if place and (place[2] == "latin" or not ctx["block"]):
                if place[2] == "latin" or ctx["district"] is None:
                    ctx["block"], ctx["district"] = place[0], place[1]

            for table in page.find_tables():
                for raw in table.extract():
                    cells = [clean(c) for c in raw]
                    parsed = split_row(cells)
                    if not parsed:
                        # a stranded reservation tail belongs to the row above
                        if pending:
                            tail = continuation_tail(cells)
                            if tail:
                                pending["reservation_raw"] += " " + tail
                            # a long GP name wraps onto this row at the same
                            # cell index it occupied on the seat row
                            col = pending.get("gp_column")
                            if col is not None and col < len(cells):
                                frag = cells[col]
                                if frag and not _all_continuation_words(frag) \
                                        and not is_ward_dash(frag):
                                    pending["gram_panchayat"] = \
                                        f"{pending['gram_panchayat']} {frag}".strip()
                                    # the panch rows below inherit the GP name,
                                    # so repair the carried-forward copy too
                                    gp = pending["gram_panchayat"]
                        continue
                    yield from finish(pending)
                    (kind, row_sr, row_gp, ward, raw_name, raw_father, raw_res,
                     gp_column) = parsed
                    # Sarpanch rows carry the GP identity; the Panch rows under
                    # them leave those cells blank.
                    if row_sr:
                        if last_sr is not None and int(row_sr) <= last_sr:
                            printing += 1  # numbering restarted: next printing
                        last_sr = int(row_sr)
                        sr = row_sr
                    if row_gp:
                        gp = row_gp
                    name, unopposed = strip_unopposed(raw_name)
                    pending = {
                        "source_pdf": path.name,
                        "notification": ctx["notif"],
                        "printing": printing,
                        "district": ctx["district"],
                        "block": ctx["block"],
                        "sr_no": sr,
                        "gram_panchayat": gp,
                        "ward_no": ward,
                        "office": kind,
                        "reservation_raw": raw_res,
                        "winner": name,
                        "father_husband": strip_unopposed(raw_father)[0],
                        "unopposed": int(unopposed),
                        "gp_column": gp_column if kind == "sarpanch" else None,
                    }
    yield from finish(pending)

def crosscheck(rows):
    """Compare the Hindi and English printings of each notification.

    They are independent typesettings of the same seats, so agreement on the
    reservation of every GP is a real check on the parse rather than a
    self-consistency check. Disagreement means one printing was misread.
    """
    seats = collections.defaultdict(dict)
    for r in rows:
        if r["office"] == "sarpanch" and r["sr_no"]:
            seats[(r["source_pdf"], r["sr_no"])][r["script"]] = r["reservation"]

    both = {k: v for k, v in seats.items() if len(v) > 1}
    disagree = {k for k, v in both.items() if len(set(v.values())) > 1}

    # flag the seats where the two printings do not agree, so the doubt travels
    # with the data instead of being silently resolved in favour of English
    for r in rows:
        key = (r["source_pdf"], r["sr_no"])
        r["printings_agree"] = "" if key not in both else int(key not in disagree)

    if both:
        agreed = len(both) - len(disagree)
        print(f"\ncross-printing check: {agreed}/{len(both)} GPs agree between "
              f"the Hindi and English printings ({agreed / len(both) * 100:.1f}%)")
        for k in list(disagree)[:5]:
            print(f"    disagree: {both[k]}")
    return both, disagree


def select_printing(rows):
    """Keep one printing per file.

    Prefer the English printing - its gram panchayat names are readable without
    transliterating Kruti Dev - and among printings in the same script prefer the
    most complete one, since a printing can be cut short by a page the table
    finder could not read.
    """
    printings = collections.defaultdict(list)
    for r in rows:
        printings[(r["source_pdf"], r["printing"])].append(r)

    by_file = collections.defaultdict(list)
    for (pdf_name, _), group in printings.items():
        by_file[pdf_name].append(group)

    kept = []
    for groups in by_file.values():
        kept += max(
            groups,
            key=lambda g: (
                sum(r["script"] == "latin" for r in g) / len(g) > 0.5,
                sum(r["office"] == "sarpanch" for r in g),
                len(g),
            ),
        )
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="parse only the first N PDFs")
    ap.add_argument("--year", default=YEAR, help="election year to parse")
    args = ap.parse_args()

    out = DATA / args.year
    pdf_dir = out / "pdfs"
    pdfs = sorted(pdf_dir.glob("*.pdf"))[: args.limit]
    if not pdfs:
        sys.exit(f"no PDFs in {pdf_dir} - run harvest.py first")
    manifest = load_manifest(out / "manifest.csv")
    if not manifest:
        print("warning: no manifest.csv - run harvest.py", file=sys.stderr)

    rows = []
    for i, path in enumerate(pdfs, 1):
        try:
            rows.extend(parse_pdf(path))
        except Exception as exc:  # noqa: BLE001 - keep going, report at the end
            print(f"\nERROR {path.name}: {exc}", file=sys.stderr)
        print(f"\r  {i}/{len(pdfs)} {path.name:24s} rows={len(rows)}", end="", file=sys.stderr)
    print(file=sys.stderr)

    # the index is authoritative for where a notification belongs; the preamble
    # inside the PDF is only a fallback, and is missing entirely for the one
    # block published solely in Kruti Dev
    for r in rows:
        district, block = manifest.get(r["source_pdf"], ("", ""))
        r["district"] = district or r["district"] or ""
        r["block"] = block or r["block"] or ""

    crosscheck(rows)
    rows = select_printing(rows)
    gp = [r for r in rows if r["office"] == "sarpanch"]
    ward = [r for r in rows if r["office"] == "panch"]

    gp_cols = [
        "district", "block", "sr_no", "gram_panchayat", "reservation",
        "caste_reservation", "woman_reserved", "winner", "father_husband",
        "unopposed", "reservation_raw", "script", "printings_agree",
        "notification", "source_pdf",
    ]
    ward_cols = gp_cols[:4] + ["ward_no"] + gp_cols[4:]

    for name, data, cols in (
        ("gp_reservation.csv", gp, gp_cols),
        ("ward_reservation.csv", ward, ward_cols),
    ):
        data.sort(key=lambda r: ((r["district"] or ""), (r["block"] or ""),
                                 int(r["sr_no"]) if (r["sr_no"] or "").isdigit() else 0,
                                 int(r["ward_no"]) if (r["ward_no"] or "").isdigit() else 0))
        with (out / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore",
                                lineterminator="\n")
            w.writeheader()
            w.writerows(data)
        print(f"wrote {out / name}  ({len(data)} rows)")

    print(f"\nparsed {len(gp)} gram panchayats and {len(ward)} ward seats "
          f"from {len(pdfs)} notifications")
    print("run validate.py for the data checks")


if __name__ == "__main__":
    main()

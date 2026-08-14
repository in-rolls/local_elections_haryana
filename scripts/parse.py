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

from normalize import is_vacant, label, normalize_reservation, strip_unopposed

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
YEAR = "2022"

SARPANCH = {"sarpanch", "ljiap", "ljaip", "ljip", "lliap"}
PANCH = {"panch", "iap", "ipa"}

# "... Block-Narnaul, District-Mahendergarh during General Elections-2022"
RE_BLOCK_EN = re.compile(
    r"Block\s*[-–—]?\s*['‘\"]?\s*(?P<block>[A-Za-z][A-Za-z0-9 .&\-]{1,30}?)\s*['’\"]?\s*,?\s*"
    r"(?:and\s+)?District\s*[-–—:]?\s*['‘\"]?\s*(?P<district>[A-Za-z][A-Za-z .&\-]{1,25}?)"
    # 2022 ends "... during General Elections-2022", 2016 "... in the General
    # Election held in the month of January, 2016"
    r"\s*(?:during|for|in\b|,|$)",
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
def notification_re(year):
    """The notification's own serial number, e.g. "No. SEC/4E-II/2022/7385.- In
    pursuance ..." or, in Kruti Dev, "...@2022@7385-& gfj;k.kk iapk;rh jkt".

    This is the join key that makes the corpus tractable. The trailing s.161
    phrase is required because the same number format also appears inside table
    cells, in footnotes citing *other* notifications. The 2016 notifications put
    a "Dated: 10.02.2016" between the number and that phrase.
    """
    return re.compile(
        rf"{year}\s*[@/]\s*(\d{{3,5}})\s*[.,\-–—&]{{0,3}}\s*"
        rf"(?:Dated\s*:?\s*[\d.\-/]+\s*)?"
        rf"(?:In\s+pursuance|gfj;k\.kk\s+iapk;rh\s+jkt|,rn)",
        re.I,
    )


def clean(cell):
    return re.sub(r"\s+", " ", (cell or "").replace("\n", " ")).strip()


# **A known defect, diagnosed and not yet fixed.** Four attempts are recorded
# here so the fifth starts from evidence rather than from the beginning.
#
# pdfplumber.find_tables() splits one fully-ruled seven-column grid into two
# tables on some of these gazettes. Palwal/Prithla page 2 comes back as two,
# the right-hand one holding [father, office, reservation] - so split_row,
# which anchors on the office cell, parses all 29 rows happily while reading
# **the father as the winner with no ward at all**. That single failure is the
# source of both open entries on the worklist: 883 rows with no ward number,
# and 1,157 sharing a seat key, because the panchayat name is printed once per
# panchayat and blank on the ward rows beneath, so a panchayat whose column is
# never read lets its wards inherit the previous one's. Machhrauli had 23
# different people filed under one ward.
#
# The page is not at fault. It renders correctly in Devanagari and its text
# layer is faithful Kruti Dev; word positions are stable to the pixel, with the
# panchayat at x=99, the ward at 180, the name at 225 and the office at 377.
#
# What was tried, and what each cost:
#
#   1. Fall back to a positional read where the page has no office cell.
#      Never fired: the fragment has one.
#   2. Fall back where most panch rows lack a ward. Fired too widely and cost
#      365 rows of 2016 while fixing 2022.
#   3. Read both ways, keep whichever finds more numbered wards. 2022 improved;
#      2016 still lost 357 rows and colliding keys tripled. Maximising one
#      number let the others move.
#   4. Drop find_tables and always read positionally. Measurably worse: only
#      747 of 2,040 rows on Bhiwani come out identical, because a line-based
#      read loses the wrapped continuation lines that find_tables merges into
#      one cell - "vuqlwfpr ttkfr efgyk ds flok;" truncates to "... efgyk" -
#      and it reads preamble prose as rows.
#   5. Pass the page's own vertical rules as explicit_vertical_lines. On three
#      documents this looked right - Prithla gained 91 wards, Bhiwani and
#      Ambala were untouched - and across all 187 it lost 447 rows of 2022 and
#      raised ward-number holes from 713 to 972.
#
# The lesson from 3 and 5 is the same: a sample of three documents and a single
# scalar are both too small to choose between two readings of 187 files. A
# working fix has to be judged per document against several criteria at once -
# rows must not fall, numbered wards must rise, collisions and ward holes must
# not - and the criteria checked before the run rather than after.
#
# Surya is not the answer here, and was checked: the text layer is exact, so
# OCR would read a picture of text we can already extract, and would lose the
# cell merging exactly as attempt 4 did.


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


# A ward cell is usually a bare number, but Karnal and Palwal 2022 print the
# notification twice - Hindi, then English - and the English table writes
# "Ward 1" in that column. `isdigit()` is false there, so the cell was left
# behind and every field after it shifted one place right: the ward number
# ended up in `winner` and the winner's name in `father_husband`. 1,678 rows
# shipped with "Ward 1" where a person's name belongs.
RE_WARD_NUMBER = re.compile(r"^\s*(?:ward\s*(?:no\.?)?\s*)?(\d{1,3})\s*$", re.I)


def ward_number(cell):
    """The ward number a cell states, or None if it does not state one."""
    match = RE_WARD_NUMBER.match(cell or "")
    return match.group(1) if match else None


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
        ward = ""
        if left and ward_number(left[0][1]) is not None:
            ward = ward_number(left.pop(0)[1])
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


def parse_pdf(path, notif_pattern=None):
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
    notif_pattern = notif_pattern or notification_re("2022")
    ctx: dict[str, str | None] = {"notif": None, "block": None, "district": None}
    printing = 0
    # (ward, category) found on a row of their own, waiting for the row below
    stranded = None
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
            match = notif_pattern.search(text)
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
                        # A row holding a ward number and nothing but a
                        # category belongs to the row *below* it, not above.
                        # Where the category text wraps, the ward digit and the
                        # category are top-aligned in their cells while the
                        # name is baseline-aligned lower, so one printed line
                        # comes out as two: this one, and the next carrying the
                        # person and the office.
                        #
                        # Both halves were being read wrongly. split_row
                        # anchors on the office cell, so this half was dropped
                        # and its ward lost - and the continuation logic below,
                        # which exists for tails that really do belong to the
                        # row above, then attached this row's category to the
                        # *previous* seat. 1,014 rows of Kaithal, Mewat and
                        # Sirsa 2016 carried the neighbouring seat's
                        # reservation, which is worse than carrying none.
                        lone = [c for c in cells if c]
                        if lone and ward_number(lone[0]) is not None:
                            stranded = lone
                            continue
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
                    if stranded:
                        # Re-split the two halves as one row. The reservation
                        # is moved behind the office cell because that is where
                        # split_row expects it - on a wrapped line it is
                        # printed before the office, not after.
                        head = list(stranded)
                        res = (head.pop() if len(head) > 1
                               and normalize_reservation(head[-1]) else None)
                        rejoined = split_row(head + cells + ([res] if res else []))
                        # only where the row is actually missing its ward. A
                        # row that already states one is not a continuation of
                        # anything, and merging into it shifts the seat by one:
                        # Karnal produced ward 5 carrying ward 6's contents.
                        if (rejoined and rejoined[0] == "panch" and rejoined[3]
                                and not parsed[3]):
                            parsed = rejoined
                        stranded = None
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
                        "vacant": int(is_vacant(name)),
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
    # A notification number is only missing before the first preamble a file
    # yields - some Kruti Dev printings render theirs as doubled characters and
    # defeat the match. Those rows belong to that file's first notification.
    first = {}
    for r in rows:
        if r["notification"]:
            first.setdefault(r["source_pdf"], r["notification"])
    for r in rows:
        if not r["notification"]:
            r["notification"] = first.get(r["source_pdf"])

    printings = collections.defaultdict(list)
    for r in rows:
        printings[(r["source_pdf"], r["notification"], r["printing"])].append(r)

    # Group by notification rather than by file: a 2022 PDF holds one
    # notification printed two or three times, but a 2016 district PDF holds a
    # separate notification for each of its blocks, all of which must survive.
    by_notification = collections.defaultdict(list)
    for (pdf_name, notif, _), group in printings.items():
        by_notification[(pdf_name, notif)].append(group)

    kept = []
    for groups in by_notification.values():
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
    notif_pattern = notification_re(args.year)
    manifest = load_manifest(out / "manifest.csv")
    if not manifest:
        print("warning: no manifest.csv - run harvest.py", file=sys.stderr)

    rows = []
    for i, path in enumerate(pdfs, 1):
        try:
            rows.extend(parse_pdf(path, notif_pattern))
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
        "unopposed", "vacant", "reservation_raw", "script", "printings_agree",
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

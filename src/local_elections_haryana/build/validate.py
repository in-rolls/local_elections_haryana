"""Check the parsed data against the source, the manifest and the statute.

Final stage of the pipeline. Reads only the CSVs - no network, no PDF parsing -
so it can be re-run cheaply and its verdict is reproducible.

Exits non-zero if any FAIL check trips, so `make validate` is usable as a gate.
"""

import argparse
import collections
import csv
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parents[3] / "data"
YEAR = "2022"

# Official totals published by the State Election Commission.
# "basis" says what the published figure counts. 2022's was announced before
# polling and counts seats to be filled; 2016's was published afterwards and
# counts people actually elected, which excludes seats left vacant. Comparing
# our seat rows against an "elected" figure made 2016 look like a 102%
# over-count when it was really 98.8%.
OFFICIAL = {
    "2022": {
        "gram_panchayats": 6220,
        "panches": 61993,
        "blocks": 143,
        "basis": "seats",
    },
    "2016": {"gram_panchayats": 6193, "panches": 60438, "basis": "elected"},
    # SEC report on the 2010 general elections, sections 15.4-15.5: seats for
    # which elections were held.
    "2010": {"gram_panchayats": 6075, "panches": 58608, "basis": "seats"},
    # SEC, panch reservation table for the March 2000 elections (block rows in
    # data/2000/reference/sec_panch_reservation_2000.csv): seats to be filled.
    "2000": {"gram_panchayats": 6035, "panches": 54764, "basis": "seats"},
    # No 2005 total has been found: the commission's 2005 statistics page is
    # listed on its site but did not load. Coverage is reported, not tested.
}

# Haryana applies its reservations block by block, not statewide, which makes a
# per-block check far sharper than a state total: offsetting errors cannot hide
# in it. The shares themselves changed between the two elections - the women's
# quota went from one third to one half, and BC(A) reservation in panchayats
# did not exist before the 2021 amendment.
STATUTE = {
    "2022": {"women": 0.50, "bc_a": 0.08},
    "2016": {"women": 0.33, "bc_a": None},
    "2010": {"women": 0.33, "bc_a": None},
    "2005": {"women": 0.33, "bc_a": None},
    "2000": {"women": 0.33, "bc_a": None},
}


# Reservation categories a sarpanch row may carry. 2005 printed BC on a few
# sarpanch rows; whether that is a seat category is reviewed per block.
CASTES = {
    "default": ("NONE", "SC", "ST", "BC_A"),
    "2005": ("NONE", "SC", "BC"),
    "2000": ("NONE", "SC", "BC"),
}
# Sarpanch rows without a readable category: 2005's were found blank or
# ambiguous by a source-cell review (data/2005/reviews/reservation_reviews.csv);
# 2000's are cells the transcription could not resolve.
REVIEWED_BLANK = {"2005": 12, "2000": 38}
# 2000 sarpanch rows whose GP heading neither the transcription nor Tesseract
# read (data/2000/reference/sarpanch_provenance.csv, name_basis heading_unread);
# 2000's unresolved categories are transcription gaps, listed in the same file.
UNREAD_HEADINGS = {"2000": 36}


class Report:
    def __init__(self):
        self.failed = 0

    def check(self, ok, label, detail="", hard=True):
        if ok:
            status = "PASS"
        else:
            status = "FAIL" if hard else "WARN"
            self.failed += hard
        print(f"  [{status}] {label}" + (f" - {detail}" if detail else ""))


def read_csv(path):
    if not path.exists():
        sys.exit(f"{path} not found - run parse.py first")
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--year", default=YEAR, choices=("2000", "2005", "2010", "2016", "2022")
    )
    ap.add_argument("--input-dir", type=pathlib.Path, help="directory of derived CSVs")
    ap.add_argument("--verbose", action="store_true", help="list every offending block")
    args = ap.parse_args()

    year_dir = DATA / args.year
    inputs = args.input_dir or year_dir
    gp = read_csv(inputs / "gp_reservation.csv")
    ward = read_csv(inputs / "ward_reservation.csv")
    manifest = (
        read_csv(year_dir / "manifest.csv")
        if (year_dir / "manifest.csv").exists()
        else []
    )
    official = OFFICIAL.get(args.year, {})
    statute = STATUTE.get(args.year, STATUTE["2022"])
    report = Report()

    print(f"\n=== {args.year} Haryana gram panchayat reservation ===\n")

    # ---------------------------------------------------------------- coverage
    print("Coverage")
    blocks = {(r["district"], r["block"]) for r in gp}
    if official:
        # compare like with like: against an "elected" figure, drop vacant seats
        if official.get("basis") == "elected":
            gp_count = [r for r in gp if r.get("vacant") != "1"]
            ward_count = [r for r in ward if r.get("vacant") != "1"]
            print(
                f"  [INFO] basis - official figures count people elected; "
                f"{len(gp) - len(gp_count)} GP and {len(ward) - len(ward_count)} "
                f"ward seats were vacant"
            )
        else:
            gp_count, ward_count = gp, ward
        got, want = len(gp_count), official["gram_panchayats"]
        report.check(
            pct(got, want) >= 97,
            "gram panchayats vs official total",
            f"{got} of {want} ({pct(got, want):.1f}%)",
            hard=False,
        )
        got_w, want_w = len(ward_count), official["panches"]
        report.check(
            pct(got_w, want_w) >= 97,
            "panch seats vs official total",
            f"{got_w} of {want_w} ({pct(got_w, want_w):.1f}%)",
            hard=False,
        )
        if "blocks" in official:
            report.check(
                abs(len(blocks) - official["blocks"]) <= 2,
                "block count",
                f"{len(blocks)} parsed, {official['blocks']} expected",
                hard=False,
            )
        else:
            print(f"  [INFO] blocks parsed - {len(blocks)}")

    if manifest:
        seats = {r["source_pdf"] for r in gp} | {r["source_pdf"] for r in ward}
        # Zila Parishad and Panchayat Samiti notifications legitimately contain
        # no sarpanch or panch rows, so only block notifications must appear.
        block_pdfs = {
            r["saved_as"]
            for r in manifest
            if "Members" not in r["block"] and "Member" not in r["block"]
        }
        missing = sorted(block_pdfs - seats)
        report.check(
            not missing,
            "every block notification produced rows",
            f"{len(missing)} produced none: {missing[:3]}",
        )
        if all(r.get("archive_path") for r in manifest):
            held = sum((DATA / r["archive_path"]).exists() for r in manifest)
            print(f"  [INFO] source PDFs kept in the raw archive - {held} of "
                  f"{len(manifest)} held locally")  # fmt: skip
        else:
            present = {p.name for p in (year_dir / "pdfs").glob("*.pdf")}
            absent = {r["saved_as"] for r in manifest} - present
            report.check(
                not absent, "manifest files present on disk", f"{len(absent)} missing"
            )

    # ------------------------------------------------------------- correctness
    print("\nParse correctness")
    blank = [r for r in gp if not r["gram_panchayat"] or not r["block"]]
    unread = UNREAD_HEADINGS.get(args.year, 0)
    report.check(
        len(blank) <= unread,
        "no blank gram panchayat or block",
        f"{len(blank)} rows, {unread} of them GP headings not read",
    )

    # Kruti Dev mojibake is pure ASCII, so the script column is the only honest
    # way to tell whether a name is readable.
    untranslit = [r for r in gp if r["script"] == "krutidev"]
    report.check(
        not untranslit,
        "gram panchayat names readable",
        f"{len(untranslit)} rows only published in Kruti Dev",
        hard=False,
    )

    dupes = [
        k
        for k, n in collections.Counter(
            (r["district"], r["block"], r["gram_panchayat"]) for r in gp
        ).items()
        if n > 1
    ]
    report.check(
        not dupes,
        "gram panchayat names unique within block",
        f"{len(dupes)} repeated: {dupes[:3]}",
        hard=False,
    )

    # A panchayat's wards are numbered 1..N, so a gap is a seat we did not
    # read and a repeat is a seat we read twice. Nothing else here can see
    # either: every other check counts rows that exist, and the failures this
    # was written for **deleted** rows - a gazette typo that made
    # normalize_reservation return None, which discards the whole row rather
    # than blanking a field, and a wrapped line extracted as two rows where the
    # half carrying the ward number had no office cell to anchor on. Barnala
    # shipped five of its nine panches and every count said it was fine.
    wards_of = collections.defaultdict(list)
    for r in ward:
        if r["ward_no"].isdigit():
            wards_of[(r["district"], r["block"], r["gram_panchayat"])].append(
                int(r["ward_no"])
            )
    gaps, repeats, absent = [], [], 0
    for place, numbers in wards_of.items():
        missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
        if missing:
            gaps.append((place, missing))
            absent += len(missing)
        if len(numbers) != len(set(numbers)):
            repeats.append(place)
    report.check(
        not gaps,
        "ward numbers run 1..N within a panchayat",
        f"{len(gaps)} panchayats have a gap, {absent} seats absent; "
        f"e.g. {[(p[2], m[:4]) for p, m in gaps[:3]]}",
        hard=False,
    )
    report.check(
        not repeats,
        "no ward number appears twice in a panchayat",
        f"{len(repeats)} panchayats repeat a ward: {[p[2] for p in repeats[:3]]}",
        hard=False,
    )

    unnumbered = [r for r in ward if not r["ward_no"].strip()]
    report.check(
        not unnumbered,
        "every ward seat states its ward number",
        f"{len(unnumbered)} rows have none, so they share a seat key "
        f"with their neighbours",
        hard=False,
    )

    fabricated = [r for r in ward if r["winner"].strip().lower().startswith("ward ")]
    report.check(
        not fabricated,
        "no winner is a column label",
        f"{len(fabricated)} rows name a person 'Ward N' - the English "
        f"printing writes 'Ward 1' where the Hindi writes '1', and a "
        f"parser that wants a bare digit shifts every field right",
    )

    srs = collections.defaultdict(set)
    for r in gp:
        if r["sr_no"].isdigit():
            srs[(r["district"], r["block"])].add(int(r["sr_no"]))
    gappy = {
        b: sorted(set(range(1, max(v) + 1)) - v)
        for b, v in srs.items()
        if v and set(range(1, max(v) + 1)) - v
    }
    report.check(
        not gappy,
        "serial numbers contiguous within block",
        f"{len(gappy)} blocks have gaps",
        hard=False,
    )

    # Reported, not gated. Agreement measures the *worse* of the two printings,
    # and the Kruti Dev one is materially worse: it arrives with characters
    # doubled, words split mid-token, labels truncated and glyph runs reordered.
    # Every disagreement inspected by hand had the English right. The
    # independent evidence for that is the per-block statutory check below,
    # which the English-derived rows satisfy and the Hindi-derived ones do not.
    # So a disagreement marks a seat worth auditing, not a seat known to be
    # wrong - hence the per-row printings_agree flag rather than a hard gate.
    agree = [r for r in gp if r["printings_agree"] == "1"]
    disagree = [r for r in gp if r["printings_agree"] == "0"]
    checked = len(agree) + len(disagree)
    report.check(
        pct(len(agree), checked) >= 99,
        "Hindi and English printings agree",
        f"{len(agree)}/{checked} ({pct(len(agree), checked):.1f}%), "
        f"{len(gp) - checked} had only one printing; "
        f"disagreements are flagged in printings_agree",
        hard=False,
    )

    unparsed = [
        r
        for r in gp
        if r["caste_reservation"] not in CASTES.get(args.year, CASTES["default"])
        or r["woman_reserved"] not in ("0", "1")
    ]
    # 2005's source cells that a review found blank or ambiguous stay blank;
    # each carries its reason in the parse's reservation review, so they are
    # reported, and the shares below are taken over the readable rows.
    reviewed_blank = REVIEWED_BLANK.get(args.year, 0)
    report.check(
        len(unparsed) <= reviewed_blank,
        "reservation normalised on every row",
        f"{len(unparsed)} rows, {reviewed_blank} of them explained in the year's notes",
    )

    # --------------------------------------------------------------- statutory
    print("\nStatutory shares (the sharpest check: these bind per block)")
    women_share, bc_share = statute["women"], statute["bc_a"]
    known = [r for r in gp if r["woman_reserved"] in ("0", "1")]
    women = sum(int(r["woman_reserved"]) for r in known)
    report.check(
        abs(pct(women, len(known)) - 100 * women_share) <= 3,
        f"statewide women's share is {women_share * 100:.0f}%",
        f"{women}/{len(known)} = {pct(women, len(known)):.1f}%",
    )

    by_block = collections.defaultdict(list)
    for r in gp:
        by_block[(r["district"], r["block"])].append(r)

    # Blocks whose printed categories were reviewed and found defective in the
    # source itself are reported, not failed; an unreviewed block still fails.
    defects_path = year_dir / "reference" / "category_defects.csv"
    reviewed = (
        {(r["district"], r["block"]): r["decision"] for r in read_csv(defects_path)}
        if defects_path.exists()
        else {}
    )
    off_women, off_bc = [], []
    for key, rows in by_block.items():
        rows = [x for x in rows if x["woman_reserved"] in ("0", "1")]
        w = pct(sum(int(x["woman_reserved"]) for x in rows), len(rows))
        if abs(w - 100 * women_share) > 6:
            off_women.append((key, len(rows), w))
        if bc_share is not None:
            b = pct(sum(x["caste_reservation"] == "BC_A" for x in rows), len(rows))
            if abs(b - 100 * bc_share) > 6:
                off_bc.append((key, len(rows), b))

    unreviewed = [o for o in off_women if o[0] not in reviewed]
    report.check(
        len(unreviewed) <= 0.05 * len(by_block),
        f"per-block women's share within 6pp of {women_share * 100:.0f}%",
        f"{len(off_women)} of {len(by_block)} blocks off, "
        f"{len(off_women) - len(unreviewed)} of them reviewed in {defects_path.name}",
    )
    if bc_share is None:
        # Panchayat BC(A) reservation only arrived with the 2021 amendment, so a
        # handful of 2016 rows labelled "Backward Class" is plausible as a
        # stray, but a real share would mean the parse is wrong.
        bc_rows = sum(
            r["caste_reservation"] in ("BC_A", "BC")
            and (r["district"], r["block"]) not in reviewed
            for r in gp
        )
        report.check(
            pct(bc_rows, len(gp)) < 0.5,
            "BC(A) seats negligible (not a category until 2021)",
            f"{bc_rows} rows = {pct(bc_rows, len(gp)):.2f}% outside reviewed blocks",
        )
    else:
        report.check(
            len(off_bc) <= 0.15 * len(by_block),
            f"per-block BC(A) share within 6pp of {bc_share * 100:.0f}%",
            f"{len(off_bc)} of {len(by_block)} blocks off",
            hard=False,
        )

    for title, offenders in (("women", off_women), ("BC(A)", off_bc)):
        shown = sorted(offenders, key=lambda x: -abs(x[2] - 100 * women_share))
        for key, n, share in shown if args.verbose else shown[:5]:
            print(f"        {title:6s} {key[0]}/{key[1]}: n={n}, {share:.0f}%")

    # ----------------------------------------------------------------- profile
    print("\nDistribution")
    for k, v in collections.Counter(r["reservation"] for r in gp).most_common():
        print(f"  {v:6d}  {pct(v, len(gp)):5.1f}%  {k}")
    print(
        f"\n  {len(by_block)} blocks, {len({r['district'] for r in gp})} districts, "
        f"{len(gp)} gram panchayats, {len(ward)} ward seats"
    )

    print(
        f"\n{'FAILED' if report.failed else 'OK'}: "
        f"{report.failed} hard check(s) failed\n"
    )
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())

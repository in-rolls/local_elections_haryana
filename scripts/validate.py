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

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
YEAR = "2022"

# Official totals published for the 2022 Haryana panchayat general election.
OFFICIAL = {"2022": {"gram_panchayats": 6220, "panches": 61993, "blocks": 143}}

# Haryana reserves half of all sarpanch seats for women and 8% for BC(A), and
# both are applied block by block, not statewide. That makes a per-block check
# far sharper than a state total: offsetting errors cannot hide in it.
WOMEN_SHARE = 0.50
BC_A_SHARE = 0.08


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
    ap.add_argument("--year", default=YEAR)
    ap.add_argument("--verbose", action="store_true", help="list every offending block")
    args = ap.parse_args()

    year_dir = DATA / args.year
    gp = read_csv(year_dir / "gp_reservation.csv")
    ward = read_csv(year_dir / "ward_reservation.csv")
    manifest = read_csv(year_dir / "manifest.csv") if (year_dir / "manifest.csv").exists() else []
    official = OFFICIAL.get(args.year, {})
    report = Report()

    print(f"\n=== {args.year} Haryana gram panchayat reservation ===\n")

    # ---------------------------------------------------------------- coverage
    print("Coverage")
    blocks = {(r["district"], r["block"]) for r in gp}
    if official:
        got, want = len(gp), official["gram_panchayats"]
        report.check(pct(got, want) >= 97, "gram panchayats vs official total",
                     f"{got} of {want} ({pct(got, want):.1f}%)", hard=False)
        got_w, want_w = len(ward), official["panches"]
        report.check(pct(got_w, want_w) >= 97, "panch seats vs official total",
                     f"{got_w} of {want_w} ({pct(got_w, want_w):.1f}%)", hard=False)
        report.check(abs(len(blocks) - official["blocks"]) <= 2, "block count",
                     f"{len(blocks)} parsed, {official['blocks']} expected", hard=False)

    if manifest:
        seats = {r["source_pdf"] for r in gp} | {r["source_pdf"] for r in ward}
        # Zila Parishad and Panchayat Samiti notifications legitimately contain
        # no sarpanch or panch rows, so only block notifications must appear.
        block_pdfs = {r["saved_as"] for r in manifest
                      if "Members" not in r["block"] and "Member" not in r["block"]}
        missing = sorted(block_pdfs - seats)
        report.check(not missing, "every block notification produced rows",
                     f"{len(missing)} produced none: {missing[:3]}")
        present = {p.name for p in (year_dir / "pdfs").glob("*.pdf")}
        absent = {r["saved_as"] for r in manifest} - present
        report.check(not absent, "manifest files present on disk",
                     f"{len(absent)} missing")

    # ------------------------------------------------------------- correctness
    print("\nParse correctness")
    blank = [r for r in gp if not r["gram_panchayat"] or not r["block"]]
    report.check(not blank, "no blank gram panchayat or block",
                 f"{len(blank)} rows")

    # Kruti Dev mojibake is pure ASCII, so the script column is the only honest
    # way to tell whether a name is readable.
    untranslit = [r for r in gp if r["script"] == "krutidev"]
    report.check(not untranslit, "gram panchayat names readable",
                 f"{len(untranslit)} rows only published in Kruti Dev", hard=False)

    dupes = [k for k, n in collections.Counter(
        (r["district"], r["block"], r["gram_panchayat"]) for r in gp).items() if n > 1]
    report.check(not dupes, "gram panchayat names unique within block",
                 f"{len(dupes)} repeated: {dupes[:3]}", hard=False)

    srs = collections.defaultdict(set)
    for r in gp:
        if r["sr_no"].isdigit():
            srs[(r["district"], r["block"])].add(int(r["sr_no"]))
    gappy = {b: sorted(set(range(1, max(v) + 1)) - v) for b, v in srs.items()
             if v and set(range(1, max(v) + 1)) - v}
    report.check(not gappy, "serial numbers contiguous within block",
                 f"{len(gappy)} blocks have gaps", hard=False)

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
    report.check(pct(len(agree), checked) >= 99,
                 "Hindi and English printings agree",
                 f"{len(agree)}/{checked} ({pct(len(agree), checked):.1f}%), "
                 f"{len(gp) - checked} had only one printing; "
                 f"disagreements are flagged in printings_agree", hard=False)

    unparsed = [r for r in gp if r["caste_reservation"] not in
                ("NONE", "SC", "ST", "BC_A") or r["woman_reserved"] not in ("0", "1")]
    report.check(not unparsed, "reservation normalised on every row",
                 f"{len(unparsed)} rows")

    # --------------------------------------------------------------- statutory
    print("\nStatutory shares (the sharpest check: these bind per block)")
    women = sum(int(r["woman_reserved"]) for r in gp)
    report.check(abs(pct(women, len(gp)) - 100 * WOMEN_SHARE) <= 2,
                 "statewide women's share is 50%",
                 f"{women}/{len(gp)} = {pct(women, len(gp)):.1f}%")

    by_block = collections.defaultdict(list)
    for r in gp:
        by_block[(r["district"], r["block"])].append(r)

    off_women, off_bc = [], []
    for key, rows in by_block.items():
        w = pct(sum(int(x["woman_reserved"]) for x in rows), len(rows))
        if abs(w - 100 * WOMEN_SHARE) > 6:
            off_women.append((key, len(rows), w))
        b = pct(sum(x["caste_reservation"] == "BC_A" for x in rows), len(rows))
        if abs(b - 100 * BC_A_SHARE) > 6:
            off_bc.append((key, len(rows), b))

    report.check(len(off_women) <= 0.05 * len(by_block),
                 "per-block women's share within 6pp of 50%",
                 f"{len(off_women)} of {len(by_block)} blocks off")
    report.check(len(off_bc) <= 0.15 * len(by_block),
                 "per-block BC(A) share within 6pp of 8%",
                 f"{len(off_bc)} of {len(by_block)} blocks off", hard=False)

    for title, offenders in (("women", off_women), ("BC(A)", off_bc)):
        shown = sorted(offenders, key=lambda x: -abs(x[2] - 50))
        for key, n, share in (shown if args.verbose else shown[:5]):
            print(f"        {title:6s} {key[0]}/{key[1]}: n={n}, {share:.0f}%")

    # ----------------------------------------------------------------- profile
    print("\nDistribution")
    for k, v in collections.Counter(r["reservation"] for r in gp).most_common():
        print(f"  {v:6d}  {pct(v, len(gp)):5.1f}%  {k}")
    print(f"\n  {len(by_block)} blocks, {len({r['district'] for r in gp})} districts, "
          f"{len(gp)} gram panchayats, {len(ward)} ward seats")

    print(f"\n{'FAILED' if report.failed else 'OK'}: "
          f"{report.failed} hard check(s) failed\n")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())

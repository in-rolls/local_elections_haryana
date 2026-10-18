"""Candidate block pairs between two elections, for review by hand.

The block crosswalks in `data/crosswalks/` are decisions, not outputs, so they
are never regenerated. This writes the evidence a reviewer reads before making
them: for every earlier and later block in the same blocking group (a district,
or districts whose blocks moved between them), how many folded GP names they
share. A pair is proposed `linked` when it shares at least five names or a fifth
of the later block's GPs, and `excluded` when it shares a few, which is what two
blocks sharing common village names look like.

    uv run python -m local_elections_haryana.linkage.block_evidence 2005 2010

Writes `data/crosswalks/evidence/block_<a>_<b>.csv`.
"""

import argparse
from pathlib import Path

import pandas as pd

from local_elections_haryana.linkage.gp_links import CROSSWALKS, DATA, PAIRS, name_key

MIN_SHARED, MIN_SHARE, MIN_LISTED = 5, 0.20, 3


def names(year, to_later, family, later):
    d = pd.read_parquet(DATA / "fin" / f"gp_reservation_{year}.parquet")
    district = d["district"] if year == later else d["district"].map(to_later)
    if district.isna().any():
        missing = sorted(d.loc[district.isna(), "district"].unique())
        raise SystemExit(f"{year} districts missing from the crosswalk: {missing}")
    d["group"] = district.replace(family)
    d["folded"] = [name_key(n)[0] for n in d["gram_panchayat"]]
    return d


def evidence(a, b):
    label = f"{a}_{b}"
    family = PAIRS[label]["family"]
    districts = pd.read_csv(CROSSWALKS / f"district_{a}_{b}.csv")
    to_later = dict(
        zip(districts[f"district_{a}"], districts[f"district_{b}"], strict=True)
    )
    left, right = names(a, to_later, family, b), names(b, to_later, family, b)
    rows = []
    for group in sorted(set(left["group"]) & set(right["group"])):
        lg, rg = left[left["group"] == group], right[right["group"] == group]
        for (da, ba), x in lg.groupby(["district", "block"]):
            for (db, bb), y in rg.groupby(["district", "block"]):
                shared = len(set(x["folded"]) & set(y["folded"]))
                if shared < MIN_LISTED:
                    continue
                share = shared / len(y)
                rows.append(
                    {
                        f"district_{a}": da,
                        f"block_{a}": ba,
                        f"district_{b}": db,
                        f"block_{b}": bb,
                        "proposed": "linked"
                        if shared >= MIN_SHARED or share >= MIN_SHARE
                        else "excluded",
                        "shared_gp_names": shared,
                        f"gps_{a}": len(x),
                        f"gps_{b}": len(y),
                        f"shared_share_of_{b}": round(share, 3),
                    }
                )
    out = CROSSWALKS / "evidence" / f"block_{a}_{b}.csv"
    out.parent.mkdir(exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(out, index=False)
    return table, out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("earlier", type=int)
    ap.add_argument("later", type=int)
    args = ap.parse_args()
    table, out = evidence(args.earlier, args.later)
    print(f"{len(table)} candidate pairs -> {Path(out)}")


if __name__ == "__main__":
    main()

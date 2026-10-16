"""Link sarpanch seats between the 2016 and 2022 elections.

No GP identifier survives between the two notifications, and blocks were split
and renamed in between. Districts and blocks are therefore matched through the
reviewed crosswalks in `data/crosswalks/`, and a GP pair is a candidate only when
its two blocks form a `linked` row there. Inside those block pairs, GP names are
folded to absorb romanization variants and paired one-to-one with preclink.
Numbers and compass words in a name ("Kheri-1", "Uttari") veto a pair whose
counterpart says otherwise.

Two passes run. The first accepts names alone. The second, on what remains, also
requires the same number of ward seats, an attribute that shares nothing with the
name. Ward agreement among first-pass links is reported as the check on the
names and is not used to make them.

Names the 2022 notifications printed in Kruti Dev are read in their romanized
form from `data/inferred/kruti_dev_names_2022.csv`.
"""

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from preclink import ExactComparison, Pipeline
from rapidfuzz import fuzz

DATA = Path("data")
OUT = DATA / "linkage"
CROSSWALKS = DATA / "crosswalks"
KRUTI = DATA / "inferred" / "kruti_dev_names_2022.csv"
KEY = ["district", "block", "sr_no", "gram_panchayat"]
NAME_THRESHOLD = 0.80
# Equal weights on name and ward count: 0.85 requires equal wards and a name
# score of at least 0.70. Equal ward counts arise by chance for about one pair in
# seven within a block, so they cannot rescue a weaker name.
WARD_PASS_THRESHOLD = 0.85
FOLDS = [
    (r"[^a-z]", ""),
    (r"aa+", "a"),
    (r"ee+|ii+", "i"),
    (r"oo+|uu+", "u"),
    (r"w", "v"),
    (r"z", "j"),
    (r"ph", "f"),
    (r"q", "k"),
    (r"([bcdgjkpt])h", r"\1"),
    (r"sh", "s"),
    (r"rh", "r"),
    (r"y", "i"),
    (r"(.)\1", r"\1"),
]
DIRECTIONS = {
    "east": r"purv|poorv|purab",
    "west": r"pash?chim|pachim",
    "north": r"uttar|utter",
    "south": r"dakshin|dakhin|dachhin",
    # Twin villages are distinguished by these; Surpura Kalan is not Surpura Khurd.
    "kalan": r"\bkal[ae]?n\b|\bkalaan\b",
    "khurd": r"\bkhurd\b|\bkhurad\b",
    "buzurg": r"\bbuzurg\b|\bbujurg\b",
    "khas": r"\bkhas\b|\bkhaas\b",
}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4}


def fold(name):
    text = (name or "").lower()
    for pattern, replacement in FOLDS:
        text = re.sub(pattern, replacement, text)
    return text


def name_key(name):
    """Folded name, with numbers (Arabic or Roman), directions and twin-village
    qualifiers read from it; qualifiers are removed from the folded name."""
    text = (name or "").lower()
    numbers = {int(n) for n in re.findall(r"\d+", text)}
    numbers |= {ROMAN[w] for w in re.findall(r"\b(i{1,3}|iv)\b", text)}
    directions = {d for d, p in DIRECTIONS.items() if re.search(p, text)}
    stripped = re.sub(r"\b(i{1,3}|iv)\b|\d+", " ", text)
    for pattern in list(DIRECTIONS.values())[4:]:
        stripped = re.sub(pattern, " ", stripped)
    return fold(stripped), frozenset(numbers), frozenset(directions)


def similarity(a, b):
    if not a or not b:
        return 0.0
    skeleton = fuzz.ratio(re.sub("[aeiou]", "", a), re.sub("[aeiou]", "", b)) - 5
    return max(fuzz.ratio(a, b), skeleton) / 100


@dataclass(frozen=True, slots=True)
class PlaceName:
    """preclink comparison on `name_key` tuples (folded, numbers, directions,
    block pair allowed)."""

    column: str = "name_key"
    weight: float = 1.0

    def compare(self, left, right):
        scores = []
        for (a, a_num, a_dir, a_block), (b, b_num, b_dir, b_block) in zip(
            left, right, strict=True
        ):
            conflict = (a_num and b_num and a_num != b_num) or (
                a_dir and b_dir and a_dir != b_dir
            )
            allowed = (a_block, b_block) in ALLOWED
            scores.append(similarity(a, b) if allowed and not conflict else 0.0)
        return pd.Series(scores, index=left.index)


ALLOWED: set = set()


def crosswalks():
    districts = pd.read_csv(CROSSWALKS / "district_2016_2022.csv")
    blocks = pd.read_csv(CROSSWALKS / "block_2016_2022.csv")
    linked = blocks[blocks["decision"] == "linked"]
    # Districts whose blocks moved between them share one blocking group.
    family = {"Charkhi Dadri": "Bhiwani"}
    to_2022 = dict(
        zip(districts["district_2016"], districts["district_2022"], strict=True)
    )
    pairs = {
        ((r.district_2016, r.block_2016), (r.district_2022, r.block_2022))
        for r in linked.itertuples()
    }
    return to_2022, family, pairs, blocks


def gps(year, to_2022, family):
    d = pd.read_parquet(DATA / "fin" / f"gp_reservation_{year}.parquet")
    wards = (
        pd.read_parquet(DATA / "fin" / f"ward_reservation_{year}.parquet")
        .groupby(KEY)
        .size()
        .rename("wards")
    )
    d = d.join(wards, on=KEY)
    d = d[~d.duplicated(KEY, keep=False)].copy()
    d["name"] = d["gram_panchayat"]
    if year == 2022:
        kruti = pd.read_csv(KRUTI, dtype={"sr_no": str})
        latin = kruti.set_index(["district", "block", "sr_no", "gram_panchayat"])
        romanized = latin["gram_panchayat_latin"].reindex(d.set_index(KEY).index)
        d["name"] = romanized.where(romanized.notna(), d["name"].to_numpy()).to_numpy()
    district_2022 = d["district"] if year == 2022 else d["district"].map(to_2022)
    d["group"] = district_2022.replace(family)
    d["key"] = d[KEY].astype(str).agg("|".join, axis=1)
    d["name_key"] = [
        (*name_key(n), (dist, blk))
        for n, dist, blk in zip(d["name"], d["district"], d["block"], strict=True)
    ]
    return d.reset_index(drop=True)


def link(left, right, comparisons, threshold):
    pipeline = (
        Pipeline()
        .block(on="group")
        .score(comparisons=comparisons)
        .filter(min_score=threshold)
        .decide(method="hungarian")
        .build()
    )
    found = []
    for group in sorted(set(left["group"]) & set(right["group"])):
        lg = left[left["group"] == group].reset_index(drop=True)
        rg = right[right["group"] == group].reset_index(drop=True)
        matches = pipeline.link(
            lg[["group", "name_key", "wards"]], rg[["group", "name_key", "wards"]]
        ).matches
        if matches.empty:
            continue
        found.append(
            pd.DataFrame(
                {
                    "key_2016": lg.loc[matches["left_index"], "key"].to_numpy(),
                    "key_2022": rg.loc[matches["right_index"], "key"].to_numpy(),
                    "name_score": matches["name_key_score"].to_numpy(),
                }
            )
        )
    return pd.concat(found, ignore_index=True) if found else pd.DataFrame()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out=OUT):
    to_2022, family, pairs, _ = crosswalks()
    ALLOWED.clear()
    ALLOWED.update(pairs)
    g16, g22 = gps(2016, to_2022, family), gps(2022, to_2022, family)
    first = link(g16, g22, [PlaceName()], NAME_THRESHOLD).assign(link_pass="name")
    rest16 = g16[~g16["key"].isin(first["key_2016"])]
    rest22 = g22[~g22["key"].isin(first["key_2022"])]
    second = link(
        rest16, rest22, [PlaceName(), ExactComparison("wards")], WARD_PASS_THRESHOLD
    ).assign(link_pass="name_and_wards")
    pairs_found = pd.concat([first, second], ignore_index=True)
    side = {
        2016: g16.set_index("key")[[*KEY, "name", "wards"]],
        2022: g22.set_index("key")[[*KEY, "name", "wards"]],
    }
    table = pairs_found.join(side[2016].add_suffix("_2016"), on="key_2016").join(
        side[2022].add_suffix("_2022"), on="key_2022"
    )
    table = table.drop(columns=["key_2016", "key_2022"]).sort_values(
        ["district_2016", "block_2016", "sr_no_2016"]
    )
    named = table[table["link_pass"] == "name"]
    agree = (named["wards_2016"] == named["wards_2022"]).mean()
    shuffled = named.groupby("block_2022")["wards_2022"].transform(
        lambda s: s.sample(frac=1, random_state=1).to_numpy()
    )
    checks = {
        "gps_2016": len(g16),
        "gps_2022": len(g22),
        "linked": len(table),
        "linked_by_name": len(named),
        "linked_by_name_and_wards": len(table) - len(named),
        "ward_count_agreement_name_pass": round(agree, 4),
        "ward_count_agreement_shuffled_within_block": round(
            (named["wards_2016"] == shuffled).mean(), 4
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    path = out / "gp_2016_2022.parquet"
    table.to_parquet(path, index=False)
    inputs = [
        *(DATA / "fin" / f"{t}_reservation_{y}.parquet" for t in ("gp", "ward")
          for y in (2016, 2022)),
        CROSSWALKS / "district_2016_2022.csv",
        CROSSWALKS / "block_2016_2022.csv",
        KRUTI,
    ]  # fmt: skip
    manifest = {
        "purpose": (
            "Research crosswalk between 2016 and 2022 sarpanch seats. A link states "
            "that names agree inside a reviewed block pair, not that boundaries "
            "are unchanged."
        ),
        "matcher": {
            "preclink": version("preclink"),
            "name_threshold": NAME_THRESHOLD,
            "ward_pass_threshold": WARD_PASS_THRESHOLD,
        },
        "inputs": {str(p): sha(p) for p in inputs},
        "code_sha256": sha(__file__),
        "validation": checks,
        "files": [{"path": path.name, "rows": len(table), "sha256": sha(path)}],
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()

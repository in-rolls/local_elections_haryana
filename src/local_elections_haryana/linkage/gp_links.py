"""Link sarpanch seats between consecutive elections (2010-2016, 2016-2022).

No GP identifier survives between notifications, and blocks were split and
renamed in between. Districts and blocks are therefore matched through the
reviewed crosswalks in `data/manual/crosswalks/`, and a GP pair is a candidate only when
its two blocks form a `linked` row there. Inside those block pairs, GP names are
folded to absorb romanization variants and paired one-to-one with preclink.
Numbers and compass words in a name ("Kheri-1", "Uttari") veto a pair whose
counterpart says otherwise.

Two passes run. The first accepts names alone. The second, on what remains, also
requires the same number of ward seats, an attribute that shares nothing with the
name. Ward agreement among first-pass links is reported as the check on the
names and is not used to make them.

Names the 2022 notifications printed in Kruti Dev are read in their romanized
form from `data/release/inferred/kruti_dev_names_2022.csv`.
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

from local_elections_haryana.paths import SEAT_TABLES

DATA = Path("data")
OUT = DATA / "release" / "linkage"
CROSSWALKS = DATA / "manual" / "crosswalks"
KRUTI = DATA / "release" / "inferred" / "kruti_dev_names_2022.csv"
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
    "south": r"daksh[ai]n|dakhin|dachhin",
    # Twin villages are distinguished by these; Surpura Kalan is not Surpura Khurd.
    "kalan": r"\bkal[ae]?n\b|\bkalaan\b",
    "khurd": r"\bkhurd\b|\bkhurad\b",
    "buzurg": r"\bbuzurg\b|\bbujurg\b",
    "khas": r"\bkhas\b|\bkhaas\b",
}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4}


# A name may state a direction, a twin-village qualifier, both or neither. Two
# names conflict only when both state one from the same family and they differ.
QUALIFIER_FAMILIES = (
    frozenset({"east", "west", "north", "south"}),
    frozenset({"kalan", "khurd", "buzurg", "khas"}),
)


def qualifiers_conflict(a, b):
    return any((a & f) and (b & f) and (a & f) != (b & f) for f in QUALIFIER_FAMILIES)


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
            conflict = (a_num and b_num and a_num != b_num) or qualifiers_conflict(
                a_dir, b_dir
            )
            allowed = (a_block, b_block) in ALLOWED
            scores.append(similarity(a, b) if allowed and not conflict else 0.0)
        return pd.Series(scores, index=left.index)


ALLOWED: set = set()
# Districts whose blocks moved between them share one blocking group.
PAIRS = {
    # Mewat district was formed in 2005 from Gurgaon's Nuh, Nagina, Punhana,
    # Firozpur Jhirka and Taoru blocks and Faridabad's Hathin.
    "2000_2005": {
        "years": (2000, 2005),
        "family": {"Mewat": "Gurgaon", "Faridabad": "Gurgaon"},
    },
    # Palwal district was formed in 2008 from Faridabad's Palwal, Hassanpur and
    # Hodal blocks and Mewat's Hathin.
    "2005_2010": {
        "years": (2005, 2010),
        "family": {"Palwal": "Faridabad", "Mewat": "Faridabad"},
    },
    "2010_2016": {"years": (2010, 2016), "family": {}},
    "2016_2022": {"years": (2016, 2022), "family": {"Charkhi Dadri": "Bhiwani"}},
}


def crosswalks(a, b):
    districts = pd.read_csv(CROSSWALKS / f"district_{a}_{b}.csv")
    blocks = pd.read_csv(CROSSWALKS / f"block_{a}_{b}.csv")
    linked = blocks[blocks["decision"] == "linked"]
    to_later = dict(
        zip(districts[f"district_{a}"], districts[f"district_{b}"], strict=True)
    )
    pairs = {
        ((getattr(r, f"district_{a}"), getattr(r, f"block_{a}")),
         (getattr(r, f"district_{b}"), getattr(r, f"block_{b}")))
        for r in linked.itertuples()
    }  # fmt: skip
    return to_later, pairs


def gps(year, later, to_later, family):
    # 2000 GPs whose printed serial was not read carry no sr_no
    d = pd.read_parquet(DATA / "release" / str(year) / SEAT_TABLES["gp"])
    d[KEY] = d[KEY].fillna("")
    wards = (
        pd.read_parquet(DATA / "release" / str(year) / SEAT_TABLES["ward"])
        .fillna(dict.fromkeys(KEY, ""))
        .groupby(KEY)
        .size()
        .rename("wards")
    )
    d = d.join(wards, on=KEY)
    # a GP whose heading was not read (2000) has no name to link on
    d = d[d.gram_panchayat.fillna("").str.strip() != ""]
    d = d[~d.duplicated(KEY, keep=False)].copy()
    d["name"] = d["gram_panchayat"]
    if year == 2022:
        kruti = pd.read_csv(KRUTI, dtype={"sr_no": str})
        latin = kruti.set_index(["district", "block", "sr_no", "gram_panchayat"])
        romanized = latin["gram_panchayat_latin"].reindex(d.set_index(KEY).index)
        d["name"] = romanized.where(romanized.notna(), d["name"].to_numpy()).to_numpy()
    district_later = d["district"] if year == later else d["district"].map(to_later)
    d["group"] = district_later.replace(family)
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
                    "key_a": lg.loc[matches["left_index"], "key"].to_numpy(),
                    "key_b": rg.loc[matches["right_index"], "key"].to_numpy(),
                    "name_score": matches["name_key_score"].to_numpy(),
                }
            )
        )
    return pd.concat(found, ignore_index=True) if found else pd.DataFrame()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_pair(label):
    a, b = PAIRS[label]["years"]
    to_later, pairs = crosswalks(a, b)
    ALLOWED.clear()
    ALLOWED.update(pairs)
    family = PAIRS[label]["family"]
    ga, gb = gps(a, b, to_later, family), gps(b, b, to_later, family)
    first = link(ga, gb, [PlaceName()], NAME_THRESHOLD).assign(link_pass="name")
    rest_a = ga[~ga["key"].isin(first["key_a"])]
    rest_b = gb[~gb["key"].isin(first["key_b"])]
    second = link(
        rest_a, rest_b, [PlaceName(), ExactComparison("wards")], WARD_PASS_THRESHOLD
    ).assign(link_pass="name_and_wards")
    found = pd.concat([first, second], ignore_index=True)
    cols = [*KEY, "name", "wards"]
    table = found.join(ga.set_index("key")[cols].add_suffix(f"_{a}"), on="key_a").join(
        gb.set_index("key")[cols].add_suffix(f"_{b}"), on="key_b"
    )
    table = table.drop(columns=["key_a", "key_b"]).sort_values(
        [f"district_{a}", f"block_{a}", f"sr_no_{a}"]
    )
    named = table[table["link_pass"] == "name"]
    agree = (named[f"wards_{a}"] == named[f"wards_{b}"]).mean()
    shuffled = named.groupby(f"block_{b}")[f"wards_{b}"].transform(
        lambda s: s.sample(frac=1, random_state=1).to_numpy()
    )
    checks = {
        f"gps_{a}": len(ga),
        f"gps_{b}": len(gb),
        "linked": len(table),
        "linked_by_name": len(named),
        "linked_by_name_and_wards": len(table) - len(named),
        "ward_count_agreement_name_pass": round(agree, 4),
        "ward_count_agreement_shuffled_within_block": round(
            (named[f"wards_{a}"] == shuffled).mean(), 4
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"gp_{a}_{b}.parquet"
    table.to_parquet(path, index=False)
    inputs = [
        *(DATA / "release" / str(y) / SEAT_TABLES[t] for t in ("gp", "ward")
          for y in (a, b)),
        CROSSWALKS / f"district_{a}_{b}.csv",
        CROSSWALKS / f"block_{a}_{b}.csv",
        *([KRUTI] if 2022 in (a, b) else []),
    ]  # fmt: skip
    return {
        "inputs": {str(p): sha(p) for p in inputs},
        "validation": checks,
        "file": {"path": path.name, "rows": len(table), "sha256": sha(path)},
    }


def build():
    manifest = {
        "purpose": (
            "Research crosswalks between sarpanch seats of consecutive elections. "
            "A link states that names agree inside a reviewed block pair, not that "
            "boundaries are unchanged."
        ),
        "matcher": {
            "preclink": version("preclink"),
            "name_threshold": NAME_THRESHOLD,
            "ward_pass_threshold": WARD_PASS_THRESHOLD,
        },
        "code_sha256": sha(__file__),
        "pairs": {label: build_pair(label) for label in PAIRS},
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps({k: v["validation"] for k, v in manifest["pairs"].items()}, indent=2)
    )


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()

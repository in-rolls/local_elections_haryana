"""Inferred probability that an elected sarpanch is a woman.

The notifications record no sex for an elected person. This module infers it from
the printed name and keeps the inference separate from the source tables: the
outputs live in `data/inferred/`, carry every input beside the probability, and
are never written back into `data/fin/`.

The evidence is a first-name score from naampy (electoral-roll first-name
composition) plus fixed surname and honorific markers, because Haryana names often
carry sex in the last word ("Jasbir Kaur", "Parveen Kumar") where a first-name
model cannot see it. A logistic recalibration combines them.

The labels come from the law, not from names. The 2020 amendment to section 9 of
the Haryana Panchayati Raj Act lets only women contest a sarpanch office reserved
for women in 2022, and only persons other than women contest the others. So a 2022
winner's sex is known from the seat. The model is fit on those winners and scored
by cross-validation grouped on first name, so no first name is in both a training
and a test fold.
"""

import argparse
import hashlib
import json
import re
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

DATA = Path("data")
OUT = DATA / "inferred"
KRUTI = OUT / "kruti_dev_names_2022.csv"
TRAINING_YEAR = 2022
YEARS = (2000, 2005, 2010, 2016, 2022)
# Honorifics and titles stripped before the first name is read. "Smt"/"Shrimati"
# and "Kumari" also mark a woman; the rest are uninformative here.
FEMALE_TITLES = {"smt", "shrimati", "srimati", "kumari", "km", "mrs", "ms"}
OTHER_TITLES = {"sh", "shri", "sri", "mr", "dr", "mohd", "md", "ch", "ch.", "late"}
# Last words that mark sex in Haryana names. Fixed in advance; not learned.
FEMALE_SURNAMES = {
    "kaur", "devi", "rani", "kumari", "bai", "begum", "khatoon", "khatun", "bano",
    "banu", "bibi", "wati", "vati", "lata", "bala",
}  # fmt: skip
MALE_SURNAMES = {
    "kumar", "singh", "lal", "ram", "chand", "dass", "das", "parsad", "prasad",
    "khan", "ali", "dutt", "nath", "parkash", "prakash", "bhan", "dev",
}  # fmt: skip
FEATURES = [
    "naampy_logit",
    "naampy_abstained",
    "female_marker",
    "male_marker",
    "female_title",
]


def tokens(name):
    return re.sub(r"[^a-z ]", " ", (name or "").lower().replace(".", " ")).split()


def name_parts(name):
    """First name after titles, plus the markers read from the whole name."""
    words = tokens(name)
    female_title = False
    while words and words[0] in FEMALE_TITLES | OTHER_TITLES:
        female_title |= words[0] in FEMALE_TITLES
        words = words[1:]
    last = words[-1] if len(words) > 1 else ""
    return {
        "first_name": words[0] if words else None,
        "female_marker": int(last in FEMALE_SURNAMES),
        "male_marker": int(last in MALE_SURNAMES),
        "female_title": int(female_title),
    }


def features(winners):
    from naampy import estimate_first_name_pattern

    parts = pd.DataFrame([name_parts(n) for n in winners], index=winners.index)
    est = estimate_first_name_pattern(parts["first_name"].tolist())
    score = est["female_label_score"].to_numpy(dtype=float)
    abstained = est["abstained"].to_numpy(dtype=bool)
    clipped = np.clip(np.nan_to_num(score, nan=0.5), 1e-4, 1 - 1e-4)
    parts["naampy_score"] = score
    parts["naampy_abstained"] = abstained.astype(int)
    # An abstention contributes nothing through the score; its own indicator
    # carries the base rate for names naampy cannot read.
    parts["naampy_logit"] = np.where(abstained, 0.0, np.log(clipped / (1 - clipped)))
    parts["naampy_revision"] = est["model_revision"].to_numpy()
    return parts


def seats(year):
    """Elected seats. Winner names printed in Kruti Dev are replaced by their
    romanization from `data/inferred/kruti_dev_names_2022.csv`."""
    d = pd.read_parquet(DATA / "fin" / f"gp_reservation_{year}.parquet")
    elected = d["winner"].notna() & ~d["vacant"].fillna(False).astype(bool)
    d = d[elected].reset_index(drop=True)
    d["winner_read"] = d["winner"]
    if year == 2022:
        key = ["district", "block", "sr_no", "gram_panchayat"]
        kruti = pd.read_csv(KRUTI, dtype={"sr_no": str}).set_index(key)
        romanized = kruti["winner_latin"].reindex(d.set_index(key).index).to_numpy()
        d["winner_read"] = d["winner"].where(pd.isna(romanized), romanized)
    return d


def evaluate(x, y, groups):
    """Grouped cross-validated predictions for the recalibrated model and for the
    naampy score alone."""
    predicted = np.zeros(len(y))
    for train, test in GroupKFold(n_splits=10).split(x, y, groups):
        model = LogisticRegression(max_iter=1000).fit(x.iloc[train], y[train])
        predicted[test] = model.predict_proba(x.iloc[test])[:, 1]
    return predicted


def metrics(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "n": len(y),
        "auc": round(roc_auc_score(y, p), 4),
        "log_loss": round(log_loss(y, p), 4),
        "brier": round(brier_score_loss(y, p), 4),
        "accuracy_at_0.5": round(float(((p > 0.5) == y).mean()), 4),
    }


def calibration(y, p):
    bins = pd.cut(p, [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1], include_lowest=True)
    table = pd.DataFrame({"bin": bins, "y": y, "p": p}).groupby("bin", observed=True)
    return [
        {
            "bin": str(b),
            "n": len(g),
            "mean_probability": round(g.p.mean(), 4),
            "female_share": round(g.y.mean(), 4),
        }
        for b, g in table
    ]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out=OUT):
    train = seats(TRAINING_YEAR)
    tf = features(train["winner_read"])
    # Placeholders such as "...." are not names; they get no probability.
    readable = tf["first_name"].notna().to_numpy()
    train, tf = (
        train[readable].reset_index(drop=True),
        tf[readable].reset_index(drop=True),
    )
    y = train["woman_reserved"].astype(int).to_numpy()
    groups = tf["first_name"].fillna("").to_numpy()
    cv = evaluate(tf[FEATURES], y, groups)
    naampy_only = np.where(tf["naampy_abstained"] == 1, y.mean(), tf["naampy_score"])
    model = LogisticRegression(max_iter=1000).fit(tf[FEATURES], y)
    validation = {
        "training": {
            "year": TRAINING_YEAR,
            "label": "woman_reserved; the 2020 amendment bars women from other seats",
        },
        "recalibrated_cross_validated": metrics(y, cv),
        "naampy_alone": metrics(y, naampy_only),
        "calibration_cross_validated": calibration(y, cv),
        "coefficients": dict(
            zip(
                ["intercept", *FEATURES],
                [model.intercept_[0], *model.coef_[0]],
                strict=True,
            )
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for year in YEARS:
        d = seats(year)
        f = features(d["winner_read"])
        keep = [
            "year",
            "district",
            "block",
            "sr_no",
            "gram_panchayat",
            "winner",
            "winner_read",
        ]
        table = pd.concat([d[keep], f], axis=1)
        # Named for what they are: an inference from the printed name, never a
        # recorded sex.
        prob = "winner_female_probability_from_name"
        table[prob] = model.predict_proba(f[FEATURES])[:, 1]
        table.loc[f["first_name"].isna(), prob] = np.nan
        table["winner_female_probability_method"] = (
            f"naampy {version('naampy')} first-name score + fixed name markers, "
            f"logistic recalibration on {TRAINING_YEAR} winners"
        )
        reserved = d["woman_reserved"].astype(bool)
        validation[f"mean_probability_{year}_women_reserved"] = round(
            table.loc[reserved, prob].mean(), 4
        )
        path = out / f"winner_female_probability_{year}.parquet"
        table.to_parquet(path, index=False)
        files.append({"path": path.name, "rows": len(table), "sha256": sha(path)})
    manifest = {
        "purpose": (
            "Inferred probability that an elected sarpanch is a woman. Not a source "
            "value; for aggregate analysis only."
        ),
        "packages": {p: version(p) for p in ("naampy", "scikit-learn")},
        "inputs": {
            f"data/fin/gp_reservation_{y}.parquet": sha(
                DATA / "fin" / f"gp_reservation_{y}.parquet"
            )
            for y in YEARS
        },
        "code_sha256": sha(__file__),
        "validation": validation,
        "files": files,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()

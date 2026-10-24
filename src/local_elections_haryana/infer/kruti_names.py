"""Romanize the GP and person names that 2022 notifications printed in Kruti Dev.

Two 2022 blocks (Fatehabad: Bhattu Kalan; Jhajjar: Machhrauli) were published only
in Kruti Dev Hindi, so their names reach the released seat tables in the legacy
font encoding ("ekNjkSyh" for माछरौली). Linking and name-based inference need
readable names.
This decodes them to Unicode with the vendored Kruti Dev 010 mapping, romanizes
the result with indicate's local model, and writes one row per source record to
`data/release/inferred/kruti_dev_names_2022.csv`. The source tables are not changed.

Needs the `transliterate` dependency group (indicate and PyTorch).
"""

import json
import re
import unicodedata
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from local_elections_haryana.paths import SEAT_TABLES

DATA = Path("data")
OUT = DATA / "release" / "inferred" / "kruti_dev_names_2022.csv"
MAP = Path(__file__).with_name("kruti_dev_010.json")
# क-ह and the precomposed nukta letters क़-य़, escaped so editors cannot decompose them.
CONSONANTS = "\u0915-\u0939\u0958-\u095f"
CLUSTER = rf"[{CONSONANTS}]़?(?:्[{CONSONANTS}]़?)*"
NAME_COLUMNS = ["gram_panchayat", "winner", "father_husband"]


def logical_text(text):
    """Undo visual-order short-i and reph glyphs; preserve source spelling."""
    text = re.sub(
        rf"ि([ंँ]?)(?)({CLUSTER})",
        lambda m: ("र्" if m[2] else "") + m[3] + "ि" + m[1],
        text,
    )
    text = re.sub(rf"({CLUSTER}[ािीुूृॄेैोौंँ़]*)", r"र्\1", text)
    if "" in text:
        raise ValueError(f"Unresolved reph: {text!r}")
    return unicodedata.normalize("NFC", " ".join(text.split()))


def kruti_text(text):
    """Decode Kruti Dev 010 to Unicode Devanagari."""
    for old, new in json.loads(MAP.read_text())["mapping"]:
        text = text.replace(old, new)
    text = (
        text.replace("±", "Zं")
        .replace("Æ", "र्f")
        .replace("Ç", "fं")
        .replace("É", "र्fं")
        .replace("Ê", "ीZ")
        .replace("f", "ि")
        .replace("Z", "")
    )
    return logical_text(text)


def build(out=OUT):
    import indicate

    d = pd.read_parquet(DATA / "release" / "2022" / SEAT_TABLES["gp"])
    rows = d[d["script"] == "krutidev"].copy()
    names = []
    for column in NAME_COLUMNS:
        rows[f"{column}_unicode"] = rows[column].map(
            lambda s: kruti_text(s) if isinstance(s, str) else None
        )
        names += rows[f"{column}_unicode"].dropna().tolist()
    names = sorted(set(names))
    latin = dict(
        zip(
            names,
            indicate.transliterate_batch(names, source="hindi", engine=["model"]),
            strict=True,
        )
    )
    for column in NAME_COLUMNS:
        rows[f"{column}_latin"] = rows[f"{column}_unicode"].map(latin)
    rows["romanized_by"] = f"indicate {version('indicate')} model"
    keep = ["district", "block", "sr_no"]
    keep += [f"{c}{s}" for c in NAME_COLUMNS for s in ("", "_unicode", "_latin")]
    out.parent.mkdir(parents=True, exist_ok=True)
    rows[[*keep, "romanized_by"]].to_csv(out, index=False)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    build()

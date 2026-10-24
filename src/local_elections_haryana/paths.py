"""Repository folders (in-rolls/local_elections docs/layout.md), and the
translation of paths recorded before the handoff.

Evidence files written while this pipeline lived in in-rolls/local_elections
record source paths relative to that repository, under
data/source_search/national/haryana/. Rewriting them would change the hashes the
evidence is pinned by, so paths are translated when they are resolved instead.
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
# The git-ignored 2000/2005 gazette collection (data/raw/gazette_archive/README.md)
ARCHIVE = RAW / "gazette_archive"
MANUAL = DATA / "manual"
EXTRACTED = DATA / "extracted"
BUILD = DATA / "build"
RELEASE = DATA / "release"
INFERRED = RELEASE / "inferred"
LINKAGE = RELEASE / "linkage"
# The 2000 gazette OCR review corpus, released by occurrence, not by seat
OCCURRENCES = RELEASE / "2000" / "gazette_occurrences"
CROSSWALKS = MANUAL / "crosswalks"
CROSSWALK_EVIDENCE = BUILD / "crosswalk_evidence"
MANIFEST = DATA / "MANIFEST.json"
YEARS = (2000, 2005, 2010, 2016, 2022)
SEAT_TABLES = {
    "gp": "gram_panchayat_head_seat_reservation.parquet",
    "ward": "gram_panchayat_ward_member_seat_reservation.parquet",
}

LEGACY_PREFIX = "data/source_search/national/haryana/"
ARCHIVE_PREFIX = "data/raw/gazette_archive/national/"


def raw(year):
    """Source PDFs as received, with the harvest's manifest.csv."""
    return RAW / str(year)


def extracted(year):
    """Parsed seat CSVs and OCR caches for one election."""
    return EXTRACTED / str(year)


def manual(year):
    """Hand readings, reviews and corrections for one election."""
    return MANUAL / str(year)


def seats(kind, year):
    """The released seat table for one election: kind is "gp" or "ward"."""
    return RELEASE / str(year) / SEAT_TABLES[kind]


def current(path):
    """A recorded source path, relative to this repository."""
    text = str(path)
    return (
        ARCHIVE_PREFIX + text[len(LEGACY_PREFIX) :]
        if text.startswith(LEGACY_PREFIX)
        else text
    )


def digest(path):
    """SHA-256 of a file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inside(root, relative):
    """Resolve a recorded path, refusing one that escapes the repository."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Source path escapes its repository: {relative}")
    return path

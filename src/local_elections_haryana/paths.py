"""Repository root, and the translation of paths recorded before the handoff.

Evidence files written while this pipeline lived in in-rolls/local_elections
record source paths relative to that repository, under
data/source_search/national/haryana/. Rewriting them would change the hashes the
evidence is pinned by, so paths are translated when they are resolved instead.
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_PREFIX = "data/source_search/national/haryana/"
RAW = "data/raw_archive/national/"


def current(path):
    """A recorded source path, relative to this repository."""
    text = str(path)
    return RAW + text[len(LEGACY_PREFIX) :] if text.startswith(LEGACY_PREFIX) else text


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

"""Write data/raw/fetch_log.csv: one row per tracked raw file (in-rolls docs/layout.md).

    python -m local_elections_haryana.build.fetch_log          # write
    python -m local_elections_haryana.build.fetch_log --check  # compare only

URLs come from the harvest's own manifests (data/raw/<year>/manifest.csv) and,
for 2022's index PDF, from acquire.harvest.SOURCES. The manifests record no
capture times, so `fetched_at_utc` is blank. A file no record names (the
manifests themselves, the gazette archive's README and MANIFEST.csv, and the
13-district 2010 reservation PDF) gets a blank `url` and `method=unknown`; the
log never invents one.
"""

import argparse
import csv
import io
import subprocess
import sys

from local_elections_haryana.acquire.harvest import SOURCES
from local_elections_haryana.paths import RAW, ROOT, YEARS, digest

LOG = RAW / "fetch_log.csv"
COLUMNS = ["path", "url", "sha256", "bytes", "fetched_at_utc", "method"]


def tracked():
    out = subprocess.run(
        ["git", "ls-files", "-z", "data/raw"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return [p for p in out.decode().split("\0") if p]


def urls():
    """Repository path -> URL, from every record that names one."""
    found = {}
    for year in YEARS:
        with (RAW / str(year) / "manifest.csv").open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if row.get("archive_path"):
                    continue
                path = (RAW / str(year) / row["saved_as"]).relative_to(ROOT)
                found[path.as_posix()] = row["url"]
    for year, source in SOURCES.items():
        if source["style"] == "index-pdf":
            path = (RAW / year / "index.pdf").relative_to(ROOT)
            found[path.as_posix()] = source["url"]
    return found


def method(url):
    if not url:
        return "unknown"
    return "wayback" if "web.archive.org" in url else "live"


def rows():
    known = urls()
    out = []
    for name in sorted(tracked()):
        if name == LOG.relative_to(ROOT).as_posix():
            continue
        path = ROOT / name
        url = known.get(name, "")
        out.append(
            {
                "path": name,
                "url": url,
                "sha256": digest(path),
                "bytes": path.stat().st_size,
                "fetched_at_utc": "",
                "method": method(url),
            }
        )
    return out


def render(table):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(table)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Write the raw-file fetch log.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render(rows())
    name = LOG.relative_to(ROOT)
    if args.check:
        if not LOG.exists() or LOG.read_text(encoding="utf-8") != text:
            print(f"{name} is out of date; run without --check")
            return 1
        print(f"{name}: up to date")
        return 0
    LOG.write_text(text, encoding="utf-8")
    print(f"wrote {name} ({text.count(chr(10)) - 1} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

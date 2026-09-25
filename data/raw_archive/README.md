# Haryana raw-data archive

Raw source material too large for git: 25493 files, about 3.8 GB. The files live here, git-ignored; this README and `MANIFEST.csv` (path, SHA-256, bytes, origin) are tracked.

**Download:** Google Drive: _link to be added_. The file is `local_elections_haryana_raw_<date>.tar.gz`, with its `.sha256` alongside.

To restore, extract the tarball into `data/raw_archive/`, then run `make raw-verify`. To publish a new archive, run `make raw-archive OUT=/path/with/room` (it verifies first) and upload the result.

| Path | What it is |
|---|---|
| `national/` | The 2000 and 2005 gazette collection: acquisition ledgers, `raw/` source PDFs and HTML, `early_cycles/` OCR and review corpus, `gap_recovery/`, `report_2000/`, `report_annexures/`, `review/`, `repairs/` |
| `2022121688.pdf` | A 2022 notification that sat, unparsed, in the central repository's `data/haryana/` |

Both came unaltered from [in-rolls/local_elections](https://github.com/in-rolls/local_elections) at commit `fa4c4e79`. There, `national/` was the untracked `data/source_search/national/haryana/`. Evidence files written before the move record paths under that old prefix; `local_elections_haryana.paths.current` translates them, so none of the files had to change.

You don't need the archive to rebuild the released 2000 tables: `make release` uses only tracked inputs in `data/release/`. It is needed for re-running OCR, parsing or review.

# Haryana Local Election Data

[![CI](https://github.com/in-rolls/local_elections_haryana/actions/workflows/ci.yml/badge.svg)](https://github.com/in-rolls/local_elections_haryana/actions/workflows/ci.yml)
[![Code license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)

Gram panchayat head (sarpanch) and ward member (panch) records from Haryana's 2016 and 2022 local elections. The data record seat reservations and elected candidates from State Election Commission notifications. Source PDFs, acquisition manifests, published CSVs, and typed Parquet exports are included.

## Data

Each row is a seat record recovered from a notification. Coverage is incomplete, and repeated names and missing ward numbers prevent treating the usual geographic columns as a universally unique key.

| File | Election | Unit | Rows |
|---|---:|---|---:|
| [gp_reservation_2016.parquet](data/fin/gp_reservation_2016.parquet) | 2016 | GP head seat | 6,090 |
| [ward_reservation_2016.parquet](data/fin/ward_reservation_2016.parquet) | 2016 | GP ward seat | 61,879 |
| [gp_reservation_2022.parquet](data/fin/gp_reservation_2022.parquet) | 2022 | GP head seat | 6,123 |
| [ward_reservation_2022.parquet](data/fin/ward_reservation_2022.parquet) | 2022 | GP ward seat | 60,981 |

[MANIFEST.json](data/fin/MANIFEST.json) records each export's schema, row count, SHA-256, and input CSV checksum. CSV snapshots remain in [data/2016/](data/2016/) and [data/2022/](data/2022/), alongside the source manifests, PDFs, and cached OCR. `make verify-data` checks every exported value against its CSV and verifies the notification PDFs against their acquisition checksums.

No dataset DOI is recorded in this repository. Cite the repository using [CITATION.cff](CITATION.cff), and record the commit used in your analysis.

## Column dictionary

Parquet adds `year` to the CSV fields. Empty CSV cells become null; `0`/`1` flags become booleans. Other values, row order, and repeated observations are preserved. Identifiers remain strings, including any leading zeroes.

| Column | Parquet type | Meaning |
|---|---|---|
| `year` | int16 | Election year |
| `district`, `block` | string | Administrative location from the index or notification |
| `sr_no` | string | GP serial within a block notification; not a statewide identifier |
| `gram_panchayat` | string | GP name recovered from the source |
| `ward_no` | string | Printed ward number; ward export only; can be null |
| `reservation` | string | Harmonized seat-reservation label |
| `caste_reservation` | string | `SC`, `ST`, `BC_A`, or `NONE`; `NONE` means no caste reservation |
| `woman_reserved` | bool | Whether the seat is reserved for a woman |
| `winner` | string | Elected person's name or the source's vacancy text |
| `father_husband` | string | Relation-name column as printed |
| `unopposed` | bool | Elected unopposed, indicated by a source asterisk |
| `vacant` | bool | Source records an unfilled seat |
| `reservation_raw` | string | Extracted category cell before normalization |
| `script` | string | `latin` or `krutidev`, as identified by the category normalizer |
| `printings_agree` | bool | Agreement on the GP reservation across printings; null when unchecked |
| `notification`, `source_pdf` | string | Notification identifier and saved source filename |

Caste and women's reservations are separate dimensions. An SC-reserved seat can also be woman-reserved. Seat reservation is not the elected person's caste or gender. `printings_agree` is a GP-level comparison propagated to its ward rows; it does not establish independent agreement on each ward's category.

## Coverage and known gaps

The 2016 files cover 126 blocks in 21 districts; 2022 covers 143 blocks in 22 districts. Administrative boundaries and names changed between elections, including the creation of Charkhi Dadri and the Mewat/Nuh name change. There is no validated cross-year crosswalk or LGD/census identifier. Exact names can differ across publications, and fuzzy matching requires review.

The validator retains the original SEC reference totals and their different denominators. Its 2016 totals count people elected, excluding vacant seats: the data contain 6,081 non-vacant GP records and 59,980 non-vacant ward records. Its 2022 totals count seats: 6,123 of 6,220 GP seats and 60,981 of 61,993 ward seats are represented. These coverage checks do not establish that every recovered record is correct.

Current validation findings include:

| Finding | 2016 | 2022 |
|---|---:|---:|
| GP names repeated within a district/block | 13 names | 1 name |
| Ward rows without a ward number | 164 | 259 |
| GPs with gaps in their numbered wards | 166 | 305 |
| GPs with repeated ward numbers | 32 | 37 |
| GP rows marked as Kruti Dev | 0 | 45 |
| GP rows with cross-printing disagreement | Not checked | 144 |

Do not deduplicate on district, block, and GP name without examining the notification. Missing ward numbers remain missing. A successful `make validate` means its required checks passed; warnings remain visible and are not recoded into successful readings.

The published files exclude 2000, 2005, 2010, and later bye-elections. Work on the 2000 sources using Muse Spark Contributor is underway in the [local_reservations project](https://github.com/in-rolls/local_reservations). Those outputs remain under review and are not included in these releases.

## How collected

| Election | Source | Extraction |
|---|---|---|
| 2016 | [SEC fifth-general-election notifications](https://secharyana.gov.in/notifications-of-elected-candidates-of-panchayati-raj-institution-in-5th-general-elections-2016-in-the-state-of-haryana/), 21 district PDFs | Offline PDF table extraction; one printing retained per notification |
| 2022 | [SEC notifications](https://secharyana.gov.in/orders-notifications-related-to-panchayat-elections-2021/) and [statewide index](https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c/uploads/2022/12/2022121338.pdf), 187 linked PDFs | Offline PDF table extraction with retained Surya OCR for 26 pages whose table grids were fragmented |

The 2022 index includes Zila Parishad and Panchayat Samiti notifications as well as GP notifications; all 187 files are retained, but only sarpanch and panch rows enter these exports. The older NIC URLs for 2016 were unavailable during acquisition. The source manifest records the exact Wayback URLs used to recover them. Saved filenames identify the district and block where available, and manifests preserve the original filename, URL, byte count, and SHA-256.

Notifications can contain multiple Hindi and English printings with restarted serials. The parser groups rows by notification and chooses one printing, preferring English. It handles wrapped reservation labels, doubled glyphs, and Kruti Dev text encoding. These are consequential cases: a detached `Women` label can otherwise turn a woman-reserved seat into a plausible but incorrect record.

Cached OCR from 41 pages of the 2016 PDFs is retained for research but excluded from parsing. Earlier evaluation found it could attach ward rows to the wrong GP across page boundaries. Ordinary parsing requires neither a model nor paid API calls. The optional [OCR tool](scripts/ocr.py) documents its separate environment and the rejected 2016 experiment.

The [original implementation](https://github.com/in-rolls/local_elections_haryana/tree/2981e75) records the collection history. Existing published CSVs are preserved; a new parse writes to `data/derived/` for comparison before any release update.

## Usage

```sh
git clone https://github.com/in-rolls/local_elections_haryana.git
cd local_elections_haryana
uv sync --frozen --group dev
make verify-data
```

Read a published file:

```python
import pyarrow.parquet as pq

table = pq.read_table("data/fin/gp_reservation_2022.parquet")
print(table.num_rows)
print(table.schema)
```

Rebuild the four Parquet exports from their existing CSV inputs:

```sh
make to-parquet
make verify-data
```

Re-parse a small local source sample:

```sh
uv run python scripts/parse.py --year 2022 --limit 1 --out data/derived/smoke
```

`make parse YEAR=2022` processes that year's saved PDFs and writes derived CSVs under `data/derived/2022/`. Failed PDF reads stop publication of the run's outputs. A limited parse cannot overwrite the published CSV directory. Run `make validate-derived YEAR=2022` on a complete derived year and compare it with the existing release before replacing any published files.

Harvesting is a separate, explicitly invoked network operation:

```sh
make harvest YEAR=2022
```

Downloads must contain a readable PDF and match any advertised content length before they replace a saved file. Existing downloads are reused unless `--refresh` is passed to `scripts/harvest.py`. Use `make verify-data` to check the retained source bytes before relying on a cache.

## Development

```sh
make check
make ci-docker
```

`make check` runs Ruff, formatting, pytest, pre-commit, both years' data validators, CSV-to-Parquet equality checks, and source checksums. CI tests Python 3.12 and 3.14. The Docker target uses the standard Python images. The environment is a data-repository environment managed by uv; the scripts do not require an installed library package.

## Citation

Gaurav Sood. *Haryana Gram Panchayat and Ward Seat Reservation Data, 2016 and 2022*. Include the repository URL and commit used. Machine-readable metadata are in [CITATION.cff](CITATION.cff). Contact: [contact@gsood.com](mailto:contact@gsood.com).

## License

The code is [MIT licensed](LICENSE). Source notifications are publications of the Haryana State Election Commission. The code license does not grant rights over those documents; no separate data license is asserted here.

## 🔗 Adjacent Repositories

- [in-rolls/local_elections_up](https://github.com/in-rolls/local_elections_up) — UP Local Election Data --- GP and ULB. Seat reservation, winner, and candidates for some elections
- [in-rolls/up-2023-electoral-rolls](https://github.com/in-rolls/up-2023-electoral-rolls)
- [in-rolls/local_elections_bihar](https://github.com/in-rolls/local_elections_bihar) — Candidate Info. + Valid Votes Won by Cands. in the 2016 Bihar Panchayat Elections
- [in-rolls/quota](https://github.com/in-rolls/quota) — Effects of Randomly Assigned Reservations for Women Leaders in Indian Local Government on Allocation and Development Outcomes
- [in-rolls/mnrega_social](https://github.com/in-rolls/mnrega_social) — MNREGA Social Audit Data

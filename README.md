# Haryana Local Election Data

[![Code license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)

Gram panchayat head (sarpanch) and ward member (panch) records from Haryana's 2016 and 2022 local elections. The data record seat reservations and elected candidates from State Election Commission notifications. Source PDFs, acquisition manifests, published CSVs, and typed Parquet exports are included.

## Data

Each row is a seat record recovered from a notification. Coverage is incomplete, and repeated names and missing ward numbers prevent treating the usual geographic columns as a universally unique key.

<!-- datasets:start -->

| File | Rows | Each row represents |
| --- | ---: | --- |
| [fin/gp_reservation_2016.parquet](data/fin/gp_reservation_2016.parquet) | 6,090 | GP head seat record |
| [fin/gp_reservation_2022.parquet](data/fin/gp_reservation_2022.parquet) | 6,123 | GP head seat record |
| [fin/ward_reservation_2016.parquet](data/fin/ward_reservation_2016.parquet) | 61,879 | GP ward seat record |
| [fin/ward_reservation_2022.parquet](data/fin/ward_reservation_2022.parquet) | 60,981 | GP ward seat record |
| [release/historical/historical_provisional_observations.parquet](data/release/historical/historical_provisional_observations.parquet) | 67,770 | Provisional OCR or reviewed non-seat occurrence |
| [release/historical/historical_quarantine.parquet](data/release/historical/historical_quarantine.parquet) | 61 | Reviewed 2000 occurrence with unresolved fields |
| [release/historical/historical_reviewed_occurrences.parquet](data/release/historical/historical_reviewed_occurrences.parquet) | 2,761 | Reviewed 2000 printed occurrence |

<details>
<summary>Retained observation snapshots</summary>

| File | Rows | Each row represents |
| --- | ---: | --- |
| [observations/00a6da628624/seat_rows.parquet](data/release/observations/00a6da6286242535c6f7ed6d7434e1fe58f97972b71ed3fdfed5ef1f949b6b80/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/1e6f85e0692d/seat_rows.parquet](data/release/observations/1e6f85e0692d5b7d87fffcaeb733db48665f70951f42e525d654d8115a352b39/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/20f6f91fea7f/seat_rows.parquet](data/release/observations/20f6f91fea7f6f32e7b87900ce79a5cc933e9c06542be3239fdb7bde88150af4/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/28a794b45d44/seat_rows.parquet](data/release/observations/28a794b45d444830079dd758b316af358149c9895872564ef70c56e8e4868aea/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/2f043cbcd088/seat_rows.parquet](data/release/observations/2f043cbcd088859de5bf5dcdbdaad145125039071629a052b86533a7713eb8f9/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/5c6160d7c982/seat_rows.parquet](data/release/observations/5c6160d7c982d0cb55743f88ba90d95d82dc5fa1d47402bb5493fa6d443bc7fa/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/6ad3161f4b7c/seat_rows.parquet](data/release/observations/6ad3161f4b7c750e4446542bc4cf48dc5acd822c7897c4efeffdfbc56021da34/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/6f92fe34f6a5/seat_rows.parquet](data/release/observations/6f92fe34f6a54dd011dadc1602556a0935b9434c44a2452b4a01d8f0f0e98b34/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/7715dfc0287a/seat_rows.parquet](data/release/observations/7715dfc0287adec5a8aa072f0762e56150210c2653580114fe995b8f44fb82aa/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/88adc00fa2d6/seat_rows.parquet](data/release/observations/88adc00fa2d60b6e6f6d33bafd827e60afd38f4763202985e8b2e9001b1bd335/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/951e414ba7a6/seat_rows.parquet](data/release/observations/951e414ba7a68c948cf11d3870dedf2d3d792a054797feb6595ab78d890bb67a/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/99cc306ae058/seat_rows.parquet](data/release/observations/99cc306ae058ef8824515602b5a2b3e56465c28dc5c44580d791b9be1525081e/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/a00a66abee45/seat_rows.parquet](data/release/observations/a00a66abee459c7e0a4ed1e457f3ebf6591d6463e57c0a4e717e84405146a768/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/a2128bd97e57/seat_rows.parquet](data/release/observations/a2128bd97e575b9e779478b6622d63a06e73bb796a05374a571ea4ef0defd17c/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/ae4fa5939922/seat_rows.parquet](data/release/observations/ae4fa5939922729c37aeed5cfb9a9dbdd7ca90bbc13823548b606b70ff0f140b/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/bc94a933c77a/seat_rows.parquet](data/release/observations/bc94a933c77aac8e4386a202e0597b384bfa295c89591fa2cf7907aecf077062/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/c3b40ce51cf0/seat_rows.parquet](data/release/observations/c3b40ce51cf00467ec0e85d18c78272a32aafc7d0ab8309d7bc34edd540e4651/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/de78517b40a1/seat_rows.parquet](data/release/observations/de78517b40a12fc843ca8852cca3639bd44c19f2cc4ef69d3b070ffd7e6795b6/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e22fc34f7116/seat_rows.parquet](data/release/observations/e22fc34f7116bf3dd93d6284f6004f075b4fa2ef65d74d2a44ae968a930dea06/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e35273b41413/seat_rows.parquet](data/release/observations/e35273b4141320ac6984fc437779be2744ec24dcf8c07880153d4a70fbcdafd3/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e9f6fd031efc/seat_rows.parquet](data/release/observations/e9f6fd031efc80233b64b9c1e9fdafed6121de22b17016c0c2f129a3812c8b7c/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/edef31fd37bd/seat_rows.parquet](data/release/observations/edef31fd37bdc0af3b49561a796f1b6cc0c918125431e969cd48ec23ce59ff3a/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/fb220eb88315/historical_provisional_observations.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_provisional_observations.parquet) | 67,770 | Provisional OCR or reviewed non-seat occurrence |
| [observations/fb220eb88315/historical_quarantine.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_quarantine.parquet) | 61 | Reviewed 2000 occurrence with unresolved fields |
| [observations/fb220eb88315/historical_reviewed_occurrences.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_reviewed_occurrences.parquet) | 2,761 | Reviewed 2000 printed occurrence |
| [observations/fb220eb88315/modern_quarantine.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/modern_quarantine.parquet) | 1,202 | Archived modern record requiring review |
| [observations/fb220eb88315/modern_seats.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/modern_seats.parquet) | 133,871 | Archived modern seat record |
| [observations/fb220eb88315/printing_reconciliation.parquet](data/release/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/printing_reconciliation.parquet) | 1,536 | Archived comparison of printed occurrences |

</details>

<!-- datasets:end -->

[MANIFEST.json](data/fin/MANIFEST.json) records each export's schema, row count, SHA-256, and input CSV checksum. CSV snapshots remain in [data/2016/](data/2016/) and [data/2022/](data/2022/), alongside the source manifests, PDFs, and cached OCR. `make verify` checks every exported value against its CSV and verifies the notification PDFs against their acquisition checksums.

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

The published 2016/2022 files exclude 2000, 2005, 2010, and later bye-elections. The 2000 and 2005 gazette work, built with Muse Spark Contributor, is released separately; see [Historical 2000 gazette pipeline](#historical-2000-gazette-pipeline).

## How collected

| Election | Source | Extraction |
|---|---|---|
| 2016 | [SEC fifth-general-election notifications](https://secharyana.gov.in/notifications-of-elected-candidates-of-panchayati-raj-institution-in-5th-general-elections-2016-in-the-state-of-haryana/), 21 district PDFs | Offline PDF table extraction; one printing retained per notification |
| 2022 | [SEC notifications](https://secharyana.gov.in/orders-notifications-related-to-panchayat-elections-2021/) and [statewide index](https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c/uploads/2022/12/2022121338.pdf), 187 linked PDFs | Offline PDF table extraction with retained Surya OCR for 26 pages whose table grids were fragmented |

The 2022 index includes Zila Parishad and Panchayat Samiti notifications as well as GP notifications; all 187 files are retained, but only sarpanch and panch rows enter these exports. The older NIC URLs for 2016 were unavailable during acquisition. The source manifest records the exact Wayback URLs used to recover them. Saved filenames identify the district and block where available, and manifests preserve the original filename, URL, byte count, and SHA-256.

Notifications can contain multiple Hindi and English printings with restarted serials. The parser groups rows by notification and chooses one printing, preferring English. It handles wrapped reservation labels, doubled glyphs, and Kruti Dev text encoding. These are consequential cases: a detached `Women` label can otherwise turn a woman-reserved seat into a plausible but incorrect record.

Cached OCR from 41 pages of the 2016 PDFs is retained for research but excluded from parsing. Earlier evaluation found it could attach ward rows to the wrong GP across page boundaries. Ordinary parsing requires neither a model nor paid API calls. The optional [OCR tool](src/local_elections_haryana/parse/ocr.py) documents its separate environment and the rejected 2016 experiment.

The [original implementation](https://github.com/in-rolls/local_elections_haryana/tree/2981e75) records the collection history. Existing published CSVs are preserved; a new parse writes to `data/derived/` for comparison before any release update.

## Usage

```sh
git clone https://github.com/in-rolls/local_elections_haryana.git
cd local_elections_haryana
uv sync --frozen --group dev
make verify
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
make data
make verify
```

Re-parse a small local source sample:

```sh
uv run python -m local_elections_haryana.parse.parse --year 2022 --limit 1 --out data/derived/smoke
```

`make parse YEAR=2022` processes that year's saved PDFs and writes derived CSVs under `data/derived/2022/`. Failed PDF reads stop publication of the run's outputs. A limited parse cannot overwrite the published CSV directory. Run `make validate-derived YEAR=2022` on a complete derived year and compare it with the existing release before replacing any published files.

Harvesting is a separate, explicitly invoked network operation:

```sh
make harvest YEAR=2022
```

Downloads must contain a readable PDF and match any advertised content length before they replace a saved file. Existing downloads are reused unless `--refresh` is passed to `src/local_elections_haryana/acquire/harvest.py`. Use `make verify` to check the retained source bytes before relying on a cache.

## Historical 2000 gazette pipeline

The 2000 and 2005 gazette work (OCR, parsing, source review, and the 2000 release) moved here from the central [in-rolls/local_elections](https://github.com/in-rolls/local_elections). It is the `local_elections_haryana` package in `src/`.

- `make historical` rebuilds `data/release/historical/` (reviewed occurrences, quarantine, provisional observations, with a receipt and `SHA256SUMS`) from tracked inputs only: `data/release/observations/` and `data/release/inputs/`.
- The source PDFs, OCR corpus and review ledgers are in the [raw-data archive](data/raw_archive/README.md). They are git-ignored, with a tracked SHA-256 manifest and a tarball for download.
- Logging, checksum and HTML-link helpers live in the package; their MIT attribution is in `THIRD_PARTY_NOTICES`.
- Hosted-OCR tools read `MODEL_API_KEY`, or `~/.config/local_elections/haryana_ocr.toml`.

The historical tables are occurrence-level. They must not be appended to the 2016/2022 seat CSVs.

## Development

```sh
make check
```

`make check` runs Ruff and compares the published Parquet fields against the retained sources. The historical release is rebuilt in a temporary directory and compared before accepting its values. Maintained Python code lives under `src/local_elections_haryana/{acquire,parse,build}`.

## Citation

Gaurav Sood. *Haryana Gram Panchayat and Ward Seat Reservation Data, 2016 and 2022*. Include the repository URL and commit used. Machine-readable metadata are in [CITATION.cff](CITATION.cff). Contact: [contact@gsood.com](mailto:contact@gsood.com).

## License

The code is [MIT licensed](LICENSE). Source notifications are publications of the Haryana State Election Commission. The code license does not grant rights over those documents; no separate data license is asserted here.

## 🔗 Adjacent Repositories

- [in-rolls/local_elections_rajasthan](https://github.com/in-rolls/local_elections_rajasthan) — Rajasthan GP Election Reservation Status and Results for 2020--2022
- [in-rolls/local_elections_bihar](https://github.com/in-rolls/local_elections_bihar) — Bihar panchayat elections: 2016 candidates and votes for six offices; 2021 mukhiya candidates, results, winners and seat reservations
- [in-rolls/local_elections_kerala](https://github.com/in-rolls/local_elections_kerala) — Kerala Local Government Seat Reservation Data and Winner Attributes
- [in-rolls/local_elections_uttarakhand](https://github.com/in-rolls/local_elections_uttarakhand) — Data on Local Elections from Uttarakhand
- [in-rolls/local_elections_up](https://github.com/in-rolls/local_elections_up) — UP Local Election Data --- GP and ULB. Seat reservation, winner, and candidates for some elections

✨ _Powered by [Adjacent](https://github.com/gojiplus/adjacent)_ 🚀

## Maintenance

This is a point-in-time data collection; see the [shared maintenance policy](https://github.com/soodoku/data-repos#maintenance-policy). Run the affected parsers on retained inputs when code changes and the relevant data validators when inputs or outputs change. Full-data checks and publication are explicit operations. Routine edits do not require hosted CI, Docker, a Python-version matrix, Preen or pre-commit.

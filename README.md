# Haryana Local Election Data

[![Code license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)

Gram panchayat head (sarpanch) and ward member (panch) records from Haryana's 2016 and 2022 local elections. The data record seat reservations and elected candidates from State Election Commission notifications. Source PDFs, acquisition manifests, published CSVs, and typed Parquet exports are included.

## Data

Each row is a seat record recovered from a notification. Coverage is incomplete, and repeated names and missing ward numbers prevent treating the usual geographic columns as a universally unique key.

<!-- datasets:start -->

| File | Rows | Each row represents |
| --- | ---: | --- |
| [release/2000/gazette_occurrences/historical_provisional_observations.parquet](data/release/2000/gazette_occurrences/historical_provisional_observations.parquet) | 67,770 | Provisional OCR or reviewed non-seat occurrence |
| [release/2000/gazette_occurrences/historical_quarantine.parquet](data/release/2000/gazette_occurrences/historical_quarantine.parquet) | 61 | Reviewed 2000 occurrence with unresolved fields |
| [release/2000/gazette_occurrences/historical_reviewed_occurrences.parquet](data/release/2000/gazette_occurrences/historical_reviewed_occurrences.parquet) | 2,761 | Reviewed 2000 printed occurrence |
| [release/2000/gram_panchayat_head_seat_reservation.parquet](data/release/2000/gram_panchayat_head_seat_reservation.parquet) | 5,932 | GP head seat record |
| [release/2000/gram_panchayat_ward_member_seat_reservation.parquet](data/release/2000/gram_panchayat_ward_member_seat_reservation.parquet) | 53,701 | GP ward seat record |
| [release/2005/gram_panchayat_head_seat_reservation.parquet](data/release/2005/gram_panchayat_head_seat_reservation.parquet) | 6,198 | GP head seat record |
| [release/2005/gram_panchayat_ward_member_seat_reservation.parquet](data/release/2005/gram_panchayat_ward_member_seat_reservation.parquet) | 60,425 | GP ward seat record |
| [release/2010/gram_panchayat_head_seat_reservation.parquet](data/release/2010/gram_panchayat_head_seat_reservation.parquet) | 5,924 | GP head seat record |
| [release/2010/gram_panchayat_ward_member_seat_reservation.parquet](data/release/2010/gram_panchayat_ward_member_seat_reservation.parquet) | 57,856 | GP ward seat record |
| [release/2016/gram_panchayat_head_seat_reservation.parquet](data/release/2016/gram_panchayat_head_seat_reservation.parquet) | 6,090 | GP head seat record |
| [release/2016/gram_panchayat_ward_member_seat_reservation.parquet](data/release/2016/gram_panchayat_ward_member_seat_reservation.parquet) | 61,879 | GP ward seat record |
| [release/2022/gram_panchayat_head_seat_reservation.parquet](data/release/2022/gram_panchayat_head_seat_reservation.parquet) | 6,123 | GP head seat record |
| [release/2022/gram_panchayat_ward_member_seat_reservation.parquet](data/release/2022/gram_panchayat_ward_member_seat_reservation.parquet) | 60,981 | GP ward seat record |

<details>
<summary>Retained observation snapshots</summary>

| File | Rows | Each row represents |
| --- | ---: | --- |
| [observations/00a6da628624/seat_rows.parquet](data/extracted/observations/00a6da6286242535c6f7ed6d7434e1fe58f97972b71ed3fdfed5ef1f949b6b80/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/1e6f85e0692d/seat_rows.parquet](data/extracted/observations/1e6f85e0692d5b7d87fffcaeb733db48665f70951f42e525d654d8115a352b39/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/20f6f91fea7f/seat_rows.parquet](data/extracted/observations/20f6f91fea7f6f32e7b87900ce79a5cc933e9c06542be3239fdb7bde88150af4/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/28a794b45d44/seat_rows.parquet](data/extracted/observations/28a794b45d444830079dd758b316af358149c9895872564ef70c56e8e4868aea/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/2f043cbcd088/seat_rows.parquet](data/extracted/observations/2f043cbcd088859de5bf5dcdbdaad145125039071629a052b86533a7713eb8f9/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/5c6160d7c982/seat_rows.parquet](data/extracted/observations/5c6160d7c982d0cb55743f88ba90d95d82dc5fa1d47402bb5493fa6d443bc7fa/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/6ad3161f4b7c/seat_rows.parquet](data/extracted/observations/6ad3161f4b7c750e4446542bc4cf48dc5acd822c7897c4efeffdfbc56021da34/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/6f92fe34f6a5/seat_rows.parquet](data/extracted/observations/6f92fe34f6a54dd011dadc1602556a0935b9434c44a2452b4a01d8f0f0e98b34/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/7715dfc0287a/seat_rows.parquet](data/extracted/observations/7715dfc0287adec5a8aa072f0762e56150210c2653580114fe995b8f44fb82aa/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/88adc00fa2d6/seat_rows.parquet](data/extracted/observations/88adc00fa2d60b6e6f6d33bafd827e60afd38f4763202985e8b2e9001b1bd335/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/951e414ba7a6/seat_rows.parquet](data/extracted/observations/951e414ba7a68c948cf11d3870dedf2d3d792a054797feb6595ab78d890bb67a/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/99cc306ae058/seat_rows.parquet](data/extracted/observations/99cc306ae058ef8824515602b5a2b3e56465c28dc5c44580d791b9be1525081e/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/a00a66abee45/seat_rows.parquet](data/extracted/observations/a00a66abee459c7e0a4ed1e457f3ebf6591d6463e57c0a4e717e84405146a768/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/a2128bd97e57/seat_rows.parquet](data/extracted/observations/a2128bd97e575b9e779478b6622d63a06e73bb796a05374a571ea4ef0defd17c/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/ae4fa5939922/seat_rows.parquet](data/extracted/observations/ae4fa5939922729c37aeed5cfb9a9dbdd7ca90bbc13823548b606b70ff0f140b/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/bc94a933c77a/seat_rows.parquet](data/extracted/observations/bc94a933c77aac8e4386a202e0597b384bfa295c89591fa2cf7907aecf077062/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/c3b40ce51cf0/seat_rows.parquet](data/extracted/observations/c3b40ce51cf00467ec0e85d18c78272a32aafc7d0ab8309d7bc34edd540e4651/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/de78517b40a1/seat_rows.parquet](data/extracted/observations/de78517b40a12fc843ca8852cca3639bd44c19f2cc4ef69d3b070ffd7e6795b6/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e22fc34f7116/seat_rows.parquet](data/extracted/observations/e22fc34f7116bf3dd93d6284f6004f075b4fa2ef65d74d2a44ae968a930dea06/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e35273b41413/seat_rows.parquet](data/extracted/observations/e35273b4141320ac6984fc437779be2744ec24dcf8c07880153d4a70fbcdafd3/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/e9f6fd031efc/seat_rows.parquet](data/extracted/observations/e9f6fd031efc80233b64b9c1e9fdafed6121de22b17016c0c2f129a3812c8b7c/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/edef31fd37bd/seat_rows.parquet](data/extracted/observations/edef31fd37bdc0af3b49561a796f1b6cc0c918125431e969cd48ec23ce59ff3a/seat_rows.parquet) | 70,592 | Archived OCR/review observation; not a unique seat |
| [observations/fb220eb88315/historical_provisional_observations.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_provisional_observations.parquet) | 67,770 | Provisional OCR or reviewed non-seat occurrence |
| [observations/fb220eb88315/historical_quarantine.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_quarantine.parquet) | 61 | Reviewed 2000 occurrence with unresolved fields |
| [observations/fb220eb88315/historical_reviewed_occurrences.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/historical_reviewed_occurrences.parquet) | 2,761 | Reviewed 2000 printed occurrence |
| [observations/fb220eb88315/modern_quarantine.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/modern_quarantine.parquet) | 1,202 | Archived modern record requiring review |
| [observations/fb220eb88315/modern_seats.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/modern_seats.parquet) | 133,871 | Archived modern seat record |
| [observations/fb220eb88315/printing_reconciliation.parquet](data/extracted/observations/fb220eb883155fa07df14b1aa9d1c709441463d8ff9f16f965d20df96ee28637/printing_reconciliation.parquet) | 1,536 | Archived comparison of printed occurrences |

</details>

<!-- datasets:end -->

[MANIFEST.json](data/MANIFEST.json) records each export's schema, row count, SHA-256, and input CSV checksum. The parsed CSVs are in `data/extracted/<year>/` with cached OCR; the PDFs and the harvest's source manifests are in `data/raw/<year>/`, listed with their URLs in [data/raw/fetch_log.csv](data/raw/fetch_log.csv). `make verify` checks every exported value against its CSV and verifies the notification PDFs against their acquisition checksums.

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
| `reserved_label` | string | Harmonized seat-reservation label |
| `reserved_caste` | string | `SC`, `ST`, `BC_A`, or `NONE`; `NONE` means no caste reservation |
| `reserved_woman` | bool | Whether the seat is reserved for a woman |
| `winner` | string | Elected person's name or the source's vacancy text |
| `father_husband` | string | Relation-name column as printed |
| `unopposed` | bool | Elected unopposed, indicated by a source asterisk |
| `vacant` | bool | Source records an unfilled seat |
| `reserved_raw` | string | Extracted category cell before normalization |
| `script` | string | `latin` or `krutidev`, as identified by the category normalizer |
| `printings_agree` | bool | Agreement on the GP reservation across printings; null when unchecked |
| `notification`, `source_pdf` | string | Notification identifier and saved source filename |

Caste and women's reservations are separate dimensions. An SC-reserved seat can also be woman-reserved. Seat reservation is not the elected person's caste or gender. `printings_agree` is a GP-level comparison propagated to its ward rows; it does not establish independent agreement on each ward's category.

## Derived crosswalks, links and inferred values

These sit beside the source exports and never change them.

- [District and block crosswalks](data/manual/crosswalks/README.md): reviewed 2016→2022 correspondences, with evidence and a reason for each decision.
- [Sarpanch seat links](data/release/linkage/README.md): 2016→2022 GP pairs within reviewed block pairs. Ward counts agree for 91.9% of name links, against 14.8% at random.
- [Inferred values](data/release/inferred/README.md): romanized Kruti Dev names, and the probability that each elected sarpanch is a woman. The probability is validated against 2022 winners, whose sex the 2020 law fixes (cross-validated AUC 0.993).

## Coverage and known gaps

**2010 categories.** The 2010 notifications were recovered from Wayback captures of the SEC site (see `data/raw/2010/manifest.csv`). In seven blocks they print far fewer women's seats than the statutory third: Palwal/Palwal, Sirsa/Nathusari Chopta, Sirsa/Baruguda, Karnal/Assandh, Rewari/Bawal, Jhajjar/Matanhail and Yamuna Nagar/Mustafabad. The Hindi printings of the same notifications agree with the English. The SEC's own reservation table and the winners' names disagree with both. [`data/manual/2010/category_defects.csv`](data/manual/2010/category_defects.csv) records each block, its evidence and the decision `reservation_unreliable`. The printed values are published unchanged.

**2000 results.** The March 2000 results come from the gazette scans the SEC republished, transcribed by Muse Spark and rebuilt by [`parse_2000.py`](src/local_elections_haryana/parse/parse_2000.py), which removes repeated scans, sets aside rows spilled from neighbouring notifications, recovers printed GP serials with Tesseract and records each block's completeness against the SEC's own GP counts. 83 of 113 blocks are complete; [`data/extracted/2000/README.md`](data/extracted/2000/README.md) explains the fixes, the partial blocks and the accuracy checks.

**2005 results.** The 2005 sarpanch and panch results are the SEC's 119 block result lists, recovered from Wayback captures made in 2007-2009 (see `data/raw/2005/manifest.csv`). The lists carry a text layer and are parsed without OCR. They print no serial, so `sr_no` is a GP's order within its block file. A leading `*` on many winners is unexplained in the files; it is removed from `winner` and not read as unopposed. Four blocks print too few women's sarpanch seats and Naraingarh prints BC on 39% of its sarpanch rows; [`data/manual/2005/category_defects.csv`](data/manual/2005/category_defects.csv) records the evidence and decisions. No official 2005 total has been found, so coverage is reported rather than tested.

The 2000 files cover 113 blocks in 19 districts; 2005 covers 119 blocks in 20 districts; 2010 covers 118 blocks in 21 districts; 2016 covers 126 blocks in 21 districts; 2022 covers 143 blocks in 22 districts. Administrative boundaries and names changed between elections, including the creation of Mewat, Palwal and Charkhi Dadri and the Mewat/Nuh name change. Reviewed district and block crosswalks between consecutive elections are in [`data/manual/crosswalks/`](data/manual/crosswalks/README.md); there is no LGD or census identifier. Exact names can differ across publications, and fuzzy matching requires review.

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

The published files cover 2000, 2005, 2010, 2016 and 2022, and exclude later bye-elections. The 2000 samiti and zila parishad gazette work is released separately; see [Historical 2000 gazette pipeline](#historical-2000-gazette-pipeline).

## How collected

| Election | Source | Extraction |
|---|---|---|
| 2000 | SEC gazette scans (April 2000) republished in 2022, 113 PDFs | Muse Spark transcription, Tesseract serials and page numbers ([`parse_2000.py`](src/local_elections_haryana/parse/parse_2000.py)) |
| 2005 | SEC block result lists (`PCRESULTPDF`), 119 PDFs from Wayback captures | Offline text-layer extraction ([`parse_2005.py`](src/local_elections_haryana/parse/parse_2005.py)) with source-cell reservation reviews |
| 2016 | [SEC fifth-general-election notifications](https://secharyana.gov.in/notifications-of-elected-candidates-of-panchayati-raj-institution-in-5th-general-elections-2016-in-the-state-of-haryana/), 21 district PDFs | Offline PDF table extraction; one printing retained per notification |
| 2022 | [SEC notifications](https://secharyana.gov.in/orders-notifications-related-to-panchayat-elections-2021/) and [statewide index](https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c/uploads/2022/12/2022121338.pdf), 187 linked PDFs | Offline PDF table extraction with retained Surya OCR for 26 pages whose table grids were fragmented |

The 2022 index includes Zila Parishad and Panchayat Samiti notifications as well as GP notifications; all 187 files are retained, but only sarpanch and panch rows enter these exports. The older NIC URLs for 2016 were unavailable during acquisition. The source manifest records the exact Wayback URLs used to recover them. Saved filenames identify the district and block where available, and manifests preserve the original filename, URL, byte count, and SHA-256.

Notifications can contain multiple Hindi and English printings with restarted serials. The parser groups rows by notification and chooses one printing, preferring English. It handles wrapped reservation labels, doubled glyphs, and Kruti Dev text encoding. These are consequential cases: a detached `Women` label can otherwise turn a woman-reserved seat into a plausible but incorrect record.

Cached OCR from 41 pages of the 2016 PDFs is retained for research but excluded from parsing. Earlier evaluation found it could attach ward rows to the wrong GP across page boundaries. Ordinary parsing requires neither a model nor paid API calls. The optional [OCR tool](src/local_elections_haryana/parse/ocr.py) documents its separate environment and the rejected 2016 experiment.

The [original implementation](https://github.com/in-rolls/local_elections_haryana/tree/2981e75) records the collection history. Existing published CSVs are preserved; a new parse writes to `data/build/parse/` for comparison before any release update.

## Layout

Folders follow the in-rolls [layout standard](https://github.com/in-rolls/local_elections/blob/main/docs/layout.md):

| Folder | Holds |
| --- | --- |
| `data/raw/<year>/` | Notification PDFs as received and the harvest's `manifest.csv`; `raw/fetch_log.csv` lists every file with its URL |
| `data/raw/gazette_archive/` | The git-ignored 2000/2005 gazette collection (see its README) |
| `data/extracted/<year>/` | Parsed seat CSVs and cached OCR; `extracted/observations/` holds the retained observation snapshots |
| `data/manual/<year>/`, `data/manual/crosswalks/` | Hand readings, reviews and corrections; reviewed block and district crosswalks |
| `data/build/` | Rebuildable intermediates (crosswalk evidence, trial parses) |
| `data/release/<year>/` | The published seat tables; `release/2000/gazette_occurrences/` holds the 2000 gazette occurrence release |
| `data/release/linkage/`, `data/release/inferred/` | GP links across elections; inferred winner sex and romanized Kruti Dev names |
| `data/search_log/` | Leads not admitted to the build |

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

table = pq.read_table("data/release/2022/gram_panchayat_head_seat_reservation.parquet")
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
uv run python -m local_elections_haryana.parse.parse --year 2022 --limit 1 --out data/build/parse/smoke
```

`make parse YEAR=2022` processes that year's saved PDFs and writes CSVs under `data/build/parse/2022/`. Failed PDF reads stop publication of the run's outputs. A limited parse cannot overwrite the published CSV directory. Run `make validate-derived YEAR=2022` on a complete derived year and compare it with the existing release before replacing any published files.

Harvesting is a separate, explicitly invoked network operation:

```sh
make harvest YEAR=2022
```

Downloads must contain a readable PDF and match any advertised content length before they replace a saved file. Existing downloads are reused unless `--refresh` is passed to `src/local_elections_haryana/acquire/harvest.py`. Use `make verify` to check the retained source bytes before relying on a cache.

## Historical 2000 gazette pipeline

The 2000 and 2005 gazette work (OCR, parsing, source review, and the 2000 release) moved here from the central [in-rolls/local_elections](https://github.com/in-rolls/local_elections). It is the `local_elections_haryana` package in `src/`.

- `make historical` rebuilds `data/release/2000/gazette_occurrences/` (reviewed occurrences, quarantine, provisional observations, with a receipt and `SHA256SUMS`) from tracked inputs only: `data/extracted/observations/` and `data/manual/`.
- The source PDFs, OCR corpus and review ledgers are in the [raw-data archive](data/raw/gazette_archive/README.md). They are git-ignored, with a tracked SHA-256 manifest and a tarball for download.
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

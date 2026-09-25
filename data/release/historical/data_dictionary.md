# Haryana historical release data dictionary

| artifact | row unit | universe | missing policy | provenance |
|---|---|---|---|---|
| `historical_reviewed_occurrences.parquet` | printed occurrence | source-reviewed 2000 seat occurrences with body, tier, ward where required, and category | no imputation | frozen review snapshot and source-review hashes |
| `historical_quarantine.parquet` | printed occurrence | reviewed occurrences missing an essential release field | preserve null and reason | frozen review snapshot; includes exactly 32 missing-heading rows |
| `historical_provisional_observations.parquet` | OCR occurrence | unvalidated OCR and reviewed non-seat records | outside release universe | frozen review snapshot |

Historical raw OCR fields remain in every partition. Null historical cells are
unknown, not zero.

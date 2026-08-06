## Haryana Gram Panchayat Seat Reservation Status

Reservation status of every gram panchayat (sarpanch) seat in Haryana, plus the
ward-level (panch) seats within each GP.

Haryana reserves GP seats along two independent dimensions — caste
(Scheduled Caste / Backward Class 'A' / open) and gender (woman-reserved or not)
— assigned by rotation and draw of lots. Both are recorded here, along with the
person elected to the seat.

* [data](data/)
* [scripts](scripts/)

### Layout

Data is partitioned by election year:

```
data/2022/
  manifest.csv           one row per source notification: district, block, SHA-256, URL
  gp_reservation.csv     one row per gram panchayat        <- the main file
  ward_reservation.csv   one row per GP ward (panch seat)
  index.pdf              the SEC's statewide index
  pdfs/                  the 187 notification PDFs
```

The source PDFs are committed, under readable names built from the index
(`Rohtak__Meham.pdf`, not `2022120213-3.pdf`), so any row can be checked against
the gazette page it came from without a network round trip. `manifest.csv`
carries the URL, byte count and SHA-256 of each, so a re-harvest can prove it
fetched the same bytes. It is about 150 MB per election year.

### Columns

| column | meaning |
|---|---|
| `district`, `block` | administrative location, taken from the SEC index |
| `sr_no` | serial number within the block notification |
| `gram_panchayat` | GP name as printed |
| `ward_no` | ward number (ward file only) |
| `reservation` | harmonised label, e.g. `Woman`, `SC Other than Woman` |
| `caste_reservation` | `SC` / `ST` / `BC_A` / `NONE` |
| `woman_reserved` | 1 if the seat is reserved for a woman |
| `winner` | person elected to the seat |
| `father_husband` | as printed |
| `unopposed` | 1 if elected unopposed (a `*` in the source) |
| `reservation_raw` | the source cell, unmodified, for auditing |
| `script` | `latin` or `krutidev` — which typesetting the row was read from |
| `printings_agree` | 1 if the Hindi and English printings agree on this seat, 0 if not, blank if only one printing exists |
| `notification`, `source_pdf` | provenance |

`caste_reservation` and `woman_reserved` are orthogonal: a seat can be
SC-reserved and woman-reserved at once.

### Pipeline

Three stages, deliberately separated — only the first touches the network, and
only the second reads PDFs, so the checks in the third are cheap to re-run.

```
make harvest    # index PDF -> 187 notification PDFs + manifest.csv (network)
make parse      # PDFs -> gp_reservation.csv, ward_reservation.csv  (offline)
make validate   # check the CSVs; non-zero exit on failure          (CSV only)
make test       # unit tests for the normalizer and row splitter
make all        # all three, in order
```

`make harvest` is idempotent — it skips files already downloaded, and re-checksums
everything. Pass `YEAR=` to any target.

### Source

The State Election Commission's statutory notification under s.161(4) of the
Haryana Panchayati Raj Act, 1994, published in the Haryana Government Gazette
(Extraordinary) of 30 November 2022. A [statewide index
PDF](https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c/uploads/2022/12/2022121338.pdf)
carries one hyperlink per Zila Parishad, Panchayat Samiti and block — 187 in all.
Listed on the SEC's [2021–22 orders and
notifications](https://secharyana.gov.in/orders-notifications-related-to-panchayat-elections-2021/)
page.

All 187 PDFs are digitally generated text, not scans, so no OCR is involved.

### Four things worth knowing about the source

**Each PDF prints its notification two or three times** — typeset in Kruti Dev
Hindi, then in English, sometimes in English twice — with the gram panchayats
renumbered from 1 in each printing. Parse it naively and every GP appears two or
three times. `parse.py` detects printings by the serial number restarting and
keeps one, preferring English.

That redundancy is also the best check available: the printings are independent
typesettings of the same seats, so agreement on a seat is real evidence rather
than self-consistency.

**Reservation labels wrap**, sometimes to a second line inside the cell and
sometimes into a ruled row of their own. The second case is the dangerous one:
`Scheduled Caste` with `Women` stranded on the next row reads as a perfectly
plausible SC-but-not-woman seat, so the error is silent rather than loud. Worse,
that stranded row often also carries the tail of a long name
(`['Singh', 'other than Women']`), so only the reservation part can be merged.

**Roughly a third of blocks are typeset in legacy Kruti Dev font encoding**
rather than Unicode, so their text extracts as mojibake: `vuqlwfpr tkfr efgyk ds
flok;` is अनुसूचित जाति महिला के सिवाय, "SC other than Woman". This is a
deterministic byte mapping, not corruption.

**The vocabulary is not standardised, and some of it is damaged.** Beyond the
expected variants — `Other than Women` / `Other Than Women` / `Other than
Woman`, `Scheduled Caste` / `Schedule Caste` / `Schedulded Caste`, and
`Backward Class 'A'` with three different apostrophe characters — the
typesetting itself breaks words. `Scheduled Cast e Women` in English; nine
distinct spellings of *anusuchit* in Kruti Dev (`vuqlwfpr`, `vuqlqfpr`,
`vuqlfpr`, `vuqwlwfpr` …); whole lines rendered with every character doubled
(`EEXXTTRRAAOORRDDIINNAARRYY`). Each unmatched variant silently downgraded a
reserved seat to an open one, so the matchers are pattern-based rather than
literal. `scripts/test_normalize.py` pins every string observed in the corpus.

### Validation

`make validate` checks the parsed CSVs against the manifest, the official
totals, and the statute. Two of its checks are worth trusting:

* **Per-block statutory shares.** Haryana's 50% women's reservation and 8%
  BC(A) reservation bind *per block*, not statewide, so a block far off those
  shares means rows were dropped or misread there. Offsetting errors cannot hide
  in a per-block check the way they can in a state total. This is what caught
  the wrapped-label bug.
* **Cross-printing agreement.** Disagreement between the Hindi and English
  printings is evidence of a misread. Seats that still disagree are marked in
  `printings_agree` rather than quietly resolved in favour of English.

Reference totals for 2022: 6,220 gram panchayats, 61,993 panches, 143 blocks.

### Not included

* **No LGD or census village codes.** GP names are free text; joining to other
  data needs fuzzy matching against the Local Government Directory.
* **2022 only.** The 2016 (5th) general election is published in the same
  7-column format, in English, per district, and is reachable through the
  Wayback Machine — the original host (`164.100.137.42`) is dead. The same GP
  joins across the two years, so a 2016+2022 panel is feasible, and rotation of
  reservation across cycles is what makes this data useful for identification.
  The normalizer already handles the 2016 vocabulary; only a harvester for that
  year is missing.
* **Bye-elections since 2022** are not folded in; this is the roster as elected
  in November 2022.

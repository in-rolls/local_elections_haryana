## Haryana Gram Panchayat Seat Reservation Status

Reservation status of every gram panchayat (sarpanch) seat in Haryana for the
2022 and 2016 panchayat general elections, plus the ward-level (panch) seats
within each GP.

Haryana reserves GP seats along two independent dimensions — caste
(Scheduled Caste / Backward Class 'A' / open) and gender (woman-reserved or not)
— assigned by rotation and draw of lots. Both are recorded here, along with the
person elected to the seat.

* [data](data/)
* [scripts](scripts/)

### Layout

Data is partitioned by election year:

```
data/2022/                 data/2016/
  manifest.csv               manifest.csv
  gp_reservation.csv         gp_reservation.csv     <- the main file
  ward_reservation.csv       ward_reservation.csv
  index.pdf                  pdfs/   (21 district PDFs)
  pdfs/   (187 block PDFs)
```

| | gram panchayats | ward seats | blocks | districts |
|---|---|---|---|---|
| 2022 | 6,159 (99.0% of official) | 61,362 (99.0%) | 143 | 22 |
| 2016 | 6,079 (98.0%) | 61,618 (98.8% of elected) | 126 | 21 |

2016 has fewer blocks and districts because Charkhi Dadri was not created until
December 2016 and Nuh was still called Mewat. Joining the years on district and
gram panchayat name matches 4,269 GPs, which is enough to see reservation
rotate: only 50 of the 775 SC-reserved seats in 2016 were still SC-reserved in
2022. Raising that match rate needs fuzzy name matching — the gazettes
transliterate inconsistently ("Ado Majra" in 2016, "Adho Majra" in 2022).

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
| `vacant` | 1 if the seat went unfilled; official "elected" totals exclude these |
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

### Sources

**2016** is published as one PDF per district, each containing a separate
notification per block, linked from the SEC's [5th general elections
page](https://secharyana.gov.in/notifications-of-elected-candidates-of-panchayati-raj-institution-in-5th-general-elections-2016-in-the-state-of-haryana/).
The NIC host serving those files no longer answers, so `harvest.py` fetches them
from the Internet Archive and pins the exact snapshot in `manifest.csv`.

**2022.** The State Election Commission's statutory notification under s.161(4) of the
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

Reference totals: 6,220 gram panchayats / 61,993 panches / 143 blocks for 2022,
and 6,193 / 60,438 for 2016. These are not the same kind of number — the 2022
figures were announced before polling and count *seats*, the 2016 figures were
published afterwards and count *people elected*, which excludes vacancies.
`validate.py` records that basis per year and compares like with like.

The statutory shares also differ: the women's quota rose from one third to one
half, and BC(A) reservation in panchayats did not exist before the 2021
amendment. Asserting the 2022 rules against 2016 would be wrong.

### Not included

* **No LGD or census village codes.** GP names are free text; joining to other
  data needs fuzzy matching against the Local Government Directory.
* **No crosswalk between the two years.** The 70% match above is on exact
  normalised names. Closing the rest needs fuzzy matching, ideally against the
  Local Government Directory so both years get stable codes.
* **2010 and 2005** are not built. 2005 exists on the live CDN but as scanned
  images, so it would need OCR.
* **Bye-elections since 2022** are not folded in; this is the roster as elected
  in November 2022.

## 🔗 Adjacent Repositories

- [in-rolls/local_elections_up](https://github.com/in-rolls/local_elections_up) — UP Local Election Data --- GP and ULB. Seat reservation, winner, and candidates for some elections
- [in-rolls/up-2023-electoral-rolls](https://github.com/in-rolls/up-2023-electoral-rolls)
- [in-rolls/local_elections_bihar](https://github.com/in-rolls/local_elections_bihar) — Candidate Info. + Valid Votes Won by Cands. in the 2016 Bihar Panchayat Elections
- [in-rolls/quota](https://github.com/in-rolls/quota) — Effects of Randomly Assigned Reservations for Women Leaders in Indian Local Government on Allocation and Development Outcomes
- [in-rolls/local_reservations](https://github.com/in-rolls/local_reservations) — Data on Indian local elections, including reservation status

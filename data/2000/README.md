# 2000 sarpanch and panch results

`gp_reservation.csv` and `ward_reservation.csv` hold the March 2000 results in
the same schema as 2005-2022: 5,932 sarpanch and 53,701 panch rows in 113
blocks of 19 districts. The commission's own block table counts 6,035 GPs and
54,764 panch seats in 114 blocks.

The source is the gazette scans the SEC republished in 2022
(`manifest.csv`: public URL and SHA-256 of each of the 113 PDFs). They are
images, 660 MB, and stay in the git-ignored raw archive. Muse Spark transcribed
every row (`acquire/rollout_hosted.py`); `parse/parse_2000.py` builds these
tables from that transcription and the files in `reference/`, so the year
rebuilds without the archive.

## What was fixed

Comparing the transcription with the SEC block table found these problems; each
fix is recorded in a file here.

| Problem | Fix | Record |
| --- | --- | --- |
| A page scanned twice (Kharkhoda, Bapoli), or a block's last page reprinted at the head of the next block's file (Odhan opens with Dabwali's GPs 45-46) | Drop the repeat | `reference/repeated_pages.csv` |
| Hindi rows on English pages: the previous notification's tail, usually another block's | Set aside, not this block's seats | `reference/spilled_hindi_rows.csv` |
| Thirteen Faridabad and Sirsa notifications printed whole in Hindi and English | Keep English; pair the Hindi twin and record agreement | `printings_agree` |
| Nineteen blocks spelled differently by the gazette index and the SEC table | Map to the SEC name | `reference/block_names.csv` |
| GP serial ("17 PINJOKHERA") dropped by the transcription | Read with Tesseract; consecutive serials fix a page's numbering | `reference/serial_ocr.csv`, `sr_no` |
| A GP heading the model did not read, so the previous GP's name ran on | Name from the Tesseract serial line, or left blank | `reference/sarpanch_provenance.csv` |
| A gazette page missing from the scan (Hansi-I skips page 2435) | Rows after it open an unnamed GP instead of joining the wrong one | `reference/page_numbers.csv`, `reference/serial_steps.csv` |

`*` beside a ward or sarpanch row is the gazette's mark for a member returned
unopposed, defined in each page's footer; it sets `unopposed`.

## How complete each block is

`reference/block_status.csv` compares every block with the SEC's GP count:

| Status | Blocks | GPs held |
| --- | ---: | ---: |
| `complete`: count matches and serials run without a break | 83 | 4,348 |
| `partial`: GPs missing, located as a serial gap or a missing first or last page | 27 | 1,486 |
| `review`: one GP more than the SEC table | 3 | 98 |

Gharaunda's file stops at GP 24 of 51 and Radaur's misses six; neither has a
second part on the SEC server, and the official gazette repositories did not
answer. Panchkula/Barwala is not held at all.

The SEC's panch seat counts are not used as a gate. They agree with the
transcription in most blocks but not in some where every GP and ward is
present (Nagina: 93 SC panch seats in the table, 23 in the gazette and 22 in
2005), so the table and the gazette may count different things.

## Accuracy

- **Two printings.** Where a notification was printed whole in Hindi and English,
  the two independent transcriptions agree on the category of 97.7% of 645
  sarpanch pairs and 98.6% of 5,912 panch pairs. Some disagreements are
  mis-paired rows, so this bounds the error rate from above.
- **Pages read against the image.** Tosham page 5 (46 rows) and Begpur's page
  match the transcription row for row.
- **Statutory share.** Women hold 33.3% of sarpanch seats statewide; two blocks
  are more than 6 points off a third.
- **Not resolved.** 38 sarpanch categories and 36 GP names were not read.

A frozen, hand-labelled sample of sarpanch rows is the remaining check.

```sh
uv run python -m local_elections_haryana.parse.serials_2000  # needs the archive
uv run python -m local_elections_haryana.parse.parse_2000
uv run python -m local_elections_haryana.build.validate --year 2000
```

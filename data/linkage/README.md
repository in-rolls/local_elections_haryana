# Sarpanch seat links, 2016 to 2022

`gp_2016_2022.parquet` pairs a 2016 sarpanch seat with its 2022 seat. Each side
carries its source key (`district`, `block`, `sr_no`, `gram_panchayat`), the name
used for matching, and its number of ward seats. A link states that two GP names
agree inside a reviewed block pair. It is not an official identifier or proof of
unchanged boundaries.

A pair is a candidate only when its blocks form a `linked` row in
`data/crosswalks/block_2016_2022.csv`. Names are folded to absorb romanization
variants. Numbers, compass words and twin-village qualifiers (Kalan, Khurd,
Buzurg, Khas) veto a pair whose counterpart says otherwise. preclink then makes
the optimal one-to-one assignment. Two passes run:

- `link_pass = "name"`: name score of at least 0.80.
- `link_pass = "name_and_wards"`: on what remains, the same number of ward seats
  and a name score of at least 0.70.

The ward count shares nothing with the name. Among name-pass links, the two
years agree on it for 91.9% of GPs. Pairing GPs at random within the 2022 block
gives 14.8%. Ward boundaries were re-fixed after the 2020 amendment, so some
correct links have different counts.

Records whose key repeats within a year are left unlinked. `MANIFEST.json`
records input and output hashes, thresholds and these checks.

```sh
uv run python -m local_elections_haryana.linkage.gp_2016_2022
```

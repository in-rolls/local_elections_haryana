# Sarpanch seat links between consecutive elections

| File | Row |
| --- | --- |
| `gp_2005_2010.parquet` | A 2005 sarpanch seat paired with its 2010 seat |
| `gp_2010_2016.parquet` | A 2010 sarpanch seat paired with its 2016 seat |
| `gp_2016_2022.parquet` | A 2016 sarpanch seat paired with its 2022 seat |

Each side carries its source key (`district`, `block`, `sr_no`,
`gram_panchayat`), suffixed with its year, together with the name used for
matching and its number of ward seats. A link states that two GP names agree
inside a reviewed block pair. It is not an official identifier or proof of
unchanged boundaries.

A pair is a candidate only when its blocks form a `linked` row in
`data/crosswalks/block_<earlier>_<later>.csv`. Names are folded to absorb
romanization variants. Numbers, compass words and twin-village qualifiers (Kalan,
Khurd, Buzurg, Khas) veto a pair whose counterpart says otherwise. preclink then
makes the optimal one-to-one assignment. Two passes run:

- `link_pass = "name"`: name score of at least 0.80.
- `link_pass = "name_and_wards"`: on what remains, the same number of ward seats
  and a name score of at least 0.70.

## Checks

| Pair | Linked | Same ward count, name links | Same ward count, random pairs in block | Same winner name, linked | Same winner name, random pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2005→2010 | 5,724 | 96.9% | 16.4% | 1.15% | 0.21% |
| 2010→2016 | 5,623 | 48.3% | 14.3% | 0.76% | 0.10% |
| 2016→2022 | 5,715 | 91.9% | 14.8% | — | — |

The ward count and the winner's name share nothing with the GP name. Wards were
redrawn after the 2011 census, between 2010 and 2016, and again after the 2020
amendment. So a correct link can carry a different ward count, which is why the
2010→2016 agreement is lower than 2016→2022's.

Records whose key repeats within a year are left unlinked. Blocks that a
crosswalk excludes stay unlinked; their reasons are in the crosswalk. For 2010,
these are Palwal/Hassanpur, Karnal/Nissing and Fatehabad/Bhuna, whose 2010 rows
are missing or incomplete. `MANIFEST.json` records input and output hashes,
thresholds and these checks for each pair.

```sh
uv run python -m local_elections_haryana.linkage.gp_links
```

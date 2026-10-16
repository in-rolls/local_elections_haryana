# Inferred values

Nothing in this folder is a source value. Each file states how it was inferred,
keeps its inputs beside the result, and is never written back into `data/fin/`.

| File | Row | What is inferred |
| --- | --- | --- |
| `kruti_dev_names_2022.csv` | A 2022 GP record printed in Kruti Dev | Unicode and romanized GP, winner and relation names |
| `winner_female_probability_2016.parquet` | An elected 2016 sarpanch | Probability that the winner is a woman |
| `winner_female_probability_2022.parquet` | An elected 2022 sarpanch | Probability that the winner is a woman |

## Kruti Dev names

Two 2022 blocks (Fatehabad: Bhattu Kalan; Jhajjar: Machhrauli) were published
only in Kruti Dev Hindi, so 45 GP records carry names in the legacy font
encoding. `kruti_names.py` decodes them with the vendored Kruti Dev 010 mapping.
Its output is identical to the decoder in `local_elections_bihar` on all 135
names. The decoded names are romanized with indicate's local model, and the
package version is recorded in each row.

## Winner sex

The notifications record no sex. `winner_sex.py` infers a probability from the
printed name:

- naampy's female-label score for the first name, after titles are removed;
- fixed surname markers (Kaur, Devi, Rani, Kumari, ... versus Kumar, Singh, Lal,
  Ram, Chand, ...), because Haryana names often carry sex in the last word;
- an "Smt"/"Kumari" title marker.

A logistic regression combines them. It is fit on 2022 winners, whose sex is
fixed by law: the 2020 amendment to section 9 of the Haryana Panchayati Raj Act
lets only women contest the women's offices and only persons other than women
contest the rest. Performance is cross-validated with folds grouped by first
name, so no first name is in both a training and a test fold.

| 2022 winners, grouped cross-validation | AUC | Log loss | Brier | Accuracy at 0.5 |
| --- | ---: | ---: | ---: | ---: |
| naampy first-name score alone | 0.957 | 0.258 | 0.077 | 0.894 |
| This model | 0.993 | 0.099 | 0.026 | 0.965 |

Within each probability band, the predicted and observed shares of women differ
by at most five points (`MANIFEST.json`). As an out-of-sample check, 2016 winners
of women-reserved offices, who must be women, average a probability of 0.946.

Use these probabilities as an outcome in aggregate analyses, for example as the
expected share of women, rather than as a label for any person. Winners printed
only as placeholders ("_", "...") get no probability: 106 in 2016 and 259 in
2022. The 2022 placeholders come from whole blocks: Bawal, Dabwali, Nuh, Raipur
Rani, Nizampur and Uklana. The training labels contain a few impossible pairs,
such as a man recorded as winning a women's office. These are left in place as
source errors.

Rebuild:

```sh
uv sync --frozen --group infer --group transliterate
uv run python -m local_elections_haryana.infer.kruti_names
uv run python -m local_elections_haryana.infer.winner_sex
```

# District and block crosswalks, 2016 to 2022

These two files are reviewed by hand. They are the record of which administrative
units continue between the elections, and they are not regenerated.

| File | Row |
| --- | --- |
| `district_2016_2022.csv` | A 2016 district and the 2022 district it became (`same`, `renamed`, `split`) |
| `block_2016_2022.csv` | A candidate pair of a 2016 block and a 2022 block, with evidence and a decision |

Districts: Gurgaon became Gurugram and Mewat became Nuh. Mahendergarh is printed
"M/garh" in 2022. Charkhi Dadri was formed from Bhiwani's Badhra, Dadri-I and
Dadri-II blocks.

Blocks: for every pair, `shared_gp_names` counts the 2022 block's GP names that
appear, after case and punctuation are removed, in the 2016 block of the same
district family. A pair is `linked` when they share at least five names or a
fifth of the 2022 block. Pairs sharing three common village names are
`excluded`. The decisions were then reviewed one by one:

- **New blocks** take their GPs from the parent blocks shown, e.g. Ujhana from
  Narwana, Kunjpura from Karnal and Indri, and Pipli from Thanesar and Ladwa.
- **Machhrauli and Bhattu Kalan (2022)** were printed in Kruti Dev. Their
  evidence uses the romanized names in `data/inferred/kruti_dev_names_2022.csv`.
  Machhrauli takes 9 GPs from Jhajjar and 8 from Salhawas.
- **Palwal, 2022:** the English tables printed for Badoli and Hodal are
  identical, although their Hindi preambles name different blocks. The table
  shares no GP name with 2016 Hodal and 22 with Palwal and Hassanpur, so it is
  Badoli's. 2022 Hodal rows are excluded.

`note` gives the reason for every decision. GP links in `data/linkage/` use
only `linked` pairs.

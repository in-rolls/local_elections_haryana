# District and block crosswalks between consecutive elections

These two files are reviewed by hand. They are the record of which administrative
units continue between the elections, and they are not regenerated.

| File | Row |
| --- | --- |
| `district_2010_2016.csv`, `district_2016_2022.csv` | A district and the district it became (`same`, `renamed`, `split`) |
| `block_2010_2016.csv`, `block_2016_2022.csv` | A candidate pair of an earlier and a later block, with evidence and a decision |

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

## 2010 to 2016

Districts are unchanged. Blocks created by 2016 take their GPs from the parents
shown in the evidence: Satnali from Mahendergarh (all 25 GP names), Sihma and
Nizampur from Ateli Nangal, Narnaul and Nangal Chaudhary, Ismailabad from Pehowa,
Shahabad and Thanesar, Prithla from Palwal, Murthal from Ganaur, Rai and
Sonepat, and Sanauli Khurd from Bapoli. Three blocks are excluded because the
2010 parse holds too few of their rows: Palwal/Hassanpur (no rows; the Hindi
printing lists 32), Karnal/Nissing (21 of 47) and Fatehabad/Bhuna (1 of about
29).


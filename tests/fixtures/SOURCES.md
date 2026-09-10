# Test sources

The normalizer and row-splitting tests were inherited from repository commit `2981e75`. They contain short table-cell examples from the retained 2016/2022 Haryana SEC notifications. The original tests did not record exact capture times or page numbers for every example; these are unknown, not newly inferred. Original notification URLs and checksums are retained in `data/2016/manifest.csv` and `data/2022/manifest.csv`.

The synthetic CSV rows in `test_to_parquet.py` use invented district, block, and GP labels to test leading-zero identifiers, duplicates, missing cells, and invalid flags. The parser CLI tests use synthetic paths and a deliberately invalid PDF, with no new source capture. No hosted OCR was run to create these tests.

The successful download test reuses the retained `data/2022/index.pdf`, originally published at https://cdnbbsr.s3waas.gov.in/s31c6a0198177bfcc9bd93f6aab94aad3c/uploads/2022/12/2022121338.pdf. It makes no network call; its original capture time was not recorded. Invalid-download cases are synthetic.

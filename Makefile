YEAR ?= 2022
PY   ?= uv run python

.PHONY: all harvest parse validate validate-derived test clean help release raw-verify raw-archive

help:
	@echo "make harvest  YEAR=$(YEAR)   download index + notification PDFs, write manifest.csv"
	@echo "make parse    YEAR=$(YEAR)   PDFs -> data/derived/$(YEAR)/ CSVs"
	@echo "make validate YEAR=$(YEAR)   check the CSVs; non-zero exit on failure"
	@echo "make test                    unit tests for the normalizer and row splitter"
	@echo "make all                     harvest, parse, validate"

all: harvest parse validate-derived

harvest:
	cd scripts && $(PY) harvest.py --year $(YEAR)

parse:
	cd scripts && $(PY) parse.py --year $(YEAR)

validate:
	cd scripts && $(PY) validate.py --year $(YEAR)

validate-derived:
	$(PY) scripts/validate.py --year $(YEAR) --input-dir data/derived/$(YEAR)

test:
	uv run pytest -q

clean:
	rm -f data/derived/$(YEAR)/gp_reservation.csv data/derived/$(YEAR)/ward_reservation.csv

.PHONY: check to-parquet verify-data

check:
	uv sync --frozen --group dev
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q

to-parquet:
	$(PY) scripts/to_parquet.py

verify-data:
	$(PY) scripts/to_parquet.py --check

# Haryana 2000 historical release (tracked inputs only; no raw archive needed)
release:
	$(PY) -m local_elections_haryana.build_release

# Raw-data archive (see data/raw_archive/README.md)
raw-verify:
	$(PY) scripts/raw_archive.py verify

raw-archive:
	$(PY) scripts/raw_archive.py pack $(if $(OUT),--out $(OUT),)

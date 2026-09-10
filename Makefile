YEAR ?= 2022
PY   ?= uv run python

.PHONY: all harvest parse validate validate-derived test clean help

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

.PHONY: check to-parquet verify-data ci-docker

check:
	uv sync --frozen --group dev
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q
	uv run pre-commit run --all-files
	$(MAKE) validate YEAR=2016
	$(MAKE) validate YEAR=2022
	$(MAKE) verify-data

to-parquet:
	$(PY) scripts/to_parquet.py

verify-data:
	$(PY) scripts/to_parquet.py --check

ci-docker:
	@for version in 3.12 3.14; do \
	  COPYFILE_DISABLE=1 tar --exclude=._* --exclude=__pycache__ --exclude=.DS_Store --exclude=.git --exclude=.venv --exclude=.ruff_cache --exclude=.pytest_cache -cf - . | \
	  docker run --rm -i python:$$version-slim sh -ec 'mkdir /work; tar -xf - -C /work; cd /work; pip install -q uv; uv sync --frozen --group dev; uv run ruff check .; uv run ruff format --check .; uv run pytest -q; uv run python scripts/validate.py --year 2016; uv run python scripts/validate.py --year 2022; uv run python scripts/to_parquet.py --check' || exit $$?; \
	done

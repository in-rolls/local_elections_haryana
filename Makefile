YEAR ?= 2022
PY   ?= python3

.PHONY: all harvest parse validate test clean help

help:
	@echo "make harvest  YEAR=$(YEAR)   download index + notification PDFs, write manifest.csv"
	@echo "make parse    YEAR=$(YEAR)   PDFs -> gp_reservation.csv, ward_reservation.csv"
	@echo "make validate YEAR=$(YEAR)   check the CSVs; non-zero exit on failure"
	@echo "make test                    unit tests for the normalizer and row splitter"
	@echo "make all                     harvest, parse, validate"

all: harvest parse validate

harvest:
	cd scripts && $(PY) harvest.py --year $(YEAR)

parse:
	cd scripts && $(PY) parse.py --year $(YEAR)

validate:
	cd scripts && $(PY) validate.py --year $(YEAR)

test:
	cd scripts && $(PY) -m pytest -q

clean:
	rm -f data/$(YEAR)/gp_reservation.csv data/$(YEAR)/ward_reservation.csv

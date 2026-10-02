YEAR ?= 2022
PY ?= uv run python
RUFF ?= uv run ruff

.PHONY: sync data harvest parse validate lint verify check data-summary historical raw-verify raw-archive

sync:
	uv sync --frozen --group dev

data:
	$(PY) -m local_elections_haryana.parse.to_parquet
	$(MAKE) historical data-summary

historical:
	$(PY) -m local_elections_haryana.build.build_release

harvest:
	$(PY) -m local_elections_haryana.acquire.harvest --year $(YEAR)

parse:
	$(PY) -m local_elections_haryana.parse.parse --year $(YEAR)

validate:
	$(PY) -m local_elections_haryana.build.validate --year $(YEAR)

lint:
	$(RUFF) check .
	$(RUFF) format --check .

verify:
	$(PY) -m local_elections_haryana.build.release verify

data-summary:
	$(PY) -m local_elections_haryana.build.release summary

check: lint verify

raw-verify:
	$(PY) -m local_elections_haryana.acquire.raw_archive verify

raw-archive:
	$(PY) -m local_elections_haryana.acquire.raw_archive pack $(if $(OUT),--out $(OUT),)

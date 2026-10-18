"""Decisions behind the 2000 tables, built from the hosted transcription."""

import csv

import pandas as pd
import pytest

from local_elections_haryana.parse import parse_2000 as P
from local_elections_haryana.paths import ROOT

DATA = ROOT / "data" / "2000"


@pytest.fixture(scope="module")
def built():
    P.PROVENANCE.clear()
    P.SPILLED.clear()
    return P.build()


def committed(name):
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_tables_reproduce_from_tracked_inputs(built):
    gp_rows, ward_rows, *_ = built
    assert gp_rows == committed("gp_reservation.csv")
    assert ward_rows == committed("ward_reservation.csv")


def test_repeated_scans_and_reprinted_tails_are_dropped(built):
    repeats = built[2]
    pairs = set(zip(repeats.source_path.str[4:14], repeats.source_page, strict=True))
    # Kharkhoda scans pages 7 and 9 twice; Bapoli repeats pages 5-7 as 8-10
    assert {("6f844d750a", 8), ("6f844d750a", 10)} <= pairs
    assert {("fd81ac2c0a", 8), ("fd81ac2c0a", 9), ("fd81ac2c0a", 10)} <= pairs
    # Odhan's file opens with Dabwali's last page
    assert ("05e69a55e7", 1) in pairs


def test_a_dropped_leading_digit_still_supports_the_offset():
    assert P.supports(51, 2, 1)  # serial 52 read as 2
    assert not P.supports(51, 7, 1)


def test_one_misread_run_does_not_make_a_gap():
    # positions 0-9 read correctly, 10-12 read ten too low, then correct again
    reads = [(k, k + 1) for k in range(10)] + [(k, k - 9) for k in (10, 11, 12)]
    reads += [(k, k + 1) for k in range(13, 20)]
    assert P.segments(reads) == [(0, 19, 1)]


def test_a_real_gap_is_a_lasting_step():
    reads = [(k, k + 1) for k in range(10)] + [(k, k + 5) for k in range(10, 20)]
    assert P.segments(reads) == [(0, 9, 1), (10, 19, 5)]


def test_rows_after_a_missing_page_open_their_own_gp():
    rows = pd.DataFrame(
        [
            ("gp_head", None, 9), ("gp_ward", 1.0, 9), ("gp_ward", 9.0, 9),
            # page 10 opens at ward 6: the page with GP 41's start is missing
            ("gp_ward", 6.0, 10), ("gp_ward", 7.0, 10), ("gp_head", None, 10),
        ],
        columns=["tier", "ward", "source_page"],
    )  # fmt: skip
    assert P.gp_units(rows).tolist() == [0, 0, 0, 1, 1, 2]


def test_bilingual_printings_agree_almost_always():
    gp = pd.DataFrame(committed("gp_reservation.csv"))
    paired = gp[gp.printings_agree != ""]
    assert len(paired) > 500
    assert (paired.printings_agree == "1").mean() > 0.95


def test_block_status_accounts_for_every_block():
    status = pd.read_csv(DATA / "reference/block_status.csv")
    assert len(status) == 113
    assert set(status.status) <= {"complete", "partial", "review"}
    assert (status.status == "complete").sum() >= 80

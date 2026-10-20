"""Decisions behind the 2005 results tables."""

import csv

import pandas as pd
import pytest

from local_elections_haryana.parse import parse_2005 as P
from local_elections_haryana.paths import ROOT

DATA = ROOT / "data" / "2005"


@pytest.fixture(scope="module")
def tables():
    frame, dropped = P.parse()
    return (*P.tables(frame), dropped)


def committed(name):
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_committed_tables_reproduce_from_the_pdfs(tables):
    gp_rows, ward_rows, dropped = tables
    assert gp_rows == committed("gp_reservation.csv")
    assert ward_rows == committed("ward_reservation.csv")
    assert dropped == 354


def test_wrapped_names_are_read_whole_in_either_direction(tables):
    gp = pd.DataFrame(tables[0])
    # bottom-aligned: the first line prints above the row
    assert "GADHI SIKENDER PUR" in set(gp[gp.block == "Panipat"].gram_panchayat)
    assert P.WRAP["PANIPAT.pdf"] == "above"
    # top-aligned: the overflow prints below the row
    assert "Palwal Rural Urf Shamshabad" in set(gp[gp.block == "Palwal"].gram_panchayat)
    assert P.WRAP["PALWAL.pdf"] == "below"


def test_a_name_cut_at_a_page_break_takes_its_runs_full_name(tables):
    ward = pd.DataFrame(tables[1])
    palwal = ward[ward.gram_panchayat.str.startswith("Palwal Rural")]
    assert set(palwal.gram_panchayat) == {"Palwal Rural Urf Shamshabad"}
    assert palwal.ward_no.astype(int).max() == 20


def test_page_break_mending_needs_consecutive_offices():
    assert P.office_step("Sarpanch", "1")
    assert P.office_step("19", "20")
    assert not P.office_step("7", "1")
    assert not P.office_step("Sarpanch", "2")


def test_headings_overridden_on_review():
    manifest = {r["saved_as"]: r for r in committed("manifest.csv")}
    assert (manifest["SIWAN.pdf"]["district"], manifest["SIWAN.pdf"]["block"]) == (
        "Kaithal",
        "Siwan",
    )
    assert manifest["MGARH.pdf"]["district"] == "Mahendergarh"
    assert all(r["heading_note"] for r in manifest.values() if r["saved_as"] in {
        "SIWAN.pdf", "MGARH.pdf"})  # fmt: skip


def test_the_unexplained_asterisk_is_not_read_as_unopposed(tables):
    gp = pd.DataFrame(tables[0])
    assert not gp.winner.str.startswith("*").any()
    assert set(gp.unopposed) == {""}

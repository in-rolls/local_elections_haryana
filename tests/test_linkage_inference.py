"""Rules behind the 2016-2022 links and the inferred winner sex."""

import pandas as pd

from local_elections_haryana.infer.kruti_names import kruti_text
from local_elections_haryana.infer.winner_sex import name_parts
from local_elections_haryana.linkage.gp_2016_2022 import name_key


def test_titles_are_removed_and_markers_read_from_the_last_word():
    assert name_parts("Smt. Sunita") == {
        "first_name": "sunita",
        "female_marker": 0,
        "male_marker": 0,
        "female_title": 1,
    }
    assert name_parts("Jasbir Kaur")["female_marker"] == 1
    assert name_parts("Parveen Kumar")["male_marker"] == 1
    assert name_parts("....")["first_name"] is None


def test_twin_villages_numbers_and_directions_are_kept_apart():
    assert name_key("Surpura Kalan")[2] == {"kalan"}
    assert name_key("Surpura Khurd")[2] == {"khurd"}
    assert name_key("Surpura Kalan")[0] == name_key("Surpura Khurd")[0]
    assert name_key("Ambala-II")[1] == {2}
    assert name_key("Mohammadpur Rohi 1")[1] == {1}
    assert name_key("Sanha Purvi")[2] == {"east"}


def test_kruti_dev_decodes_place_and_person_names():
    assert kruti_text("ekNjkSyh") == "माछरौली"
    assert kruti_text("<k.kh pkuujke") == "ढाणी चाननराम"


def test_crosswalk_decisions_are_explained_and_cover_2022():
    blocks = pd.read_csv("data/crosswalks/block_2016_2022.csv")
    assert set(blocks["decision"]) <= {"linked", "excluded"}
    assert blocks["note"].notna().all()
    gp = pd.read_parquet("data/fin/gp_reservation_2022.parquet")
    linked = blocks[blocks["decision"] == "linked"]
    covered = set(zip(linked["district_2022"], linked["block_2022"], strict=True))
    blocks_2022 = set(zip(gp["district"], gp["block"], strict=True))
    assert blocks_2022 - covered == {("Palwal", "Hodal")}


def test_links_are_one_to_one_within_linked_block_pairs():
    links = pd.read_parquet("data/linkage/gp_2016_2022.parquet")
    keys = ["district", "block", "sr_no", "gram_panchayat"]
    for year in (2016, 2022):
        assert not links.duplicated([f"{k}_{year}" for k in keys]).any()
    blocks = pd.read_csv("data/crosswalks/block_2016_2022.csv")
    linked = blocks[blocks["decision"] == "linked"]
    allowed = set(
        zip(
            linked["district_2016"],
            linked["block_2016"],
            linked["district_2022"],
            linked["block_2022"],
            strict=True,
        )
    )
    pairs = zip(
        links["district_2016"],
        links["block_2016"],
        links["district_2022"],
        links["block_2022"],
        strict=True,
    )
    assert set(pairs) <= allowed

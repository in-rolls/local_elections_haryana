"""Row-shape cases taken from real notifications.

Every one of these was a bug that produced plausible, wrong data rather than an
error, which is why they are pinned here.
"""

from parse import continuation_tail, is_continuation, office_kind, split_row


def test_office_detection():
    assert office_kind("Sarpanch") == "sarpanch"
    assert office_kind("ljiap") == "sarpanch"
    assert office_kind("Panch") == "panch"
    assert office_kind("iap") == "panch"
    assert office_kind("Name of Office") is None
    assert office_kind("") is None


def test_clean_seven_column_sarpanch_row():
    cells = ["1", "Ado Majra", "-", "Sarjant Singh", "Joginder Singh", "Sarpanch", "Unreserved"]
    assert split_row(cells) == (
        "sarpanch", "1", "Ado Majra", "", "Sarjant Singh", "Joginder Singh", "Unreserved", 1,
    )


def test_clean_seven_column_panch_row():
    cells = ["", "", "2", "*Sunita Rani", "Jagtar Singh", "Panch", "Scheduled Caste (Women)"]
    assert split_row(cells) == (
        "panch", None, None, "2", "*Sunita Rani", "Jagtar Singh",
        "Scheduled Caste (Women)", None,
    )


def test_multi_word_gp_name_survives_fragmented_columns():
    """Fragmented tables spread the GP name over cells; the ward dash is the
    only boundary between it and the sarpanch's name."""
    cells = ["6", "", "Bahlba", "Panri", "&", "", "Rajbir", "", "Ramphal", "ljiap", "efgyk"]
    kind, sr, gp, ward, name, father, res, _ = split_row(cells)
    assert (kind, sr, gp) == ("sarpanch", "6", "Bahlba Panri")
    assert name == "Rajbir"
    assert res == "efgyk"


def test_doubled_cells_do_not_become_the_gp_name():
    """Some notifications render each glyph run twice."""
    cells = ["7", "7", "Bedwa", "Bedwa", "----", "----", "Subash", "Subash",
             "Bhagwan", "Sarpanch", "Sarpanch", "Scheduled Caste"]
    kind, sr, gp, _, name, _, res, _col = split_row(cells)
    assert (kind, sr, gp, name) == ("sarpanch", "7", "Bedwa", "Subash")
    assert res == "Sarpanch Scheduled Caste"  # the doubled office cell is harmless


def test_header_row_is_not_a_seat():
    assert split_row(["Sr. No.", "Name of Gram Panchayat", "Ward No.", "Name",
                      "Father's Name", "Name of Office", "Reservation"]) is None


def test_continuation_row_is_all_reservation_words():
    assert is_continuation(["", "Other than", "Women"])
    assert is_continuation(["efgyk ds", "flok;"])
    assert not is_continuation(["1", "*Deepak", "Dharmbir Singh", "Panch", "Other than Women"])


def test_continuation_tail_ignores_a_wrapped_name():
    """The row carries the tail of a father's name AND the tail of the
    reservation. Taking only the reservation part is what keeps
    "Scheduled Caste" from being read as a non-woman seat."""
    assert continuation_tail(["Singh", "other than Women"]) == "other than Women"
    assert continuation_tail(["Kumar"]) == ""
    assert continuation_tail(["", "efgyk ds", "flok;"]) == "efgyk ds flok;"


def test_gp_column_is_reported_for_reattaching_a_wrapped_name():
    """The GP name wraps onto the next row at this same cell index."""
    cells = ["8", "", "", "", "Bhaini", "", "----", "", "", "Priyanka", "", "",
             "Naveen Duggle", "", "", "Sarpanch", "", "", "", "Scheduled Caste", ""]
    kind, sr, gp, _, name, _, res, gp_column = split_row(cells)
    assert (kind, sr, gp, name) == ("sarpanch", "8", "Bhaini", "Priyanka")
    assert gp_column == 4
    # the following row carries "Bhainro" at index 4 and "Women" at index 19
    nxt = [""] * 21
    nxt[4], nxt[19] = "Bhainro", "Women"
    assert continuation_tail(nxt) == "Women"
    assert nxt[gp_column] == "Bhainro"

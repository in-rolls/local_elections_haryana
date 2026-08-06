"""Every reservation string variant observed across the 2016 and 2022 corpora."""

import pytest

from normalize import is_vacant, label, normalize_reservation, strip_unopposed

# (raw cell, caste, woman_reserved, script)
CASES = [
    # 2022, English
    ("Women", "NONE", 1, "latin"),
    ("Woman", "NONE", 1, "latin"),
    ("Other than Women", "NONE", 0, "latin"),
    ("Other Than Woman", "NONE", 0, "latin"),
    ("Scheduled Caste Women", "SC", 1, "latin"),
    ("Schedule Caste Women", "SC", 1, "latin"),
    ("Scheduled Caste Other than Women", "SC", 0, "latin"),
    ("Schedule Caste Other than Woman", "SC", 0, "latin"),
    ("Backward Class 'A' Women", "BC_A", 1, "latin"),
    ("Backward Class ‘A’ Women", "BC_A", 1, "latin"),
    ("Backward Class 'A' Other Than Women", "BC_A", 0, "latin"),
    ("Backward Class A Women", "BC_A", 1, "latin"),
    # 2016, English - open seats are "Unreserved", and a bare caste name means
    # caste-reserved but not woman-reserved. "Schedulded" is a source typo.
    ("Unreserved", "NONE", 0, "latin"),
    ("Scheduled Caste", "SC", 0, "latin"),
    ("Schedulded Caste (Women)", "SC", 1, "latin"),
    ("Backward Class", "BC_A", 0, "latin"),
    # 2022, Kruti Dev legacy font encoding. "ds flok;" / "d¢ flok;" = "ke sivay"
    # (other than); its absence means the seat is woman-reserved.
    ("efgyk", "NONE", 1, "krutidev"),
    ("efgyk ds flok;", "NONE", 0, "krutidev"),
    ("efgyk d¢ flok;", "NONE", 0, "krutidev"),
    ("efgykvksa ds flok; vU;", "NONE", 0, "krutidev"),
    ("efgyk,a", "NONE", 1, "krutidev"),
    ("vuqlwfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqlwfpr tkfr efgyk ds flok;", "SC", 0, "krutidev"),
    ("vuqlwfpr tutkfr efgyk", "ST", 1, "krutidev"),
    ("fiNMk oxZ d efgyk", "BC_A", 1, "krutidev"),
    ("fiNM+k oxZ d efgyk ds flok;", "BC_A", 0, "krutidev"),
    ("fiNMs oxZ ¼,½ efgyk", "BC_A", 1, "krutidev"),
    # Typography damage in the source. A stray space inside "Caste" and doubled
    # characters in the Kruti Dev both silently downgraded SC seats to open ones
    # until the matchers were made tolerant.
    ("Scheduled Cast e Women", "SC", 1, "latin"),
    ("Scheduled Cast e other than Women", "SC", 0, "latin"),
    ("Backward Clas s 'A' Women", "BC_A", 1, "latin"),
    ("vuqllwfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqllwfpr tkfr efgyk ds flok;", "SC", 0, "krutidev"),
    # All nine Kruti Dev spellings of "anusuchit" found in the corpus, and the
    # English spellings of the caste prefixes. Every one of these was being read
    # as an unreserved seat before the matchers became pattern-based.
    ("vuqlqfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqlfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqwlwfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqlwqfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqfpr tkfr efgyk", "SC", 1, "krutidev"),
    ("vuqlwlfp tkfr efgyk ds flok;", "SC", 0, "krutidev"),
    ("vuqlwfpr tutkfr efgyk", "ST", 1, "krutidev"),
    ("fiNM+k oxZ ¼d½ efgyk", "BC_A", 1, "krutidev"),
    ("fiNMk oxZ ^d^ efgyk ds flok;", "BC_A", 0, "krutidev"),
    ("fiNM+k oxZ defgyk", "BC_A", 1, "krutidev"),
    ("Scheduled Cast Women", "SC", 1, "latin"),
    ("Schedule Cast other than Women", "SC", 0, "latin"),
    ("BackClass (A) Women", "BC_A", 1, "latin"),
    ("Back Class 'A' Women", "BC_A", 1, "latin"),
    ("Backward Class-A Other than Women", "BC_A", 0, "latin"),
    ("Backward Class (A) Women", "BC_A", 1, "latin"),
    # Kruti Dev damage seen only in the Hindi printings: characters doubled and
    # words split by a stray space ("fll ok;" for "flok;"), and labels truncated
    # mid-phrase to a trailing "ds" (के). Both dropped the "other than" marker
    # and turned open seats into woman-reserved ones.
    ("eefgyk ds fll ok;", "NONE", 0, "krutidev"),
    ("ljiap vuqlwfpr tkfr efgyk ds", "SC", 0, "krutidev"),
    ("ljiap fiNM+k oxZ d efgyk ds", "BC_A", 0, "krutidev"),
    ("vv uqlwfpr tkff rr efgyk ds", "SC", 0, "krutidev"),
    # "Seheduled" (c -> e) defeated every pattern anchored on "sch", which is
    # why the caste is keyed on the head noun instead. And the "+" diacritic in
    # the Kruti Dev floats, hiding the "fiNM" stem.
    ("Seheduled Caste Women", "SC", 1, "latin"),
    ("Seheduled Caste other than Women", "SC", 0, "latin"),
    ("fiN+Mk oxZ d efgyk", "BC_A", 1, "krutidev"),
    # Abbreviated categories: 188 "SC" and 117 "BC (A)" in the 2022 corpus.
    ("Sc Women", "SC", 1, "latin"),
    ("Sc Other Than Women", "SC", 0, "latin"),
    ("SC Women", "SC", 1, "latin"),
    ("BC (A) Women", "BC_A", 1, "latin"),
    ("BC (A) Other than Women", "BC_A", 0, "latin"),
    ("B.C. A Women", "BC_A", 1, "latin"),
]

NON_CATEGORIES = ["", None, "Sarpanch", "iap", "Independent", "5", "--"]


@pytest.mark.parametrize("raw,caste,woman,script", CASES)
def test_normalize(raw, caste, woman, script):
    assert normalize_reservation(raw) == (caste, woman, script)


@pytest.mark.parametrize("raw", NON_CATEGORIES)
def test_rejects_non_categories(raw):
    assert normalize_reservation(raw) is None


def test_wrapped_cell_is_whitespace_insensitive():
    """pdfplumber joins wrapped cells with a newline; that must not change the result."""
    assert normalize_reservation("Scheduled Caste\nOther than Women") == ("SC", 0, "latin")
    assert normalize_reservation("vuqlwfpr tkfr efgyk\nds flok;") == ("SC", 0, "krutidev")


def test_labels():
    assert label("NONE", 1) == "Woman"
    assert label("NONE", 0) == "Other than Woman"
    assert label("SC", 1) == "SC Woman"
    assert label("BC_A", 0) == "BC-A Other than Woman"


def test_unopposed_marker():
    assert strip_unopposed("*Sunita Rani") == ("Sunita Rani", True)
    assert strip_unopposed("Sunita Rani") == ("Sunita Rani", False)


def test_vacant():
    assert is_vacant("Rikt")
    assert is_vacant("fjDr in")
    assert not is_vacant("Sunita Rani")

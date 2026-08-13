"""Normalise the reservation column.

The gazette is not internally consistent: the same category appears as
"Other than Women" / "Other Than Women" / "Other than Woman", as
"Scheduled Caste" / "Schedule Caste", and with three different apostrophe
characters in "Backward Class 'A'". Hindi-typeset blocks use legacy Kruti Dev
font encoding, so the same strings arrive as mojibake such as
"vuqlwfpr tkfr efgyk ds flok;".

Both are mapped onto two orthogonal fields:
    caste_reservation in {SC, ST, BC_A, NONE}
    woman_reserved    in {0, 1}
"""

import re
import unicodedata

# Kruti Dev fragments. These are byte-for-byte deterministic, not OCR guesses.
#
# "anusuchit" is spelt nine different ways across the corpus - vuqlwfpr,
# vuqlqfpr, vuqlfpr, vuqwlwfpr, vuqlwlfp ... - so it is matched as "vuq
# anything, then jati" rather than by literal. The same goes for "pichhda varg",
# whose 'A' appears as d, ¼d½, ^d^, *d^ and ¼,½.
KD_SC = re.compile(r"vuq\S*\s+tkfr")  # anusuchit jati
KD_ST = re.compile(r"vuq\S*\s+tutkfr")  # anusuchit janjati
KD_SC_TIGHT = re.compile(r"vuq\w*tkfr")
KD_ST_TIGHT = re.compile(r"vuq\w*tutkfr")
KD_BC = "fiNM"  # pichhda/pichhde varg
KD_WOMAN = "efgyk"  # mahila (also efgykvksa, efgyk,a)
KD_OTHER_THAN = "flok;"  # sivay ("other than")

VACANT = ("rikt", "riet", "vacant", "fjDr", "[kkyh")


def _squash(s):
    """Collapse whitespace and fold the apostrophe variants together."""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("‘", "'").replace("’", "'").replace("‛", "'")
    return re.sub(r"\s+", " ", s).strip()


def _undouble(s):
    """Collapse runs of a repeated character to one.

    Some notifications are typeset with characters doubled - "vuqllwfpr" for
    "vuqlwfpr", and whole lines rendered as "EEXXTTRRAAOORRDDIINNAARRYY". None
    of the strings matched below contain a genuine doubled character, so
    collapsing runs is safe and makes the match survive it.
    """
    return re.sub(r"(.)\1+", r"\1", s)


def is_vacant(name):
    """True when nobody holds the seat - it went unfilled, or the election there
    was countermanded. Official "elected" totals exclude these."""
    n = _squash(name).lstrip("*").strip().lower()
    return not n or any(n.startswith(v.lower()) for v in VACANT)


def strip_unopposed(name):
    """A leading '*' marks a candidate elected unopposed/unanimously."""
    n = _squash(name)
    unopposed = n.startswith("*")
    return n.lstrip("*").strip(), unopposed


def normalize_reservation(raw):
    """Return (caste_reservation, woman_reserved, script) or None if unparseable.

    script is "latin" or "krutidev" - useful for auditing which blocks were
    read off the English table and which off the Hindi one.
    """
    s = _squash(raw)
    if not s:
        return None

    # Kruti Dev arrives with characters doubled ("eefgyk") and words split by
    # stray spaces ("fll ok;" for "flok;"), so test against a form with runs
    # collapsed and spaces removed as well as the plain one.
    # "+" is a diacritic mark that floats: "fiNM+k" is also typeset "fiN+Mk",
    # which hides the "fiNM" stem. Drop it for matching.
    kd = _undouble(s).replace("+", "")
    kd_tight = _undouble(re.sub(r"[\s+]", "", s))
    if KD_WOMAN in kd or KD_WOMAN in kd_tight:  # Hindi (Kruti Dev) row
        if KD_ST.search(kd) or KD_ST_TIGHT.search(kd_tight):
            caste = "ST"
        elif KD_SC.search(kd) or KD_SC_TIGHT.search(kd_tight):
            caste = "SC"
        elif KD_BC in kd or KD_BC in kd_tight:
            caste = "BC_A"
        else:
            caste = "NONE"
        # "ke sivay" = other than; its absence means the seat is woman-reserved.
        # A label truncated to a trailing "ds" (के) is still "ke sivay": that
        # word occurs nowhere else in this vocabulary.
        other_than = (KD_OTHER_THAN in kd or KD_OTHER_THAN in kd_tight
                      or kd.rstrip().endswith(" ds") or kd_tight.endswith("ds"))
        return caste, 0 if other_than else 1, "krutidev"

    # Words are broken by stray spaces in some printings - "Scheduled Cast e
    # Women" - so match against the space-stripped form.
    tight = re.sub(r"[^a-z]", "", s.lower())
    low = s.lower()

    # English is no more consistent: "Scheduled Caste" appears as "Scheduled
    # Cast", "Schedule Caste", "Schedulded Caste" and even "Seheduled Caste",
    # and "Backward Class 'A'" as "Back Class 'A'", "BackClass (A)", "Backward
    # Class-A" and "Backward Class A". Trying to match the qualifier means
    # chasing each new misspelling of it, so key on the head noun instead:
    # "cast" occurs only in "Scheduled Caste" and "clas" only in "Backward
    # Class", nowhere else in this vocabulary.
    # Some blocks abbreviate the category instead of spelling it: "SC Women",
    # "BC (A) Other than Women". 188 and 117 occurrences respectively.
    tokens = {re.sub(r"[^a-z]", "", t) for t in low.split()}

    # "sched" decides it even when the head noun is wrong: the 2016 gazette
    # prints "Scheduled Class" for several blocks, which is Scheduled Caste
    # misspelt, not Backward Class.
    if "trib" in tight or "st" in tokens:
        caste = "ST"
    elif "cast" in tight or "sched" in tight or "sc" in tokens:
        caste = "SC"
    elif "clas" in tight or "back" in tight or "bc" in tokens or "bca" in tokens:
        caste = "BC_A"
    else:
        caste = "NONE"

    # 2022 uses "Woman"/"Other than Woman" on every seat; 2016 uses
    # "Unreserved" for open seats and a bare caste name for reserved-but-open.
    # "unres" rather than "unreserved", for the same reason "cast" is used
    # above rather than "caste": Ambala prints "Unresreved" 79 times, and an
    # exact match returns None there - which does not blank a field, it
    # **deletes the row**, taking the elected member's name with it. One
    # panchayat, Barnala, lost four of its nine panches to that typo, and
    # nothing counted them as missing because a row never written leaves
    # nothing to count. No other term in this vocabulary begins "unres".
    if "wom" in tight:
        woman = 0 if "otherthan" in tight else 1
    elif "unres" in tight or "general" in low or caste != "NONE":
        woman = 0
    else:
        return None

    return caste, woman, "latin"


def label(caste, woman):
    """Canonical human-readable label."""
    prefix = {"SC": "SC", "ST": "ST", "BC_A": "BC-A", "NONE": ""}[caste]
    suffix = "Woman" if woman else "Other than Woman"
    return f"{prefix} {suffix}".strip()

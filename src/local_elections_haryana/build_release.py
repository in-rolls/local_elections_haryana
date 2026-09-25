# ruff: noqa: E501
"""Build the checksum-pinned Haryana 2000 historical release and its quarantines.

The historical source is an occurrence-level OCR review corpus, published apart
from the modern 2016/2022 seat CSVs; the two must not be appended or joined as
if they shared a row unit. Before this pipeline moved here from
in-rolls/local_elections, the same builder also bound those CSVs to the pooled
master; that modern table is the central repository's to publish, not this one's.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from local_elections.common.runlog import command

from local_elections_haryana.paths import ROOT

OBSERVATIONS = ROOT / (
    "data/release/observations/"
    "6ad3161f4b7c750e4446542bc4cf48dc5acd822c7897c4efeffdfbc56021da34/"
    "seat_rows.parquet"
)
# The 32 missing-heading exceptions from the 2026-09-14 release-readiness review
# (raw archive: early_cycles/release_readiness/20260914T032746928819Z/), kept
# tracked so the release rebuilds without downloading the raw archive.
MISSING_HEADINGS = ROOT / (
    "data/release/inputs/missing_headings_exceptions_"
    "f5bbbf70907e340aa17b9fa7225e1d26971f869b7c7a1a97278b0b5f8990d0df.json"
)
DEFAULT_OUT = ROOT / "data/release/historical"
BUILDER = Path(__file__).resolve()

EXPECTED = {
    OBSERVATIONS: "6e4aced101ffd3ded738830dc2a31075f66fa19cabb39637557b3803bcc72218",
    MISSING_HEADINGS: "f5bbbf70907e340aa17b9fa7225e1d26971f869b7c7a1a97278b0b5f8990d0df",
}

HISTORICAL_MEMBER_TIERS = {
    "gp_ward",
    "block_member",
    "district_member",
    "zp_member",
}

FLAG_CLASSIFICATION = {
    "anchor_corroboration_requires_source_review": "pending_review",
    "bilingual_occurrence_reconciliation_pending": "occurrence_status",
    "body_context_cross_source_reviewed_raw_preserved": "review_provenance",
    "body_serial_in_name": "unresolved_field_defect",
    "body_source_reviewed_raw_preserved": "review_provenance",
    "category_reconciled_by_aligned_column_pass": "resolved_validator_status",
    "category_recovered_by_anchor_audit": "resolved_validator_status",
    "category_source_reviewed_raw_preserved": "review_provenance",
    "category_unresolved": "unresolved_field_defect",
    "column_alignment_failed": "unresolved_field_defect",
    "column_category_unresolved": "unresolved_field_defect",
    "counting_stopped_no_declared_winner": "legitimate_source_status",
    "district_member_context_source_reviewed_raw_preserved": "review_provenance",
    "duplicate_seat_key_within_page": "unresolved_identity_defect",
    "gp_context_chain_cropped_page_margin": "review_provenance",
    "gp_fragment_context_source_reviewed_raw_preserved": "review_provenance",
    "gp_notification_context_source_reviewed": "review_provenance",
    "handwritten_category_amendment_requires_authority_review": "unresolved_authority",
    "incoming_body_context_unvalidated": "pending_review",
    "invalid_control_characters": "raw_source_status",
    "malformed_ward": "unresolved_field_defect",
    "mixed_notification_context_requires_review": "pending_review",
    "notification_number_source_unresolved": "unresolved_provenance",
    "office_category_corroborated_by_unique_name_anchor": "validator_corroboration",
    "office_source_reviewed_raw_preserved": "review_provenance",
    "office_spelling_normalized_raw_preserved": "resolved_validator_status",
    "office_unresolved": "unresolved_field_defect",
    "overlapping_source_observation_reconciliation_pending": "occurrence_status",
    "page_footnote_misattributed_as_winner": "resolved_nonperson_status",
    "printed_vacancy_source_reviewed_raw_preserved": "legitimate_source_status",
    "relation_source_reviewed_raw_preserved": "review_provenance",
    "samiti_body_context_requires_source_review": "unresolved_field_defect",
    "samiti_body_context_source_reviewed": "review_provenance",
    "samiti_or_empty_page_source_review_required": "pending_review",
    "samiti_printed_category_source_reviewed": "review_provenance",
    "samiti_section_source_reviewed_raw_preserved": "review_provenance",
    "samiti_vacancy_source_reviewed": "legitimate_source_status",
    "seat_identity_source_reviewed_raw_preserved": "review_provenance",
    "source_confirmed_nonseat_raw_preserved": "legitimate_nonseat_status",
    "tier_from_inventory_unvalidated": "pending_review",
    "unanchored_fragment": "unresolved_identity_defect",
    "ward_footnote_marker_unreadable": "raw_source_status",
    "ward_missing": "unresolved_field_defect",
    "winner_missing": "field_status_or_defect",
    "winner_not_person_source_reviewed_raw_preserved": "legitimate_nonperson_status",
    "winner_source_reviewed_raw_preserved": "review_provenance",
    "winner_status_semantics_unresolved": "unresolved_status",
}


def checksum(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_pins() -> None:
    """Refuse to build from a silently changed adjudication baseline."""
    for path, expected in EXPECTED.items():
        got = checksum(path)
        if got != expected:
            raise ValueError(f"Pinned Haryana input changed: {path}: {got}")


def split_flags(value: object) -> set[str]:
    """Read the semicolon-delimited quality annotation."""
    if not isinstance(value, str):
        return set()
    return {item for item in value.split(";") if item}


def read_historical() -> tuple[pd.DataFrame, set[tuple[str, int, int]]]:
    """Read the pinned reviewed occurrences and missing-heading exception keys."""
    frame = pq.read_table(OBSERVATIONS).to_pandas()
    payload = json.loads(MISSING_HEADINGS.read_bytes())
    rows = payload["rows"]
    if len(rows) != 32:
        raise ValueError("Missing-heading exception set no longer has 32 rows")
    keys = {
        (row["source_sha256"], row["source_page"], row["source_row_on_page"])
        for row in rows
    }
    if len(keys) != 32:
        raise ValueError("Missing-heading exception keys are not unique")
    return frame, keys


def classify_historical(
    frame: pd.DataFrame, missing_heading_keys: set[tuple[str, int, int]]
) -> pd.DataFrame:
    """Separate reviewed usable occurrences from exceptions and provisional OCR."""
    result = frame.copy()
    identity_reviewed = (
        result.source_samiti_review_status.eq("applied")
        | result.source_district_review_status.eq("applied")
        | result.source_identity_review_status.eq("applied")
    )
    nonseat = result.source_nonseat_review_status.eq("applied")
    keys = list(
        zip(
            result.source_sha256,
            result.source_page.astype(int),
            result.source_row_on_page.astype(int),
            strict=True,
        )
    )
    missing_heading = pd.Series(
        [key in missing_heading_keys for key in keys], index=result.index
    )
    reasons = []
    for index, row in result.iterrows():
        row_reasons = []
        if missing_heading.at[index]:
            row_reasons.append("original_samiti_heading_missing")
        if pd.isna(row.body_within_page):
            row_reasons.append("body_context_missing")
        if pd.isna(row.tier):
            row_reasons.append("tier_missing")
        if row.tier in HISTORICAL_MEMBER_TIERS and pd.isna(row.ward):
            row_reasons.append("member_ward_missing")
        if pd.isna(row.caste_reservation) or pd.isna(row.woman_reserved):
            row_reasons.append("reservation_category_missing_or_unverified")
        reasons.append(";".join(row_reasons))
    result["release_exception_reason"] = reasons
    result["release_reviewed_identity"] = identity_reviewed
    result["release_missing_heading_exception"] = missing_heading
    disposition = pd.Series("provisional_unvalidated", index=result.index)
    disposition.loc[nonseat] = "reviewed_nonseat"
    reviewed_seat = identity_reviewed & ~nonseat
    disposition.loc[reviewed_seat & result.release_exception_reason.ne("")] = (
        "reviewed_unresolved_quarantine"
    )
    disposition.loc[reviewed_seat & result.release_exception_reason.eq("")] = (
        "reviewed_release_occurrence"
    )
    result["release_disposition"] = disposition
    if set(result.loc[missing_heading, "release_disposition"]) != {
        "reviewed_unresolved_quarantine"
    }:
        raise ValueError("Missing-heading rows escaped historical quarantine")
    return result


def flag_reconciliation(frame: pd.DataFrame) -> dict[str, object]:
    """Count every historical annotation by release disposition."""
    counts: dict[str, Counter[str]] = {}
    observed = set()
    for _, row in frame.iterrows():
        for flag in split_flags(row.quality_flags):
            observed.add(flag)
            counts.setdefault(flag, Counter())[row.release_disposition] += 1
    unknown = observed - FLAG_CLASSIFICATION.keys()
    if unknown:
        raise ValueError(f"Unclassified Haryana quality flags: {sorted(unknown)}")
    return {
        "flags": [
            {
                "flag": flag,
                "classification": FLAG_CLASSIFICATION[flag],
                "rows": sum(counts[flag].values()),
                "release_dispositions": dict(sorted(counts[flag].items())),
                "interpretation": (
                    "The flag class describes the annotation; row release is governed by "
                    "source review and required-field completeness. Counts overlap."
                ),
            }
            for flag in sorted(observed)
        ]
    }


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    """Write a typed Parquet artifact without a pandas index."""
    pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path)


def file_record(path: Path, root: Path) -> dict[str, object]:
    """Describe a release artifact."""
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": checksum(path),
    }


def build(out: Path = DEFAULT_OUT) -> dict[str, object]:
    """Build the Haryana historical release bundle and return its receipt."""
    require_pins()
    out.mkdir(parents=True, exist_ok=True)
    historical, missing_heading_keys = read_historical()
    historical = classify_historical(historical, missing_heading_keys)

    historical_clean = historical[
        historical.release_disposition.eq("reviewed_release_occurrence")
    ].copy()
    historical_quarantine = historical[
        historical.release_disposition.eq("reviewed_unresolved_quarantine")
    ].copy()
    historical_provisional = historical[
        historical.release_disposition.isin(
            ["provisional_unvalidated", "reviewed_nonseat"]
        )
    ].copy()

    outputs = {
        "historical_reviewed_occurrences.parquet": historical_clean,
        "historical_quarantine.parquet": historical_quarantine,
        "historical_provisional_observations.parquet": historical_provisional,
    }
    for name, frame in outputs.items():
        write_parquet(frame, out / name)
        reread = pq.read_table(out / name)
        if reread.num_rows != len(frame):
            raise ValueError(f"Parquet row-count round-trip failed: {name}")
        try:
            pd.testing.assert_frame_equal(
                frame.reset_index(drop=True),
                reread.to_pandas(),
                check_dtype=False,
                check_exact=True,
                check_categorical=False,
            )
        except AssertionError as error:
            raise ValueError(f"Parquet value round-trip failed: {name}") from error

    if len(historical_clean) + len(historical_quarantine) + len(
        historical_provisional
    ) != len(historical):
        raise ValueError("Historical release row conservation failed")

    reconciliation = flag_reconciliation(historical)
    (out / "flag_reconciliation.json").write_text(
        json.dumps(reconciliation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    receipt = {
        "schema_version": 2,
        "status": "release_ready_with_explicit_quarantines",
        "row_units": {
            "historical": "one source-reviewed 2000 printed occurrence; not a unique-seat denominator",
        },
        "historical": {
            "input_observations": len(historical),
            "included_source_reviewed_occurrences": len(historical_clean),
            "reviewed_unresolved_quarantine": len(historical_quarantine),
            "missing_heading_quarantine": int(
                historical_quarantine.release_missing_heading_exception.sum()
            ),
            "provisional_or_nonseat_preserved_outside_release": len(
                historical_provisional
            ),
            "provisional_unvalidated": int(
                historical.release_disposition.eq("provisional_unvalidated").sum()
            ),
            "reviewed_nonseat": int(
                historical.release_disposition.eq("reviewed_nonseat").sum()
            ),
            "quarantine_reasons_overlapping": dict(
                Counter(
                    reason
                    for value in historical_quarantine.release_exception_reason
                    for reason in value.split(";")
                    if reason
                )
            ),
        },
        "inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": checksum(path)}
            for path in [OBSERVATIONS, MISSING_HEADINGS]
        ],
        "code_provenance": [
            {"path": str(BUILDER.relative_to(ROOT)), "sha256": checksum(BUILDER)}
        ],
        "policies": {
            "raw_literals": "Preserved in the historical OCR columns.",
            "missing_headings": "INDRI and BABAIN remain candidates/corroboration only; no heading assigned.",
            "historical_scope": "Publish only reviewed, field-complete seat occurrences; preserve automated observations separately.",
        },
        "release_ready": True,
        "limitations": [
            "The historical table is occurrence-level and cannot be appended to the modern 2016/2022 seat tables.",
            "Provisional historical OCR remains evidence, not released reservation assignments.",
        ],
    }
    (out / "release_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    dictionary = """# Haryana historical release data dictionary

| artifact | row unit | universe | missing policy | provenance |
|---|---|---|---|---|
| `historical_reviewed_occurrences.parquet` | printed occurrence | source-reviewed 2000 seat occurrences with body, tier, ward where required, and category | no imputation | frozen review snapshot and source-review hashes |
| `historical_quarantine.parquet` | printed occurrence | reviewed occurrences missing an essential release field | preserve null and reason | frozen review snapshot; includes exactly 32 missing-heading rows |
| `historical_provisional_observations.parquet` | OCR occurrence | unvalidated OCR and reviewed non-seat records | outside release universe | frozen review snapshot |

Historical raw OCR fields remain in every partition. Null historical cells are
unknown, not zero.
"""
    (out / "data_dictionary.md").write_text(dictionary, encoding="utf-8")
    ledger = """# Haryana historical release recode ledger

| derived field | source | definition | count check | reason |
|---|---|---|---|---|
| `release_disposition` | review status and required fields | reviewed release, reviewed quarantine, reviewed non-seat, or provisional | four-way row conservation | keep occurrence-level validation claims bounded |

No source literal, reservation category, winner, ward, or body heading is recoded.
"""
    (out / "recode_ledger.md").write_text(ledger, encoding="utf-8")

    names = sorted(
        path.name
        for path in out.iterdir()
        if path.name not in {"SHA256SUMS", "artifact_manifest.json"}
    )
    records = [file_record(out / name, out) for name in names]
    (out / "artifact_manifest.json").write_text(
        json.dumps({"schema_version": 1, "files": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    names = sorted(path.name for path in out.iterdir() if path.name != "SHA256SUMS")
    (out / "SHA256SUMS").write_text(
        "".join(f"{checksum(out / name)}  {name}\n" for name in names),
        encoding="ascii",
    )
    return receipt


@command("build", state="Haryana", vintage="release")
def main() -> None:
    """Build the Haryana historical release."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.out), sort_keys=True))


if __name__ == "__main__":
    main()

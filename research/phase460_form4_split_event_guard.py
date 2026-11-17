"""Classify explicit Form 4 split-filing remarks without auto-linking accessions."""
from __future__ import annotations

import re


def classify_split_remarks(remarks: str | None) -> dict:
    text = " ".join((remarks or "").split())
    lower = text.lower()
    ordinal_pair = bool(re.search(r"\b(first|second) of two forms?\s*4\b", lower))
    explicit_event = "same event" in lower or "one consolidated filing" in lower

    if not ordinal_pair or not explicit_event:
        return {
            "explicit_split_candidate": False,
            "split_reason": None,
            "automatic_cross_accession_merge": False,
            "accession_count_is_event_count": False,
            "disposition": "no_explicit_same_event_split_evidence",
        }

    if "more than 10 reporting persons" in lower or "maximum of 10 reporting persons" in lower:
        reason = "reporting_person_limit"
    elif "more than 30 rows" in lower and "single form 4" in lower:
        reason = "transaction_row_limit"
    else:
        reason = "explicit_split_reason_unclassified"

    return {
        "explicit_split_candidate": True,
        "split_reason": reason,
        "automatic_cross_accession_merge": False,
        "accession_count_is_event_count": False,
        "disposition": "candidate_same_disclosure_event_requires_exact_identity_join",
        "required_join_keys": [
            "issuer_cik",
            "period_of_report_or_transaction_date",
            "reporting_owner_cik_set_or_verified_designated_filer",
            "explicit_same_event_remarks",
            "accession_acceptance_time",
        ],
        "do_not_deduplicate_transaction_rows_without_line_level_evidence": True,
    }

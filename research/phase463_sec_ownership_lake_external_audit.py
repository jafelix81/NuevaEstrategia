"""Phase 463: conservative gates for an external SEC ownership lake.

This module does not download data or create signals. It encodes the data-quality,
point-in-time, identity and transaction-semantics checks required before the
third-party lake can be used as a secondary parser/crosswalk audit.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def quarterly_bulk_available_at(filing_date: str) -> datetime:
    """Conservative availability: end of FILING_DATE in New York, converted to UTC."""
    day = date.fromisoformat(filing_date)
    local_end = datetime.combine(day, time(23, 59, 59, 999000), tzinfo=NEW_YORK)
    return local_end.astimezone(timezone.utc)


def available_as_of(available_at: datetime, decision_at: datetime) -> bool:
    """A disclosure is usable only after its conservative/public availability time."""
    if available_at.tzinfo is None or decision_at.tzinfo is None:
        raise ValueError("availability and decision timestamps must be timezone-aware")
    return available_at <= decision_at


def owner_attribution_status(owner_count: int, explicit_line_owner_link: bool = False) -> str:
    """A filing-level owner list is not a transaction-to-owner key."""
    if owner_count < 1:
        return "invalid_no_reporting_owner"
    if owner_count == 1:
        return "single_owner_filing_grain"
    if explicit_line_owner_link:
        return "explicit_line_owner_link"
    return "multi_owner_quarantine"


def classify_form4_purchase(
    row_kind: str,
    transaction_code: str | None,
    acquired_disposed: str | None,
    footnote_status: str = "unknown",
) -> str:
    """Do not equate SEC code P with a confirmed exchange/open-market execution."""
    if row_kind != "nonderiv":
        return "derivative_or_non_common_equity_quarantine"
    if (transaction_code or "").strip().upper() != "P":
        return "not_general_purchase_code"
    if (acquired_disposed or "").strip().upper() != "A":
        return "not_acquired"
    if footnote_status == "private_purchase":
        return "private_purchase_excluded"
    if footnote_status != "open_market_confirmed":
        return "market_vs_private_unresolved"
    return "open_market_purchase_candidate"


def issuer_ticker_identity_status(
    issuer_ticker: str | None,
    issuer_cik_verified: bool,
    security_class_verified: bool,
    effective_dated: bool,
) -> str:
    """Filer-entered ticker text is a label, not a security-master key."""
    if not issuer_ticker or not issuer_ticker.strip():
        return "unresolved_no_ticker"
    if not issuer_cik_verified or not security_class_verified or not effective_dated:
        return "provisional_filer_text_only"
    return "verified_effective_dated_security_identity"


def cusip_ticker_mapping_covers_date(
    from_date: str | None,
    to_date: str | None,
    as_of_date: str,
    never_changed_security_verified: bool = False,
) -> bool:
    """Reject undated CUSIP/ticker pairs unless permanence is independently proven."""
    if from_date is None and to_date is None:
        return never_changed_security_verified
    if from_date is not None and as_of_date < from_date:
        return False
    if to_date is not None and as_of_date > to_date:
        return False
    return True


def snapshot_is_pinned(
    generated_at: str | None,
    source_commit: str | None,
    snapshot_sha256: str | None,
    table_file_hashes: dict[str, str] | None,
) -> bool:
    """Require an immutable dataset vintage and per-file integrity manifest."""
    if not generated_at or not source_commit or not snapshot_sha256 or not table_file_hashes:
        return False
    if not SHA256.fullmatch(snapshot_sha256.lower()):
        return False
    if not table_file_hashes:
        return False
    return all(
        bool(name) and bool(digest) and SHA256.fullmatch(digest.lower())
        for name, digest in table_file_hashes.items()
    )


def bulk_timestamp_intraday_eligible() -> bool:
    """Date-only quarterly filing dates cannot support same-day intraday decisions."""
    return False


def thirteen_f_is_trade_flow() -> bool:
    """13F is a lagged holdings snapshot, not a transaction tape."""
    return False

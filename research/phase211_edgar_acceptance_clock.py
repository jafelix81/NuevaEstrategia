#!/usr/bin/env python3
"""Parse EDGAR acceptance time and map it to a conservative next-session clock."""
from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable

ET = ZoneInfo("America/New_York")


def parse_edgar_acceptance(header_text: str) -> dict:
    """Extract accession, submission form and ACCEPTANCE-DATETIME from SGML header.

    EDGAR's header timestamp is interpreted in Eastern Time. The parser does not
    infer public dissemination to the second; callers should use a conservative
    trading clock such as the first regular-session open strictly after acceptance.
    """
    accepted = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", header_text, re.I)
    if not accepted:
        raise ValueError("ACCEPTANCE-DATETIME not found")
    raw = accepted.group(1)
    naive = datetime.strptime(raw, "%Y%m%d%H%M%S")
    accepted_at = naive.replace(tzinfo=ET)

    accession = re.search(r"ACCESSION NUMBER:\s*([0-9-]{18,25})", header_text, re.I)
    form = re.search(r"CONFORMED SUBMISSION TYPE:\s*([A-Z0-9/.-]+)", header_text, re.I)
    return {
        "accession": accession.group(1) if accession else None,
        "form": form.group(1).upper() if form else None,
        "accepted_at_et": accepted_at.isoformat(),
        "accepted_at": accepted_at,
    }


def first_session_open_after(accepted_at: datetime, session_opens: Iterable[datetime]) -> datetime:
    """Return the earliest supplied regular-session open strictly after acceptance."""
    if accepted_at.tzinfo is None:
        raise ValueError("accepted_at must be timezone-aware")
    candidates = []
    for opening in session_opens:
        if opening.tzinfo is None:
            raise ValueError("all session opens must be timezone-aware")
        if opening > accepted_at:
            candidates.append(opening)
    if not candidates:
        raise ValueError("no session open after acceptance in supplied calendar")
    return min(candidates)


def conservative_event_clock(header_text: str, session_opens: Iterable[datetime]) -> dict:
    parsed = parse_edgar_acceptance(header_text)
    next_open = first_session_open_after(parsed["accepted_at"], session_opens)
    return {
        "accession": parsed["accession"],
        "form": parsed["form"],
        "accepted_at_et": parsed["accepted_at"].isoformat(),
        "first_session_open_after_acceptance_et": next_open.isoformat(),
    }

"""Phase 254: issuer/accession-scoped SEC XBRL class join and prior-vintage gate."""
from datetime import date, datetime, timezone

from research.phase253_form144_xbrl_registered_security_crosswalk_audit import norm


def normalize_cik(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    normalized = digits.lstrip("0")
    return normalized or None


def parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def parse_aware_datetime(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def select_prior_vintage_scoped(filings, issuer_cik, event_filing_date):
    """Select the latest strictly prior filing for one issuer; amendments remain vintages."""
    expected_cik = normalize_cik(issuer_cik)
    event_date = parse_date(event_filing_date)
    if not expected_cik:
        return {"status": "MISSING_EXPECTED_ISSUER_CIK"}
    if not event_date:
        return {"status": "INVALID_EVENT_FILING_DATE"}

    issuer_rows = []
    eligible = []
    for filing in filings:
        cik = normalize_cik(filing.get("issuer_cik"))
        if cik != expected_cik:
            continue
        issuer_rows.append(filing)
        filed = parse_date(filing.get("filing_date"))
        accession = str(filing.get("accession") or "").strip()
        if filed is None or not accession or filed >= event_date:
            continue
        eligible.append((filed, filing))

    if not issuer_rows:
        return {"status": "NO_FILINGS_FOR_ISSUER", "issuer_cik": expected_cik}
    if not eligible:
        return {"status": "NO_STRICTLY_PRIOR_VINTAGE", "issuer_cik": expected_cik}

    latest_date = max(item[0] for item in eligible)
    latest = [filing for filed, filing in eligible if filed == latest_date]
    if len(latest) == 1:
        chosen = latest[0]
        return {
            "status": "SELECTED_STRICTLY_PRIOR_ISSUER_VINTAGE",
            "issuer_cik": expected_cik,
            "accession": str(chosen["accession"]).strip(),
            "filing_date": latest_date.isoformat(),
            "form": chosen.get("form"),
            "acceptance_order_used": False,
        }

    ordered = []
    for filing in latest:
        accepted = parse_aware_datetime(filing.get("acceptance_datetime"))
        if accepted is None or accepted.date() != latest_date:
            return {
                "status": "SAME_DAY_VINTAGE_TIE_UNKNOWN",
                "issuer_cik": expected_cik,
                "filing_date": latest_date.isoformat(),
            }
        ordered.append((accepted, filing))

    ordered.sort(key=lambda item: item[0])
    if ordered[-1][0] == ordered[-2][0]:
        return {
            "status": "SAME_DAY_VINTAGE_TIE_UNKNOWN",
            "issuer_cik": expected_cik,
            "filing_date": latest_date.isoformat(),
        }
    chosen = ordered[-1][1]
    return {
        "status": "SELECTED_STRICTLY_PRIOR_ISSUER_VINTAGE",
        "issuer_cik": expected_cik,
        "accession": str(chosen["accession"]).strip(),
        "filing_date": latest_date.isoformat(),
        "form": chosen.get("form"),
        "acceptance_order_used": True,
    }


def resolve_form144_class_scoped(security_label, contexts, selected_vintage):
    """Resolve only contexts belonging to the selected issuer/accession/date vintage."""
    if selected_vintage.get("status") != "SELECTED_STRICTLY_PRIOR_ISSUER_VINTAGE":
        return {"status": "NO_ADMITTED_PRIOR_VINTAGE"}
    expected_cik = normalize_cik(selected_vintage.get("issuer_cik"))
    expected_accession = str(selected_vintage.get("accession") or "").strip()
    expected_date = parse_date(selected_vintage.get("filing_date"))
    if not expected_cik or not expected_accession or expected_date is None:
        return {"status": "INVALID_SELECTED_VINTAGE_SCOPE"}
    if not contexts:
        return {"status": "NO_CONTEXTS"}

    # Reject the whole input if the caller accidentally mixed issuers or filing vintages.
    for context in contexts:
        cik = normalize_cik(context.get("issuer_cik"))
        accession = str(context.get("accession") or "").strip()
        filed = parse_date(context.get("filing_date"))
        if not cik:
            return {"status": "CONTEXT_ISSUER_CIK_MISSING"}
        if cik != expected_cik:
            return {"status": "CONTEXT_ISSUER_SCOPE_MISMATCH"}
        if not accession:
            return {"status": "CONTEXT_ACCESSION_MISSING"}
        if accession != expected_accession:
            return {"status": "CONTEXT_ACCESSION_MISMATCH"}
        if filed is None:
            return {"status": "CONTEXT_FILING_DATE_MISSING"}
        if filed != expected_date:
            return {"status": "CONTEXT_FILING_DATE_MISMATCH"}

    target = norm(security_label)
    matches = [
        context for context in contexts
        if context.get("status") == "VALID_NORMALIZED_CONTEXT"
        and norm(context.get("security_title")) == target
    ]
    if not matches:
        return {"status": "NO_EXACT_CLASS_TITLE_MATCH"}

    # A listing axis is not a class axis. Require explicit class-axis evidence.
    if any(
        context.get("class_scope") != "EXACT_CLASS_MEMBER"
        or not context.get("class_axis")
        or not context.get("class_member")
        for context in matches
    ):
        return {"status": "CLASS_SCOPE_UNKNOWN"}

    if any(
        context.get("symbol_status") != "HAS_TRADING_SYMBOL"
        or not str(context.get("symbol") or "").strip()
        for context in matches
    ):
        return {"status": "TRADING_SYMBOL_UNKNOWN"}

    classes = {
        (context.get("class_axis"), context.get("class_member"))
        for context in matches
    }
    symbols = {str(context["symbol"]).strip().upper() for context in matches}
    if len(classes) != 1 or len(symbols) != 1:
        return {
            "status": "AMBIGUOUS_CLASS_OR_SYMBOL",
            "class_members": sorted((str(a), str(m)) for a, m in classes),
            "symbols": sorted(symbols),
        }

    class_axis, class_member = next(iter(classes))
    symbol = next(iter(symbols))
    listings = {
        (
            context.get("listing_axis"),
            context.get("listing_member"),
            context.get("exchange"),
        )
        for context in matches
    }
    result = {
        "issuer_cik": expected_cik,
        "accession": expected_accession,
        "filing_date": expected_date.isoformat(),
        "class_axis": class_axis,
        "class_member": class_member,
        "symbol": symbol,
        "context_count": len(matches),
    }
    if len(listings) > 1:
        result["status"] = "MULTIPLE_LISTINGS_SAME_CLASS"
        result["listings"] = [
            {"axis": axis, "member": member, "exchange": exchange}
            for axis, member, exchange in sorted(listings, key=str)
        ]
    else:
        axis, member, exchange = next(iter(listings))
        if axis or member or exchange:
            result["status"] = "UNIQUE_CLASS_LISTING"
            result["listing"] = {"axis": axis, "member": member, "exchange": exchange}
        else:
            result["status"] = "UNIQUE_CLASS_SYMBOL_LISTING_UNKNOWN"
    return result

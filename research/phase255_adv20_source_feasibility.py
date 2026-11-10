"""Phase 255: point-in-time ADV20 dollar-volume contract for Form 144 events."""
from datetime import date
from decimal import Decimal, InvalidOperation


def _date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _fmt(value):
    return format(value, "f")


def daily_dollar_volume(vwap, volume, price_basis, volume_basis):
    """Compute reported notional only when VWAP and volume share one valid basis."""
    allowed = {"raw", "split_adjusted"}
    if price_basis not in allowed or volume_basis not in allowed:
        return {"status": "UNSUPPORTED_ADJUSTMENT_BASIS"}
    if price_basis != volume_basis:
        return {"status": "ADJUSTMENT_BASIS_MISMATCH"}
    p, v = _decimal(vwap), _decimal(volume)
    if p is None or v is None:
        return {"status": "MISSING_OR_INVALID_VWAP_VOLUME"}
    if p <= 0 or v <= 0:
        return {"status": "NONPOSITIVE_VWAP_OR_VOLUME"}
    return {
        "status": "VALID",
        "price_basis": price_basis,
        "volume_basis": volume_basis,
        "dollar_volume_usd": _fmt(p * v),
    }


def compute_adv20(bars, expected_sessions, event_filing_date):
    """Mean VWAP×volume over exactly 20 supplied XNYS sessions strictly before event date.

    The caller must supply the authoritative 20-session XNYS calendar window. Missing
    bars are UNKNOWN, never zero-filled. No close×volume fallback is permitted.
    """
    event_date = _date(event_filing_date)
    if event_date is None:
        return {"status": "INVALID_EVENT_FILING_DATE"}
    if not isinstance(expected_sessions, (list, tuple)) or len(expected_sessions) != 20:
        return {"status": "INVALID_EXPECTED_SESSION_COUNT"}
    expected = [_date(x) for x in expected_sessions]
    if any(x is None for x in expected):
        return {"status": "INVALID_EXPECTED_SESSION_DATE"}
    if len(set(expected)) != 20:
        return {"status": "DUPLICATE_EXPECTED_SESSION"}
    if expected != sorted(expected):
        return {"status": "UNSORTED_EXPECTED_SESSIONS"}
    if any(x >= event_date for x in expected):
        return {"status": "LOOKAHEAD_EXPECTED_SESSION_REJECTED"}

    if not isinstance(bars, (list, tuple)) or len(bars) != 20:
        return {
            "status": "MISSING_OR_EXTRA_SESSION",
            "expected_count": 20,
            "observed_count": len(bars) if isinstance(bars, (list, tuple)) else None,
        }

    dated = []
    for bar in bars:
        if not isinstance(bar, dict):
            return {"status": "INVALID_BAR_RECORD"}
        session = _date(bar.get("date"))
        if session is None:
            return {"status": "INVALID_BAR_DATE"}
        if session >= event_date:
            return {"status": "LOOKAHEAD_SESSION_REJECTED"}
        dated.append((session, bar))
    observed = [x[0] for x in dated]
    if len(set(observed)) != 20:
        return {"status": "DUPLICATE_SESSION"}
    if set(observed) != set(expected):
        return {"status": "MISSING_OR_EXTRA_SESSION"}

    values = []
    bases = set()
    for session, bar in sorted(dated, key=lambda x: x[0]):
        if bar.get("status", "VALID") != "VALID":
            return {"status": "INVALID_OR_MISSING_BAR", "date": session.isoformat()}
        result = daily_dollar_volume(
            bar.get("vwap"),
            bar.get("volume"),
            bar.get("price_basis"),
            bar.get("volume_basis"),
        )
        if result["status"] != "VALID":
            return {"status": result["status"], "date": session.isoformat()}
        bases.add(result["price_basis"])
        values.append(Decimal(result["dollar_volume_usd"]))

    if len(bases) != 1:
        return {"status": "MIXED_SESSION_ADJUSTMENT_BASIS"}
    adv = sum(values, Decimal("0")) / Decimal("20")
    return {
        "status": "VALID_ADV20",
        "adv20_usd": _fmt(adv),
        "session_count": 20,
        "first_session": min(expected).isoformat(),
        "last_session": max(expected).isoformat(),
        "adjustment_basis": next(iter(bases)),
        "dollar_volume_method": "VWAP_TIMES_MATCHING_BASIS_VOLUME",
    }


def proposed_notional_to_adv20_days(proposed_notional, adv20_result):
    """Descriptive proposed-notional / ADV20 ratio; not executed-sale pressure."""
    if not isinstance(adv20_result, dict) or adv20_result.get("status") != "VALID_ADV20":
        return {"status": "ADV20_NOT_AVAILABLE"}
    notional = _decimal(proposed_notional)
    adv = _decimal(adv20_result.get("adv20_usd"))
    if notional is None or adv is None or notional <= 0 or adv <= 0:
        return {"status": "NONPOSITIVE_OR_INVALID_NOTIONAL"}
    return {
        "status": "VALID_PROPOSED_NOTIONAL_ADV20_DAYS",
        "days": _fmt(notional / adv),
        "interpretation": "PROPOSED_NOTIONAL_RELATIVE_TO_HISTORICAL_DOLLAR_TURNOVER_NOT_EXECUTED_SALE",
    }

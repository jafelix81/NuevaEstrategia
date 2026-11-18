"""Strict post-close FINRA flow label construction.

This module builds executable, first-seen labels only. It does not calculate
signals, optimize features, or run a backtest. Historical rows without an
observed first-seen timestamp are rejected rather than assigned a guessed
publication time.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from math import isfinite
import re
from typing import Any, Iterable, Mapping

_ALLOWED_PRICE_BASES = {
    "split_adjusted_ohlc",
    "total_return_adjusted_ohlc",
}
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field}_not_string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _positive_finite(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_not_numeric") from exc
    if not isfinite(number) or number <= 0:
        raise ValueError(f"{field}_not_positive_finite")
    return number


def _normalize_sessions(
    sessions: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[date, int]]:
    normalized: list[dict[str, Any]] = []
    seen: set[date] = set()
    for raw in sessions:
        d = _parse_date(raw.get("session_date"), "session_date")
        if d in seen:
            raise ValueError(f"duplicate_session_date:{d.isoformat()}")
        seen.add(d)
        opened = _parse_utc(raw.get("open_utc"), "open_utc")
        closed = _parse_utc(raw.get("close_utc"), "close_utc")
        if opened >= closed:
            raise ValueError(f"invalid_session_clock:{d.isoformat()}")
        normalized.append(
            {"session_date": d, "open_utc": opened, "close_utc": closed}
        )
    normalized.sort(key=lambda row: row["session_date"])
    for previous, current in zip(normalized, normalized[1:]):
        if current["open_utc"] <= previous["open_utc"]:
            raise ValueError("session_open_times_not_strictly_increasing")
        if current["open_utc"] <= previous["close_utc"]:
            raise ValueError("session_clocks_overlap")
    return normalized, {
        row["session_date"]: i for i, row in enumerate(normalized)
    }


def _normalize_prices(
    price_bars: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, date], dict[str, Any]]:
    prices: dict[tuple[str, date], dict[str, Any]] = {}
    for raw in price_bars:
        symbol = str(raw.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("price_symbol_missing")
        d = _parse_date(raw.get("session_date"), "price_session_date")
        key = (symbol, d)
        if key in prices:
            raise ValueError(f"duplicate_price_bar:{symbol}:{d.isoformat()}")
        basis = str(raw.get("price_basis", "")).strip()
        if basis not in _ALLOWED_PRICE_BASES:
            raise ValueError(f"unsupported_price_basis:{basis or 'missing'}")
        prices[key] = {
            "open": _positive_finite(raw.get("open"), "open"),
            "close": _positive_finite(raw.get("close"), "close"),
            "price_basis": basis,
        }
    return prices


def build_executable_labels(
    flow_observations: Iterable[Mapping[str, Any]],
    price_bars: Iterable[Mapping[str, Any]],
    sessions: Iterable[Mapping[str, Any]],
    horizons: Iterable[int] = (5, 10, 20),
) -> dict[str, Any]:
    """Create first-seen, post-close labels using the next executable session.

    Each flow observation must represent the first-seen version of one
    symbol/trade-date row from a raw FINRA daily file. Required provenance:
    poll_start_utc, first_seen_utc, poll_end_utc, HTTP 200, SHA-256, row_count,
    schema_version, and observation_kind='first_seen'.

    first_seen_utc is the local first-receipt time (a conservative upper bound
    on public availability), not a claim about the exact instant FINRA first
    published the file. Entry is the open of the first supplied XNYS session
    whose open timestamp is strictly later than first_seen_utc. Horizon H
    exits at the close of the H-th session counting the entry session as 1.

    Only split-adjusted or total-return-adjusted OHLC inputs are accepted.
    Split-adjusted price returns omit cash dividends and are not, by
    themselves, a final economic portfolio test.
    """
    horizon_input = tuple(horizons)
    if (
        not horizon_input
        or any(isinstance(h, bool) or not isinstance(h, int) for h in horizon_input)
    ):
        raise ValueError("horizons_must_be_positive_integers")
    horizon_values = tuple(sorted(set(horizon_input)))
    if any(h <= 0 for h in horizon_values):
        raise ValueError("horizons_must_be_positive_integers")

    session_rows, session_index = _normalize_sessions(sessions)
    price_map = _normalize_prices(price_bars)
    observations = list(flow_observations)

    keys = []
    for raw in observations:
        try:
            symbol = str(raw.get("symbol", "")).strip().upper()
            trade_date = _parse_date(raw.get("trade_date"), "trade_date")
            keys.append((symbol, trade_date))
        except ValueError:
            keys.append(("", date.min))
    key_counts = Counter(keys)

    labels: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    horizon_counts = {str(h): 0 for h in horizon_values}

    for raw in observations:
        symbol = str(raw.get("symbol", "")).strip().upper()
        try:
            if not symbol:
                raise ValueError("symbol_missing")
            trade_date = _parse_date(raw.get("trade_date"), "trade_date")
            key = (symbol, trade_date)
            if key_counts[key] > 1:
                raise ValueError("duplicate_first_seen_symbol_trade_date")
            if raw.get("observation_kind") != "first_seen":
                raise ValueError("observation_not_first_seen")
            try:
                status_value = float(raw.get("http_status"))
            except (TypeError, ValueError) as exc:
                raise ValueError("http_status_invalid") from exc
            if not isfinite(status_value) or status_value != 200:
                raise ValueError("http_status_not_200")
            digest = str(raw.get("raw_sha256", "")).strip()
            if not _SHA256_RE.fullmatch(digest):
                raise ValueError("raw_sha256_invalid")
            try:
                row_count_value = float(raw.get("row_count"))
            except (TypeError, ValueError) as exc:
                raise ValueError("row_count_invalid") from exc
            if (
                not isfinite(row_count_value)
                or not row_count_value.is_integer()
            ):
                raise ValueError("row_count_invalid")
            row_count = int(row_count_value)
            if row_count <= 0:
                raise ValueError("row_count_not_positive")
            if not str(raw.get("schema_version", "")).strip():
                raise ValueError("schema_version_missing")

            poll_start = _parse_utc(raw.get("poll_start_utc"), "poll_start_utc")
            first_seen = _parse_utc(raw.get("first_seen_utc"), "first_seen_utc")
            poll_end = _parse_utc(raw.get("poll_end_utc"), "poll_end_utc")
            if poll_end < poll_start:
                raise ValueError("poll_end_precedes_poll_start")
            if first_seen < poll_start:
                raise ValueError("first_seen_precedes_poll_start")
            if first_seen > poll_end:
                raise ValueError("first_seen_follows_poll_end")
            if trade_date not in session_index:
                raise ValueError("trade_date_not_in_session_calendar")
            trade_idx = session_index[trade_date]
            trade_close = session_rows[trade_idx]["close_utc"]
            if first_seen <= trade_close:
                raise ValueError("first_seen_not_strictly_post_close")

            entry_idx = next(
                (
                    i
                    for i, session in enumerate(session_rows)
                    if session["open_utc"] > first_seen
                ),
                None,
            )
            if entry_idx is None:
                raise ValueError("no_future_executable_session")
            if entry_idx <= trade_idx:
                raise ValueError("entry_not_after_flow_trade_session")

            entry_session = session_rows[entry_idx]
            entry_date = entry_session["session_date"]
            entry_bar = price_map.get((symbol, entry_date))
            if entry_bar is None:
                raise ValueError("entry_price_missing")
            entry_open = entry_bar["open"]
            entry_basis = entry_bar["price_basis"]

            row: dict[str, Any] = {
                "symbol": symbol,
                "trade_date": trade_date.isoformat(),
                "poll_start_utc": poll_start.isoformat().replace("+00:00", "Z"),
                "first_seen_utc": first_seen.isoformat().replace("+00:00", "Z"),
                "poll_end_utc": poll_end.isoformat().replace("+00:00", "Z"),
                "signal_age_sessions": entry_idx - trade_idx,
                "raw_sha256": digest.lower(),
                "row_count": row_count,
                "schema_version": str(raw["schema_version"]).strip(),
                "entry_date": entry_date.isoformat(),
                "entry_open_utc": entry_session["open_utc"].isoformat().replace(
                    "+00:00", "Z"
                ),
                "entry_open": entry_open,
                "price_basis": entry_basis,
            }

            valid_horizons = 0
            per_horizon_status: dict[str, str] = {}
            for horizon in horizon_values:
                exit_idx = entry_idx + horizon - 1
                h_key = str(horizon)
                if exit_idx >= len(session_rows):
                    per_horizon_status[h_key] = "insufficient_future_sessions"
                    row[f"fwd_{horizon}"] = None
                    continue
                path = session_rows[entry_idx : exit_idx + 1]
                path_bars = [
                    price_map.get((symbol, session["session_date"]))
                    for session in path
                ]
                if any(bar is None for bar in path_bars):
                    per_horizon_status[h_key] = "incomplete_price_path"
                    row[f"fwd_{horizon}"] = None
                    continue
                if any(bar["price_basis"] != entry_basis for bar in path_bars):
                    per_horizon_status[h_key] = "price_basis_changed"
                    row[f"fwd_{horizon}"] = None
                    continue
                exit_session = session_rows[exit_idx]
                exit_close = path_bars[-1]["close"]
                if exit_session["close_utc"] <= first_seen:
                    per_horizon_status[h_key] = "exit_not_after_first_seen"
                    row[f"fwd_{horizon}"] = None
                    continue
                row[f"fwd_{horizon}"] = exit_close / entry_open - 1.0
                row[f"exit_date_{horizon}"] = exit_session[
                    "session_date"
                ].isoformat()
                row[f"exit_close_utc_{horizon}"] = exit_session[
                    "close_utc"
                ].isoformat().replace("+00:00", "Z")
                row[f"exit_close_{horizon}"] = exit_close
                per_horizon_status[h_key] = "eligible"
                horizon_counts[h_key] += 1
                valid_horizons += 1

            row["horizon_status"] = per_horizon_status
            if valid_horizons:
                labels.append(row)
            else:
                rejections.append(
                    {
                        "symbol": symbol,
                        "trade_date": trade_date.isoformat(),
                        "reason": "no_horizon_has_complete_executable_prices",
                        "horizon_status": per_horizon_status,
                    }
                )
        except ValueError as exc:
            rejections.append(
                {
                    "symbol": symbol or None,
                    "trade_date": raw.get("trade_date"),
                    "reason": str(exc),
                }
            )

    return {
        "labels": labels,
        "rejections": rejections,
        "summary": {
            "input_events": len(observations),
            "eligible_events": len(labels),
            "rejected_events": len(rejections),
            "horizon_counts": horizon_counts,
            "entry_convention": "first_session_open_strictly_after_first_seen",
            "exit_convention": "close_of_Hth_session_including_entry_session",
            "signal_date_close_used": False,
            "historical_rows_without_first_seen_admitted": False,
        },
    }

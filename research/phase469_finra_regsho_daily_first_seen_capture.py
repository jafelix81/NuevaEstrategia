from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
BASE_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
POLL_FIELDS = [
    "run_id", "mode", "trade_date", "poll_start_utc", "poll_end_utc",
    "http_status", "poll_status", "error", "raw_sha256", "response_bytes",
    "row_count", "symbol_count", "schema_version", "observation_kind",
    "research_observation_eligible", "signal_eligible", "url",
]
EVENT_FIELDS = [
    "run_id", "trade_date", "observation_kind", "poll_start_utc",
    "first_seen_utc", "poll_end_utc", "revision_seen_utc", "http_status",
    "raw_sha256", "previous_sha256", "response_bytes", "row_count",
    "symbol_count", "schema_version", "research_observation_eligible",
    "signal_eligible", "url",
]
REQUIRED_HEADERS = {
    "date": "date",
    "symbol": "symbol",
    "shortvolume": "short_volume",
    "shortexemptvolume": "short_exempt_volume",
    "totalvolume": "total_volume",
    "market": "market",
}
OPTIONAL_HEADERS: dict[str, str] = {}


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp_must_be_timezone_aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_trade_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("trade_date_invalid")


def _normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{field}_invalid") from None
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field}_negative_or_nonfinite")
    return result


def parse_finra_file(raw: bytes, requested_trade_date: date) -> dict[str, Any]:
    """Parse a FINRA CNMS daily file without double-counting facilities.

    Current consolidated CNMS rows are security-grain: the Market field may
    contain a comma-separated list of reporting facilities (for example
    B,Q,N), and the volume columns are already consolidated. Older or
    facility-grain snapshots can contain repeated symbols with one facility
    code per row; those are aggregated by (symbol, market).

    If any row carries a multi-facility list, the file is treated as
    security-grain and duplicate symbols are rejected. This avoids summing an
    already-consolidated row with another row for the same security.
    """
    if not isinstance(raw, bytes) or not raw:
        raise ValueError("file_empty")
    try:
        lines = [line.strip() for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    except UnicodeDecodeError:
        raise ValueError("file_not_utf8") from None
    if len(lines) < 2:
        raise ValueError("header_or_trailer_missing")

    header_cells = lines[0].split("|")
    if header_cells and header_cells[-1] == "":
        header_cells = header_cells[:-1]
    normalised = [_normalise_header(x) for x in header_cells]
    if len(set(normalised)) != len(normalised):
        raise ValueError("duplicate_header")
    positions: dict[str, int] = {}
    for index, name in enumerate(normalised):
        if name in REQUIRED_HEADERS:
            positions[REQUIRED_HEADERS[name]] = index
        elif name in OPTIONAL_HEADERS:
            positions[OPTIONAL_HEADERS[name]] = index
    missing = sorted(set(REQUIRED_HEADERS.values()) - set(positions))
    if missing:
        raise ValueError("required_header_missing:" + ",".join(missing))

    trailer = lines[-1].split("|")
    if len(trailer) != 1 or not trailer[0].strip().isdigit():
        raise ValueError("trailer_count_missing_or_invalid")
    declared_count = int(trailer[0].strip())
    data_lines = lines[1:-1]

    parsed_rows: list[dict[str, Any]] = []
    market_codes: set[str] = set()
    has_composite_market_list = False

    for line_number, line in enumerate(data_lines, start=2):
        cells = line.split("|")
        if cells and cells[-1] == "" and len(cells) == len(header_cells) + 1:
            cells = cells[:-1]
        if len(cells) != len(header_cells):
            raise ValueError(f"row_field_count_mismatch:{line_number}")
        trade_date = _parse_trade_date(cells[positions["date"]])
        if trade_date != requested_trade_date:
            raise ValueError("row_trade_date_mismatch")
        symbol = cells[positions["symbol"]].strip().upper()
        if not symbol or any(ch.isspace() for ch in symbol):
            raise ValueError("symbol_invalid")

        market_value = cells[positions["market"]].strip().upper()
        market_tokens = [token.strip() for token in market_value.split(",")]
        if not market_value or any(
            not token or len(token) != 1 or not token.isalpha()
            for token in market_tokens
        ):
            raise ValueError("market_code_invalid")
        if len(set(market_tokens)) != len(market_tokens):
            raise ValueError("market_code_duplicate")
        if len(market_tokens) > 1:
            has_composite_market_list = True
        market_codes.update(market_tokens)

        short_volume = _decimal(cells[positions["short_volume"]], "short_volume")
        short_exempt = _decimal(cells[positions["short_exempt_volume"]], "short_exempt_volume")
        total_volume = _decimal(cells[positions["total_volume"]], "total_volume")
        if short_exempt > short_volume:
            raise ValueError("short_exempt_exceeds_short")
        if short_volume > total_volume:
            raise ValueError("short_exceeds_total")

        parsed_rows.append({
            "symbol": symbol,
            "trade_date": requested_trade_date.isoformat(),
            "short_volume": short_volume,
            "short_exempt_volume": short_exempt,
            "total_volume": total_volume,
            "markets": market_tokens,
        })

    if len(parsed_rows) != declared_count:
        raise ValueError("trailer_count_mismatch")

    rows: list[dict[str, Any]] = []
    if has_composite_market_list:
        # A comma-separated Market field denotes an already consolidated
        # security row. Never aggregate its volumes with another row.
        seen_symbols: set[str] = set()
        for item in parsed_rows:
            symbol = item["symbol"]
            if symbol in seen_symbols:
                raise ValueError("duplicate_symbol_in_consolidated_file")
            seen_symbols.add(symbol)
            rows.append({
                "symbol": symbol,
                "trade_date": item["trade_date"],
                "short_volume": item["short_volume"],
                "short_exempt_volume": item["short_exempt_volume"],
                "total_volume": item["total_volume"],
                "market": ",".join(sorted(item["markets"])),
            })
        row_grain = "security_rows_with_market_lists"
    else:
        # Single-code rows can be facility-grain. Aggregate only when a
        # security appears in more than one distinct facility.
        seen_symbol_markets: set[tuple[str, str]] = set()
        aggregates: dict[str, dict[str, Any]] = {}
        for item in parsed_rows:
            symbol = item["symbol"]
            market = item["markets"][0]
            symbol_market = (symbol, market)
            if symbol_market in seen_symbol_markets:
                raise ValueError("duplicate_symbol_market")
            seen_symbol_markets.add(symbol_market)
            aggregate = aggregates.setdefault(
                symbol,
                {
                    "short_volume": Decimal("0"),
                    "short_exempt_volume": Decimal("0"),
                    "total_volume": Decimal("0"),
                    "markets": set(),
                },
            )
            aggregate["short_volume"] += item["short_volume"]
            aggregate["short_exempt_volume"] += item["short_exempt_volume"]
            aggregate["total_volume"] += item["total_volume"]
            aggregate["markets"].add(market)
        for symbol, values in aggregates.items():
            rows.append({
                "symbol": symbol,
                "trade_date": requested_trade_date.isoformat(),
                "short_volume": values["short_volume"],
                "short_exempt_volume": values["short_exempt_volume"],
                "total_volume": values["total_volume"],
                "market": ",".join(sorted(values["markets"])),
            })
        row_grain = (
            "facility_rows_aggregated"
            if len(rows) < len(parsed_rows)
            else "single_market_symbol_rows"
        )

    header_signature = hashlib.sha256("|".join(normalised).encode("utf-8")).hexdigest()[:16]
    market_encoding = (
        "comma_separated_facility_codes"
        if has_composite_market_list
        else "single_facility_code_per_row"
    )
    return {
        "trade_date": requested_trade_date.isoformat(),
        "rows": rows,
        "row_count": len(parsed_rows),
        "facility_row_count": len(parsed_rows),
        "symbol_count": len(rows),
        "facility_count": len(market_codes),
        "row_grain": row_grain,
        "market_encoding": market_encoding,
        "response_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "schema_version": f"CNMSshvol:{header_signature}:{row_grain}",
        "header": normalised,
    }

def build_symbol_observations(parsed: dict[str, Any], file_event: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a hash-verified file event into one aggregated row per symbol."""
    if not file_event.get("research_observation_eligible"):
        return []
    observation_kind = file_event.get("observation_kind")
    if observation_kind not in {"first_seen", "late_first_seen"}:
        return []
    if parsed.get("raw_sha256") != file_event.get("raw_sha256"):
        raise ValueError("raw_file_hash_does_not_match_first_seen_manifest")
    if parsed.get("trade_date") != file_event.get("trade_date"):
        raise ValueError("raw_file_trade_date_does_not_match_manifest")
    if parsed.get("row_count", 0) <= 0:
        return []
    required = ("poll_start_utc", "first_seen_utc", "poll_end_utc")
    if any(not file_event.get(key) for key in required):
        raise ValueError("first_seen_poll_clock_incomplete")
    return [
        {
            "symbol": row["symbol"],
            "trade_date": parsed["trade_date"],
            "poll_start_utc": file_event["poll_start_utc"],
            "first_seen_utc": file_event["first_seen_utc"],
            "poll_end_utc": file_event["poll_end_utc"],
            "http_status": 200,
            "raw_sha256": parsed["raw_sha256"],
            "row_count": parsed["row_count"],
            "schema_version": parsed["schema_version"],
            "observation_kind": observation_kind,
        }
        for row in parsed["rows"]
    ]


def _fetch_http(url: str, timeout: int = 30) -> tuple[int | None, bytes, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "NuevaEstrategia-Phase469/1.0 (public FINRA data research)",
            "Accept": "text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read(), ""
    except HTTPError as exc:
        return int(exc.code), exc.read(), str(exc)
    except (URLError, TimeoutError, OSError) as exc:
        return None, b"", f"{type(exc).__name__}:{exc}"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "files": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"state_json_invalid:{type(exc).__name__}") from None
    if state.get("version") != 1 or not isinstance(state.get("files"), dict):
        raise ValueError("state_schema_invalid")
    return state


def _has_prior_scheduled_not_available(
    path: Path,
    trade_date: date,
    current_poll_start: datetime,
    current_run_id: str,
) -> bool:
    """Return True only when an earlier scheduled poll failed to receive this date.

    This is collector-specific evidence, not a claim that FINRA had not made
    the file public. It allows a later first receipt to be timestamped honestly
    and traded only after that later receipt; it never backdates availability.
    """
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"run_id", "mode", "trade_date", "poll_end_utc", "poll_status"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("prior_poll_ledger_schema_invalid")
        for row in reader:
            if row.get("trade_date") != trade_date.isoformat():
                continue
            if row.get("mode") != "schedule" or row.get("poll_status") != "not_available":
                continue
            if row.get("run_id") == str(current_run_id):
                continue
            raw_end = str(row.get("poll_end_utc", "")).strip()
            try:
                previous_end = datetime.fromisoformat(raw_end.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("prior_poll_timestamp_invalid") from None
            if previous_end.tzinfo is None or previous_end.utcoffset() is None:
                raise ValueError("prior_poll_timestamp_timezone_missing")
            previous_end = previous_end.astimezone(timezone.utc)
            current_start = current_poll_start.astimezone(timezone.utc)
            if previous_end >= current_start:
                continue
            previous_ny = previous_end.astimezone(NY)
            if previous_ny.date() >= trade_date and previous_ny.time() >= time(16, 0):
                return True
    return False


def _append_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    if exists:
        with path.open("r", encoding="utf-8", newline="") as handle:
            first = next(csv.reader(handle), [])
        if first != fields:
            raise ValueError(f"ledger_header_mismatch:{path.name}")
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def candidate_trade_dates(ny_date: date, lookback_days: int = 10) -> list[date]:
    if not 1 <= lookback_days <= 30:
        raise ValueError("lookback_days_out_of_range")
    return [
        ny_date - timedelta(days=offset)
        for offset in range(lookback_days)
        if (ny_date - timedelta(days=offset)).weekday() < 5
    ]


def run_capture(
    *,
    mode: str,
    run_id: str,
    data_dir: str | Path,
    output_dir: str | Path,
    lookback_days: int = 10,
    now_fn: Callable[[], datetime] | None = None,
    fetcher: Callable[[str], tuple[int | None, bytes, str]] | None = None,
) -> dict[str, Any]:
    if mode not in {"schedule", "manual"}:
        raise ValueError("mode_invalid")
    now_fn = now_fn or (lambda: datetime.now(timezone.utc))
    fetcher = fetcher or _fetch_http
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    state_path = data_dir / "state.json"
    state = _load_state(state_path)
    run_start = now_fn()
    if run_start.tzinfo is None or run_start.utcoffset() is None:
        raise ValueError("now_must_be_timezone_aware")
    ny_now = run_start.astimezone(NY)
    trade_dates = candidate_trade_dates(ny_now.date(), lookback_days)
    poll_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    counts = {
        "http_200": 0, "valid_files": 0, "first_seen": 0,
        "late_first_seen": 0, "bootstrap": 0,
        "revisions": 0, "unchanged": 0, "not_available": 0,
        "http_errors": 0, "invalid_files": 0, "eligible_first_seen": 0,
    }

    for trade_date in trade_dates:
        url = BASE_URL.format(yyyymmdd=trade_date.strftime("%Y%m%d"))
        poll_start = now_fn()
        try:
            http_status, body, error = fetcher(url)
        except Exception as exc:
            http_status, body, error = None, b"", f"{type(exc).__name__}:{exc}"
        poll_end = now_fn()
        start_iso, end_iso = _utc_iso(poll_start), _utc_iso(poll_end)
        digest = ""
        response_bytes = 0
        row_count = ""
        symbol_count = ""
        schema_version = ""
        observation_kind = ""
        eligible = False
        poll_status = ""

        if http_status != 200:
            if http_status in {403, 404}:
                poll_status = "not_available"
                counts["not_available"] += 1
            else:
                poll_status = "http_error"
                counts["http_errors"] += 1
        else:
            counts["http_200"] += 1
            # Preserve a reproducible fingerprint even when HTTP 200 contains
            # a malformed or schema-incompatible payload. Raw bytes are not saved.
            digest = hashlib.sha256(body).hexdigest()
            response_bytes = len(body)
            try:
                parsed = parse_finra_file(body, trade_date)
            except ValueError as exc:
                poll_status = "invalid_file"
                error = str(exc)
                counts["invalid_files"] += 1
            else:
                counts["valid_files"] += 1
                digest = parsed["raw_sha256"]
                response_bytes = parsed["response_bytes"]
                row_count = parsed["row_count"]
                symbol_count = parsed["symbol_count"]
                schema_version = parsed["schema_version"]
                key = trade_date.isoformat()
                previous = state["files"].get(key)
                if previous is None:
                    if mode == "manual":
                        observation_kind = "manual_diagnostic"
                    elif (
                        trade_date == ny_now.date()
                        and ny_now.time() >= time(16, 0)
                        and parsed["row_count"] > 0
                    ):
                        observation_kind = "first_seen"
                        eligible = True
                    elif (
                        trade_date < ny_now.date()
                        and ny_now.time() >= time(16, 0)
                        and parsed["row_count"] > 0
                        and _has_prior_scheduled_not_available(
                            data_dir / "polls.csv", trade_date, poll_start, run_id
                        )
                    ):
                        observation_kind = "late_first_seen"
                        eligible = True
                    else:
                        observation_kind = "bootstrap"
                    if observation_kind in {"first_seen", "manual_diagnostic"}:
                        counts["first_seen"] += 1
                    elif observation_kind == "late_first_seen":
                        counts["late_first_seen"] += 1
                    else:
                        counts["bootstrap"] += 1
                    event_rows.append({
                        "run_id": run_id, "trade_date": key,
                        "observation_kind": observation_kind,
                        "poll_start_utc": start_iso,
                        "first_seen_utc": end_iso,
                        "poll_end_utc": end_iso,
                        "revision_seen_utc": "",
                        "http_status": 200, "raw_sha256": digest,
                        "previous_sha256": "", "response_bytes": response_bytes,
                        "row_count": row_count, "symbol_count": symbol_count,
                        "schema_version": schema_version,
                        "research_observation_eligible": eligible,
                        "signal_eligible": False, "url": url,
                    })
                    if mode == "schedule":
                        state["files"][key] = {
                            "first_seen_utc": end_iso,
                            "first_seen_sha256": digest,
                            "first_seen_kind": observation_kind,
                            "latest_sha256": digest,
                            "last_seen_utc": end_iso,
                            "row_count": row_count,
                            "symbol_count": symbol_count,
                            "schema_version": schema_version,
                        }
                elif digest == previous.get("latest_sha256"):
                    observation_kind = "unchanged"
                    counts["unchanged"] += 1
                    if mode == "schedule":
                        previous["last_seen_utc"] = end_iso
                else:
                    observation_kind = "revision"
                    counts["revisions"] += 1
                    event_rows.append({
                        "run_id": run_id, "trade_date": key,
                        "observation_kind": "revision",
                        "poll_start_utc": start_iso,
                        "first_seen_utc": previous.get("first_seen_utc", ""),
                        "poll_end_utc": end_iso,
                        "revision_seen_utc": end_iso,
                        "http_status": 200, "raw_sha256": digest,
                        "previous_sha256": previous.get("latest_sha256", ""),
                        "response_bytes": response_bytes,
                        "row_count": row_count, "symbol_count": symbol_count,
                        "schema_version": schema_version,
                        "research_observation_eligible": False,
                        "signal_eligible": False, "url": url,
                    })
                    if mode == "schedule":
                        previous["latest_sha256"] = digest
                        previous["last_seen_utc"] = end_iso
                        previous["row_count"] = row_count
                        previous["symbol_count"] = symbol_count
                        previous["schema_version"] = schema_version
                if eligible:
                    counts["eligible_first_seen"] += 1
                poll_status = "valid_file"

        poll_rows.append({
            "run_id": run_id, "mode": mode, "trade_date": trade_date.isoformat(),
            "poll_start_utc": start_iso, "poll_end_utc": end_iso,
            "http_status": http_status if http_status is not None else "",
            "poll_status": poll_status, "error": error, "raw_sha256": digest,
            "response_bytes": response_bytes, "row_count": row_count,
            "symbol_count": symbol_count, "schema_version": schema_version,
            "observation_kind": observation_kind,
            "research_observation_eligible": eligible,
            "signal_eligible": False, "url": url,
        })

    run_end = now_fn()
    summary = {
        "phase": 469,
        "run_id": str(run_id),
        "mode": mode,
        "poll_started_utc": _utc_iso(run_start),
        "poll_completed_utc": _utc_iso(run_end),
        "ny_trade_date": ny_now.date().isoformat(),
        "lookback_calendar_days": lookback_days,
        "requested_trade_dates": [x.isoformat() for x in trade_dates],
        "counts": counts,
        "research_observation_eligible_count": counts["eligible_first_seen"],
        "signal_eligible_count": 0,
        "raw_market_data_persisted": False,
        "historical_first_seen_imputed": False,
        "revision_policy": "append_revision_event; preserve_original_first_seen; never_relabel_revision_as_first_seen",
        "manual_mode_persists_state": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_dir / "summary.json", summary)
    if mode == "schedule":
        _append_csv(data_dir / "polls.csv", POLL_FIELDS, poll_rows)
        _append_csv(data_dir / "events.csv", EVENT_FIELDS, event_rows)
        state["last_poll_completed_utc"] = summary["poll_completed_utc"]
        state["last_run_id"] = str(run_id)
        _write_json_atomic(state_path, state)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="FINRA CNMS daily short-volume first-seen metadata capture")
    parser.add_argument("--mode", choices=("schedule", "manual"), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--data-dir", default="research/data/finra_regsho_daily_first_seen")
    parser.add_argument("--output", default="phase469_output")
    parser.add_argument("--lookback-days", type=int, default=10)
    args = parser.parse_args()
    result = run_capture(
        mode=args.mode, run_id=args.run_id, data_dir=args.data_dir,
        output_dir=args.output, lookback_days=args.lookback_days,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

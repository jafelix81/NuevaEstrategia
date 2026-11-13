"""Phase 351: audit the public Cboe TBT sample without making PIT/alpha claims."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

SAMPLE_URL = "https://datashop.cboe.com/download/sample/289"
EXPECTED_COLUMNS = [
    "TRANSACT_TIME", "TRADING_DT", "FLOOR_ACTION_TS", "UNDERLYING",
    "OSI_ROOT", "EXPIRE_DATE", "CALL_PUT_FLAG", "STRIKE_PRICE", "SIZE",
    "PRICE", "NBBO_BID", "NBBO_ASK", "BBO_BID", "BBO_ASK", "SIDE",
    "OPEN_CLOSE", "CAPACITY", "TRADE_TYPE", "EXEC_ID", "COMPLEX_EXEC_ID",
    "SESSION", "TRADING_SEGMENT",
]
CAPACITIES = {"MarketMaker", "Customer", "ProCustomer", "BrokerDealer", "Firm"}
SESSIONS = {"RTH", "GTH", "CURB"}
SIDES = {"B", "S"}
OPEN_CLOSE = {"O", "C"}
CALL_PUT = {"C", "P"}


def _parse_datetime(value: str):
    value = (value or "").strip()
    if not value:
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognized timestamp format: {value[:40]}")


def _parse_decimal(value: str, field: str, *, optional=True):
    value = (value or "").strip()
    if not value:
        if optional:
            return None
        raise ValueError(f"{field} is blank")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not number.is_finite():
        raise ValueError(f"{field} is not finite")
    return number


def _trade_date(value: str):
    parsed = _parse_datetime(value)
    return parsed.date().isoformat() if parsed else ""


def _member_bytes(name: str, payload: bytes) -> bytes:
    return gzip.decompress(payload) if name.lower().endswith(".gz") else payload


def _find_csv_payloads(archive_bytes: bytes) -> list[tuple[str, bytes]]:
    found = []

    def scan_zip(payload: bytes, prefix: str, depth: int):
        if depth > 3:
            raise ValueError("nested sample archive depth exceeds safety limit")
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            bad = zf.testzip()
            if bad:
                raise ValueError(f"nested ZIP CRC failure: {bad}")
            for member in zf.namelist():
                if member.endswith("/"):
                    continue
                child = zf.read(member)
                label = f"{prefix}{member}"
                if child.startswith(bytes((80, 75, 3, 4))):
                    scan_zip(child, label + "!", depth + 1)
                    continue
                if child.startswith(bytes((31, 139))):
                    child = gzip.decompress(child)
                try:
                    decoded = child.decode("utf-8-sig")
                except UnicodeDecodeError:
                    continue
                first_line = next((line for line in decoded.splitlines() if line.strip()), "")
                if not first_line:
                    continue
                try:
                    header = [str(x).strip().upper() for x in next(csv.reader([first_line]))]
                except (csv.Error, StopIteration):
                    continue
                if len(header) == len(EXPECTED_COLUMNS) and set(header) == set(EXPECTED_COLUMNS):
                    found.append((label, child))

    scan_zip(archive_bytes, "", 0)
    return found


def audit_zip_bytes(archive_bytes: bytes) -> dict:
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    members = []
    total_rows = 0
    trade_dates, transact_dates = set(), set()
    underlyings, series_keys = set(), set()
    counters = {key: Counter() for key in
                ("side", "open_close", "capacity", "call_put", "session",
                 "trading_segment", "trade_type")}
    exec_groups = defaultdict(lambda: {"rows": 0, "sides": set(), "contracts": set(),
                                        "capacities": set(), "open_close": set()})
    complex_groups = defaultdict(lambda: {"rows": 0, "contracts": set(), "sides": set()})
    exact_rows = set()
    duplicate_exact_rows = 0
    missing_exec_id = missing_complex_id = 0
    invalid_quotes = crossed_nbbo = crossed_bbo = outside_nbbo = 0
    missing_nbbo = missing_bbo = 0
    missing_floor_ts = late_floor = negative_floor_lag = 0
    trading_date_calendar_mismatch = 0
    missing_required_cells = Counter()
    row_width_errors = 0
    timestamp_parse_failures = 0
    timestamp_awareness = Counter()
    price_zero = size_zero = 0
    exec_row_sizes = Counter()
    complex_row_sizes = Counter()

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        bad_member = zf.testzip()
        if bad_member:
            raise ValueError(f"ZIP CRC failure: {bad_member}")
        csv_payloads = _find_csv_payloads(archive_bytes)
        if not csv_payloads:
            names = [n for n in zf.namelist() if not n.endswith("/")][:12]
            raise ValueError(f"sample ZIP has no member matching the 22-field TBT header; members={names}")
        for name, raw in csv_payloads:
            text = raw.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text, newline=""))
            if not reader.fieldnames:
                raise ValueError(f"{name}: missing CSV header")
            headers = [str(h).strip().upper() for h in reader.fieldnames]
            if len(headers) != len(set(headers)):
                raise ValueError(f"{name}: duplicate header names")
            if len(headers) != len(EXPECTED_COLUMNS) or set(headers) != set(EXPECTED_COLUMNS):
                raise ValueError(f"{name}: header contract mismatch; got {len(headers)} fields")
            member_rows = 0
            for raw_row in reader:
                if None in raw_row:
                    row_width_errors += 1
                    raise ValueError(f"{name}: row has more fields than header")
                row = {str(k).strip().upper(): (v or "").strip()
                       for k, v in raw_row.items() if k is not None}
                if len(row) != len(EXPECTED_COLUMNS):
                    row_width_errors += 1
                    raise ValueError(f"{name}: row width mismatch")
                member_rows += 1
                total_rows += 1

                for field in EXPECTED_COLUMNS:
                    if not row.get(field):
                        missing_required_cells[field] += 1
                if any(not row.get(x) for x in
                       ("TRANSACT_TIME", "TRADING_DT", "UNDERLYING", "OSI_ROOT",
                        "CALL_PUT_FLAG", "SIZE", "PRICE", "SIDE", "OPEN_CLOSE",
                        "CAPACITY", "SESSION")):
                    raise ValueError(f"{name}: required trade field is blank")

                transact = _parse_datetime(row["TRANSACT_TIME"])
                trading = _trade_date(row["TRADING_DT"])
                if transact is None or not trading:
                    raise ValueError(f"{name}: missing transaction or trading date")
                transact_dates.add(transact.date().isoformat())
                trade_dates.add(trading)
                timestamp_awareness["aware" if transact.tzinfo else "naive"] += 1
                if transact.date().isoformat() != trading:
                    trading_date_calendar_mismatch += 1

                side, oc = row["SIDE"], row["OPEN_CLOSE"]
                cp, capacity, session = row["CALL_PUT_FLAG"], row["CAPACITY"], row["SESSION"].upper()
                if side not in SIDES or oc not in OPEN_CLOSE or cp not in CALL_PUT:
                    raise ValueError(f"{name}: invalid side/open-close/call-put code")
                if capacity not in CAPACITIES:
                    raise ValueError(f"{name}: unknown capacity value {capacity!r}")
                if session not in SESSIONS:
                    raise ValueError(f"{name}: unknown session value {session!r}")
                counters["side"][side] += 1
                counters["open_close"][oc] += 1
                counters["call_put"][cp] += 1
                counters["capacity"][capacity] += 1
                counters["session"][session] += 1
                counters["trading_segment"][row["TRADING_SEGMENT"]] += 1
                counters["trade_type"][row["TRADE_TYPE"] or "UNKNOWN_BLANK"] += 1

                size = _parse_decimal(row["SIZE"], "SIZE", optional=False)
                price = _parse_decimal(row["PRICE"], "PRICE", optional=False)
                if size <= 0 or size != size.to_integral_value():
                    raise ValueError(f"{name}: SIZE must be a positive integer")
                if size == 0:
                    size_zero += 1
                if price < 0:
                    raise ValueError(f"{name}: PRICE cannot be negative")
                if price == 0:
                    price_zero += 1
                strike = _parse_decimal(row["STRIKE_PRICE"], "STRIKE_PRICE", optional=False)
                contract = (row["UNDERLYING"], row["OSI_ROOT"], row["EXPIRE_DATE"],
                            cp, str(strike))
                underlyings.add(row["UNDERLYING"])
                series_keys.add(contract)

                nbbo_bid = _parse_decimal(row["NBBO_BID"], "NBBO_BID")
                nbbo_ask = _parse_decimal(row["NBBO_ASK"], "NBBO_ASK")
                bbo_bid = _parse_decimal(row["BBO_BID"], "BBO_BID")
                bbo_ask = _parse_decimal(row["BBO_ASK"], "BBO_ASK")
                if nbbo_bid is None or nbbo_ask is None:
                    missing_nbbo += 1
                elif nbbo_bid > nbbo_ask:
                    crossed_nbbo += 1
                if bbo_bid is None or bbo_ask is None:
                    missing_bbo += 1
                elif bbo_bid > bbo_ask:
                    crossed_bbo += 1
                if nbbo_bid is not None and nbbo_ask is not None and not (nbbo_bid <= nbbo_ask):
                    invalid_quotes += 1
                if nbbo_bid is not None and nbbo_ask is not None and (price < nbbo_bid or price > nbbo_ask):
                    outside_nbbo += 1

                floor_value = row["FLOOR_ACTION_TS"]
                if not floor_value:
                    missing_floor_ts += 1
                else:
                    floor_ts = _parse_datetime(floor_value)
                    lag = (transact - floor_ts).total_seconds()
                    if lag < 0:
                        negative_floor_lag += 1
                    if lag >= 90:
                        late_floor += 1

                exec_id = row["EXEC_ID"]
                if not exec_id:
                    missing_exec_id += 1
                else:
                    g = exec_groups[exec_id]
                    g["rows"] += 1
                    g["sides"].add(side)
                    g["contracts"].add(contract)
                    g["capacities"].add(capacity)
                    g["open_close"].add(oc)
                complex_id = row["COMPLEX_EXEC_ID"]
                if not complex_id:
                    missing_complex_id += 1
                else:
                    g = complex_groups[complex_id]
                    g["rows"] += 1
                    g["contracts"].add(contract)
                    g["sides"].add(side)

                exact_key = tuple(row[c] for c in EXPECTED_COLUMNS)
                if exact_key in exact_rows:
                    duplicate_exact_rows += 1
                else:
                    exact_rows.add(exact_key)

            members.append({"name": name, "bytes": len(raw), "rows": member_rows,
                            "sha256": hashlib.sha256(raw).hexdigest()})

    if total_rows == 0:
        raise ValueError("sample contains no data rows")
    for g in exec_groups.values():
        exec_row_sizes[g["rows"]] += 1
    for g in complex_groups.values():
        complex_row_sizes[g["rows"]] += 1

    paired_exec = sum({"B", "S"}.issubset(g["sides"]) for g in exec_groups.values())
    multi_contract_exec = sum(len(g["contracts"]) > 1 for g in exec_groups.values())
    multi_capacity_exec = sum(len(g["capacities"]) > 1 for g in exec_groups.values())
    complex_multi_leg = sum(len(g["contracts"]) > 1 for g in complex_groups.values())

    return {
        "status": "PASS_SAMPLE_SCHEMA_AND_LINKAGE_DIAGNOSTICS_NO_PIT_NO_ALPHA",
        "archive_bytes": len(archive_bytes),
        "archive_sha256": archive_hash,
        "members": members,
        "rows": total_rows,
        "trade_dates": sorted(trade_dates),
        "transact_calendar_dates": sorted(transact_dates),
        "trading_date_calendar_mismatch_rows": trading_date_calendar_mismatch,
        "timestamp_timezone_awareness": dict(timestamp_awareness),
        "unique_underlyings": len(underlyings),
        "unique_option_series": len(series_keys),
        "capacity_counts": dict(sorted(counters["capacity"].items())),
        "side_counts": dict(sorted(counters["side"].items())),
        "open_close_counts": dict(sorted(counters["open_close"].items())),
        "call_put_counts": dict(sorted(counters["call_put"].items())),
        "session_counts": dict(sorted(counters["session"].items())),
        "trading_segment_counts": dict(sorted(counters["trading_segment"].items())),
        "trade_type_counts": dict(sorted(counters["trade_type"].items())),
        "missing_required_cells": dict(sorted(missing_required_cells.items())),
        "execution_id": {
            "nonblank_rows": total_rows - missing_exec_id,
            "unique_ids": len(exec_groups),
            "rows_per_id_distribution": dict(sorted(exec_row_sizes.items())),
            "ids_with_both_buy_and_sell_sides": paired_exec,
            "ids_spanning_multiple_option_series": multi_contract_exec,
            "ids_spanning_multiple_capacities": multi_capacity_exec,
        },
        "complex_execution_id": {
            "nonblank_rows": total_rows - missing_complex_id,
            "unique_ids": len(complex_groups),
            "rows_per_id_distribution": dict(sorted(complex_row_sizes.items())),
            "ids_spanning_multiple_option_series": complex_multi_leg,
        },
        "quote_diagnostics": {
            "missing_nbbo_rows": missing_nbbo,
            "missing_bbo_rows": missing_bbo,
            "crossed_nbbo_rows": crossed_nbbo,
            "crossed_bbo_rows": crossed_bbo,
            "trade_price_outside_nbbo_rows": outside_nbbo,
            "zero_trade_price_rows": price_zero,
        },
        "floor_action_diagnostics": {
            "missing_floor_action_timestamp_rows": missing_floor_ts,
            "late_rows_ge_90_seconds": late_floor,
            "negative_floor_lag_rows": negative_floor_lag,
        },
        "exact_duplicate_rows": duplicate_exact_rows,
        "row_width_errors": row_width_errors,
        "size_zero_rows": size_zero,
        "gates": {
            "sample_schema_pass": True,
            "row_grain_reconciled": False,
            "historical_pit_admitted": False,
            "prospective_pit_admitted": False,
            "all_opra_coverage_established": False,
            "inactive_underlying_coverage_established": False,
            "licensing_confirmed": False,
            "return_test_authorized": False,
            "alpha_admission": False,
            "f80_frozen": True,
            "holdout_used": False,
        },
    }


def download_sample() -> dict:
    request = urllib.request.Request(
        SAMPLE_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NuevaEstrategia-Research/1.0)",
                 "Accept": "application/zip, application/octet-stream, */*"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        headers = dict(response.headers.items())
        status = response.status
        final_url = response.geturl()
    result = audit_zip_bytes(body)
    result.update({
        "source_url": SAMPLE_URL,
        "final_url": final_url,
        "http_status": status,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "content_type": headers.get("Content-Type"),
        "pit_note": "Current sample retrieval is not a historical first-receipt record.",
    })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = download_sample()
        code = 0
    except Exception as exc:
        result = {
            "status": "SAMPLE_DOWNLOAD_OR_PARSE_FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "source_url": SAMPLE_URL,
            "historical_pit_admitted": False,
            "alpha_admission": False,
            "f80_frozen": True,
        }
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(code)


if __name__ == "__main__":
    main()

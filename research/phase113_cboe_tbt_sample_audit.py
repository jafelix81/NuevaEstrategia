#!/usr/bin/env python3
"""Audit the public sample for Cboe Enhanced US Options Trade-by-Trade (TBT)."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, re, zipfile
from collections import Counter, defaultdict
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any
import requests

SAMPLE_URL = "https://datashop.cboe.com/download/sample/289"
SPEC_URL = "https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf"
PRODUCT_URL = "https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail"
REQUIRED_FIELDS = [
    "TRANSACT_TIME", "TRADING_DT", "FLOOR_ACTION_TS", "UNDERLYING",
    "OSI_ROOT", "EXPIRE_DATE", "CALL_PUT_FLAG", "STRIKE_PRICE", "SIZE",
    "PRICE", "NBBO_BID", "NBBO_ASK", "BBO_BID", "BBO_ASK", "SIDE",
    "OPEN_CLOSE", "CAPACITY", "TRADE_TYPE", "EXEC_ID",
    "COMPLEX_EXEC_ID", "SESSION", "TRADING_SEGMENT",
]
VALID_SIDE = {"B", "S"}
VALID_OPEN_CLOSE = {"O", "C"}
VALID_CAPACITY = {"MARKETMAKER", "CUSTOMER", "PROCUSTOMER", "BROKERDEALER", "FIRM"}

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def request_bytes(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0 research-feasibility"})
    return {"url": url, "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "bytes": len(response.content), "sha256": sha256(response.content),
            "content": response.content}

def looks_like_csv(data: bytes) -> bool:
    preview = data[:20000].decode("utf-8-sig", errors="replace").upper()
    return all(x in preview for x in ("TRANSACT_TIME", "TRADING_DT", "UNDERLYING"))

def collect_csv_payloads(data: bytes, name: str = "sample", depth: int = 0):
    found, entries = [], []
    if depth > 5:
        return found, entries
    bio = io.BytesIO(data)
    if zipfile.is_zipfile(bio):
        with zipfile.ZipFile(bio) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                payload = archive.read(info)
                child = f"{name}!{info.filename}"
                entries.append(f"{child} ({len(payload)} bytes)")
                f, e = collect_csv_payloads(payload, child, depth + 1)
                found.extend(f); entries.extend(e)
        return found, entries
    if data[:2] == b"\x1f\x8b" or name.lower().endswith(".gz"):
        try:
            unpacked = gzip.decompress(data)
            entries.append(f"{name} [gzip decompressed: {len(unpacked)} bytes]")
            f, e = collect_csv_payloads(unpacked, re.sub(r"\.gz$", "", name, flags=re.I), depth + 1)
            found.extend(f); entries.extend(e)
            return found, entries
        except OSError:
            pass
    if looks_like_csv(data):
        found.append({"name": name, "bytes": len(data), "sha256": sha256(data), "content": data})
    return found, entries

def parse_datetime(value: str):
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")), "iso"
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt), fmt
            except ValueError:
                pass
    return None, "unparsed"

def parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        return date.fromisoformat(value[:10]), "iso_date"
    except ValueError:
        for fmt in ("%m/%d/%Y", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt).date(), fmt
            except ValueError:
                pass
    return None, "unparsed"

def number(value: str):
    try:
        return float((value or "").strip())
    except (TypeError, ValueError):
        return None

def normalize_capacity(value: str) -> str:
    return re.sub(r"[^A-Z]", "", (value or "").strip().upper())

def parse_trade_csv(payload: bytes) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig", errors="replace")))
    fields = [str(x or "").strip().upper() for x in (reader.fieldnames or [])]
    missing = sorted(set(REQUIRED_FIELDS) - set(fields))
    errors = Counter()
    counters = {k: Counter() for k in (
        "side", "open_close", "capacity", "session", "segment", "trade_type",
        "underlying", "trading_date", "time_format", "timezone", "nbbo", "bbo", "floor_delay",
        "side_trade_type", "open_close_trade_type", "session_segment"
    )}
    exception_samples = []
    exact_hashes = Counter()
    exec_sizes, complex_sizes = Counter(), Counter()
    exec_sides = defaultdict(set)
    row_count = parsed_time = parsed_date = parsed_floor = 0
    date_mismatch = positive_size = positive_price = nonnegative_strike = 0
    invalid_side = invalid_oc = invalid_capacity = 0
    for raw in reader:
        row_count += 1
        row = {str(k or "").strip().upper(): (v or "").strip() for k, v in raw.items() if k is not None}
        exact_hashes[sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode())] += 1
        side, oc = row.get("SIDE", "").upper(), row.get("OPEN_CLOSE", "").upper()
        cap = normalize_capacity(row.get("CAPACITY", ""))
        counters["side"][side or "<blank>"] += 1
        counters["open_close"][oc or "<blank>"] += 1
        counters["capacity"][cap or "<blank>"] += 1
        counters["session"][row.get("SESSION", "").upper() or "<blank>"] += 1
        counters["segment"][row.get("TRADING_SEGMENT", "") or "<blank>"] += 1
        trade_type = row.get("TRADE_TYPE", "") or "<blank>"
        session = row.get("SESSION", "").upper() or "<blank>"
        segment = row.get("TRADING_SEGMENT", "") or "<blank>"
        counters["trade_type"][trade_type] += 1
        counters["underlying"][row.get("UNDERLYING", "") or "<blank>"] += 1
        counters["side_trade_type"][f"{side or '<blank>'}|{trade_type}"] += 1
        counters["open_close_trade_type"][f"{oc or '<blank>'}|{trade_type}"] += 1
        counters["session_segment"][f"{session}|{segment}"] += 1
        if side not in VALID_SIDE: invalid_side += 1
        if oc not in VALID_OPEN_CLOSE: invalid_oc += 1
        if (side not in VALID_SIDE or oc not in VALID_OPEN_CLOSE) and len(exception_samples) < 60:
            exception_samples.append({
                "underlying": row.get("UNDERLYING", ""), "osi_root": row.get("OSI_ROOT", ""),
                "side": side, "open_close": oc, "capacity": cap, "trade_type": trade_type,
                "session": session, "trading_segment": segment, "size": row.get("SIZE", ""),
                "price": row.get("PRICE", ""), "exec_id": row.get("EXEC_ID", ""),
                "complex_exec_id": row.get("COMPLEX_EXEC_ID", "")
            })
        if cap not in VALID_CAPACITY: invalid_capacity += 1

        td, _ = parse_date(row.get("TRADING_DT", ""))
        if td:
            parsed_date += 1; counters["trading_date"][td.isoformat()] += 1
        else: errors["unparsed_trading_date"] += 1
        tt, fmt = parse_datetime(row.get("TRANSACT_TIME", ""))
        if tt:
            parsed_time += 1
            counters["time_format"][fmt or "unknown"] += 1
            counters["timezone"]["aware" if tt.tzinfo else "naive"] += 1
            if td and tt.date() != td: date_mismatch += 1
        else: errors["unparsed_transact_time"] += 1
        floor, _ = parse_datetime(row.get("FLOOR_ACTION_TS", ""))
        if floor:
            parsed_floor += 1
            if tt and ((tt.tzinfo is None) == (floor.tzinfo is None)):
                delay = (tt - floor).total_seconds()
                counters["floor_delay"]["late_ge_90s" if delay >= 90 else "not_late_or_negative"] += 1
            elif tt: counters["floor_delay"]["timezone_mismatch"] += 1

        size, price, strike = number(row.get("SIZE", "")), number(row.get("PRICE", "")), number(row.get("STRIKE_PRICE", ""))
        if size is not None and size > 0: positive_size += 1
        else: errors["nonpositive_or_invalid_size"] += 1
        if price is not None and price > 0: positive_price += 1
        else: errors["nonpositive_or_invalid_price"] += 1
        if strike is not None and strike >= 0: nonnegative_strike += 1
        else: errors["negative_or_invalid_strike"] += 1

        for prefix, bid_field, ask_field in (("nbbo", "NBBO_BID", "NBBO_ASK"), ("bbo", "BBO_BID", "BBO_ASK")):
            bid, ask = number(row.get(bid_field, "")), number(row.get(ask_field, ""))
            if bid is None or ask is None or bid <= 0 or ask <= 0: counters[prefix]["zero_or_missing"] += 1
            elif ask < bid: counters[prefix]["crossed"] += 1
            elif ask == bid: counters[prefix]["locked"] += 1
            else: counters[prefix]["valid"] += 1

        exid = row.get("EXEC_ID", "")
        if exid: exec_sizes[exid] += 1; exec_sides[exid].add(side)
        cxid = row.get("COMPLEX_EXEC_ID", "")
        if cxid: complex_sizes[cxid] += 1

    repeated_exec = [n for n in exec_sizes.values() if n > 1]
    repeated_complex = [n for n in complex_sizes.values() if n > 1]
    result = {
        "row_count": row_count, "fields": fields, "missing_required_fields": missing,
        "unique_underlyings": len(counters["underlying"]),
        "underlying_counts": dict(sorted(counters["underlying"].items())),
        "trading_dates": dict(sorted(counters["trading_date"].items())),
        "parsed_trading_date_count": parsed_date, "parsed_transact_time_count": parsed_time,
        "parsed_floor_action_time_count": parsed_floor,
        "transact_time_format_counts": dict(counters["time_format"]),
        "transact_time_timezone_counts": dict(counters["timezone"]),
        "trading_dt_vs_transact_calendar_date_mismatch_count": date_mismatch,
        "side_counts": dict(counters["side"]), "open_close_counts": dict(counters["open_close"]),
        "capacity_counts": dict(counters["capacity"]), "session_counts": dict(counters["session"]),
        "trading_segment_counts": dict(counters["segment"]), "session_segment_counts": dict(counters["session_segment"]),
        "trade_type_counts": dict(counters["trade_type"]),
        "side_by_trade_type": dict(counters["side_trade_type"]),
        "open_close_by_trade_type": dict(counters["open_close_trade_type"]),
        "unclassified_side_rows": invalid_side, "blank_or_unmapped_open_close_rows": invalid_oc,
        "convention_exception_samples": exception_samples,
        "nbbo_state_counts": dict(counters["nbbo"]), "bbo_state_counts": dict(counters["bbo"]),
        "floor_action_delay_counts": dict(counters["floor_delay"]),
        "exec_id_nonblank_rows": sum(exec_sizes.values()), "exec_id_unique_count": len(exec_sizes),
        "exec_id_repeated_group_count": len(repeated_exec),
        "exec_id_repeated_group_size_counts": dict(Counter(repeated_exec)),
        "exec_id_groups_with_both_sides": sum(1 for s in exec_sides.values() if s == {"B", "S"}),
        "complex_exec_id_nonblank_rows": sum(complex_sizes.values()),
        "complex_exec_id_unique_count": len(complex_sizes),
        "complex_exec_id_repeated_group_count": len(repeated_complex),
        "complex_exec_id_repeated_group_size_counts": dict(Counter(repeated_complex)),
        "exact_duplicate_row_excess": sum(n - 1 for n in exact_hashes.values() if n > 1),
        "positive_size_rows": positive_size, "positive_price_rows": positive_price,
        "nonnegative_strike_rows": nonnegative_strike, "invalid_side_rows": invalid_side,
        "invalid_open_close_rows": invalid_oc, "invalid_capacity_rows": invalid_capacity,
        "errors": dict(errors),
    }
    return result

def audit_payloads(csv_payloads, sample_meta, spec_meta, zip_entries):
    parsed = [{"file": x["name"], "bytes": x["bytes"], "sha256": x["sha256"],
               "audit": parse_trade_csv(x["content"])} for x in csv_payloads]
    total_rows = sum(x["audit"]["row_count"] for x in parsed)
    pass_all = sample_meta["http_status"] == 200 and spec_meta["http_status"] == 200 and bool(parsed)
    for x in parsed:
        a = x["audit"]
        pass_all = pass_all and a["row_count"] > 0 and not a["missing_required_fields"]
        pass_all = pass_all and a["parsed_transact_time_count"] == a["row_count"]
        pass_all = pass_all and a["parsed_trading_date_count"] == a["row_count"]
        pass_all = pass_all and a["invalid_capacity_rows"] == 0 and a["positive_size_rows"] == a["row_count"]
        pass_all = pass_all and a["positive_price_rows"] == a["row_count"]
        pass_all = pass_all and a["nonnegative_strike_rows"] == a["row_count"]
        pass_all = pass_all and a["exact_duplicate_row_excess"] == 0
    return {
        "phase": 113, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "product": "Cboe Enhanced US Options Trade-by-Trade Execution Detail",
        "product_url": PRODUCT_URL, "spec_url": SPEC_URL,
        "sample": {k: v for k, v in sample_meta.items() if k != "content"},
        "spec": {k: v for k, v in spec_meta.items() if k != "content"},
        "zip_entries": zip_entries, "csv_results": parsed,
        "total_csv_payloads": len(parsed), "total_rows": total_rows,
        "data_gate": (
            "PASS_PARSE_WITH_UNRESOLVED_CONVENTIONS"
            if pass_all and any(x["audit"]["invalid_side_rows"] or x["audit"]["invalid_open_close_rows"] for x in parsed)
            else ("PASS_SAMPLE_SCHEMA" if pass_all else "FAIL_OR_INCOMPLETE_SAMPLE")
        ),
        "limitations": [
            "Public sample does not establish full C1 date/symbol coverage or historical archive completeness.",
            "TBT is currently C1 only; BZX, C2 and EDGX are listed as future releases.",
            "Capacity is an exchange/account-capacity classification, not beneficial-owner identity or proof of informed trading.",
            "Published delivery is T+1 and may be delayed; the sample does not prove historical file-availability timestamps.",
            "No purchase, subscription, vendor contact, forward-return test or alpha test was performed."
        ]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase113_cboe_tbt_output")
    args = parser.parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    sample = request_bytes(SAMPLE_URL)
    (out / "cboe_tbt_public_sample.zip").write_bytes(sample["content"])
    csv_payloads, entries = collect_csv_payloads(sample["content"], "cboe_tbt_public_sample.zip")
    spec = request_bytes(SPEC_URL)
    (out / "cboe_tbt_spec_v1_1.pdf").write_bytes(spec["content"])
    summary = audit_payloads(csv_payloads, sample, spec, entries)
    (out / "phase113_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if sample["http_status"] == 200 and spec["http_status"] == 200 and bool(csv_payloads) else 2

if __name__ == "__main__":
    raise SystemExit(main())

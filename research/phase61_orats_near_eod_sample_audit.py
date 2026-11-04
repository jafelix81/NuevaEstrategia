#!/usr/bin/env python3
"""Inspect ORATS' public Near-EOD sample; no paid data or return tests."""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
SAMPLE_URL = "https://s3.amazonaws.com/assets.orats.com/ORATS_SMV_Strikes_20240103.zip"
OUT_DIR = Path("phase61_orats_near_eod_sample_audit")


def norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def load_universe() -> set[str]:
    tree = ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    values = {str(v).strip().upper() for v in ast.literal_eval(node.value)}
                    if len(values) != 335:
                        raise RuntimeError(f"Expected frozen 335 tickers, got {len(values)}")
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")


def parse_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = raw.decode("utf-8-sig", "replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return [], []
    header_idx = 0
    for i, line in enumerate(lines[:30]):
        low = norm(line)
        if "ticker" in low and "strike" in low and ("expirdate" in low or "expiration" in low):
            header_idx = i
            break
    sample = "\n".join(lines[header_idx:header_idx + 12])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(lines[header_idx:], dialect=dialect)
    rows = [row for row in reader if row and any(v not in (None, "") for v in row.values())]
    return reader.fieldnames or [], rows


def extract_csvs(raw: bytes, prefix: str = "") -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in archive.namelist():
            payload = archive.read(name)
            full_name = prefix + name
            if name.lower().endswith(".csv"):
                out.append((full_name, payload))
            elif name.lower().endswith(".zip"):
                out.extend(extract_csvs(payload, full_name + "!"))
    return out


def find_field(headers: list[str], aliases: tuple[str, ...]) -> str | None:
    lookup = {norm(header): header for header in headers}
    for alias in aliases:
        actual = lookup.get(norm(alias))
        if actual:
            return actual
    return None


def field_stats(rows: list[dict[str, str]], field: str | None) -> dict[str, object]:
    if not field:
        return {"present": False, "nonnull_rate": 0.0, "positive_rate": None, "zero_rate": None}
    values: list[float] = []
    missing = 0
    nonnumeric = 0
    for row in rows:
        raw = row.get(field)
        if raw is None or str(raw).strip() == "":
            missing += 1
            continue
        try:
            values.append(float(str(raw).replace(",", "")))
        except ValueError:
            nonnumeric += 1
    n = len(rows)
    return {
        "present": True,
        "nonnull_rate": (n - missing) / n if n else 0.0,
        "numeric_rate_of_nonnull": len(values) / (n - missing) if n > missing else None,
        "positive_rate_of_numeric": sum(v > 0 for v in values) / len(values) if values else None,
        "zero_rate_of_numeric": sum(v == 0 for v in values) / len(values) if values else None,
        "nonnumeric": nonnumeric,
    }


def compute_coverage(universe: set[str], observed: set[str]) -> dict[str, object]:
    found = sorted(universe & observed)
    return {
        "universe_size": len(universe),
        "observed_universe_tickers": len(found),
        "coverage_rate": len(found) / len(universe) if universe else 0.0,
        "missing_tickers": sorted(universe - observed),
        "found_tickers": found,
    }


def fetch_sample() -> tuple[bytes, dict[str, object]]:
    last_error = None
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(
                SAMPLE_URL,
                headers={"User-Agent": "NuevaEstrategia quantitative research contact jose.felix@felixsarmiento.com"},
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = response.read()
                meta = {
                    "url": SAMPLE_URL,
                    "http_status": getattr(response, "status", 200),
                    "content_type": response.headers.get("Content-Type"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "attempt": attempt,
                }
                return payload, meta
        except Exception as exc:
            last_error = repr(exc)
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Unable to download public ORATS sample after 3 attempts: {last_error}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = load_universe()
    raw, download_meta = fetch_sample()
    (OUT_DIR / "download_metadata.json").write_text(
        json.dumps(download_meta, indent=2), encoding="utf-8"
    )
    files = extract_csvs(raw)
    if not files:
        raise RuntimeError("No CSV members found in public ORATS sample ZIP")

    file_summaries = []
    ticker_rows: Counter[str] = Counter()
    all_observed: set[str] = set()
    for member, csv_bytes in files:
        headers, rows = parse_csv(csv_bytes)
        ticker_field = find_field(headers, ("ticker", "underlying", "underlying_symbol"))
        if not ticker_field:
            raise RuntimeError(f"No ticker/underlying field in {member}: {headers[:30]}")
        observed = {
            str(row.get(ticker_field, "")).strip().upper()
            for row in rows
            if str(row.get(ticker_field, "")).strip()
        }
        all_observed.update(observed)
        for row in rows:
            ticker = str(row.get(ticker_field, "")).strip().upper()
            if ticker:
                ticker_rows[ticker] += 1

        aliases = {
            "trade_date": ("tradeDate", "trade_date", "quoteDate", "quote_date"),
            "expiration": ("expirDate", "expiration", "expiration_date", "expir_date"),
            "strike": ("strike", "strike_price"),
            "call_volume": ("cVolu", "callVolume", "call_volume"),
            "put_volume": ("pVolu", "putVolume", "put_volume"),
            "call_oi": ("cOi", "callOpenInterest", "call_oi"),
            "put_oi": ("pOi", "putOpenInterest", "put_oi"),
            "call_bid": ("cBidPx", "callBidPrice", "call_bid"),
            "call_ask": ("cAskPx", "callAskPrice", "call_ask"),
            "put_bid": ("pBidPx", "putBidPrice", "put_bid"),
            "put_ask": ("pAskPx", "putAskPrice", "put_ask"),
            "call_bid_iv": ("cBidIv", "callBidIv"),
            "call_ask_iv": ("cAskIv", "callAskIv"),
            "put_bid_iv": ("pBidIv", "putBidIv"),
            "put_ask_iv": ("pAskIv", "putAskIv"),
            "smoothed_iv": ("smoothSmvVol", "smvVol", "smooth_smv_vol"),
            "delta": ("delta",),
            "gamma": ("gamma",),
            "vega": ("vega",),
        }
        resolved = {name: find_field(headers, options) for name, options in aliases.items()}
        stats = {name: field_stats(rows, field) for name, field in resolved.items()}
        dates = sorted({
            str(row.get(resolved["trade_date"], "")).strip()
            for row in rows
            if resolved["trade_date"] and row.get(resolved["trade_date"])
        })
        file_summaries.append({
            "member": member,
            "row_count": len(rows),
            "header_count": len(headers),
            "headers": headers,
            "trade_dates": dates,
            "unique_underlyings": len(observed),
            "universe_coverage": compute_coverage(universe, observed),
            "resolved_fields": resolved,
            "field_stats": stats,
            "multiplier_or_deliverable_fields": [
                h for h in headers
                if any(token in norm(h) for token in ("multiplier", "deliverable", "sharespercontract", "contractsize"))
            ],
            "stock_price_field_present": bool(find_field(headers, ("stockPrice", "underlying_price", "close_price"))),
        })

    coverage = compute_coverage(universe, all_observed)
    ticker_csv = "ticker,row_count,in_frozen_universe\n" + "".join(
        f"{ticker},{count},{str(ticker in universe).lower()}\n"
        for ticker, count in sorted(ticker_rows.items())
    )
    (OUT_DIR / "ticker_coverage.csv").write_text(ticker_csv, encoding="utf-8")

    required = ("trade_date", "expiration", "strike", "call_volume", "put_volume",
                "call_oi", "put_oi", "call_bid", "call_ask", "put_bid", "put_ask",
                "smoothed_iv", "delta")
    all_required_present = all(
        all(summary["resolved_fields"].get(name) for name in required)
        for summary in file_summaries
    )
    summary = {
        "phase": "61_ORATS_NEAR_EOD_PUBLIC_SAMPLE_AUDIT",
        "status": "COMPLETE",
        "download": download_meta,
        "sample_files": file_summaries,
        "frozen_universe_coverage": coverage,
        "required_fields": list(required),
        "required_fields_present": all_required_present,
        "schema_gate": "PASS" if all_required_present and sum(x["row_count"] for x in file_summaries) > 0 else "FAIL",
        "coverage_gate": "MEASURED_NOT_PASSED",
        "delisted_retention_gate": "NOT_TESTED_BY_SINGLE_DATE_SAMPLE",
        "contract_multiplier_gate": "NEEDS_EXTERNAL_CONTRACT_REFERENCE" if not any(x["multiplier_or_deliverable_fields"] for x in file_summaries) else "FIELDS_PRESENT_REQUIRES_VALIDATION",
        "pit_rule": "Use next trading session as conservative KnowledgeDate; historical archive does not itself evidence when each file was first available.",
        "volume_semantics": "Call/put volume is the cumulative total at the 3:46 p.m. ET snapshot, not necessarily final full-day volume.",
        "open_interest_semantics": "Call/put OI is OCC data updated the previous night; do not treat as same-day final OI.",
        "underlying_price_semantics": "ORATS stockPrice/stkPx is derived from option prices via put-call parity, not an independent stock-price series.",
        "forward_returns_used": False,
        "alpha_test_authorized": False,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "stage": "ORATS_SAMPLE_AUDIT_COMPLETE",
        "rows": sum(x["row_count"] for x in file_summaries),
        "sample_files": len(file_summaries),
        "target_coverage": coverage["coverage_rate"],
        "schema_gate": summary["schema_gate"],
        "sha256": download_meta["sha256"],
    }), flush=True)
    if summary["schema_gate"] != "PASS":
        raise RuntimeError("ORATS sample schema gate failed")


if __name__ == "__main__":
    main()

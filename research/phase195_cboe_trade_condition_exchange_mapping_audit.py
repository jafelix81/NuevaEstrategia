#!/usr/bin/env python3
"""Phase 195: Cboe Option Trades condition/exchange reference mapping audit.

Downloads only public Cboe reference files and the one-day public sample.
No raw trades or mapping workbook bytes are persisted; only hashes, observed
ID counts, mapping descriptions and reconciliation results are emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import posixpath
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from research.phase194_cboe_option_trades_daily_flow_sample_audit import csv_members

CONDITION_XLSX_URL = "https://datashop.cboe.com/documents/livevol_trade_condition_ids.xlsx"
EXCHANGE_CSV_URL = "https://datashop.cboe.com/documents/livevol_exchange_ids.csv"
SAMPLE_URL = "https://datashop.cboe.com/download/sample/216"
MAX_FILE_BYTES = 100 * 1024 * 1024
RETRIES = 3


class DownloadError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].split(":")[-1]


def normalize_header(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())


def column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref.upper())
    if not letters:
        raise ValueError("xlsx_cell_reference_invalid")
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - 64
    return result - 1


def read_xlsx_sheets(payload: bytes) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
            raise ValueError("xlsx_workbook_parts_missing")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in root.iter():
                if local_name(si.tag) == "si":
                    shared.append("".join(x.text or "" for x in si.iter() if local_name(x.tag) == "t"))

        wb = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.attrib.get("Id"): r.attrib.get("Target") for r in rels}
        sheets: dict[str, list[list[str]]] = {}
        for sheet in wb.iter():
            if local_name(sheet.tag) != "sheet":
                continue
            sheet_name = sheet.attrib.get("name", "Sheet")
            rel_id = next((v for k, v in sheet.attrib.items() if k.endswith("}id") or k == "r:id"), None)
            target = rel_map.get(rel_id)
            if not target:
                continue
            path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
            if path not in names:
                continue
            root = ET.fromstring(archive.read(path))
            rows: list[list[str]] = []
            for row_node in root.iter():
                if local_name(row_node.tag) != "row":
                    continue
                cells: dict[int, str] = {}
                for cell in list(row_node):
                    if local_name(cell.tag) != "c":
                        continue
                    idx = column_index(cell.attrib.get("r", "A1"))
                    cell_type = cell.attrib.get("t", "")
                    value_node = next((x for x in list(cell) if local_name(x.tag) == "v"), None)
                    if cell_type == "s" and value_node is not None and value_node.text is not None:
                        value = shared[int(value_node.text)]
                    elif cell_type == "inlineStr":
                        value = "".join(x.text or "" for x in cell.iter() if local_name(x.tag) == "t")
                    else:
                        value = "" if value_node is None or value_node.text is None else value_node.text
                    cells[idx] = value
                if cells:
                    width = max(cells) + 1
                    rows.append([cells.get(i, "") for i in range(width)])
            sheets[sheet_name] = rows
        if not sheets:
            raise ValueError("xlsx_has_no_readable_sheets")
        return sheets


def _find_header(rows: list[list[str]], kind: str) -> tuple[int, list[str], int, int | None, int | None, int | None]:
    for row_index, row in enumerate(rows[:30]):
        normalized = [normalize_header(x) for x in row]
        if kind == "condition":
            ids = [i for i, h in enumerate(normalized) if h in {"tradeconditionid", "conditionid", "livevoltradeconditionid"} or ("condition" in h and h.endswith("id")) or h == "id"]
        else:
            ids = [i for i, h in enumerate(normalized) if h in {"exchangeid", "livevolexchangeid"} or ("exchange" in h and h.endswith("id")) or h == "id"]
        names = [i for i, h in enumerate(normalized) if "name" in h or "description" in h]
        if not ids or not names:
            continue
        id_idx = sorted(ids, key=lambda i: (0 if normalized[i] in {"tradeconditionid", "conditionid", "exchangeid"} else 1, i))[0]
        name_idx = sorted(names, key=lambda i: (0 if "name" in normalized[i] else 1, i))[0]
        type_idx = next((i for i, h in enumerate(normalized) if "messagetype" in h or h == "type"), None)
        security_idx = next((i for i, h in enumerate(normalized) if "securitytype" in h), None)
        return row_index, [str(x).strip() for x in row], id_idx, name_idx, type_idx, security_idx
    raise ValueError(f"{kind}_mapping_header_not_found")


def _id_int(value: object) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if not number.is_finite() or number != number.to_integral_value():
        return None
    return int(number)


def parse_condition_mapping(payload: bytes) -> dict[str, object]:
    sheets = read_xlsx_sheets(payload)
    candidates = []
    for sheet_name, rows in sheets.items():
        try:
            header_row, headers, id_idx, name_idx, type_idx, security_idx = _find_header(rows, "condition")
        except ValueError:
            continue
        entries = []
        for row in rows[header_row + 1:]:
            padded = row + [""] * max(0, len(headers) - len(row))
            code = _id_int(padded[id_idx])
            if code is None:
                continue
            fields = {headers[i]: padded[i] for i in range(min(len(headers), len(padded))) if padded[i] != ""}
            name = padded[name_idx].strip()
            message_type = padded[type_idx].strip().lower() if type_idx is not None else ""
            security_types = padded[security_idx].strip().lower() if security_idx is not None else ""
            entries.append({
                "id": code,
                "name": name,
                "message_type": message_type or None,
                "security_types": security_types or None,
                "fields": fields,
            })
        if entries:
            candidates.append((len(entries), sheet_name, headers, entries))
    if not candidates:
        raise ValueError("condition_mapping_rows_not_found")
    _, sheet_name, headers, entries = max(candidates, key=lambda x: x[0])
    by_id = {}
    for entry in entries:
        by_id.setdefault(entry["id"], entry)
    effective_fields = [h for h in headers if any(token in normalize_header(h) for token in ("effective", "startdate", "enddate", "validfrom", "validto"))]
    return {
        "sheet_name": sheet_name,
        "headers": headers,
        "row_count": len(entries),
        "mapping_by_id": by_id,
        "effective_date_fields": effective_fields,
    }


def parse_exchange_mapping_csv(payload: bytes) -> dict[str, object]:
    decoded = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = [str(x).strip() for x in (reader.fieldnames or [])]
    normalized = [normalize_header(x) for x in headers]
    id_candidates = [i for i, h in enumerate(normalized) if h in {"exchangeid", "livevolexchangeid"} or ("exchange" in h and h.endswith("id")) or h == "id"]
    name_candidates = [i for i, h in enumerate(normalized) if "name" in h or "description" in h]
    if not id_candidates or not name_candidates:
        raise ValueError("exchange_mapping_header_not_found")
    id_idx = id_candidates[0]
    name_idx = name_candidates[0]
    code_idx = next((i for i, h in enumerate(normalized) if "code" in h or "symbol" in h), None)
    by_id = {}
    for row in reader:
        values = [str(row.get(h, "") or "").strip() for h in headers]
        code = _id_int(values[id_idx])
        if code is None:
            continue
        by_id.setdefault(code, {
            "id": code,
            "name": values[name_idx],
            "code": values[code_idx] if code_idx is not None else None,
            "fields": {headers[i]: values[i] for i in range(len(headers)) if values[i]},
        })
    return {"headers": headers, "row_count": len(by_id), "mapping_by_id": by_id}


def classify_condition(entry: dict[str, object]) -> str:
    name = str(entry.get("name") or "").strip().lower()
    fields = entry.get("fields") if isinstance(entry.get("fields"), dict) else {}
    combined = " ".join([name] + [str(v).lower() for v in fields.values()])
    compact = normalize_header(combined)
    if any(token in compact for token in ("cancel", "bust", "broken", "correction", "corrected")):
        return "cancel_or_correction"
    if any(token in compact for token in ("late", "outofseq", "outofsequence", "priorreference")):
        return "late_or_out_of_sequence"
    if any(token in compact for token in ("complex", "spread", "combo", "multileg")):
        return "complex_or_spread"
    if any(token in compact for token in ("auction", "cross", "iso", "opening", "closing", "floor")):
        return "auction_or_cross"
    if any(token in compact for token in ("extended", "curb", "gth")):
        return "extended_hours"
    if name in {"regular", "normal"}:
        return "regular"
    return "unclassified_semantics"


def count_sample_ids(raw_zip: bytes) -> dict[str, object]:
    members = []
    for name, payload in csv_members(raw_zip):
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
        condition_counts: Counter[str] = Counter()
        exchange_counts: Counter[str] = Counter()
        cancel_counts: Counter[str] = Counter()
        nonblank = 0
        for row in reader:
            if not any(str(v or "").strip() for v in row.values()):
                continue
            nonblank += 1
            condition = str(row.get("trade_condition_id", "") or "").strip()
            exchange = str(row.get("exchange_id", "") or "").strip()
            cancel = str(row.get("canceled_trade_condition_id", "") or "").strip()
            condition_counts[condition or "BLANK"] += 1
            exchange_counts[exchange or "BLANK"] += 1
            cancel_counts[cancel or "BLANK"] += 1
        members.append({
            "member_basename": name.replace("\\", "/").rsplit("/", 1)[-1],
            "nonblank_rows": nonblank,
            "condition_counts": dict(sorted(condition_counts.items())),
            "exchange_counts": dict(sorted(exchange_counts.items())),
            "canceled_condition_counts": dict(sorted(cancel_counts.items())),
        })
    if not members:
        raise ValueError("sample_has_no_csv_members")
    condition_sets = {json.dumps(m["condition_counts"], sort_keys=True) for m in members}
    exchange_sets = {json.dumps(m["exchange_counts"], sort_keys=True) for m in members}
    row_counts = {m["nonblank_rows"] for m in members}
    expected_pair_present = len(members) == 2 and any("calcs" not in m["member_basename"].lower() for m in members) and any("calcs" in m["member_basename"].lower() for m in members)
    return {
        "member_count": len(members),
        "expected_two_member_pair_present": expected_pair_present,
        "members": members,
        "core_id_counts_match_across_members": expected_pair_present and len(condition_sets) == 1 and len(exchange_sets) == 1 and len(row_counts) == 1,
        "observed_condition_counts": members[0]["condition_counts"],
        "observed_exchange_counts": members[0]["exchange_counts"],
        "observed_canceled_condition_counts": members[0]["canceled_condition_counts"],
    }


def _fetch(url: str, max_bytes: int) -> tuple[bytes, dict[str, str]]:
    request = Request(url, headers={
        "User-Agent": "NuevaEstrategia research audit",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,application/zip,*/*",
        "Accept-Encoding": "identity",
    })
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read(max_bytes + 1)
                if len(payload) > max_bytes:
                    raise DownloadError("file_size_limit_exceeded")
                headers = {
                    "http_status": str(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "date": response.headers.get("Date", ""),
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "content_length": response.headers.get("Content-Length", ""),
                }
                return payload, headers
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise DownloadError(f"http_{exc.code}") from None
        except URLError:
            if attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise DownloadError("url_error") from None
    raise DownloadError("retry_exhausted")


def run_audit() -> dict[str, object]:
    result: dict[str, object] = {
        "phase": 195,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING",
        "condition_mapping_url": CONDITION_XLSX_URL,
        "exchange_mapping_url": EXCHANGE_CSV_URL,
        "sample_url": SAMPLE_URL,
        "data_purchase": False,
        "vendor_contact": False,
        "raw_sample_persisted": False,
        "raw_mapping_files_persisted": False,
        "raw_trade_rows_persisted": False,
        "raw_symbols_persisted": False,
        "raw_contracts_persisted": False,
        "first_receipt_verified": False,
        "mapping_effective_dates_verified": False,
        "historical_mapping_pit_verified": False,
        "strict_pit_admitted": False,
        "signed_flow_feature_admitted": False,
        "alpha_admission": False,
        "holdout_used": False,
        "production_changed": False,
        "f80_frozen": True,
    }
    try:
        condition_bytes, condition_headers = _fetch(CONDITION_XLSX_URL, 15 * 1024 * 1024)
        exchange_bytes, exchange_headers = _fetch(EXCHANGE_CSV_URL, 5 * 1024 * 1024)
        time.sleep(0.25)
        sample_bytes, sample_headers = _fetch(SAMPLE_URL, MAX_FILE_BYTES)
        condition_map = parse_condition_mapping(condition_bytes)
        exchange_map = parse_exchange_mapping_csv(exchange_bytes)
        sample_ids = count_sample_ids(sample_bytes)

        observed_conditions = sample_ids["observed_condition_counts"]
        observed_exchanges = sample_ids["observed_exchange_counts"]
        condition_lookup = condition_map["mapping_by_id"]
        exchange_lookup = exchange_map["mapping_by_id"]
        condition_reconciliation = []
        for raw_id, count in observed_conditions.items():
            code = _id_int(raw_id)
            entry = condition_lookup.get(code) if code is not None else None
            if entry:
                condition_reconciliation.append({
                    "id": code,
                    "observed_rows": count,
                    "name": entry["name"],
                    "message_type": entry["message_type"],
                    "security_types": entry["security_types"],
                    "classification": classify_condition(entry),
                    "candidate_side_eligible": (
                        classify_condition(entry) == "regular"
                        and entry["message_type"] == "trade"
                        and "option" in str(entry["security_types"] or "")
                    ),
                    "mapping_fields": entry["fields"],
                })
            else:
                condition_reconciliation.append({"id": code, "observed_rows": count, "mapping_status": "UNMAPPED"})
        exchange_reconciliation = []
        for raw_id, count in observed_exchanges.items():
            code = _id_int(raw_id)
            entry = exchange_lookup.get(code) if code is not None else None
            if entry:
                exchange_reconciliation.append({"id": code, "observed_rows": count, "name": entry["name"], "code": entry["code"], "mapping_fields": entry["fields"]})
            else:
                exchange_reconciliation.append({"id": code, "observed_rows": count, "mapping_status": "UNMAPPED"})

        unmapped_conditions = [x["id"] for x in condition_reconciliation if x.get("mapping_status") == "UNMAPPED"]
        unmapped_exchanges = [x["id"] for x in exchange_reconciliation if x.get("mapping_status") == "UNMAPPED"]
        eligible_rows = sum(x["observed_rows"] for x in condition_reconciliation if x.get("candidate_side_eligible"))
        result.update({
            "status": "MAPPINGS_RECONCILED" if not unmapped_conditions and not unmapped_exchanges and sample_ids["core_id_counts_match_across_members"] else "MAPPING_GAP_OR_MEMBER_MISMATCH",
            "condition_mapping_sha256": hashlib.sha256(condition_bytes).hexdigest(),
            "exchange_mapping_sha256": hashlib.sha256(exchange_bytes).hexdigest(),
            "sample_archive_sha256": hashlib.sha256(sample_bytes).hexdigest(),
            "condition_mapping_bytes": len(condition_bytes),
            "exchange_mapping_bytes": len(exchange_bytes),
            "sample_archive_bytes": len(sample_bytes),
            "condition_mapping_response_headers": condition_headers,
            "exchange_mapping_response_headers": exchange_headers,
            "sample_response_headers": sample_headers,
            "condition_mapping_sheet": condition_map["sheet_name"],
            "condition_mapping_headers": condition_map["headers"],
            "condition_mapping_rows": condition_map["row_count"],
            "condition_mapping_effective_date_fields": condition_map["effective_date_fields"],
            "exchange_mapping_headers": exchange_map["headers"],
            "exchange_mapping_rows": exchange_map["row_count"],
            "sample_id_audit": sample_ids,
            "condition_reconciliation": condition_reconciliation,
            "exchange_reconciliation": exchange_reconciliation,
            "unmapped_condition_ids": unmapped_conditions,
            "unmapped_exchange_ids": unmapped_exchanges,
            "all_observed_condition_ids_mapped": not unmapped_conditions,
            "all_observed_exchange_ids_mapped": not unmapped_exchanges,
            "sample_core_id_counts_match_across_members": sample_ids["core_id_counts_match_across_members"],
            "candidate_side_eligible_condition_ids": [x["id"] for x in condition_reconciliation if x.get("candidate_side_eligible")],
            "candidate_side_eligible_rows_under_strict_mapping_rule": eligible_rows,
            "mapping_effective_date_fields_present": bool(condition_map["effective_date_fields"]),
            "mapping_effective_dates_verified": False,
            "mapping_current_snapshot_only": not bool(condition_map["effective_date_fields"]),
            "historical_mapping_pit_verified": False,
            "decision": "Current public mapping files are reconciled to the one-day sample only. Even a complete ID mapping does not establish historical effective dates or first receipt. Candidate side eligibility is deliberately restricted to a mapping row explicitly marked Regular/Normal, trade, and options; all other conditions remain quarantined. No signed-flow feature or alpha test is admitted."
        })
    except (DownloadError, ValueError, zipfile.BadZipFile, ET.ParseError, KeyError, IndexError, json.JSONDecodeError) as exc:
        result.update({"status": "DOWNLOAD_OR_PARSE_FAILED", "error_code": exc.code if isinstance(exc, DownloadError) else str(exc)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase195_output")
    args = parser.parse_args()
    result = run_audit()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "phase195_cboe_trade_condition_exchange_mapping_audit.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

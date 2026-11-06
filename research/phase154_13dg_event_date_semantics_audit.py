#!/usr/bin/env python3
"""Phase 154: audit Schedule 13D/G event-date semantics and reporting-regime breaks.

Consumes the immutable Phase 35/28D artifact only. It does not download SEC data,
assign a trade signal, or treat event_date as the market-knowledge timestamp.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

EXPECTED_OUTER_SHA256 = "1ba55129f8a2f2365b37e20f557759fbccd2ab2f22781f03930065c11f16337f"
EXPECTED_CSV_SHA256 = "4a1b40cf7e104be0dc5bad4d579cd65ef78ab4783a4f525f19a299b50f3efa14"
SOURCE_RUN_ID = 41575083622
SOURCE_ARTIFACT_ID = 13212292743
SOURCE_MEMBER = "phase28d_events.csv"
REGIME_BREAK = date(2024, 9, 30)


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date {value!r}") from exc


def base_form(value: str) -> str:
    value = (value or "").strip().upper()
    return value[:-2] if value.endswith("/A") else value


def is_quarter_end(value: date | None) -> bool:
    if value is None:
        return False
    last = {3: 31, 6: 30, 9: 30, 12: 31}
    return value.month in last and value.day == last[value.month]


def pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 4) if d else None


def is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def lag_stats(values: list[int]) -> dict:
    values = sorted(values)
    if not values:
        return {"median": None, "p90": None, "p99": None, "min": None, "max": None,
                "over_365_days": 0, "negative": 0}

    def quantile(p: float) -> float:
        pos = (len(values) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (pos - lo)

    return {"median": quantile(.5), "p90": quantile(.9), "p99": quantile(.99),
            "min": values[0], "max": values[-1],
            "over_365_days": sum(x > 365 for x in values),
            "negative": sum(x < 0 for x in values)}


def audit_rows(rows: list[dict[str, str]], outer_sha256: str | None, csv_sha256: str) -> dict:
    if not rows:
        raise ValueError("No event rows")
    required = {"ticker", "issuer_cik", "form", "filing_date", "report_date", "event_date",
                "filing_lag_business_days", "accession", "reporting_person",
                "reporting_person_type", "purpose_text", "event_date_available",
                "is_amendment", "mapping_source"}
    if not required.issubset(rows[0]):
        raise ValueError(f"Missing columns: {sorted(required - set(rows[0]))}")

    accessions = [r["accession"].strip() for r in rows]
    if any(not x for x in accessions):
        raise ValueError("Missing accession")
    accession_counts = Counter(accessions)
    duplicate_accessions = sum(n - 1 for n in accession_counts.values() if n > 1)

    forms, amendments, mapping, lag_field = Counter(), Counter(), Counter(), Counter()
    groups = defaultdict(lambda: {"rows": 0, "event_valid": 0, "event_missing": 0,
                                   "event_after_filing": 0, "event_same_day": 0,
                                   "quarter_end_event": 0, "calendar_lags": [],
                                   "reporting_person_missing": 0, "purpose_text_present": 0})
    filing_dates, source_ciks, source_tickers, all_lags = [], set(), set(), []
    report_date_missing = reporting_person_missing = person_type_missing = purpose_present = 0
    future_events, event_missing, event_after, event_same = [], 0, 0, 0

    for row in rows:
        filing = parse_date(row.get("filing_date", ""))
        event = parse_date(row.get("event_date", ""))
        if filing is None:
            raise ValueError("Missing filing_date")
        filing_dates.append(filing)
        source_ciks.add(row.get("issuer_cik", "").strip())
        source_tickers.add(row.get("ticker", "").strip())
        form = (row.get("form", "") or "").strip().upper()
        base = base_form(form)
        if base not in {"SC 13D", "SC 13G"}:
            raise ValueError(f"Unexpected form {form!r}")
        is_amend = form.endswith("/A") or row.get("is_amendment", "").strip().lower() == "true"
        forms[form] += 1
        amendments[str(bool(is_amend)).lower()] += 1
        mapping[(row.get("mapping_source", "") or "").strip()] += 1
        lag_value = (row.get("filing_lag_business_days", "") or "").strip()
        lag_field[lag_value if lag_value else "<MISSING>"] += 1
        report_date_missing += not bool((row.get("report_date", "") or "").strip())
        reporting_person_missing += not bool((row.get("reporting_person", "") or "").strip())
        person_type_missing += not bool((row.get("reporting_person_type", "") or "").strip())
        purpose_present += bool((row.get("purpose_text", "") or "").strip())

        regime = "pre_2024-09-30" if filing < REGIME_BREAK else "post_2024-09-30"
        key = (base, "amendment" if is_amend else "original", regime)
        group = groups[key]
        group["rows"] += 1
        if event is None:
            event_missing += 1
            group["event_missing"] += 1
        else:
            group["event_valid"] += 1
            lag = (filing - event).days
            group["calendar_lags"].append(lag)
            all_lags.append(lag)
            if is_quarter_end(event):
                group["quarter_end_event"] += 1
            if event > filing:
                event_after += 1
                group["event_after_filing"] += 1
                future_events.append({"accession": row["accession"], "issuer_cik": row["issuer_cik"],
                                      "ticker": row["ticker"], "form": form,
                                      "filing_date": filing.isoformat(), "event_date": event.isoformat()})
            elif event == filing:
                event_same += 1
                group["event_same_day"] += 1
        group["reporting_person_missing"] += not bool((row.get("reporting_person", "") or "").strip())
        group["purpose_text_present"] += bool((row.get("purpose_text", "") or "").strip())

    groups_out = {}
    for key, group in sorted(groups.items()):
        name = "|".join(key)
        groups_out[name] = {
            "rows": group["rows"], "event_valid": group["event_valid"],
            "event_missing": group["event_missing"], "event_after_filing": group["event_after_filing"],
            "event_same_day": group["event_same_day"],
            "quarter_end_event_count": group["quarter_end_event"],
            "quarter_end_event_pct_of_valid": pct(group["quarter_end_event"], group["event_valid"]),
            "calendar_lag_days": lag_stats(group["calendar_lags"]),
            "reporting_person_missing": group["reporting_person_missing"],
            "purpose_text_present": group["purpose_text_present"]
        }

    lag_numeric = {k: v for k, v in lag_field.items() if k != "<MISSING>"}
    negative_lag_rows = sum(v for k, v in lag_numeric.items() if is_number(k) and float(k) < 0)
    zero_lag_rows = sum(v for k, v in lag_numeric.items() if is_number(k) and float(k) == 0)
    distinct_lag_values = sorted(lag_numeric, key=lambda x: float(x) if is_number(x) else x)

    return {
        "phase": 154,
        "status": "COMPLETED_OFFLINE_EVENT_DATE_SEMANTICS_AUDIT",
        "source": {"provider": "SEC", "phase35_run_id": SOURCE_RUN_ID,
                   "artifact_id": SOURCE_ARTIFACT_ID, "outer_zip_sha256": outer_sha256,
                   "github_artifact_digest_sha256": EXPECTED_OUTER_SHA256,
                   "member": SOURCE_MEMBER, "member_sha256": csv_sha256, "rows": len(rows)},
        "identity_and_integrity": {"unique_accessions": len(accession_counts),
                                   "duplicate_accession_rows": duplicate_accessions,
                                   "unique_source_ciks_not_subject_validated": len(source_ciks), "unique_source_tickers_not_subject_validated": len(source_tickers),\n                                   "identity_scope": "CIK_SUBMISSIONS_QUERY_SOURCE_NOT_SUBJECT_ISSUER_VALIDATED",
                                   "filing_date_min": min(filing_dates).isoformat(),
                                   "filing_date_max": max(filing_dates).isoformat()},
        "form_counts": dict(sorted(forms.items())),
        "amendment_counts": dict(sorted(amendments.items())),
        "event_date_quality": {"missing": event_missing, "after_filing": event_after,
                               "same_day": event_same,
                               "before_filing": len(rows) - event_missing - event_after - event_same,
                               "calendar_lag_days_all_valid": lag_stats(all_lags),
                               "future_event_rows": future_events},
        "quarter_end_event_date_by_form_regime": groups_out,
        "reported_filing_lag_business_days": {
            "value_counts": dict(sorted(lag_field.items())),
            "negative_rows": negative_lag_rows, "zero_rows": zero_lag_rows,
            "missing_rows": lag_field["<MISSING>"],
            "distinct_nonmissing_values": distinct_lag_values,
            "decision": "INVALID_DO_NOT_USE; observed values are -1/0, not a valid nonnegative business-day lag"},
        "field_coverage": {"report_date_missing": report_date_missing,
                           "reporting_person_missing": reporting_person_missing,
                           "reporting_person_type_missing": person_type_missing,
                           "purpose_text_present": purpose_present,
                           "mapping_source_counts": dict(sorted(mapping.items()))},
        "interpretation": {
            "13D": "Treat event_date as a candidate reported trigger/event date only; filing acceptance is the earliest public-knowledge boundary. Separate original 13D from 13D/A and adjudicate stale/extreme event lags.",
            "13G": "Do not treat event_date as a common trade/accumulation timestamp. Quarter-end concentration is consistent with reporting-period anchors and the filing regime; separate original filings, amendments, filer categories and rule regimes.",
            "knowledge_time": "Use actual EDGAR acceptance timestamp, not event_date or date-only filing_date, for market-knowledge timing.",
            "amendments": "13D/A and 13G/A are filing-time state updates. Do not count each amendment as a new independent accumulation event without accession lineage and line-level changes.",
            "universe": "The 303 issuer/ticker identities in this artifact are conditional on the earlier candidate 335 list; they do not establish historical active-universe membership or survivorship-free coverage."
        },
        "alpha_test": False, "final_holdout_used": False, "f80_modified": False,
        "decision": "Quarantine the legacy filing_lag_business_days field. Do not pool 13D and 13G event_date. Retain 13D/13G only as distinct filing-time event/state hypotheses after acceptance-time, filer-category, amendment-lineage and historical-universe gates."
    }


def load_artifact(path: Path, verify_hash: bool = True):
    """Load original artifact ZIP or actions/download-artifact's extracted directory."""
    outer = None
    if path.is_dir():
        member = path / SOURCE_MEMBER
        if not member.is_file():
            raise ValueError(f"Missing extracted source member: {member}")
        payload = member.read_bytes()
    else:
        raw = path.read_bytes()
        outer = hashlib.sha256(raw).hexdigest()
        if verify_hash and outer != EXPECTED_OUTER_SHA256:
            raise ValueError(f"Outer ZIP SHA-256 mismatch: {outer}")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [name for name in archive.namelist() if name.rsplit("/", 1)[-1] == SOURCE_MEMBER]
            if len(names) != 1:
                raise ValueError(f"Expected exactly one {SOURCE_MEMBER}, found {names}")
            payload = archive.read(names[0])
    inner = hashlib.sha256(payload).hexdigest()
    if verify_hash and inner != EXPECTED_CSV_SHA256:
        raise ValueError(f"CSV SHA-256 mismatch: {inner}")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    return rows, outer, inner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True,
                        help="Original ZIP or extracted actions/download-artifact directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-hash-check", action="store_true",
                        help="Only for synthetic/local debugging")
    args = parser.parse_args()
    rows, outer, inner = load_artifact(args.input, verify_hash=not args.no_hash_check)
    result = audit_rows(rows, outer, inner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"phase": 154, "status": result["status"], "rows": result["source"]["rows"],
                      "form_counts": result["form_counts"],
                      "event_date_quality": {k: result["event_date_quality"][k]
                                             for k in ("missing", "after_filing", "same_day", "before_filing")},
                      "reported_filing_lag_business_days": result["reported_filing_lag_business_days"],
                      "quarter_end_event_date_by_form_regime": result["quarter_end_event_date_by_form_regime"]},
                     indent=2))


if __name__ == "__main__":
    main()

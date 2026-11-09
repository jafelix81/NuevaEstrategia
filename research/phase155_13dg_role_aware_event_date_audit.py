#!/usr/bin/env python3
"""Phase 155: role-aware SEC 13D/G event-date validation and Phase 154 source quarantine."""
from __future__ import annotations
import argparse, csv, hashlib, json, statistics
from collections import Counter
from datetime import datetime, date
from pathlib import Path

PHASE124_RUN_ID = 42073725379
PHASE124_ARTIFACT_ID = 13436764625
PHASE124_CSV_SHA256 = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
PHASE35_RUN_ID = 41575083622
PHASE35_ARTIFACT_ID = 13212292743
PHASE35_CSV_SHA256 = "4a1b40cf7e104be0dc5bad4d579cd65ef78ab4783a4f525f19a299b50f3efa14"
CONTROL_ACCESSION = "0000895421-24-000178"
CONTROL_FILER_CIK = "0000895421"
CONTROL_SUBJECT_CIK = "0001793855"
CONTROL_TICKER = "MS"
CONTROL_PRIMARY_DOCUMENT = "abrdnGlobalASGI.txt"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_event_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported event_date format: {value!r}")

def parse_acceptance(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d%H%M%S")

def is_quarter_end(d: date) -> bool:
    return d.month in (3, 6, 9, 12) and d.day == {3: 31, 6: 30, 9: 30, 12: 31}[d.month]

def load_csv(directory: Path, name: str, expected_sha: str, expected_rows: int):
    path = directory / name
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = path.read_bytes()
    digest = sha256(payload)
    if digest != expected_sha:
        raise ValueError(f"{name} SHA-256 mismatch: {digest}")
    rows = list(csv.DictReader(payload.decode("utf-8-sig").splitlines()))
    if len(rows) != expected_rows:
        raise ValueError(f"{name} row count mismatch: {len(rows)} != {expected_rows}")
    return rows, digest

def weighted_rate(rows: list[dict], predicate) -> dict:
    denom = sum(float(r["sample_weight"]) for r in rows)
    numer = sum(float(r["sample_weight"]) for r in rows if predicate(r))
    return {
        "unweighted_n": len(rows),
        "unweighted_count": sum(bool(predicate(r)) for r in rows),
        "unweighted_pct": round(100 * sum(bool(predicate(r)) for r in rows) / len(rows), 4) if rows else None,
        "sample_weight_denominator": round(denom, 6),
        "sample_weight_numerator": round(numer, 6),
        "sample_weighted_pct_within_observed_xml_subset": round(100 * numer / denom, 4) if denom else None
    }

def audit_phase35(rows: list[dict[str, str]]) -> dict:
    matches = [r for r in rows if r.get("accession", "").strip() == CONTROL_ACCESSION]
    if len(matches) != 1:
        raise ValueError(f"Expected one Phase 35 positive-control row, found {len(matches)}")
    r = matches[0]
    control_matches = (
        r.get("ticker") == CONTROL_TICKER
        and r.get("issuer_cik") == CONTROL_FILER_CIK
        and r.get("primary_document") == CONTROL_PRIMARY_DOCUMENT
        and r.get("form") == "SC 13G"
        and r.get("filing_date") == "2024-02-12"
        and r.get("event_date") == "2024-12-31"
    )
    if not control_matches:
        raise ValueError("Pinned Morgan Stanley/abrdn positive control no longer matches Phase 35 artifact")
    report_date_missing = sum(not (x.get("report_date") or "").strip() for x in rows)
    lag_counts = Counter((x.get("filing_lag_business_days") or "").strip() or "<MISSING>" for x in rows)
    return {
        "run_id": PHASE35_RUN_ID, "artifact_id": PHASE35_ARTIFACT_ID,
        "rows": len(rows), "report_date_missing_rows": report_date_missing,
        "report_date_missing_pct": round(100 * report_date_missing / len(rows), 4),
        "filing_lag_business_days_value_counts": dict(sorted(lag_counts.items())),
        "identity_scope": "CIK_SUBMISSIONS_QUERY_SOURCE_NOT_SUBJECT_ISSUER_VALIDATED",
        "known_positive_control": {
            "accession": CONTROL_ACCESSION, "source_ticker": r.get("ticker"),
            "source_cik": r.get("issuer_cik"), "known_filer_cik": CONTROL_FILER_CIK,
            "independently_validated_subject_cik": CONTROL_SUBJECT_CIK,
            "primary_document": r.get("primary_document"), "filing_date": r.get("filing_date"),
            "event_date": r.get("event_date"),
            "mismatch_confirmed": control_matches and r.get("issuer_cik") != CONTROL_SUBJECT_CIK,
            "interpretation": "The row is keyed to Morgan Stanley as submitting filer/query CIK, while the filing subject is abrdn Global Infrastructure Income Fund. The source CIK is not a safe issuer identity."
        },
        "decision": "FILER_SUBMISSIONS_DISCOVERY_DIAGNOSTIC_ONLY; exclude the entire Phase 35/28D panel from issuer-level events, security joins, model features and returns."
    }

def audit_phase124(rows: list[dict[str, str]]) -> dict:
    aliases = [r for r in rows if (r.get("is_index_alias") or "").lower() == "true"]
    actual = [r for r in rows if (r.get("is_index_alias") or "").lower() != "true"]
    if len(actual) != 599 or len(aliases) != 1:
        raise ValueError(f"Unexpected Phase 124 actual/alias counts: {len(actual)}/{len(aliases)}")
    xml_rows = [r for r in actual if (r.get("xml_present") or "").lower() == "true"]
    if len(xml_rows) != 102:
        raise ValueError(f"Unexpected XML rows: {len(xml_rows)}")
    if any((r.get("xml_subject_matches_header") or "").lower() != "true" or
           (r.get("xml_filer_matches_header") or "").lower() != "true" for r in xml_rows):
        raise ValueError("XML subject/filer concordance failure in Phase 124 sample")
    event_rows = [r for r in actual if (r.get("event_date") or "").strip()]
    if len(event_rows) != 102 or any(r not in xml_rows for r in event_rows):
        raise ValueError("Event-date subset is not exactly the role-validated structured XML subset")
    if any(not (r.get("subject_cik") or "").strip() for r in event_rows):
        raise ValueError("Event-date row missing SEC-header subject CIK")

    normalized = []
    for r in event_rows:
        d = parse_event_date(r["event_date"])
        filing = datetime.strptime(r["filing_date_header"], "%Y-%m-%d").date()
        accepted = parse_acceptance(r["acceptance_datetime"])
        normalized.append({
            **r, "_event": d, "_filing": filing, "_acceptance": accepted,
            "_lag": (filing - d).days, "_quarter_end": is_quarter_end(d),
            "_after_16": (accepted.hour, accepted.minute, accepted.second) > (16, 0, 0)
        })

    by_family = {}
    for family in ("13D", "13G"):
        group = [r for r in normalized if r["family"] == family]
        lags = [r["_lag"] for r in group]
        after16 = sum(r["_after_16"] for r in group)
        by_family[family] = {
            "n_event_dates": len(group),
            "quarter_end": weighted_rate(group, lambda r: r["_quarter_end"]),
            "lag_calendar_days": {
                "median": statistics.median(lags) if lags else None,
                "min": min(lags) if lags else None, "max": max(lags) if lags else None,
                "same_day": sum(x == 0 for x in lags),
                "event_after_filing": sum(x < 0 for x in lags),
                "filing_after_event": sum(x > 0 for x in lags)
            },
            "acceptance_after_160000_ET": {
                "count": after16, "pct": round(100 * after16 / len(group), 4) if group else None
            },
            "by_amendment": {}
        }
        for amendment in (False, True):
            subgroup = [r for r in group if (r.get("is_amendment") or "").lower() == str(amendment).lower()]
            by_family[family]["by_amendment"][str(amendment).lower()] = weighted_rate(subgroup, lambda r: r["_quarter_end"])

    rule_groups = {}
    rules = sorted({rule for r in normalized if r["family"] == "13G" for rule in json.loads(r.get("rule_designations") or "[]")})
    for rule in rules:
        group = [r for r in normalized if r["family"] == "13G" and rule in json.loads(r.get("rule_designations") or "[]")]
        rule_groups[rule] = weighted_rate(group, lambda r: r["_quarter_end"])

    return {
        "run_id": PHASE124_RUN_ID, "artifact_id": PHASE124_ARTIFACT_ID,
        "sample_rows": len(rows), "actual_13dg_submissions": len(actual),
        "quarantined_index_aliases": len(aliases),
        "unique_subject_ciks_in_sample": len({r["subject_cik"] for r in actual if (r.get("subject_cik") or "").strip()}),
        "xml_rows": len(xml_rows), "xml_subject_filer_header_concordance": "PASS_102_OF_102",
        "event_date_rows": len(event_rows),
        "event_date_coverage_of_actual_sample_pct": round(100 * len(event_rows) / len(actual), 4),
        "event_date_scope": "Only role-validated structured XML rows in this artifact; not a full historical event-date panel.",
        "by_family": by_family, "13g_by_rule_designation": rule_groups,
        "limitations": [
            "Deterministic hash-stratified global filing-index sample, not a full historical investable universe or active/delisted security master.",
            "Only 102/599 actual filings have event_date in this artifact; those are structured XML rows. Legacy HTML event-date extraction is not validated by this phase.",
            "Sample weights are reported only as weighted descriptive ratios within the observed XML event-date subset; schema/regime-dependent missingness prevents interpreting them as population-wide rates.",
            "No formal inferential confidence intervals are claimed; counts are modest, especially after form/rule splits.",
            "EDGAR acceptance timestamp is the earliest public-knowledge boundary available here, not proof of exact public dissemination time; after-16:00 ET filings should conservatively be treated as next-session information for regular-session strategies."
        ]
    }

def audit(phase124_rows: list[dict[str, str]], phase35_rows: list[dict[str, str]]) -> dict:
    p124 = audit_phase124(phase124_rows)
    p35 = audit_phase35(phase35_rows)
    return {
        "phase": 155,
        "status": "COMPLETED_ROLE_AWARE_EVENT_DATE_AUDIT_AND_PHASE154_SOURCE_QUARANTINE",
        "source_hashes": {"phase124_csv_sha256": PHASE124_CSV_SHA256, "phase35_csv_sha256": PHASE35_CSV_SHA256},
        "phase124_role_aware_sample": p124, "phase35_source_quarantine": p35,
        "phase154_adjudication": {
            "original_source_run_id": PHASE35_RUN_ID, "original_source_artifact_id": PHASE35_ARTIFACT_ID,
            "original_report_claims_of_303_issuer_ids_and_tickers": "INVALID_AS_SUBJECT_ISSUER_IDENTITY; these are source/query CIKs and associated tickers, not validated subject issuers.",
            "form_level_event_date_distribution": "Retain only as descriptive statistics of the filer-query sample, not a subject-issuer event panel or alpha evidence.",
            "reported_filing_lag_business_days": "INVALID; only -1, 0 and missing observed.",
            "report_date": "Missing in 100% of the Phase 35 artifact rows.",
            "decision": "Supersede Phase 154 issuer-level interpretation. Preserve descriptive form-level counts with explicit sample/provenance caveat; no issuer-level join or return test."
        },
        "alpha_test": False, "final_holdout_used": False, "f80_modified": False,
        "decision": "13D and 13G event_date semantics differ in the role-validated sample. 13G event_date is strongly quarter-end concentrated; 13D is not. Neither event_date is a knowledge timestamp. Use accession acceptance time, subject/filer role validation, filer-rule category and amendment lineage. Keep Phase 35/28D filer-query data quarantined."
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase124-input", type=Path, required=True)
    ap.add_argument("--phase35-input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    p124, h124 = load_csv(args.phase124_input, "phase124_global_13dg_submission_audit.csv", PHASE124_CSV_SHA256, 600)
    p35, h35 = load_csv(args.phase35_input, "phase28d_events.csv", PHASE35_CSV_SHA256, 20265)
    result = audit(p124, p35)
    result["source_hashes"]["phase124_csv_sha256_verified"] = h124
    result["source_hashes"]["phase35_csv_sha256_verified"] = h35
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": 155, "status": result["status"],
        "phase124": {
            "event_date_rows": result["phase124_role_aware_sample"]["event_date_rows"],
            "13D_quarter_end_n": result["phase124_role_aware_sample"]["by_family"]["13D"]["quarter_end"]["unweighted_count"],
            "13G_quarter_end_n": result["phase124_role_aware_sample"]["by_family"]["13G"]["quarter_end"]["unweighted_count"],
            "13G_quarter_end_weighted_pct": result["phase124_role_aware_sample"]["by_family"]["13G"]["quarter_end"]["sample_weighted_pct_within_observed_xml_subset"]
        },
        "phase35": {
            "report_date_missing_pct": result["phase35_source_quarantine"]["report_date_missing_pct"],
            "known_subject_mismatch": result["phase35_source_quarantine"]["known_positive_control"]["mismatch_confirmed"]
        },
        "decision": result["decision"]
    }, indent=2))

if __name__ == "__main__":
    main()

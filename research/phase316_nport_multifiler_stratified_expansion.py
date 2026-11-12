#!/usr/bin/env python3
"""Phase 316: deterministic multi-registrant, multi-quarter N-PORT raw QA.

Five distinct registrant CIKs are hash-ranked per quarter and exact data-bearing
form. The prior Phase 311 sample is excluded. This is not a probability sample,
holdings-prevalence estimate, trade-flow proxy, or return/alpha test.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
import requests

try:
    from research.phase312_nport_raw_sample_audit import (
        cusip_check_digit_valid, isin_check_digit_valid, parse_holding_rows,
    )
    from research.phase314_nport_amendment_parent_audit import (
        extract_primary_xml, parse_submission,
    )
except ModuleNotFoundError:
    from phase312_nport_raw_sample_audit import (
        cusip_check_digit_valid, isin_check_digit_valid, parse_holding_rows,
    )
    from phase314_nport_amendment_parent_audit import (
        extract_primary_xml, parse_submission,
    )

SEC_ARCHIVES = "https://www.sec.gov/Archives"
DATA_FORMS = {"NPORT-P", "NPORT-P/A"}
SAMPLE_VERSION = "phase316-five-distinct-registrants-per-quarter-form-v1"
DEFAULT_PER_STRATUM = 5


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def accession_hash(row: dict[str, str]) -> str:
    key = "|".join((SAMPLE_VERSION, row["quarter"], row["form_type"], row["accession"]))
    return hashlib.sha256(key.encode("ascii")).hexdigest()


def select_expanded_sample(census_rows, prior_sample_rows, per_stratum=DEFAULT_PER_STRATUM):
    if per_stratum < 1:
        raise ValueError("per_stratum_must_be_positive")
    accessions = [row.get("accession", "") for row in census_rows]
    if not all(accessions) or len(accessions) != len(set(accessions)):
        raise ValueError("census_accessions_missing_or_duplicated")
    prior = {row.get("accession", "") for row in prior_sample_rows}
    groups = defaultdict(list)
    for row in census_rows:
        if row.get("form_type") not in DATA_FORMS or row.get("accession") in prior:
            continue
        if not row.get("cik", "").isdigit() or not row.get("quarter") or not row.get("filename"):
            raise ValueError("census_candidate_required_field_missing")
        groups[(row["quarter"], row["form_type"])].append(row)
    strata = sorted({(r["quarter"], r["form_type"]) for r in census_rows if r.get("form_type") in DATA_FORMS})
    if len(groups) != len(strata):
        raise ValueError("one_or_more_quarter_form_strata_empty")
    selected = []
    for quarter, form_type in strata:
        items = sorted(groups[(quarter, form_type)], key=lambda r: (accession_hash(r), r["accession"]))
        distinct_ciks = {r["cik"].zfill(10) for r in items}
        chosen, used = [], set()
        for rank, row in enumerate(items, start=1):
            cik = row["cik"].zfill(10)
            if cik in used:
                continue
            used.add(cik)
            chosen.append({
                **row, "cik": cik, "sample_version": SAMPLE_VERSION,
                "sample_rule": "hash_ranked_one_accession_per_registrant_cik_within_quarter_form",
                "sample_rank": str(rank), "sample_group_size": str(len(items)),
                "distinct_registrants_available": str(len(distinct_ciks)),
                "prior_sample_excluded": "true",
            })
            if len(chosen) == per_stratum:
                break
        if len(chosen) != per_stratum:
            raise ValueError(f"insufficient_distinct_registrants:{quarter}:{form_type}:"
                             f"needed={per_stratum}:available={len(distinct_ciks)}")
        selected.extend(chosen)
    keys = [(r["quarter"], r["form_type"], r["cik"]) for r in selected]
    if len(keys) != len(set(keys)) or any(r["accession"] in prior for r in selected):
        raise ValueError("expanded_sample_uniqueness_or_exclusion_failed")
    return selected


def p312_signature(row):
    return tuple(str(row.get(k, "")) for k in
                 ("cusip", "isin", "ticker", "balance", "currency_value_usd", "percentage_nav"))


def p314_signature(row):
    return tuple(str(row.get(k, "")) for k in
                 ("cusip", "isin", "ticker", "balance", "value_usd", "percentage_nav"))


def crosscheck_short_rows(raw, expected_form, parsed):
    xml_text = extract_primary_xml(raw.decode("utf-8", errors="replace"), expected_form)
    root = ET.fromstring(xml_text)
    reference_candidates, holding_nodes = parse_holding_rows(root)
    reference_short = [r for r in reference_candidates if r.get("sign_concordant")]
    phase_short = parsed.get("short_positions", [])
    if sorted(map(p312_signature, reference_short)) != sorted(map(p314_signature, phase_short)):
        raise ValueError("phase312_phase314_short_row_reconciliation_failed")
    return holding_nodes, reference_candidates


def identifier_metrics(rows):
    return {
        "rows": len(rows),
        "cusip_present": sum(bool(str(r.get("cusip", "")).strip()) for r in rows),
        "isin_present": sum(bool(str(r.get("isin", "")).strip()) for r in rows),
        "ticker_present": sum(bool(str(r.get("ticker", "")).strip()) for r in rows),
        "cusip_check_digit_valid": sum(cusip_check_digit_valid(r.get("cusip", "")) for r in rows),
        "isin_check_digit_valid": sum(isin_check_digit_valid(r.get("isin", "")) for r in rows),
    }


def download_submission(session, candidate, contact_email):
    filename = candidate["filename"].lstrip("/")
    if ".." in filename.split("/") or not filename.lower().startswith("edgar/data/"):
        raise ValueError("unsafe_master_index_filename")
    url = f"{SEC_ARCHIVES}/{filename}"
    last_error = ""
    for attempt in range(5):
        try:
            response = session.get(url, timeout=(20, 90))
            if response.status_code in {429, 500, 502, 503, 504}:
                retry = response.headers.get("Retry-After", "")
                delay = min(float(retry), 15.0) if re.fullmatch(r"\d+(?:\.\d+)?", retry) else 2.0 * (attempt + 1)
                last_error = f"http_{response.status_code}"
                if attempt < 4:
                    time.sleep(delay)
                    continue
            response.raise_for_status()
            payload = response.content
            if len(payload) < 1000:
                raise ValueError("submission_payload_too_small")
            head = payload[:2_000_000].decode("utf-8", errors="replace")
            if "ACCESSION NUMBER:" not in head or "<SEC-HEADER>" not in head.upper():
                raise ValueError("submission_header_signature_missing")
            return payload, url, response.status_code, response.headers.get("Content-Type", "")
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if attempt < 4:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"submission_download_failed:{candidate['accession']}:{last_error}")


def build_report(result):
    c, h, ids = result["coverage"], result["holdings"], result["holdings"]["identifier_metrics"]
    return "\n".join([
        "# Phase 316 — N-PORT multi-registrant stratified expansion", "",
        f"Audit: {result['audit_started_utc']} UTC  ",
        f"Status: {result['status']}  ",
        f"Sample: {c['sampled_accessions']} accessions, {c['quarters']} quarters, "
        f"{c['strata']} quarter/form strata, {c['per_stratum']} per stratum.", "",
        "## Reconciliation", "",
        f"- Raw complete submissions downloaded and hashed: {result['retrieval']['raw_files_downloaded']}/{result['retrieval']['raw_files_expected']}.",
        f"- Core index/header reconciliations: {result['reconciliation']['core_reconciled_filings']}/{c['sampled_accessions']}.",
        f"- Independent Phase 312/314 short-row parser cross-checks: {result['reconciliation']['short_row_parser_crosschecks']}/{c['sampled_accessions']}.",
        f"- Distinct registrant CIKs: {c['distinct_registrant_ciks']}.",
        f"- Series identity states: {json.dumps(result['reconciliation']['series_identity_states'], sort_keys=True)}.",
        f"- Class identity states: {json.dumps(result['reconciliation']['class_identity_states'], sort_keys=True)}.", "",
        "## Sign-concordant reported short holdings", "",
        f"- Filings with at least one sign-concordant short row: {h['filings_with_sign_concordant_short_rows']}.",
        f"- Sign-concordant short rows: {h['sign_concordant_short_rows']}.",
        f"- CUSIP present/check-digit valid: {ids['cusip_present']}/{ids['cusip_check_digit_valid']} of {ids['rows']}.",
        f"- ISIN present/check-digit valid: {ids['isin_present']}/{ids['isin_check_digit_valid']} of {ids['rows']}.",
        f"- Ticker present: {ids['ticker_present']} of {ids['rows']}.", "",
        "## Interpretation and restrictions", "",
        "- Deterministic hash-ranked QA sample, capped at one accession per registrant CIK within each quarter/form; excludes the earlier Phase 311 56-accession sample.",
        "- Not a probability sample and not a market-wide holdings-prevalence estimate.",
        "- N-PORT positions are delayed holdings snapshots, not trades. Cross-period differences are not treated as transactions.",
        "- Filing date and acceptance metadata are not admitted as first-public timestamps.",
        "- No effective-dated security crosswalk or F80-universe coverage is established.",
        "- No returns, alpha, bootstrap, LOO, chronological OOS or holdout tests were run.",
        "- F80, production, universe, capital and parameters remain unchanged.", "",
        "## Outputs", "",
        "- nport_expanded_sample_candidates.csv",
        "- nport_expanded_filing_reconciliation.csv",
        "- nport_expanded_short_rows.csv",
        "- phase316_nport_multifiler_expansion_result.json",
        "- raw/ contains the source complete-submission bytes.", "",
    ])


def run_audit(input_dir: Path, output_dir: Path, contact_email: str, per_stratum: int):
    if not contact_email or "@" not in contact_email:
        raise RuntimeError("SEC_CONTACT_EMAIL_secret_missing_or_invalid")
    census_path = input_dir / "nport_accession_census.csv"
    prior_path = input_dir / "nport_stratified_sample_candidates.csv"
    result_path = input_dir / "phase311_nport_accession_census_result.json"
    if not all(p.is_file() for p in (census_path, prior_path, result_path)):
        raise FileNotFoundError("phase311_census_artifact_incomplete")
    census, prior = read_csv(census_path), read_csv(prior_path)
    census_sha, prior_sha = sha256_bytes(census_path.read_bytes()), sha256_bytes(prior_path.read_bytes())
    census_result = json.loads(result_path.read_text(encoding="utf-8"))
    if census_result.get("phase") != 311 or census_result.get("status") != "PASS_HISTORICAL_ACCESSION_CENSUS":
        raise ValueError("phase311_census_result_invalid")
    if len(census) != census_result["coverage"]["unique_accessions"]:
        raise ValueError("phase311_census_row_count_mismatch")
    candidates = select_expanded_sample(census, prior, per_stratum)
    strata = {(r["quarter"], r["form_type"]) for r in census if r.get("form_type") in DATA_FORMS}
    if len(candidates) != len(strata) * per_stratum:
        raise ValueError("expanded_sample_count_mismatch")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": f"NuevaEstrategia quantitative research contact {contact_email}",
        "Accept": "text/plain,application/octet-stream,*/*",
        "Accept-Encoding": "gzip, deflate",
    })

    filing_rows, short_rows = [], []
    series_states, class_states = Counter(), Counter()
    form_counts, quarter_counts = Counter(), Counter()
    core_pass = parser_crosschecks = acceptance_matches = 0
    audit_started = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for index, candidate in enumerate(candidates, start=1):
        payload = None
        accession = candidate["accession"]
        try:
            payload, url, status, content_type = download_submission(session, candidate, contact_email)
            raw_sha = sha256_bytes(payload)
            raw_path = raw_dir / f"{accession.replace('-', '')}.txt"
            raw_path.write_bytes(payload)
            parsed = parse_submission(payload, candidate["form_type"])
            if parsed.get("accession") != accession:
                raise ValueError("header_accession_mismatch")
            if parsed.get("form_type") != candidate["form_type"]:
                raise ValueError("header_form_mismatch")
            if parsed.get("registrant_cik") != candidate["cik"].zfill(10):
                raise ValueError("header_registrant_cik_mismatch")
            if parsed.get("filed_as_of_date") != candidate["filing_date"].replace("-", ""):
                raise ValueError("header_filing_date_mismatch")
            acceptance = parsed.get("acceptance_datetime_et", "")
            if not re.fullmatch(r"\d{14}", acceptance):
                raise ValueError("acceptance_datetime_missing_or_invalid")
            datetime.strptime(acceptance, "%Y%m%d%H%M%S")
            acceptance_match = acceptance[:8] == candidate["filing_date"].replace("-", "")
            acceptance_matches += int(acceptance_match)
            holding_nodes, ref_candidates = crosscheck_short_rows(payload, candidate["form_type"], parsed)
            parser_crosschecks += 1
            phase_short = parsed.get("short_positions", [])
            if len(phase_short) != sum(bool(r.get("sign_concordant")) for r in ref_candidates):
                raise ValueError("short_row_count_crosscheck_failed")
            core_pass += 1
            form_counts[candidate["form_type"]] += 1
            quarter_counts[candidate["quarter"]] += 1
            series_states[parsed.get("series_identity_state", "UNKNOWN")] += 1
            class_states[parsed.get("class_identity_state", "UNKNOWN")] += 1

            filing = {
                "quarter": candidate["quarter"], "accession": accession,
                "registrant_cik": candidate["cik"].zfill(10), "company_name": candidate["company_name"],
                "form_type": candidate["form_type"], "master_index_filing_date": candidate["filing_date"],
                "header_accession": parsed.get("accession", ""), "header_form": parsed.get("form_type", ""),
                "header_registrant_cik": parsed.get("registrant_cik", ""),
                "header_filed_as_of_date": parsed.get("filed_as_of_date", ""),
                "acceptance_datetime_et": acceptance, "acceptance_date_matches_filed_date": acceptance_match,
                "report_date": parsed.get("report_date", ""), "series_ids": ";".join(parsed.get("series_ids", [])),
                "series_identity_state": parsed.get("series_identity_state", ""),
                "class_ids": ";".join(parsed.get("class_ids", [])),
                "class_identity_state": parsed.get("class_identity_state", ""),
                "holding_rows_total": holding_nodes, "short_category_rows": len(ref_candidates),
                "short_sign_concordant_rows": len(phase_short),
                "short_rows_with_cusip": sum(bool(r.get("cusip")) for r in phase_short),
                "short_rows_with_isin": sum(bool(r.get("isin")) for r in phase_short),
                "short_rows_with_ticker": sum(bool(r.get("ticker")) for r in phase_short),
                "short_rows_cusip_check_digit_valid": sum(cusip_check_digit_valid(r.get("cusip", "")) for r in phase_short),
                "short_rows_isin_check_digit_valid": sum(isin_check_digit_valid(r.get("isin", "")) for r in phase_short),
                "raw_bytes": len(payload), "raw_sha256": raw_sha,
                "raw_file": str(raw_path.relative_to(output_dir)), "source_url": url,
                "http_status": status, "content_type": content_type, "parse_status": "PASS",
            }
            filing_rows.append(filing)
            for row_number, row in enumerate(phase_short, start=1):
                short_rows.append({
                    "quarter": candidate["quarter"], "accession": accession,
                    "registrant_cik": candidate["cik"].zfill(10), "company_name": candidate["company_name"],
                    "form_type": candidate["form_type"], "filing_date": candidate["filing_date"],
                    "acceptance_datetime_et": acceptance, "report_date": parsed.get("report_date", ""),
                    "series_ids": ";".join(parsed.get("series_ids", [])),
                    "series_identity_state": parsed.get("series_identity_state", ""),
                    "class_ids": ";".join(parsed.get("class_ids", [])),
                    "class_identity_state": parsed.get("class_identity_state", ""),
                    "row_number": row_number, **row,
                })
            print(f"{index}/{len(candidates)} {accession} {candidate['form_type']} short={len(phase_short)} "
                  f"series={parsed.get('series_identity_state')}", flush=True)
        except Exception as exc:
            stage = "download" if payload is None else "parse_or_reconcile"
            raise RuntimeError(f"{stage}_failed:{accession}:{type(exc).__name__}:{exc}") from exc
        finally:
            if index < len(candidates):
                time.sleep(0.25)

    if len(filing_rows) != len(candidates) or core_pass != len(candidates) or parser_crosschecks != len(candidates):
        raise RuntimeError("expanded_sample_incomplete")
    quota = Counter((r["quarter"], r["form_type"]) for r in candidates)
    if any(v != per_stratum for v in quota.values()):
        raise RuntimeError("quarter_form_sample_quota_failed")
    ids = identifier_metrics(short_rows)
    result = {
        "phase": 316, "status": "PASS_MULTIREGISTRANT_STRATIFIED_RAW_RECONCILIATION",
        "audit_started_utc": audit_started,
        "source": {
            "phase311_run_id": 43156706936, "phase311_artifact_id": 13916331861,
            "phase311_census_sha256": census_sha, "phase311_prior_sample_sha256": prior_sha,
            "sec_archives_base": SEC_ARCHIVES,
        },
        "coverage": {
            "historical_start_quarter": min(r["quarter"] for r in census),
            "historical_end_quarter": max(r["quarter"] for r in census),
            "quarters": len({r["quarter"] for r in candidates}), "strata": len(quota),
            "per_stratum": per_stratum, "sampled_accessions": len(candidates),
            "nport_p": form_counts["NPORT-P"], "nport_p_a": form_counts["NPORT-P/A"],
            "distinct_registrant_ciks": len({r["cik"] for r in candidates}),
            "prior_phase311_accessions_excluded": len({r["accession"] for r in prior}),
            "selection_design": SAMPLE_VERSION, "sample_is_probability_sample": False,
        },
        "retrieval": {
            "raw_files_downloaded": len(filing_rows), "raw_files_expected": len(candidates),
            "download_failures": [], "parse_failures": [], "all_raw_bytes_hashed_before_parse": True,
        },
        "reconciliation": {
            "core_reconciled_filings": core_pass, "short_row_parser_crosschecks": parser_crosschecks,
            "acceptance_date_matches_master_filing_date": acceptance_matches,
            "series_identity_states": dict(series_states), "class_identity_states": dict(class_states),
            "quarter_counts": dict(sorted(quarter_counts.items())),
        },
        "holdings": {
            "filings_with_sign_concordant_short_rows": sum(1 for r in filing_rows if r["short_sign_concordant_rows"] > 0),
            "sign_concordant_short_rows": len(short_rows),
            "unique_cusips": len({r.get("cusip", "") for r in short_rows if r.get("cusip")}),
            "unique_isins": len({r.get("isin", "") for r in short_rows if r.get("isin")}),
            "unique_tickers": len({r.get("ticker", "") for r in short_rows if r.get("ticker")}),
            "identifier_metrics": ids,
            "interpretation": "reported short holdings only; not trades, short sales or prevalence",
        },
        "controls": {
            "nport_p_and_p_a_kept_separate": True, "nt_nport_p_not_sampled_as_holdings": True,
            "prior_phase311_sample_excluded": True, "one_accession_per_registrant_within_quarter_form": True,
            "phase312_phase314_short_rows_crosschecked": True, "position_rows_are_trades": False,
            "cross_period_position_changes_are_trades": False, "acceptance_is_first_public_timestamp": False,
            "report_date_is_knowledge_date": False, "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False, "representative_prevalence_estimate": False,
            "return_test": False, "alpha_test": False, "bootstrap": False, "loo": False,
            "chronological_oos": False, "holdout_used": False, "f80_frozen": True,
            "production_changed": False, "universe_changed": False, "capital_changed": False,
            "parameters_changed": False, "data_purchase": False, "vendor_contact": False, "email_sent": False,
        },
        "decision": "Expanded raw filing QA only. Build an effective-dated security crosswalk and public-availability vintage before any event study. Do not infer trades or alpha from holdings snapshots.",
    }
    filing_fields = list(filing_rows[0].keys())
    short_fields = list(short_rows[0].keys()) if short_rows else [
        "quarter","accession","registrant_cik","company_name","form_type","filing_date",
        "acceptance_datetime_et","report_date","series_ids","series_identity_state","class_ids",
        "class_identity_state","row_number","issuer_name","issue_title","cusip","isin","ticker",
        "balance","value_usd","percentage_nav","payoff_profile","asset_category","issuer_type",
        "investment_country","units",
    ]
    write_csv(output_dir / "nport_expanded_sample_candidates.csv", candidates, list(candidates[0].keys()))
    write_csv(output_dir / "nport_expanded_filing_reconciliation.csv", filing_rows, filing_fields)
    write_csv(output_dir / "nport_expanded_short_rows.csv", short_rows, short_fields)
    (output_dir / "phase316_nport_multifiler_expansion_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "PHASE316_NPORT_MULTIFILER_STRATIFIED_EXPANSION_2026-11-12.md").write_text(
        build_report(result), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("phase311_input"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase316_output"))
    parser.add_argument("--per-stratum", type=int, default=DEFAULT_PER_STRATUM)
    args = parser.parse_args()
    result = run_audit(args.input_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""), args.per_stratum)
    print(json.dumps({
        "phase": 316, "status": result["status"],
        "sampled_accessions": result["coverage"]["sampled_accessions"],
        "distinct_registrant_ciks": result["coverage"]["distinct_registrant_ciks"],
        "short_filings": result["holdings"]["filings_with_sign_concordant_short_rows"],
        "short_rows": result["holdings"]["sign_concordant_short_rows"],
        "identifier_metrics": result["holdings"]["identifier_metrics"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

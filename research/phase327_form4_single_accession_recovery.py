#!/usr/bin/env python3
"""Phase 327: single-accession recovery for the sole Phase 326 SEC 404 quarantine.

Reuses the immutable Phase 326 metadata artifact and retries only its one missing
accession through zero-padded SEC archive CIK paths. No successful filing is
downloaded again. This is source recovery, not a signal or alpha test.
"""
from __future__ import annotations

import argparse
import json
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from research.phase320_sec_bulk_daily_index_join import (
    MIN_REQUEST_DELAY_SECONDS,
    _fetch_bytes,
    normalize_accession,
    normalize_cik,
    sha256_bytes,
    submission_url,
)
from research.phase326_form4_collision_security_title_audit import (
    N_ACCESSIONS,
    classify_symbol,
    load_plan,
    pair_summary,
    parse_filing_header,
    parse_ownership_xml,
    path_ciks_for,
    write_csv,
)

PHASE = 327
FAILED_ACCESSION = "0000939057-26-000239"
PRIOR_PHASE326_RUN_ID = 43209373482
PRIOR_PHASE326_ARTIFACT_ID = 13939999128
PRIOR_PHASE326_ARTIFACT_SHA256 = "eea7eaf97b91acfdbdac866f8d98660ec98be03adc8c4038b800f74cf86d81d5"
PHASE321_SHA256 = "e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c"
PHASE325_SHA256 = "6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
EXPECTED_PRIOR_RETRIEVED = 282


def padded_submission_urls_for(accession: str, path_cik: str):
    """Return zero-padded CIK layouts only; unpadded layouts were exhausted in Phase 326."""
    accession = normalize_accession(accession)
    cik = normalize_cik(path_cik)
    if not accession or not cik:
        raise ValueError("invalid_accession_or_path_cik")
    padded = cik.zfill(10)
    if padded == cik:
        return []
    flat = submission_url(accession, cik)
    padded_flat = flat.replace(f"/data/{cik}/", f"/data/{padded}/")
    directory = (
        f"{padded_flat.rsplit('/', 1)[0]}/"
        f"{accession.replace('-', '')}/{accession}.txt"
    )
    return [
        ("flat_zero_padded", padded_flat),
        ("accession_directory_zero_padded", directory),
    ]


def load_prior_result(path: Path):
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if digest != PRIOR_PHASE326_ARTIFACT_SHA256:
        raise ValueError(f"phase326_prior_artifact_sha256_mismatch:{digest}")
    with zipfile.ZipFile(path) as zf:
        matches = [n for n in zf.namelist() if n.endswith("phase326_result.json")]
        if len(matches) != 1:
            raise ValueError(f"phase326_result_member_count:{len(matches)}")
        result = json.loads(zf.read(matches[0]))
    if result.get("phase") != 326:
        raise ValueError("prior_result_phase_mismatch")
    source = result.get("source", {})
    if source.get("phase321_artifact_sha256") != PHASE321_SHA256:
        raise ValueError("prior_phase321_source_hash_mismatch")
    if source.get("phase325_artifact_sha256") != PHASE325_SHA256:
        raise ValueError("prior_phase325_source_hash_mismatch")
    filings = result.get("filings", [])
    accessions = [normalize_accession(x.get("accession")) for x in filings]
    if len(filings) != N_ACCESSIONS or len(set(accessions)) != N_ACCESSIONS:
        raise ValueError("prior_phase326_population_or_duplicate_mismatch")
    failed = [normalize_accession(x.get("accession")) for x in filings
              if x.get("retrieval_status") != "RETRIEVED"]
    retrieved = [x for x in filings if x.get("retrieval_status") == "RETRIEVED"]
    if len(retrieved) != EXPECTED_PRIOR_RETRIEVED or failed != [FAILED_ACCESSION]:
        raise ValueError(f"prior_phase326_quarantine_shape_mismatch:{len(retrieved)}:{failed}")
    if any(not x.get("header_identity_match") for x in retrieved):
        raise ValueError("prior_phase326_header_identity_not_complete")
    if any(x.get("xml_status") != "PARSED" or not x.get("xml_issuer_cik_match")
           or not x.get("xml_owner_ciks_match") or not x.get("xml_issuer_symbol_match")
           for x in retrieved):
        raise ValueError("prior_phase326_retrieved_xml_identity_not_complete")
    return result, digest


def recover_one(row, email):
    if not email or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required")
    accession = normalize_accession(row.get("accession"))
    if accession != FAILED_ACCESSION:
        raise ValueError("unexpected_recovery_accession")
    issuer_cik = normalize_cik(row.get("issuer_cik"))
    owners = list(row.get("reporting_owner_ciks") or [])
    path_ciks = path_ciks_for(accession, issuer_cik, owners)
    ua = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    attempts = []
    expected_entities = {issuer_cik, *[normalize_cik(x) for x in owners if normalize_cik(x)]}

    for path_cik in path_ciks:
        for route, url in padded_submission_urls_for(accession, path_cik):
            try:
                raw, headers = _fetch_bytes(url, ua, total_bytes)
            except Exception as exc:
                attempts.append({
                    "path_cik": path_cik, "route": route, "url": url,
                    "http_status": "", "result": "ERROR",
                    "error": f"{type(exc).__name__}:{str(exc)[:160]}",
                })
                # _fetch_bytes sleeps after successful responses and on retryable
                # errors. Apply the same minimum spacing to terminal 404s.
                time.sleep(MIN_REQUEST_DELAY_SECONDS)
                continue

            h = parse_filing_header(raw)
            header_ok = (
                h.get("accession") == accession
                and h.get("form_type") == row.get("form_type")
                and h.get("filed_date") == row.get("filing_date")
                and normalize_cik(h.get("cik")) in expected_entities
            )
            if not header_ok:
                attempts.append({
                    "path_cik": path_cik, "route": route, "url": url,
                    "http_status": headers.get("http_status", ""),
                    "result": "HEADER_IDENTITY_MISMATCH",
                    "error": "",
                })
                continue

            x = parse_ownership_xml(raw)
            expected_symbol = classify_symbol(row.get("ticker_as_filed"))
            recovered = {
                "accession": accession,
                "form_type": row["form_type"],
                "filing_date": row["filing_date"],
                "quarter": row["quarter"],
                "issuer_cik": issuer_cik,
                "issuer_name_bulk": row.get("issuer_name", ""),
                "ticker_as_filed": row.get("ticker_as_filed", ""),
                "ticker_candidate": expected_symbol or "",
                "reporting_owner_ciks_bulk": owners,
                "pair_memberships": [],
                "fetch_path_cik": path_cik,
                "fetch_path_route": route,
                "http_status": headers.get("http_status", ""),
                "bytes": len(raw),
                "submission_sha256": sha256_bytes(raw),
                "header_cik": normalize_cik(h.get("cik")),
                "header_filed_date": h.get("filed_date"),
                "acceptance_datetime": h.get("acceptance_datetime_et"),
                "header_identity_match": True,
                **x,
                "xml_issuer_cik_match": x["xml_issuer_cik"] == issuer_cik,
                "xml_issuer_symbol_match": bool(expected_symbol) and x["xml_issuer_symbol"] == expected_symbol,
                "xml_owner_ciks_match": bool(owners) and set(owners).issubset(set(x["xml_owner_ciks"])),
                "retrieval_status": "RETRIEVED",
                "prior_path_errors": row.get("prior_path_errors", []),
                "recovery_errors": [],
                "recovery_route_attempts": attempts,
            }
            attempts.append({
                "path_cik": path_cik, "route": route, "url": url,
                "http_status": headers.get("http_status", ""),
                "result": "RETRIEVED_AND_HEADER_VALIDATED", "error": "",
            })
            return recovered, attempts, total_bytes[0]

    quarantined = dict(row)
    quarantined["recovery_errors"] = attempts
    quarantined["recovery_route_attempts"] = attempts
    quarantined["recovery_failure_reason"] = "ALL_ZERO_PADDED_SEC_ARCHIVE_LAYOUTS_UNAVAILABLE_OR_INVALID"
    return quarantined, attempts, total_bytes[0]


def run(plan, prior, prior_digest, outdir: Path, email: str):
    expected = set(plan["selected"])
    prior_by_accession = {normalize_accession(x["accession"]): dict(x) for x in prior["filings"]}
    if set(prior_by_accession) != expected:
        raise ValueError("prior_phase326_accession_set_differs_from_immutable_plan")
    missing = [a for a, row in prior_by_accession.items() if row.get("retrieval_status") != "RETRIEVED"]
    if missing != [FAILED_ACCESSION]:
        raise ValueError(f"unexpected_missing_accessions:{missing}")

    selected = dict(plan["selected"][FAILED_ACCESSION])
    selected["accession"] = FAILED_ACCESSION
    selected["reporting_owner_ciks"] = list(selected.get("reporting_owner_ciks") or [])
    recovered, attempts, bytes_downloaded = recover_one(selected, email)
    prior_by_accession[FAILED_ACCESSION] = recovered
    filings = [prior_by_accession[a] for a in sorted(prior_by_accession)]
    pairs = pair_summary(plan["pairs"], filings)
    got = [x for x in filings if x.get("retrieval_status") == "RETRIEVED"]
    unresolved = [x["accession"] for x in filings if x.get("retrieval_status") != "RETRIEVED"]
    summary = dict(prior["summary"])
    summary.update({
        "prior_retrieved": EXPECTED_PRIOR_RETRIEVED,
        "retried_accessions": 1,
        "padded_route_attempts": len(attempts),
        "recovery_sec_bytes_downloaded": bytes_downloaded,
        "retrieved": len(got),
        "retrieval_failures": len(unresolved),
        "header_identity_matches": sum(bool(x.get("header_identity_match")) for x in got),
        "xml_parsed": sum(x.get("xml_status") == "PARSED" for x in got),
        "xml_issuer_cik_matches": sum(bool(x.get("xml_issuer_cik_match")) for x in got),
        "xml_symbol_matches": sum(bool(x.get("xml_issuer_symbol_match")) for x in got),
        "xml_owner_ciks_matches": sum(bool(x.get("xml_owner_ciks_match")) for x in got),
        "pair_title_relations": dict(sorted(
            __import__("collections").Counter(x["title_relation"] for x in pairs).items()
        )),
        "recovered_accessions": [FAILED_ACCESSION] if not unresolved else [],
        "unresolved_accessions": unresolved,
    })
    controls = dict(prior.get("controls", {}))
    controls.update({
        "f80_frozen": True,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "return_test_run": False,
        "bootstrap_loo_run": False,
        "chronological_oos_run": False,
        "holdout_used": False,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "raw_sec_bytes_uploaded": False,
        "vendor_contacted": False,
        "data_purchased": False,
        "email_sent": False,
        "only_one_previously_failed_accession_retried": True,
    })
    result = {
        "phase": PHASE,
        "status": "COMPLETED_SOURCE_RECOVERY" if not unresolved else "COMPLETED_WITH_ONE_QUARANTINED_ACCESSION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "phase321_artifact_sha256": PHASE321_SHA256,
            "phase325_artifact_sha256": PHASE325_SHA256,
            "phase326_run_id": PRIOR_PHASE326_RUN_ID,
            "phase326_artifact_id": PRIOR_PHASE326_ARTIFACT_ID,
            "phase326_artifact_sha256": prior_digest,
        },
        "summary": summary,
        "interpretation": dict(prior.get("interpretation", {})),
        "controls": controls,
        "filings": filings,
        "pairs": pairs,
        "recovery_attempts": attempts,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "phase327_recovery_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(outdir / "phase327_recovery_attempts.csv", attempts)
    write_csv(outdir / "phase327_unresolved_accession.csv",
              [x for x in filings if x.get("retrieval_status") != "RETRIEVED"])
    write_csv(outdir / "phase327_pair_summary.csv", pairs)
    print("PHASE327_STATUS=" + result["status"])
    print("PHASE327_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE327_UNRESOLVED=" + json.dumps(unresolved))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase321-zip", type=Path, required=True)
    p.add_argument("--phase325-zip", type=Path, required=True)
    p.add_argument("--phase326-zip", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--email", default="")
    a = p.parse_args()
    plan = load_plan(a.phase321_zip, a.phase325_zip)
    prior, digest = load_prior_result(a.phase326_zip)
    run(plan, prior, digest, a.output_dir, a.email)


if __name__ == "__main__":
    main()

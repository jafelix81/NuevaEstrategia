#!/usr/bin/env python3
"""Phase 327: single-accession SEC archive recovery for the sole Phase 326 quarantine."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
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
    classify_symbol,
    parse_filing_header,
    parse_ownership_xml,
    path_ciks_for,
)

PHASE = 327
FAILED_ACCESSION = "0000939057-26-000239"
PRIOR_PHASE326_RUN_ID = 43209373482
PRIOR_PHASE326_ARTIFACT_ID = 13939999128
PRIOR_PHASE326_ARTIFACT_SHA256 = "eea7eaf97b91acfdbdac866f8d98660ec98be03adc8c4038b800f74cf86d81d5"
PRIOR_MANIFEST_SHA256 = "66e3e4562234521299e3937bb0a5d8c4eabecd3eff0829e726a241748b53f009"
PHASE321_SHA256 = "e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c"
PHASE325_SHA256 = "6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
PHASE321_INDEX_FILE_SHA256 = "f7962a73b80234608c45f53cc5aac19b2374d5085e3fa73aa262448dce6d10a5"


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


def load_prior_manifest(path: Path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PRIOR_MANIFEST_SHA256:
        raise ValueError(f"prior_manifest_sha256_mismatch:{digest}")
    manifest = json.loads(raw)
    if manifest.get("phase") != 326:
        raise ValueError("prior_manifest_phase_mismatch")
    if manifest.get("phase321_artifact_sha256") != PHASE321_SHA256:
        raise ValueError("prior_manifest_phase321_hash_mismatch")
    if manifest.get("phase325_artifact_sha256") != PHASE325_SHA256:
        raise ValueError("prior_manifest_phase325_hash_mismatch")
    if manifest.get("artifact_sha256") != PRIOR_PHASE326_ARTIFACT_SHA256:
        raise ValueError("prior_manifest_phase326_artifact_hash_mismatch")
    if manifest.get("selected_accessions") != 283 or manifest.get("retrieved") != 282:
        raise ValueError("prior_manifest_population_mismatch")
    if manifest.get("retrieval_failures") != 1 or manifest.get("unresolved_accessions") != [FAILED_ACCESSION]:
        raise ValueError("prior_manifest_quarantine_mismatch")
    for key in ("header_identity_matches", "xml_parsed", "xml_issuer_cik_matches",
                "xml_symbol_matches", "xml_owner_ciks_matches"):
        if manifest.get(key) != 282:
            raise ValueError(f"prior_manifest_validated_count_mismatch:{key}")
    row = manifest.get("unresolved_accession_row", {})
    if (
        normalize_accession(row.get("accession")) != FAILED_ACCESSION
        or normalize_cik(row.get("issuer_cik")) != "1041368"
        or list(row.get("reporting_owner_ciks") or []) != ["1972440"]
        or row.get("form_type") != "4"
        or row.get("filing_date") != "2026-09-25"
        or row.get("ticker_as_filed") != "TSBK"
        or row.get("index_file_sha256") != PHASE321_INDEX_FILE_SHA256
    ):
        raise ValueError("prior_manifest_unresolved_row_mismatch")
    return manifest, digest


def retrieve_zero_padded_only(row, email):
    if not email or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required")
    accession = normalize_accession(row.get("accession"))
    if accession != FAILED_ACCESSION:
        raise ValueError("unexpected_recovery_accession")
    issuer_cik = normalize_cik(row.get("issuer_cik"))
    owners = [normalize_cik(x) for x in row.get("reporting_owner_ciks", [])]
    owners = [x for x in owners if x]
    path_ciks = path_ciks_for(accession, issuer_cik, owners)
    expected_entities = {issuer_cik, *owners}
    expected_symbol = classify_symbol(row.get("ticker_as_filed"))
    ua = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    attempts = []

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
                    "result": "HEADER_IDENTITY_MISMATCH", "error": "",
                })
                continue

            x = parse_ownership_xml(raw)
            issuer_ok = x.get("xml_status") == "PARSED" and x.get("xml_issuer_cik") == issuer_cik
            owner_ok = bool(owners) and set(owners).issubset(set(x.get("xml_owner_ciks", [])))
            if not issuer_ok or not owner_ok:
                attempts.append({
                    "path_cik": path_cik, "route": route, "url": url,
                    "http_status": headers.get("http_status", ""),
                    "result": "XML_IDENTITY_MISMATCH",
                    "error": f"issuer_ok={issuer_ok};owner_ok={owner_ok}",
                })
                continue

            record = {
                "accession": accession,
                "form_type": row["form_type"],
                "filing_date": row["filing_date"],
                "quarter": row["quarter"],
                "issuer_cik": issuer_cik,
                "issuer_name_bulk": row.get("issuer_name", ""),
                "ticker_as_filed": row.get("ticker_as_filed", ""),
                "ticker_candidate": expected_symbol or "",
                "reporting_owner_ciks_bulk": owners,
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
                "xml_issuer_cik_match": issuer_ok,
                "xml_issuer_symbol_match": bool(expected_symbol) and x.get("xml_issuer_symbol") == expected_symbol,
                "xml_owner_ciks_match": owner_ok,
                "retrieval_status": "RETRIEVED",
            }
            attempts.append({
                "path_cik": path_cik, "route": route, "url": url,
                "http_status": headers.get("http_status", ""),
                "result": "RETRIEVED_AND_XML_IDENTITY_VALIDATED", "error": "",
            })
            return record, attempts, total_bytes[0]

    return None, attempts, total_bytes[0]


def write_csv(path: Path, rows):
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(row.get(k), ensure_ascii=False, sort_keys=True)
                if isinstance(row.get(k), (dict, list)) else row.get(k, "")
                for k in fields
            })


def run(manifest, manifest_digest, outdir: Path, email: str):
    row = dict(manifest["unresolved_accession_row"])
    recovered, attempts, bytes_downloaded = retrieve_zero_padded_only(row, email)
    unresolved = [] if recovered else [FAILED_ACCESSION]
    relation_after = Counter(manifest["pair_title_relations"])
    recovered_relation = None
    if recovered:
        titles_a = set(recovered.get("non_derivative_titles", [])) | set(recovered.get("derivative_titles", []))
        titles_b = set(manifest["tsbk_pair"]["side_b_titles"])
        recovered_relation = (
            "OVERLAPPING_LABELS_NOT_SECURITY_IDENTITY"
            if titles_a.intersection(titles_b)
            else "DISJOINT_LABELS_NOT_SHARE_CLASS_PROOF"
        )
        relation_after["INCOMPLETE_RETRIEVAL"] = max(0, relation_after.get("INCOMPLETE_RETRIEVAL", 0) - 1)
        relation_after[recovered_relation] += 1

    final_retrieved = manifest["retrieved"] + (1 if recovered else 0)
    summary = {
        "prior_selected_accessions": manifest["selected_accessions"],
        "prior_retrieved": manifest["retrieved"],
        "retried_accessions": 1,
        "padded_route_attempts": len(attempts),
        "recovery_sec_bytes_downloaded": bytes_downloaded,
        "final_retrieved": final_retrieved,
        "final_unresolved_accessions": unresolved,
        "final_header_identity_matches": manifest["header_identity_matches"] + (1 if recovered else 0),
        "final_xml_parsed": manifest["xml_parsed"] + (1 if recovered else 0),
        "final_xml_issuer_cik_matches": manifest["xml_issuer_cik_matches"] + (1 if recovered else 0),
        "final_xml_owner_ciks_matches": manifest["xml_owner_ciks_matches"] + (1 if recovered else 0),
        "final_xml_symbol_matches": manifest["xml_symbol_matches"] + (
            1 if recovered and recovered.get("xml_issuer_symbol_match") else 0
        ),
        "final_pair_title_relations": dict(sorted(relation_after.items())),
        "recovered_pair_title_relation": recovered_relation,
        "recovered_accession": FAILED_ACCESSION if recovered else None,
        "prior_phase326_transaction_code_presence_by_filing": manifest["transaction_code_presence_by_filing"],
        "prior_phase326_non_derivative_transaction_rows": manifest["non_derivative_transactions"],
        "prior_phase326_derivative_transaction_rows": manifest["derivative_transactions"],
        "prior_phase326_distinct_title_labels": manifest["distinct_title_labels"],
        "zero_padded_http_404_count": sum("http_404" in x.get("error", "") for x in attempts),
        "zero_padded_non_404_error_count": sum(
            bool(x.get("error")) and "http_404" not in x.get("error", "") for x in attempts
        ),
    }
    controls = {
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
        "only_previously_failed_accession_retried": True,
        "previously_validated_filings_refetched": False,
    }
    result = {
        "phase": PHASE,
        "status": "RECOVERED_ONE_ACCESSION" if recovered else "COMPLETED_WITH_ONE_QUARANTINED_ACCESSION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "phase321_artifact_sha256": PHASE321_SHA256,
            "phase321_index_file_sha256": PHASE321_INDEX_FILE_SHA256,
            "phase325_artifact_sha256": PHASE325_SHA256,
            "phase326_run_id": PRIOR_PHASE326_RUN_ID,
            "phase326_artifact_id": PRIOR_PHASE326_ARTIFACT_ID,
            "phase326_artifact_sha256": PRIOR_PHASE326_ARTIFACT_SHA256,
            "phase326_prior_manifest_sha256": manifest_digest,
        },
        "prior_manifest": manifest,
        "summary": summary,
        "controls": controls,
        "recovered_record": recovered,
        "recovery_attempts": attempts,
        "unresolved_accessions": unresolved,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "phase327_recovery_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(outdir / "phase327_recovery_attempts.csv", attempts)
    write_csv(outdir / "phase327_unresolved_accession.csv",
              [{"accession": FAILED_ACCESSION, "reason": "NO_VALID_ZERO_PADDED_SEC_SUBMISSION_FOUND"}]
              if unresolved else [])
    write_csv(outdir / "phase327_recovered_record.csv", [recovered] if recovered else [])
    print("PHASE327_STATUS=" + result["status"])
    print("PHASE327_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE327_UNRESOLVED=" + json.dumps(unresolved))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prior-manifest", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--email", default="")
    a = p.parse_args()
    manifest, digest = load_prior_manifest(a.prior_manifest)
    run(manifest, digest, a.output_dir, a.email)


if __name__ == "__main__":
    main()

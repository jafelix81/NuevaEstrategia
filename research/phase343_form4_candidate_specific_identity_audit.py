#!/usr/bin/env python3
"""Phase 343: candidate-specific, event-time SEC Form 4 identity audit."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, shutil, xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from research.phase328_sec_collision_prior_filing_xbrl_pilot import (
    SECClient, norm_cik, retrieve_filing_facts, select_prior_periodic_filing,
)
from research.phase340_form4_transaction_date_anchor_pit_audit import (
    extract_transaction_rows, fetch_submission, sha256_bytes,
)
from research.phase341_form4_issuer_symbol_class_crosswalk_audit import (
    cls, match_title, norm, parse_symbol, raw_meta,
)
from research.phase342_sec_insider_bulk_sample_audit import (
    ARCHIVES, audit_archive, classify_purchase_row, normalize_aff,
)

PHASE = 343
EXPECTED_ARCHIVE_SHA256 = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
EXPECTED = (85, 59, 31, 48)
TARGET_FACTS = {"TradingSymbol", "Security12bTitle", "SecurityExchangeName"}
BOOL_FLAGS = ("base", "explicit_open_market", "no_private_disclosure", "no_plan_disclosure",
              "no_mechanical_disclosure", "direct_ownership", "single_reporting_owner",
              "common_stock_title", "aff_gate")


def decimal_key(value):
    raw = str(value or "").strip().replace(",", "")
    if not raw:
        return ""
    try:
        return format(Decimal(raw).normalize(), "f")
    except (InvalidOperation, ValueError):
        return raw


def tx_key_bulk(row):
    return (norm(row.get("security_title", "")), str(row.get("transaction_date", "")).strip(),
            str(row.get("transaction_code", "")).strip().upper(), "D", "A",
            decimal_key(row.get("transaction_shares")),
            decimal_key(row.get("transaction_price_per_share")))


def tx_key_xml(row):
    return (norm(row.get("security_title", "")), str(row.get("transaction_date", "")).strip(),
            str(row.get("transaction_code", "")).strip().upper(),
            str(row.get("direct_or_indirect", "")).strip().upper(),
            str(row.get("acquired_disposed", "")).strip().upper(),
            decimal_key(row.get("shares")), decimal_key(row.get("price_per_share")))


def extract_raw_footnotes(raw):
    text = raw.decode("latin-1", errors="replace")
    match = re.search(r"<XML>\s*(.*?)\s*</XML>", text, re.I | re.S)
    if not match:
        raise ValueError("missing_form4_xml_block")
    root = ET.fromstring(match.group(1))
    footnote_map = {
        str(node.attrib.get("id", "")): " ".join("".join(node.itertext()).split())
        for node in root.findall("footnotes/footnote") if node.attrib.get("id")
    }
    table = root.find("nonDerivativeTable")
    transactions = table.findall("nonDerivativeTransaction") if table is not None else []
    result = {}
    for index, row in enumerate(transactions, 1):
        refs = [x.attrib.get("id", "") for x in row.findall(".//footnoteId") if x.attrib.get("id")]
        result[index] = {
            "footnote_ids": refs,
            "missing_footnote_ids": sorted(set(refs) - set(footnote_map)),
            "footnote_texts": [footnote_map[x] for x in refs if x in footnote_map],
        }
    return result


def verify_candidate_row(candidate, xml_rows, raw_rows, footnotes, owner_count, aff_value):
    key = tx_key_bulk(candidate)
    matches = [x for x in xml_rows
               if x.get("transaction_kind") == "NON_DERIVATIVE" and tx_key_xml(x) == key]
    if len(matches) != 1:
        return {"xml_match_status": "NO_MATCH" if not matches else "MULTIPLE_IDENTICAL_XML_ROWS",
                "xml_match_count": len(matches), "xml_transaction_index": "",
                "raw_purchase_screen_pass": False, "raw_footnote_ids": [],
                "raw_missing_footnote_ids": []}
    tx = matches[0]
    index = int(tx["transaction_index"])
    raw_row = raw_rows.get(("NON_DERIVATIVE", index), {})
    fn = footnotes.get(index, {})
    text = " ".join(fn.get("footnote_texts", []))
    flags = classify_purchase_row({
        "DOCUMENT_TYPE": "4", "TRANS_FORM_TYPE": "4",
        "TRANS_CODE": tx.get("transaction_code", ""),
        "TRANS_ACQUIRED_DISP_CD": tx.get("acquired_disposed", ""),
        "DIRECT_INDIRECT_OWNERSHIP": tx.get("direct_or_indirect", ""),
        "SECURITY_TITLE": tx.get("security_title", ""),
    }, text, owner_count, aff_value, require_known_false=True)
    if fn.get("missing_footnote_ids"):
        flags["explicit_open_market"] = False
    passed = all(bool(flags.get(k)) for k in BOOL_FLAGS) and normalize_aff(aff_value) == "false"
    return {
        "xml_match_status": "UNIQUE_EXACT_TRANSACTION_ROW", "xml_match_count": 1,
        "xml_transaction_index": index, "raw_purchase_screen_pass": passed,
        "raw_purchase_screen_flags": flags, "raw_security_title": tx.get("security_title", ""),
        "raw_transaction_date": tx.get("transaction_date", ""),
        "raw_transaction_code": tx.get("transaction_code", ""),
        "raw_direct_or_indirect": tx.get("direct_or_indirect", ""),
        "raw_nature_of_ownership": raw_row.get("nature", ""),
        "raw_footnote_ids": fn.get("footnote_ids", []),
        "raw_missing_footnote_ids": fn.get("missing_footnote_ids", []),
        "raw_footnote_texts": fn.get("footnote_texts", []),
    }


def facts_to_contexts(facts):
    grouped, dimensions = defaultdict(lambda: defaultdict(set)), defaultdict(set)
    for fact in facts:
        name, context = fact.get("name"), str(fact.get("context_ref") or "")
        value = " ".join(str(fact.get("value") or "").split())
        if name not in TARGET_FACTS or not context or not value:
            continue
        grouped[context][name].add(value)
        for dim in fact.get("dimensions", []) or []:
            dimensions[context].add((str(dim.get("dimension") or ""), str(dim.get("member") or "")))
    out = []
    for context, by_name in grouped.items():
        if not TARGET_FACTS.issubset(by_name) or any(len(by_name[n]) != 1 for n in TARGET_FACTS):
            continue
        values = {n: next(iter(by_name[n])) for n in TARGET_FACTS}
        dims = sorted(dimensions[context])
        class_axes = sorted(f"{d}={m}" for d, m in dims
                            if "StatementClassOfStockAxis" in d or "ClassesOfShareCapitalAxis" in d)
        listing_axes = sorted(f"{d}={m}" for d, m in dims if "EntityListingsExchangeAxis" in d)
        kind, class_tokens, series_tokens = cls(values["Security12bTitle"])
        out.append({
            "context_ref": context, "symbol": values["TradingSymbol"].strip().upper(),
            "security_title": values["Security12bTitle"], "exchange": values["SecurityExchangeName"],
            "dimensions": [f"{d}={m}" for d, m in dims], "class_axis_members": class_axes,
            "listing_axis_members": listing_axes, "instrument_class": kind,
            "class_tokens": list(class_tokens), "series_tokens": list(series_tokens),
        })
    return out


def crosswalk(symbol_raw, transaction_title, contexts):
    token, status, exchange_prefix = parse_symbol(symbol_raw)
    base = {"form4_symbol_raw": symbol_raw, "form4_symbol_token": token,
            "form4_symbol_parse_status": status, "form4_exchange_prefix": exchange_prefix,
            "candidate_context_count": 0, "matched_xbrl_title": "", "instrument_class": "",
            "exchange_values": [], "context_refs": [], "class_axis_members": [],
            "listing_axis_members": [], "title_match_method": ""}
    if status != "SINGLE_TOKEN" or not token:
        return {**base, "crosswalk_status": "UNPARSEABLE_FORM4_SYMBOL"}
    same_symbol = [c for c in contexts if c["symbol"].strip().upper() == token]
    matches = []
    for context in same_symbol:
        ok, method, instrument = match_title(transaction_title, context["security_title"])
        if ok:
            matches.append((context, method, instrument))
    base["candidate_context_count"] = len(same_symbol)
    if not matches:
        status_out = "NO_SAME_CONTEXT_SYMBOL_TITLE_EXCHANGE" if not same_symbol else "SYMBOL_PRESENT_NO_COMPATIBLE_CLASS_TITLE"
        return {**base, "crosswalk_status": status_out}
    class_keys = {(norm(c["security_title"]), tuple(c["class_axis_members"]),
                   tuple(c["class_tokens"]), tuple(c["series_tokens"])) for c, _, _ in matches}
    if len(class_keys) != 1:
        return {**base, "crosswalk_status": "AMBIGUOUS_COMPATIBLE_SECURITY_CLASSES"}
    titles = sorted({c["security_title"] for c, _, _ in matches})
    exchanges = sorted({c["exchange"] for c, _, _ in matches})
    return {
        **base, "crosswalk_status": "UNIQUE_COMPATIBLE_SECURITY_CLASS",
        "matched_xbrl_title": titles[0] if len(titles) == 1 else titles,
        "instrument_class": sorted({i for _, _, i in matches}),
        "exchange_values": exchanges,
        "context_refs": sorted({c["context_ref"] for c, _, _ in matches}),
        "class_axis_members": sorted({x for c, _, _ in matches for x in c["class_axis_members"]}),
        "listing_axis_members": sorted({x for c, _, _ in matches for x in c["listing_axis_members"]}),
        "title_match_method": sorted({m for _, m, _ in matches}),
    }


def strict_date_relation(anchor_date, event_date):
    try:
        anchor, event = date.fromisoformat(anchor_date), date.fromisoformat(event_date)
    except (TypeError, ValueError):
        return False, None
    return anchor < event, (event - anchor).days


def group_event_units(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row.get("issuer_cik", ""), row.get("filing_date", ""))].append(row)
    out = []
    for (cik, filing_date), items in sorted(grouped.items()):
        out.append({
            "issuer_cik": cik, "filing_date": filing_date, "candidate_rows": len(items),
            "candidate_accessions": len({x["accession"] for x in items}),
            "event_time_identity_rows": sum(bool(x.get("event_time_identity")) for x in items),
            "transaction_date_identity_rows": sum(bool(x.get("transaction_date_identity")) for x in items),
            "event_time_complete": bool(items) and all(bool(x.get("event_time_identity")) for x in items),
            "transaction_date_complete": bool(items) and all(bool(x.get("transaction_date_identity")) for x in items),
            "mapped_symbols": sorted({x.get("form4_symbol_token", "") for x in items if x.get("event_time_identity")}),
            "exchanges": sorted({e for x in items if x.get("event_time_identity") for e in x.get("exchange_values", [])}),
        })
    return out


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                             if isinstance(v, (dict, list)) else v for k, v in row.items()})


def archive_candidates(path):
    digest = sha256_bytes(path.read_bytes())
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"2026Q3_archive_sha256_mismatch:{digest}")
    audit = audit_archive(path, "2026Q3")
    if audit["zip_integrity"] != "PASS":
        raise ValueError("2026Q3_archive_integrity_failed")
    candidates = audit["candidate_events"]
    counts = (len(candidates), len({x["accession"] for x in candidates}),
              len({x["issuer_cik"] for x in candidates if x["issuer_cik"]}),
              len({(x["issuer_cik"], x["filing_date"]) for x in candidates}))
    if counts != EXPECTED:
        raise ValueError(f"2026Q3_candidate_population_mismatch:{counts}")
    return audit, candidates


def run(archive_path, outdir, email):
    if not email or "@" not in email:
        raise RuntimeError("BLOCKED_MISSING_SEC_CONTACT_EMAIL")
    outdir.mkdir(parents=True, exist_ok=True)
    rawdir = outdir / "raw_sec"
    rawdir.mkdir(exist_ok=True)
    audit, candidates = archive_candidates(archive_path)
    shutil.copy2(archive_path, outdir / "2026q3_form345_source.zip")
    client = SECClient(email)
    by_accession = defaultdict(list)
    for candidate in candidates:
        by_accession[candidate["accession"]].append(candidate)

    accession_rows, accession_errors = {}, []
    for index, accession in enumerate(sorted(by_accession), 1):
        sample = by_accession[accession][0]
        filing_row = {"accession": accession, "issuer_cik": sample["issuer_cik"],
                      "form_type": "4", "filing_date": sample["filing_date"]}
        raw, meta = fetch_submission(client, filing_row)
        if raw is None:
            accession_rows[accession] = {"retrieval_status": "FAILED"}
            accession_errors.append({"accession": accession, "status": "RETRIEVAL_FAILED",
                                     "details": meta})
            print(f"PHASE343_FORM4_PROGRESS={index}/{len(by_accession)} FAILED")
            continue
        parsed = raw_meta(raw)
        xml_summary, xml_transactions = extract_transaction_rows(raw, sample["issuer_cik"])
        header_cik = norm_cik(meta.get("header_cik", "")) if meta.get("header_cik") else ""
        if parsed["cik"] != norm_cik(sample["issuer_cik"]) or xml_summary.get("issuer_matches_expected") is not True:
            raise ValueError(f"form4_xml_issuer_cik_mismatch:{accession}")
        if header_cik and header_cik != norm_cik(sample["issuer_cik"]):
            raise ValueError(f"form4_header_cik_mismatch:{accession}")
        bulk_token, bulk_status, _ = parse_symbol(sample.get("issuer_symbol_as_filed", ""))
        xml_token, xml_status, _ = parse_symbol(parsed.get("symbol", ""))
        symbol_reconciled = bulk_status == "SINGLE_TOKEN" and xml_status == "SINGLE_TOKEN" and bulk_token == xml_token
        footnotes = extract_raw_footnotes(raw)
        checks = [verify_candidate_row(c, xml_transactions, parsed["rows"], footnotes,
                                       len(parsed["owners"]), parsed.get("aff", ""))
                  for c in by_accession[accession]]
        accession_rows[accession] = {
            "retrieval_status": "RETRIEVED", "issuer_cik": norm_cik(sample["issuer_cik"]),
            "filing_date": sample["filing_date"], "raw_sha256": meta["submission_sha256"],
            "raw_bytes": meta["submission_bytes"], "path_cik": meta["path_cik"],
            "path_route": meta["route"], "header_cik": meta.get("header_cik", ""),
            "acceptance_datetime_et": meta.get("acceptance_datetime_et", ""),
            "xml_issuer_cik": parsed["cik"], "xml_symbol_raw": parsed.get("symbol", ""),
            "bulk_symbol_raw": sample.get("issuer_symbol_as_filed", ""),
            "symbol_reconciled": symbol_reconciled, "symbol_parse_status": xml_status,
            "xml_owner_count": len(parsed["owners"]), "xml_transaction_rows": len(xml_transactions),
            "candidate_rows": len(by_accession[accession]),
            "candidate_rows_xml_unique": sum(x["xml_match_status"] == "UNIQUE_EXACT_TRANSACTION_ROW" for x in checks),
            "candidate_rows_raw_screen_pass": sum(bool(x["raw_purchase_screen_pass"]) for x in checks),
            "candidate_row_checks": checks,
        }
        if not symbol_reconciled:
            accession_errors.append({"accession": accession, "status": "FORM4_SYMBOL_BULK_XML_MISMATCH"})
        if any(x["xml_match_status"] != "UNIQUE_EXACT_TRANSACTION_ROW" or not x["raw_purchase_screen_pass"] for x in checks):
            accession_errors.append({"accession": accession, "status": "CANDIDATE_ROW_XML_OR_SCREEN_RECONCILIATION_FAILED"})
        print(f"PHASE343_FORM4_PROGRESS={index}/{len(by_accession)} RETRIEVED candidates={len(checks)}")

    event_keys = sorted({(norm_cik(x["issuer_cik"]), x["filing_date"]) for x in candidates})
    submissions_cache, event_anchor, anchor_cache = {}, {}, {}
    for cik in sorted({x[0] for x in event_keys}):
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        raw, status, err, _ = client.get(url, max_bytes=20_000_000)
        if raw is None:
            submissions_cache[cik] = {"status": err or f"HTTP_{status}"}
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            submissions_cache[cik] = {"status": "JSON_PARSE_ERROR"}
            continue
        response_cik = norm_cik(str(obj.get("cik") or cik))
        if response_cik != cik:
            raise ValueError(f"submissions_json_cik_mismatch:{cik}:{response_cik}")
        submissions_cache[cik] = {"status": "OK", "object": obj, "sha256": sha256_bytes(raw)}

    for cik, filing_date in event_keys:
        source = submissions_cache.get(cik, {})
        if source.get("status") != "OK":
            event_anchor[(cik, filing_date)] = {"anchor_status": "SUBMISSIONS_JSON_UNAVAILABLE",
                                                "submissions_status": source.get("status", "")}
            continue
        filing, selection_source = select_prior_periodic_filing(source["object"], filing_date, client)
        if not filing:
            event_anchor[(cik, filing_date)] = {"anchor_status": selection_source}
            continue
        anchor_date = str(filing.get("filingDate") or "")
        prior, age = strict_date_relation(anchor_date, filing_date)
        if not prior or age is None or age <= 0:
            raise ValueError(f"periodic_anchor_not_strictly_pre_filing:{cik}:{filing_date}")
        anchor_accession = str(filing.get("accessionNumber") or "")
        if anchor_accession not in anchor_cache:
            facts, doc = retrieve_filing_facts(client, cik, filing)
            anchor_cache[anchor_accession] = {
                "filing": filing, "facts": facts, "contexts": facts_to_contexts(facts), "document": doc,
            }
        cached = anchor_cache[anchor_accession]
        event_anchor[(cik, filing_date)] = {
            "anchor_status": "SELECTED", "anchor_accession": anchor_accession,
            "anchor_form": filing.get("form", ""), "anchor_filing_date": anchor_date,
            "anchor_report_date": filing.get("reportDate", ""), "anchor_age_calendar_days": age,
            "selection_source": selection_source, "submissions_json_sha256": source.get("sha256", ""),
            "document_status": cached["document"].get("document_status", ""),
            "document_name": cached["document"].get("document_name", ""),
            "document_sha256": cached["document"].get("document_sha256", ""),
            "document_bytes": cached["document"].get("document_bytes", 0),
            "fact_count": len(cached["facts"]), "complete_context_count": len(cached["contexts"]),
        }

    row_results = []
    for accession, candidates_for_accession in by_accession.items():
        doc = accession_rows.get(accession, {})
        checks = doc.get("candidate_row_checks", [])
        for pos, candidate in enumerate(candidates_for_accession):
            verified = checks[pos] if pos < len(checks) else {}
            cik, filing_date = norm_cik(candidate["issuer_cik"]), candidate["filing_date"]
            anchor = event_anchor.get((cik, filing_date), {})
            cross = {"crosswalk_status": "NOT_TESTED"}
            if anchor.get("anchor_status") == "SELECTED":
                cached = anchor_cache[anchor["anchor_accession"]]
                cross = crosswalk(doc.get("xml_symbol_raw", ""), candidate.get("security_title", ""),
                                  cached.get("contexts", []))
            anchor_date = anchor.get("anchor_filing_date", "")
            event_pre, event_age = strict_date_relation(anchor_date, filing_date)
            tx_pre, tx_age = strict_date_relation(anchor_date, candidate.get("transaction_date", ""))
            fresh_event = bool(event_pre and event_age is not None and 0 < event_age <= 365)
            fresh_tx = bool(tx_pre and tx_age is not None and 0 < tx_age <= 365)
            source_ok = (
                doc.get("retrieval_status") == "RETRIEVED"
                and doc.get("symbol_reconciled") is True
                and verified.get("xml_match_status") == "UNIQUE_EXACT_TRANSACTION_ROW"
                and verified.get("raw_purchase_screen_pass") is True
            )
            identity_ok = cross.get("crosswalk_status") == "UNIQUE_COMPATIBLE_SECURITY_CLASS"
            event_identity = bool(source_ok and identity_ok and fresh_event)
            tx_identity = bool(source_ok and identity_ok and fresh_tx)
            row_results.append({
                "period": "2026Q3", "accession": accession, "issuer_cik": cik,
                "filing_date": filing_date, "transaction_date": candidate.get("transaction_date", ""),
                "security_title": candidate.get("security_title", ""),
                "transaction_shares": candidate.get("transaction_shares", ""),
                "transaction_price_per_share": candidate.get("transaction_price_per_share", ""),
                "aff10b5one_bulk": candidate.get("aff10b5one", ""),
                "form4_retrieval_status": doc.get("retrieval_status", "FAILED"),
                "form4_raw_sha256": doc.get("raw_sha256", ""),
                "acceptance_datetime_et": doc.get("acceptance_datetime_et", ""),
                "form4_symbol_reconciled": doc.get("symbol_reconciled", False),
                "xml_transaction_match_status": verified.get("xml_match_status", ""),
                "xml_purchase_screen_pass": verified.get("raw_purchase_screen_pass", False),
                "raw_missing_footnote_ids": verified.get("raw_missing_footnote_ids", []),
                "anchor_status": anchor.get("anchor_status", "NOT_SELECTED"),
                "anchor_accession": anchor.get("anchor_accession", ""),
                "anchor_form": anchor.get("anchor_form", ""),
                "anchor_filing_date": anchor_date,
                "anchor_age_at_filing_days": event_age,
                "anchor_age_at_transaction_days": tx_age,
                "anchor_document_status": anchor.get("document_status", ""),
                "anchor_document_sha256": anchor.get("document_sha256", ""),
                **cross,
                "event_time_anchor_fresh": fresh_event,
                "transaction_date_anchor_fresh": fresh_tx,
                "event_time_identity": event_identity,
                "transaction_date_identity": tx_identity,
            })

    event_summaries = group_event_units(row_results)
    accession_summaries = []
    for accession, candidates_for_accession in sorted(by_accession.items()):
        outputs = [x for x in row_results if x["accession"] == accession]
        doc = accession_rows.get(accession, {})
        accession_summaries.append({
            "accession": accession, "issuer_cik": norm_cik(candidates_for_accession[0]["issuer_cik"]),
            "filing_date": candidates_for_accession[0]["filing_date"],
            "candidate_rows": len(candidates_for_accession),
            "form4_retrieved": doc.get("retrieval_status") == "RETRIEVED",
            "xml_symbol_reconciled": doc.get("symbol_reconciled", False),
            "candidate_rows_xml_unique": doc.get("candidate_rows_xml_unique", 0),
            "candidate_rows_raw_screen_pass": doc.get("candidate_rows_raw_screen_pass", 0),
            "event_time_identity_rows": sum(bool(x["event_time_identity"]) for x in outputs),
            "transaction_date_identity_rows": sum(bool(x["transaction_date_identity"]) for x in outputs),
            "event_time_complete": bool(outputs) and all(x["event_time_identity"] for x in outputs),
            "transaction_date_complete": bool(outputs) and all(x["transaction_date_identity"] for x in outputs),
        })

    retrieved = [x for x in accession_rows.values() if x.get("retrieval_status") == "RETRIEVED"]
    summary = {
        "source_archive_sha256": audit["zip_sha256"], "candidate_rows": len(candidates),
        "candidate_accessions": len(by_accession),
        "candidate_issuer_ciks": len({norm_cik(x["issuer_cik"]) for x in candidates}),
        "issuer_cik_filing_date_event_units": len(event_keys),
        "form4_accessions_retrieved": len(retrieved),
        "form4_symbol_bulk_xml_reconciled": sum(bool(x.get("symbol_reconciled")) for x in retrieved),
        "candidate_rows_unique_xml_transaction_match": sum(
            x.get("xml_match_status") == "UNIQUE_EXACT_TRANSACTION_ROW"
            for d in accession_rows.values() for x in d.get("candidate_row_checks", [])),
        "candidate_rows_raw_purchase_screen_revalidated": sum(
            bool(x.get("raw_purchase_screen_pass"))
            for d in accession_rows.values() for x in d.get("candidate_row_checks", [])),
        "issuer_submissions_json_available": sum(x.get("status") == "OK" for x in submissions_cache.values()),
        "event_units_with_prior_periodic_anchor": sum(x.get("anchor_status") == "SELECTED" for x in event_anchor.values()),
        "event_units_with_fresh_anchor_le_365d": sum(
            x.get("anchor_status") == "SELECTED" and 0 < int(x.get("anchor_age_calendar_days") or 0) <= 365
            for x in event_anchor.values()),
        "unique_periodic_anchors_retrieved": len(anchor_cache),
        "unique_periodic_anchors_with_xbrl_context_triples": sum(bool(x.get("contexts")) for x in anchor_cache.values()),
        "candidate_rows_with_unique_compatible_class_context": sum(
            x.get("crosswalk_status") == "UNIQUE_COMPATIBLE_SECURITY_CLASS" for x in row_results),
        "event_time_identity_rows": sum(bool(x["event_time_identity"]) for x in row_results),
        "transaction_date_identity_rows": sum(bool(x["transaction_date_identity"]) for x in row_results),
        "event_time_identity_accessions_complete": sum(x["event_time_complete"] for x in accession_summaries),
        "event_time_identity_event_units_complete": sum(x["event_time_complete"] for x in event_summaries),
        "transaction_date_identity_event_units_complete": sum(x["transaction_date_complete"] for x in event_summaries),
        "event_time_identity_coverage_pct_rows": 100 * sum(bool(x["event_time_identity"]) for x in row_results) / len(row_results) if row_results else None,
        "event_time_identity_coverage_pct_event_units": 100 * sum(x["event_time_complete"] for x in event_summaries) / len(event_summaries) if event_summaries else None,
        "transaction_date_identity_coverage_pct_rows": 100 * sum(bool(x["transaction_date_identity"]) for x in row_results) / len(row_results) if row_results else None,
    }
    controls = {
        "candidate_sample_is_one_non_contiguous_quarter": True,
        "transaction_code_p_alone_proves_discretionary_open_market_execution": False,
        "bulk_filing_date_is_exact_first_public_timestamp": False,
        "acceptance_datetime_is_exact_first_public_timestamp": False,
        "issuer_symbol_is_permanent_security_key": False,
        "security_title_is_permanent_security_key": False,
        "strict_pit_security_master_admitted": False, "event_study_admitted": False,
        "alpha_test_run": False, "return_test_run": False, "bootstrap_loo_run": False,
        "chronological_oos_run": False, "holdout_used": False, "f80_frozen": True,
        "production_changed": False, "universe_changed": False, "capital_changed": False,
        "parameters_changed": False, "data_purchased": False, "vendor_contacted": False,
    }
    result = {
        "phase": PHASE, "status": "COMPLETED_CANDIDATE_SPECIFIC_EVENT_TIME_IDENTITY_AUDIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {"bulk_archive": ARCHIVES["2026Q3"]["url"],
                    "bulk_archive_sha256": audit["zip_sha256"],
                    "bulk_candidate_rows": len(candidates), "form4_accessions": len(by_accession),
                    "issuer_submissions_json_count": len(submissions_cache),
                    "periodic_anchor_count": len(anchor_cache)},
        "summary": summary, "event_units": event_summaries,
        "accessions": accession_summaries, "candidate_rows": row_results,
        "accession_errors": accession_errors,
        "submissions_status": {cik: {k: v for k, v in item.items() if k != "object"}
                               for cik, item in submissions_cache.items()},
        "periodic_anchors": {acc: {"filing": item["filing"], "document": item["document"],
                                   "fact_count": len(item["facts"]), "contexts": item["contexts"]}
                             for acc, item in anchor_cache.items()},
        "controls": controls,
        "interpretation": {"event_time_identity_is_not_transaction_date_identity": True,
                           "only_exact_same_context_symbol_title_exchange_triples_are_used": True,
                           "multiple_listing_contexts_are_preserved_not_merged_as_new_classes": True,
                           "unmapped_or_ambiguous_rows_remain_quarantined": True,
                           "no_fuzzy_ticker_or_security_title_matching": True},
    }
    (outdir / "phase343_candidate_identity_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(outdir / "phase343_candidate_rows.csv", row_results)
    write_csv(outdir / "phase343_accessions.csv", accession_summaries)
    write_csv(outdir / "phase343_event_units.csv", event_summaries)

    manifest = []
    for index, (url, cached) in enumerate(client.cache.items(), 1):
        raw, status, error, headers = cached
        entry = {"url": url, "http_status": status, "error": error, "headers": headers,
                 "bytes": len(raw) if raw else 0, "sha256": sha256_bytes(raw) if raw else ""}
        if raw:
            suffix = Path(urlparse(url).path).suffix or ".bin"
            name = f"{index:04d}_{hashlib.sha256(url.encode()).hexdigest()[:12]}{suffix}"
            (rawdir / name).write_bytes(raw)
            entry["artifact_file"] = f"raw_sec/{name}"
        manifest.append(entry)
    (outdir / "sec_response_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE343_STATUS=" + result["status"])
    print("PHASE343_SUMMARY=" + json.dumps(summary, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--email", default="")
    args = parser.parse_args()
    run(args.archive, args.output_dir, args.email)


if __name__ == "__main__":
    main()

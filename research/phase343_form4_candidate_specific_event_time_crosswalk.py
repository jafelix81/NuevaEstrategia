#!/usr/bin/env python3
"""Phase 343: candidate-specific 2026Q3 Form 4 original-document and event-time identity audit.

This phase is a fail-closed identity/coverage diagnostic. It does not test returns.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from research.phase328_sec_collision_prior_filing_xbrl_pilot import (
    SECClient, _parallel_rows, choose_instance_file, parse_instance_xml,
)
from research.phase339_sec_security_exchange_context_audit import (
    build_symbol_exchange_associations, extract_context_rows, find_filing_row,
)
from research.phase340_form4_transaction_date_anchor_pit_audit import fetch_submission as fetch_form4_submission
from research.phase341_form4_issuer_symbol_class_crosswalk_audit import (
    match_title, parse_symbol,
)
from research.phase342_sec_insider_bulk_sample_audit import (
    aff_gate_required, classify_purchase_row, normalize_aff, referenced_footnote_ids,
)

PHASE342_ARTIFACT_SHA256 = "16614b404f007b78f47951ef84604660ea6612f0c86f1b2ba5a6fa7b7d52d80c"
PHASE342_JSON_SHA256 = "c81e1b9a92ef7cd0bcefef29d0f4ce19e2cce84bae0838704706b212c8f95cac"
PHASE342_2026Q3_ZIP_SHA256 = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
PHASE341_ARTIFACT_SHA256 = "b15232741016bf39445acd3dde5c010c3aeef013cb59e6997a1ba9a9763e8130"
PHASE342_RUN_ID = 43265704634
PHASE342_ARTIFACT_ID = 13965917386
PHASE341_ARTIFACT_ID = 13963219558
ALLOWED_ANCHOR_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A"}
FRESHNESS_DAYS = 365


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1].split(":")[-1]


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def norm_date(value: str | None) -> str:
    value = norm_text(value)
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y"):
        try:
            return datetime.strptime(value.upper(), fmt).date().isoformat()
        except ValueError:
            pass
    return value


def norm_num(value: str | None) -> str:
    value = norm_text(value)
    if not value:
        return ""
    try:
        number = Decimal(value.replace(",", ""))
        if number == 0:
            return "0"
        return format(number.normalize(), "f")
    except (InvalidOperation, ValueError):
        return value


def child_named(parent: ET.Element | None, name: str) -> ET.Element | None:
    if parent is None:
        return None
    return next((x for x in list(parent) if local_name(x.tag) == name), None)


def path_value(root: ET.Element, path: str) -> str:
    current: ET.Element | None = root
    for part in path.split("/"):
        current = child_named(current, part)
        if current is None:
            return ""
    value = child_named(current, "value")
    target = value if value is not None else current
    return norm_text("".join(target.itertext()))


def parse_ownership_document(raw: bytes) -> dict[str, Any]:
    # SEC complete-submission text is SGML. Select the Form 4 document rather
    # than parsing the XSL display document listed as primaryDocument.
    text = raw.decode("latin-1", errors="replace")
    documents = re.findall(r"<DOCUMENT>\s*(.*?)\s*</DOCUMENT>", text, flags=re.I | re.S)
    candidates = []
    for document in documents:
        typ = re.search(r"<TYPE>\s*([^\s<]+)", document, flags=re.I)
        body = re.search(r"<TEXT>\s*(.*?)\s*</TEXT>", document, flags=re.I | re.S)
        if not body:
            continue
        content = body.group(1).strip()
        xml_match = re.search(r"<XML>\s*(.*?)\s*</XML>", content, flags=re.I | re.S)
        content = xml_match.group(1).strip() if xml_match else content
        if (typ and typ.group(1).upper() in {"4", "4/A"}) or "ownershipdocument" in content.lower():
            candidates.append(content)
    if not candidates:
        candidates = [text]

    root = None
    for candidate in candidates:
        start = re.search(r"<(?:[A-Za-z0-9_]+:)?ownershipDocument\b", candidate, re.I)
        if not start:
            continue
        xml_text = candidate[start.start():]
        end = re.search(r"</(?:[A-Za-z0-9_]+:)?ownershipDocument\s*>", xml_text, re.I)
        if end:
            xml_text = xml_text[:end.end()]
        try:
            root = ET.fromstring(xml_text.encode("latin-1"))
            if local_name(root.tag).lower() == "ownershipdocument":
                break
            root = None
        except ET.ParseError:
            root = None
    if root is None:
        raise ValueError("COMPLETE_SUBMISSION_HAS_NO_PARSEABLE_OWNERSHIP_XML")

    owners = []
    for owner in [x for x in list(root) if local_name(x.tag) == "reportingOwner"]:
        owners.append({
            "cik": path_value(owner, "reportingOwnerId/rptOwnerCik").lstrip("0"),
            "name": path_value(owner, "reportingOwnerId/rptOwnerName"),
            "is_director": path_value(owner, "reportingOwnerRelationship/isDirector"),
            "is_officer": path_value(owner, "reportingOwnerRelationship/isOfficer"),
            "is_ten_percent_owner": path_value(owner, "reportingOwnerRelationship/isTenPercentOwner"),
            "officer_title": path_value(owner, "reportingOwnerRelationship/officerTitle"),
        })

    footnotes: dict[str, str] = {}
    footnotes_parent = child_named(root, "footnotes")
    if footnotes_parent is not None:
        for item in list(footnotes_parent):
            if local_name(item.tag) == "footnote":
                fid = str(item.attrib.get("id") or "").strip()
                if fid:
                    footnotes[fid] = norm_text("".join(item.itertext()))

    transactions = []
    table = child_named(root, "nonDerivativeTable")
    if table is not None:
        for item in [x for x in list(table) if local_name(x.tag) == "nonDerivativeTransaction"]:
            refs = sorted({
                str(x.attrib.get("id") or "").strip()
                for x in item.iter()
                if local_name(x.tag) == "footnoteId" and str(x.attrib.get("id") or "").strip()
            })
            transactions.append({
                "security_title": path_value(item, "securityTitle"),
                "transaction_date": path_value(item, "transactionDate"),
                "transaction_code": path_value(item, "transactionCoding/transactionCode"),
                "acquired_disposed": path_value(item, "transactionAmounts/transactionAcquiredDisposedCode"),
                "shares": path_value(item, "transactionAmounts/transactionShares"),
                "price": path_value(item, "transactionAmounts/transactionPricePerShare"),
                "direct_indirect": path_value(item, "ownershipNature/directOrIndirectOwnership"),
                "nature_of_ownership": path_value(item, "ownershipNature/natureOfOwnership"),
                "footnote_ids": refs,
                "footnote_text": [footnotes[x] for x in refs if x in footnotes],
            })

    return {
        "issuer_cik": path_value(root, "issuer/issuerCik").lstrip("0"),
        "issuer_symbol_raw": path_value(root, "issuer/issuerTradingSymbol"),
        "aff10b5one_raw": path_value(root, "aff10b5One"),
        "owners": owners,
        "footnotes": footnotes,
        "transactions": transactions,
    }


def transaction_signature(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        norm_text(row.get("security_title")).upper(),
        norm_date(row.get("transaction_date")),
        norm_text(row.get("transaction_code")).upper(),
        norm_text(row.get("acquired_disposed")).upper(),
        norm_text(row.get("direct_indirect")).upper(),
        norm_num(row.get("shares")),
        norm_num(row.get("price")),
    )


def table_transaction_signature(row: dict[str, str]) -> tuple[str, ...]:
    return transaction_signature({
        "security_title": row.get("SECURITY_TITLE"),
        "transaction_date": row.get("TRANS_DATE"),
        "transaction_code": row.get("TRANS_CODE"),
        "acquired_disposed": row.get("TRANS_ACQUIRED_DISP_CD"),
        "direct_indirect": row.get("DIRECT_INDIRECT_OWNERSHIP"),
        "shares": row.get("TRANS_SHARES"),
        "price": row.get("TRANS_PRICEPERSHARE"),
    })


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    members = [x for x in zf.namelist() if Path(x).name.upper() == name.upper()]
    if len(members) != 1:
        raise ValueError(f"TABLE_MEMBER_NOT_UNIQUE:{name}:{members}")
    with zf.open(members[0]) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t"))


def extract_candidate_rows(archive_bytes: bytes, phase342_expected: dict) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        if zf.testzip():
            raise ValueError("2026Q3_ARCHIVE_ZIP_INTEGRITY_FAILED")
        submissions = read_tsv(zf, "SUBMISSION.tsv")
        transactions = read_tsv(zf, "NONDERIV_TRANS.tsv")
        owners = read_tsv(zf, "REPORTINGOWNER.tsv")
        footnotes = read_tsv(zf, "FOOTNOTES.tsv")

    sub_counts = Counter((x.get("ACCESSION_NUMBER") or "").strip() for x in submissions)
    sub_by_acc = {
        (x.get("ACCESSION_NUMBER") or "").strip(): x
        for x in submissions
        if (x.get("ACCESSION_NUMBER") or "").strip()
        and sub_counts[(x.get("ACCESSION_NUMBER") or "").strip()] == 1
    }
    owner_ciks: dict[str, set[str]] = defaultdict(set)
    for row in owners:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        cik = (row.get("RPTOWNERCIK") or "").strip().lstrip("0")
        if acc and cik:
            owner_ciks[acc].add(cik)
    foot_map: dict[str, dict[str, str]] = defaultdict(dict)
    for row in footnotes:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        fid = (row.get("FOOTNOTE_ID") or "").strip()
        if acc and fid:
            foot_map[acc][fid] = row.get("FOOTNOTE_TXT") or ""

    out = []
    for row in transactions:
        acc = (row.get("ACCESSION_NUMBER") or "").strip()
        sub = sub_by_acc.get(acc)
        if not sub:
            continue
        if not (
            (sub.get("DOCUMENT_TYPE") or "").strip() == "4"
            and row.get("TRANS_FORM_TYPE") == "4"
            and row.get("TRANS_CODE") == "P"
            and row.get("TRANS_ACQUIRED_DISP_CD") == "A"
        ):
            continue
        refs = referenced_footnote_ids(row)
        foot = foot_map.get(acc, {})
        missing = sorted(x for x in refs if x not in foot)
        text = " ".join(foot[x] for x in sorted(refs) if x in foot)
        require_aff_false = aff_gate_required(sub.get("FILING_DATE"))
        aff = sub.get("AFF10B5ONE", "")
        classification_row = dict(row)
        classification_row["DOCUMENT_TYPE"] = (sub.get("DOCUMENT_TYPE") or "").strip()
        flags = classify_purchase_row(classification_row, text, len(owner_ciks.get(acc, set())), aff, require_aff_false)
        if missing:
            flags["explicit_open_market"] = False
        if all(flags[k] for k in (
            "base", "explicit_open_market", "no_private_disclosure", "no_plan_disclosure",
            "no_mechanical_disclosure", "direct_ownership", "single_reporting_owner",
            "common_stock_title", "aff_gate",
        )):
            out.append({
                "accession": acc,
                "issuer_cik": (sub.get("ISSUERCIK") or "").strip().lstrip("0"),
                "filing_date": norm_date(sub.get("FILING_DATE")),
                "filing_date_raw": (sub.get("FILING_DATE") or "").strip(),
                "issuer_symbol_bulk": (sub.get("ISSUERTRADINGSYMBOL") or "").strip(),
                "aff10b5one_bulk": normalize_aff(aff),
                "owner_ciks_bulk": sorted(owner_ciks.get(acc, set())),
                "owner_count_bulk": len(owner_ciks.get(acc, set())),
                "transaction_sk": (row.get("NONDERIV_TRANS_SK") or "").strip(),
                "security_title_bulk": row.get("SECURITY_TITLE", ""),
                "transaction_date_bulk": row.get("TRANS_DATE", ""),
                "transaction_code_bulk": row.get("TRANS_CODE", ""),
                "acquired_disposed_bulk": row.get("TRANS_ACQUIRED_DISP_CD", ""),
                "direct_indirect_bulk": row.get("DIRECT_INDIRECT_OWNERSHIP", ""),
                "shares_bulk": row.get("TRANS_SHARES", ""),
                "price_bulk": row.get("TRANS_PRICEPERSHARE", ""),
                "footnote_ids_bulk": sorted(refs),
                "footnote_text_bulk": text,
                "footnote_missing": bool(missing),
            })
    counts = {
        "candidate_rows": len(out),
        "candidate_accessions": len({x["accession"] for x in out}),
        "candidate_issuer_ciks": len({x["issuer_cik"] for x in out}),
    }
    expected = {
        "candidate_rows": phase342_expected["candidate_rows"],
        "candidate_accessions": phase342_expected["candidate_accessions"],
        "candidate_issuer_ciks": phase342_expected["candidate_issuer_ciks"],
    }
    if counts != expected:
        raise ValueError(f"PHASE342_CANDIDATE_COHORT_REPRODUCTION_MISMATCH:{counts}:{expected}")
    return out


def select_prior_anchor(payload: dict, event_date: str, client: SECClient) -> tuple[dict | None, str]:
    recent = _parallel_rows(payload.get("filings", {}).get("recent", {}))
    candidates = [
        r for r in recent
        if str(r.get("form") or "").upper() in ALLOWED_ANCHOR_FORMS
        and str(r.get("filingDate") or "") < event_date
    ]
    if candidates:
        return max(candidates, key=lambda r: (r["filingDate"], r["accessionNumber"])), "RECENT"
    shards = payload.get("filings", {}).get("files", []) or []
    eligible = [
        x for x in shards
        if str(x.get("filingFrom") or "") and str(x.get("filingFrom")) <= event_date
    ]
    for shard in sorted(eligible, key=lambda x: str(x.get("filingTo") or ""), reverse=True):
        name = str(shard.get("name") or "")
        if not name:
            continue
        raw, status, err, _ = client.get(f"https://data.sec.gov/submissions/{name}", max_bytes=20_000_000)
        if not raw:
            continue
        try:
            rows = _parallel_rows(json.loads(raw).get("filings", {}).get("recent", {}))
        except (ValueError, AttributeError):
            continue
        candidates = [
            r for r in rows
            if str(r.get("form") or "").upper() in ALLOWED_ANCHOR_FORMS
            and str(r.get("filingDate") or "") < event_date
        ]
        if candidates:
            return max(candidates, key=lambda r: (r["filingDate"], r["accessionNumber"])), f"SHARD:{name}"
    return None, "NO_PRIOR_SUPPORTED_PERIODIC_FILING"


def retrieve_anchor_xbrl(client: SECClient, cik: str, filing: dict, raw_dir: Path) -> tuple[list[dict], dict]:
    accession = str(filing["accessionNumber"])
    compact = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/"
    index_raw, index_status, index_error, _ = client.get(base + "index.json", max_bytes=3_000_000)
    if not index_raw:
        return [], {"document_status": "ANCHOR_INDEX_UNAVAILABLE", "index_http_status": index_status, "index_error": index_error}
    try:
        index = json.loads(index_raw)
        instance_name = choose_instance_file(index, str(filing.get("primaryDocument") or ""))
    except (ValueError, TypeError, AttributeError):
        instance_name = None
    if not instance_name:
        return [], {"document_status": "NO_XBRL_INSTANCE_FILE", "index_http_status": index_status}
    raw, status, error, headers = client.get(base + instance_name, max_bytes=30_000_000)
    if not raw:
        return [], {"document_status": error or "ANCHOR_INSTANCE_UNAVAILABLE", "document_http_status": status, "index_http_status": index_status}
    try:
        facts = parse_instance_xml(raw)
    except ET.ParseError:
        return [], {"document_status": "ANCHOR_INSTANCE_XML_PARSE_ERROR", "document_http_status": status, "index_http_status": index_status}
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{cik}_{compact}_{Path(instance_name).name}").write_bytes(raw)
    return facts, {
        "document_status": "XBRL_INSTANCE_PARSED",
        "document_name": instance_name,
        "document_sha256": sha(raw),
        "document_bytes": len(raw),
        "document_http_status": status,
        "index_http_status": index_status,
        "last_modified": headers.get("last-modified", ""),
    }


def retrieve_form4_submission(client: SECClient, cik: str, accession: str, filing_date: str, raw_dir: Path) -> tuple[dict | None, dict]:
    row = {"accession": accession, "issuer_cik": cik, "form_type": "4", "filing_date": filing_date}
    raw, meta = fetch_form4_submission(client, row)
    if raw is None:
        return None, {"document_status": "FORM4_COMPLETE_SUBMISSION_UNAVAILABLE", **meta}
    try:
        parsed = parse_ownership_document(raw)
    except (ET.ParseError, ValueError) as exc:
        return None, {
            "document_status": f"FORM4_COMPLETE_SUBMISSION_XML_PARSE_FAILED:{str(exc)[:120]}",
            "submission_sha256": meta.get("submission_sha256", ""),
            "submission_bytes": meta.get("submission_bytes", 0),
            **meta,
        }
    raw_dir.mkdir(parents=True, exist_ok=True)
    compact = accession.replace("-", "")
    (raw_dir / f"{compact}.txt").write_bytes(raw)
    return parsed, {
        "document_status": "FORM4_COMPLETE_SUBMISSION_PARSED",
        "document_sha256": meta.get("submission_sha256", sha(raw)),
        "document_bytes": meta.get("submission_bytes", len(raw)),
        "fetch_path_cik": meta.get("path_cik", ""),
        "fetch_path_route": meta.get("route", ""),
        "header_cik": meta.get("header_cik", ""),
        "acceptance_datetime_et": meta.get("acceptance_datetime_et", ""),
        "xml_issuer_cik_from_fetcher": meta.get("xml_issuer_cik", ""),
        "xml_owner_ciks_from_fetcher": meta.get("xml_owner_ciks", []),
        "prior_route_errors": meta.get("prior_route_errors", []),
        "http_status": meta.get("http_status", ""),
    }


def crosswalk_symbol_to_anchor(symbol_raw: str, candidate_title: str, associations: list[dict]) -> dict[str, Any]:
    token, symbol_status, prefix = parse_symbol(symbol_raw)
    matches = [x for x in associations if token and x.get("symbol") == token]
    strict = [
        x for x in matches
        if x.get("association_status") == "SYMBOL_12B_TITLE_AND_EXCHANGE_SAME_CONTEXT"
        and x.get("has_symbol_12b_title_exchange_same_context")
        and len(x.get("same_context_security_12b_titles") or []) == 1
        and len(x.get("same_context_exchange_values") or []) == 1
    ]
    if len(strict) != 1:
        return {
            "symbol_token": token, "symbol_parse_status": symbol_status, "exchange_prefix": prefix,
            "symbol_context_count": len(matches), "strict_context_count": len(strict),
            "unique_symbol_context": False, "matched_xbrl_title": "",
            "matched_exchange": "", "title_match_method": "NO_UNIQUE_SAME_CONTEXT_SYMBOL_TITLE_EXCHANGE",
            "instrument_class": "", "class_axis_members": [], "listing_axis_members": [],
        }
    assoc = strict[0]
    xbrl_title = assoc["same_context_security_12b_titles"][0]
    ok, method, instrument_class = match_title(candidate_title, xbrl_title)
    return {
        "symbol_token": token, "symbol_parse_status": symbol_status, "exchange_prefix": prefix,
        "symbol_context_count": len(matches), "strict_context_count": len(strict),
        "unique_symbol_context": True, "matched_xbrl_title": xbrl_title,
        "matched_exchange": assoc["same_context_exchange_values"][0],
        "title_match_method": method if ok else method,
        "title_compatible": ok,
        "instrument_class": instrument_class,
        "class_axis_members": assoc.get("symbol_class_axis_members", []),
        "listing_axis_members": assoc.get("symbol_listing_axis_members", []),
        "symbol_context_ref": assoc.get("symbol_context_ref", ""),
    }


def run(phase342_artifact: Path, phase341_artifact: Path, email: str, output_dir: Path) -> dict:
    if sha(phase342_artifact.read_bytes()) != PHASE342_ARTIFACT_SHA256:
        raise ValueError("PHASE342_ARTIFACT_SHA256_MISMATCH")
    if sha(phase341_artifact.read_bytes()) != PHASE341_ARTIFACT_SHA256:
        raise ValueError("PHASE341_ARTIFACT_SHA256_MISMATCH")
    if not email or "@" not in email:
        raise RuntimeError("BLOCKED_MISSING_SEC_CONTACT_EMAIL")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_form4_dir = output_dir / "raw_form4"
    raw_anchor_dir = output_dir / "raw_periodic_xbrl"
    with zipfile.ZipFile(phase342_artifact) as zf:
        audit_bytes = zf.read("phase342_output/phase342_sec_insider_bulk_sample_audit.json")
        if sha(audit_bytes) != PHASE342_JSON_SHA256:
            raise ValueError("PHASE342_AUDIT_JSON_SHA256_MISMATCH")
        phase342 = json.loads(audit_bytes)
        archive_bytes = zf.read("phase342_input/2026q3_form345.zip")
    if sha(archive_bytes) != PHASE342_2026Q3_ZIP_SHA256:
        raise ValueError("PHASE342_2026Q3_SOURCE_ZIP_SHA256_MISMATCH")
    expected = phase342["archives"]["2026Q3"]
    candidate_rows = extract_candidate_rows(archive_bytes, expected)
    if len(candidate_rows) != 85:
        raise ValueError("PHASE343_EXPECTED_85_CANDIDATE_ROWS")
    candidate_accessions = sorted({x["accession"] for x in candidate_rows})
    issuer_ciks = sorted({x["issuer_cik"] for x in candidate_rows})
    event_units = {(x["issuer_cik"], x["filing_date"]) for x in candidate_rows}
    if (len(candidate_accessions), len(issuer_ciks), len(event_units)) != (59, 31, 48):
        raise ValueError("PHASE343_CANDIDATE_COHORT_DENOMINATOR_MISMATCH")

    with zipfile.ZipFile(phase341_artifact) as zf:
        crosswalk_raw = zf.read("phase341_accession_crosswalk.csv")
    phase341_rows = list(csv.DictReader(io.StringIO(crosswalk_raw.decode("utf-8-sig"))))
    phase341_2026 = [x for x in phase341_rows if str(x.get("filing_date") or "").startswith("2026-")]
    overlap_accessions = sorted(set(candidate_accessions) & {x["accession"] for x in phase341_2026})
    overlap_issuers = sorted(set(issuer_ciks) & {str(x.get("issuer_cik") or "").lstrip("0") for x in phase341_2026})
    if overlap_accessions or overlap_issuers:
        raise ValueError("PHASE341_BROAD_SAMPLE_OVERLAP_CHANGED")

    client = SECClient(email)
    submissions_cache: dict[str, tuple[dict | None, dict]] = {}
    form4_meta: dict[str, dict] = {}
    form4_docs: dict[str, dict] = {}
    accession_rows = []
    for n, accession in enumerate(candidate_accessions, 1):
        rows_for_acc = [x for x in candidate_rows if x["accession"] == accession]
        first = rows_for_acc[0]
        cik = first["issuer_cik"]
        filing_date = first["filing_date"]
        if any(x["issuer_cik"] != cik or x["filing_date"] != filing_date for x in rows_for_acc):
            raise ValueError("CANDIDATE_ACCESSION_HAS_MULTIPLE_ISSUER_OR_FILING_DATE")
        parsed, doc_meta = retrieve_form4_submission(client, cik, accession, filing_date, raw_form4_dir)
        if parsed is None:
            accession_rows.append({
                "accession": accession, "issuer_cik": cik, "filing_date_bulk": filing_date,
                "form4_status": doc_meta.get("document_status", "FORM4_COMPLETE_SUBMISSION_UNAVAILABLE"),
                **doc_meta,
            })
            continue
        symbol_bulk = parse_symbol(first["issuer_symbol_bulk"])[0]
        symbol_xml = parse_symbol(parsed["issuer_symbol_raw"])[0]
        owners_xml = sorted({x["cik"] for x in parsed["owners"] if x["cik"]})
        owner_match = owners_xml == first["owner_ciks_bulk"] and len(parsed["owners"]) == 1
        aff_xml = normalize_aff(parsed["aff10b5one_raw"])
        header_cik = str(doc_meta.get("header_cik") or "").lstrip("0")
        header_entity_match = header_cik in {cik, *first["owner_ciks_bulk"]}
        form4_ok = (
            parsed["issuer_cik"] == cik
            and symbol_bulk != ""
            and symbol_bulk == symbol_xml
            and aff_xml == first["aff10b5one_bulk"] == "false"
            and owner_match
            and header_entity_match
            and bool(doc_meta.get("document_sha256"))
        )
        accession_rows.append({
            "accession": accession, "issuer_cik": cik, "filing_date_bulk": filing_date,
            "form4_form": "4",
            "form4_status": "FORM4_COMPLETE_SUBMISSION_PARSED",
            "form4_document_sha256": doc_meta.get("document_sha256", ""),
            "form4_document_bytes": doc_meta.get("document_bytes", 0),
            "form4_fetch_path_cik": doc_meta.get("fetch_path_cik", ""),
            "form4_fetch_path_route": doc_meta.get("fetch_path_route", ""),
            "form4_header_cik": header_cik,
            "form4_header_entity_match": header_entity_match,
            "form4_acceptance_datetime_et": doc_meta.get("acceptance_datetime_et", ""),
            "issuer_cik_xml": parsed["issuer_cik"],
            "issuer_symbol_bulk": first["issuer_symbol_bulk"],
            "issuer_symbol_xml": parsed["issuer_symbol_raw"],
            "issuer_symbol_bulk_token": symbol_bulk,
            "issuer_symbol_xml_token": symbol_xml,
            "aff10b5one_bulk": first["aff10b5one_bulk"],
            "aff10b5one_xml": aff_xml,
            "owner_ciks_bulk": first["owner_ciks_bulk"],
            "owner_ciks_xml": owners_xml,
            "owner_count_xml": len(parsed["owners"]),
            "form4_metadata_reconciled": form4_ok,
            **doc_meta,
        })
        form4_meta[accession] = {
            "parsed": parsed, "meta": doc_meta,
            "reconciled": form4_ok,
        }
        form4_docs[accession] = parsed
        print(f"PHASE343_FORM4_PROGRESS={n}/{len(candidate_accessions)} status={doc_meta['document_status']} reconciled={form4_ok}")

    # Select the latest supported periodic filing strictly before each issuer/date event unit.
    anchor_cache: dict[tuple[str, str], dict] = {}
    unit_to_anchor: dict[tuple[str, str], dict] = {}
    for unit in sorted(event_units):
        cik, event_date = unit
        payload = submissions_cache.get(cik, (None, {}))[0]
        if payload is None:
            unit_to_anchor[unit] = {"anchor_status": "NO_SUBMISSIONS_PAYLOAD"}
            continue
        anchor, selection_source = select_prior_anchor(payload, event_date, client)
        if not anchor:
            unit_to_anchor[unit] = {"anchor_status": selection_source}
            continue
        anchor_date = str(anchor.get("filingDate") or "")
        age = (date.fromisoformat(event_date) - date.fromisoformat(anchor_date)).days
        base = {
            "anchor_accession": anchor.get("accessionNumber", ""),
            "anchor_form": anchor.get("form", ""),
            "anchor_filing_date": anchor_date,
            "anchor_age_calendar_days": age,
            "anchor_selection_source": selection_source,
        }
        if age <= 0:
            unit_to_anchor[unit] = {**base, "anchor_status": "SAME_DAY_OR_LOOKAHEAD_QUARANTINE"}
            continue
        if age > FRESHNESS_DAYS:
            unit_to_anchor[unit] = {**base, "anchor_status": "STALE_OVER_365_DAYS"}
            continue
        cache_key = (cik, str(anchor.get("accessionNumber") or ""))
        if cache_key not in anchor_cache:
            filing_row, row_source, row_status = find_filing_row(client, cik, cache_key[1], anchor_date)
            if not filing_row:
                anchor_cache[cache_key] = {"facts": [], "meta": {"document_status": "ANCHOR_SUBMISSIONS_ROW_NOT_FOUND", "lookup_source": row_source, "lookup_status": row_status}, "associations": []}
            else:
                facts, doc_meta = retrieve_anchor_xbrl(client, cik, filing_row, raw_anchor_dir)
                associations = build_symbol_exchange_associations(*extract_context_rows(facts)) if facts else []
                anchor_cache[cache_key] = {
                    "facts": facts, "meta": {**doc_meta, "lookup_source": row_source, "lookup_status": row_status},
                    "associations": associations, "filing_row": filing_row,
                }
        cached = anchor_cache[cache_key]
        unit_to_anchor[unit] = {**base, "anchor_status": cached["meta"].get("document_status", "UNKNOWN"), **cached["meta"]}

    transaction_rows = []
    for candidate in candidate_rows:
        accession = candidate["accession"]
        form4 = form4_meta.get(accession)
        unit = (candidate["issuer_cik"], candidate["filing_date"])
        anchor = unit_to_anchor.get(unit, {"anchor_status": "ANCHOR_NOT_PROCESSED"})
        form4_reconciled = bool(form4 and form4["reconciled"])
        parsed = form4["parsed"] if form4 else None
        xml_rows = parsed["transactions"] if parsed else []
        sig = table_transaction_signature({
            "SECURITY_TITLE": candidate["security_title_bulk"],
            "TRANS_DATE": candidate["transaction_date_bulk"],
            "TRANS_CODE": candidate["transaction_code_bulk"],
            "TRANS_ACQUIRED_DISP_CD": candidate["acquired_disposed_bulk"],
            "DIRECT_INDIRECT_OWNERSHIP": candidate["direct_indirect_bulk"],
            "TRANS_SHARES": candidate["shares_bulk"],
            "TRANS_PRICEPERSHARE": candidate["price_bulk"],
        })
        matching_xml = [x for x in xml_rows if transaction_signature(x) == sig]
        xml_row = matching_xml[0] if len(matching_xml) == 1 else None
        refs_match = bool(xml_row) and set(candidate["footnote_ids_bulk"]) == set(xml_row["footnote_ids"])
        # Reconcile the original XML row and bulk owner/issuer/plan metadata.
        row_reconciled = bool(
            form4_reconciled and xml_row and refs_match
            and norm_text(" ".join(xml_row["footnote_text"])) == norm_text(candidate["footnote_text_bulk"])
            and xml_row["transaction_code"] == "P"
            and xml_row["direct_indirect"] == "D"
        )
        anchor_date = str(anchor.get("anchor_filing_date") or "")
        age = anchor.get("anchor_age_calendar_days")
        anchor_pre_filing = bool(anchor_date and anchor_date < candidate["filing_date"])
        try:
            transaction_date_iso = norm_date(candidate["transaction_date_bulk"])
            anchor_pre_transaction = bool(anchor_date and transaction_date_iso and date.fromisoformat(anchor_date) < date.fromisoformat(transaction_date_iso))
        except ValueError:
            anchor_pre_transaction = False
        anchor_fresh = bool(isinstance(age, int) and 0 < age <= FRESHNESS_DAYS)
        cross = {"unique_symbol_context": False, "title_compatible": False, "title_match_method": "ANCHOR_NOT_ADMITTED"}
        if anchor.get("anchor_status") == "XBRL_INSTANCE_PARSED" and form4:
            cached = anchor_cache.get((candidate["issuer_cik"], anchor.get("anchor_accession", "")), {})
            associations = cached.get("associations", [])
            cross = crosswalk_symbol_to_anchor(parsed["issuer_symbol_raw"], candidate["security_title_bulk"], associations)
        event_identity = bool(
            row_reconciled and anchor_pre_filing and anchor_fresh
            and anchor.get("anchor_status") == "XBRL_INSTANCE_PARSED"
            and cross.get("unique_symbol_context") and cross.get("title_compatible")
        )
        transaction_identity = bool(event_identity and anchor_pre_transaction)
        transaction_rows.append({
            **candidate,
            "form4_primary_reconciled": form4_reconciled,
            "original_xml_transaction_match_count": len(matching_xml),
            "original_xml_transaction_unique_match": xml_row is not None,
            "original_xml_footnote_reference_match": refs_match,
            "original_xml_footnote_text_match": bool(xml_row) and norm_text(" ".join(xml_row["footnote_text"])) == norm_text(candidate["footnote_text_bulk"]),
            "original_xml_row_reconciled": row_reconciled,
            "form4_symbol_xml": parsed["issuer_symbol_raw"] if parsed else "",
            "form4_aff10b5one_xml": normalize_aff(parsed["aff10b5one_raw"]) if parsed else "unknown",
            "form4_owner_count_xml": len(parsed["owners"]) if parsed else 0,
            "anchor_status": anchor.get("anchor_status", ""),
            "anchor_accession": anchor.get("anchor_accession", ""),
            "anchor_form": anchor.get("anchor_form", ""),
            "anchor_filing_date": anchor_date,
            "anchor_age_calendar_days": age,
            "anchor_pre_filing": anchor_pre_filing,
            "anchor_pre_transaction": anchor_pre_transaction,
            "anchor_fresh_le_365d": anchor_fresh,
            "anchor_xbrl_sha256": anchor.get("document_sha256", ""),
            "anchor_document_name": anchor.get("document_name", ""),
            **cross,
            "provisional_event_time_identity": event_identity,
            "provisional_transaction_date_identity": transaction_identity,
            "disposition": (
                "EVENT_TIME_IDENTITY_CANDIDATE" if event_identity else
                "TRANSACTION_ROW_RECONCILIATION_FAILED" if not row_reconciled else
                "ANCHOR_NOT_FRESH_OR_NOT_PRE_FILING" if not (anchor_pre_filing and anchor_fresh) else
                "NO_UNIQUE_SAME_CONTEXT_SYMBOL_TITLE_EXCHANGE" if not cross.get("unique_symbol_context") else
                "INSTRUMENT_TITLE_MISMATCH"
            ),
        })

    accession_by_id = {x["accession"]: x for x in accession_rows}
    mapped_accessions = {
        x["accession"] for x in transaction_rows if x["provisional_event_time_identity"]
    }
    transaction_date_accessions = {
        x["accession"] for x in transaction_rows if x["provisional_transaction_date_identity"]
    }
    event_time_units = {
        (x["issuer_cik"], x["filing_date"]) for x in transaction_rows if x["provisional_event_time_identity"]
    }
    transaction_date_units = {
        (x["issuer_cik"], x["filing_date"]) for x in transaction_rows if x["provisional_transaction_date_identity"]
    }
    unique_symbol_accessions = {
        x["accession"] for x in transaction_rows if x.get("unique_symbol_context") and x.get("title_compatible")
    }
    summary = {
        "candidate_rows": len(candidate_rows),
        "candidate_accessions": len(candidate_accessions),
        "candidate_issuers": len(issuer_ciks),
        "candidate_issuer_filing_date_events": len(event_units),
        "phase341_2026_sample_accessions": len(phase341_2026),
        "phase341_candidate_accession_overlap": len(overlap_accessions),
        "phase341_candidate_issuer_cik_overlap": len(overlap_issuers),
        "form4_full_submissions_parsed": sum(x.get("form4_status") == "FORM4_COMPLETE_SUBMISSION_PARSED" for x in accession_rows),
        "form4_metadata_reconciled_accessions": sum(x.get("form4_metadata_reconciled", False) for x in accession_rows),
        "form4_submission_hashes_unique": len({x.get("form4_document_sha256") for x in accession_rows if x.get("form4_document_sha256")}),
        "form4_acceptance_timestamps_captured": sum(bool(x.get("form4_acceptance_datetime_et")) for x in accession_rows),
        "issuer_filing_date_units_with_fresh_prior_anchor": sum(
            x.get("anchor_status") == "XBRL_INSTANCE_PARSED" for x in unit_to_anchor.values()
        ),
        "unique_periodic_anchor_accessions": len(anchor_cache),
        "periodic_xbrl_instances_parsed": sum(x["meta"].get("document_status") == "XBRL_INSTANCE_PARSED" for x in anchor_cache.values()),
        "accessions_with_unique_symbol_class_exchange_context": len(unique_symbol_accessions),
        "event_time_identity_rows": sum(x["provisional_event_time_identity"] for x in transaction_rows),
        "event_time_identity_accessions": len(mapped_accessions),
        "event_time_identity_issuer_filing_events": len(event_time_units),
        "transaction_date_identity_rows": sum(x["provisional_transaction_date_identity"] for x in transaction_rows),
        "transaction_date_identity_accessions": len(transaction_date_accessions),
        "transaction_date_identity_issuer_filing_events": len(transaction_date_units),
        "event_time_only_rows_anchor_after_transaction": sum(
            x["provisional_event_time_identity"] and not x["provisional_transaction_date_identity"] for x in transaction_rows
        ),
        "candidate_rows_with_original_xml_transaction_match": sum(x["original_xml_transaction_unique_match"] for x in transaction_rows),
        "candidate_rows_with_original_xml_footnote_match": sum(x["original_xml_footnote_reference_match"] and x["original_xml_footnote_text_match"] for x in transaction_rows),
    }
    result = {
        "phase": 343,
        "status": "COMPLETED_CANDIDATE_SPECIFIC_EVENT_TIME_IDENTITY_AUDIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "phase342_run_id": PHASE342_RUN_ID,
            "phase342_artifact_id": PHASE342_ARTIFACT_ID,
            "phase342_artifact_sha256": PHASE342_ARTIFACT_SHA256,
            "phase342_json_sha256": PHASE342_JSON_SHA256,
            "phase342_2026q3_zip_sha256": PHASE342_2026Q3_ZIP_SHA256,
            "phase341_artifact_id": PHASE341_ARTIFACT_ID,
            "phase341_artifact_sha256": PHASE341_ARTIFACT_SHA256,
            "candidate_selection": "all Phase342 2026Q3 high-precision candidate rows; no resampling",
        },
        "summary": summary,
        "accessions": accession_rows,
        "issuer_filing_date_anchors": [
            {"issuer_cik": k[0], "filing_date": k[1], **v}
            for k, v in sorted(unit_to_anchor.items())
        ],
        "transactions": transaction_rows,
        "controls": {
            "event_time_identity_is_not_transaction_date_identity": True,
            "form4_filing_date_is_date_only_not_exact_first_public_timestamp": True,
            "security_identity_admitted": False,
            "strict_pit_admitted": False,
            "survivorship_aware_price_panel_admitted": False,
            "alpha_test_run": False,
            "return_test_run": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchased": False,
            "vendor_contacted": False,
            "email_sent": False,
        },
    }
    (output_dir / "phase343_candidate_specific_identity_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    def write_csv(path: Path, rows: list[dict]):
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    write_csv(output_dir / "phase343_accession_crosswalk.csv", accession_rows)
    write_csv(output_dir / "phase343_transaction_crosswalk.csv", transaction_rows)
    write_csv(output_dir / "phase343_quarantine.csv", [x for x in transaction_rows if not x["provisional_event_time_identity"]])
    print("PHASE343_STATUS=" + result["status"])
    print("PHASE343_SUMMARY=" + json.dumps(summary, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase342-artifact", type=Path, required=True)
    parser.add_argument("--phase341-artifact", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--email", default="")
    args = parser.parse_args()
    run(args.phase342_artifact, args.phase341_artifact, args.email, args.output_dir)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 299: stratified Form 4/A candidate validation against original EDGAR submissions.

The SEC bulk archive does not expose an authoritative parent-accession foreign key.
This audit tests whether the Phase 298 heuristic links are independently corroborated
by the original/amended submission headers and ownershipDocument XML. It does not
promote candidate links to authoritative parents or test returns/alpha.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

OUTER_HASHES = {
    "phase294": "8b256375a68ffc581134e3fb05dd96ca3a02f6acd47925a003aa3f4b3d1680f4",
    "phase298": "f7c630b8e0cbabba5fd41f25fc09777fbed8fbaa49c309fc8003b14cb880ae0e",
}
INNER_HASHES = {
    "2011Q4": "47f35cc68de7c43c7ab7dd86f00a8c9e5f5aa1f4bca0ea859b903d17f198e0b8",
    "2012Q1": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2026Q2": "11f1b2bbbdcbe6347a34437c02d04202fda0eca1dbb023726e4b56504b802e27",
    "2026Q3": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
TARGET_PERIODS = {
    "2012Q1": ("2011Q4", "2012Q1"),
    "2026Q3": ("2026Q2", "2026Q3"),
}
ARCHIVE_PATHS = {
    "2011Q4": ("phase298", "adjacent_source/2011q4_form345.zip"),
    "2012Q1": ("phase294", "raw/2012q1_form345.zip"),
    "2026Q2": ("phase298", "adjacent_source/2026q2_form345.zip"),
    "2026Q3": ("phase294", "raw/2026q3_form345.zip"),
}
NUMERIC = {
    "TRANS_SHARES", "TRANS_PRICEPERSHARE", "SHRS_OWND_FOLWNG_TRANS",
    "VALU_OWND_FOLWNG_TRANS", "CONV_EXERCISE_PRICE", "TRANS_TOTAL_VALUE",
    "UNDLYNG_SEC_SHARES", "UNDLYNG_SEC_VALUE",
}
ND_EXACT = (
    "SECURITY_TITLE", "TRANS_DATE", "DEEMED_EXECUTION_DATE", "TRANS_FORM_TYPE",
    "TRANS_CODE", "EQUITY_SWAP_INVOLVED", "TRANS_TIMELINESS", "TRANS_SHARES",
    "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD", "SHRS_OWND_FOLWNG_TRANS",
    "DIRECT_INDIRECT_OWNERSHIP", "NATURE_OF_OWNERSHIP",
)
DV_EXACT = (
    "SECURITY_TITLE", "TRANS_DATE", "DEEMED_EXECUTION_DATE", "TRANS_FORM_TYPE",
    "TRANS_CODE", "EQUITY_SWAP_INVOLVED", "TRANS_TIMELINESS", "TRANS_SHARES",
    "TRANS_TOTAL_VALUE", "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD",
    "EXCERCISE_DATE", "EXPIRATION_DATE", "CONV_EXERCISE_PRICE",
    "UNDLYNG_SEC_TITLE", "UNDLYNG_SEC_SHARES", "SHRS_OWND_FOLWNG_TRANS",
    "DIRECT_INDIRECT_OWNERSHIP", "NATURE_OF_OWNERSHIP",
)
ND_COARSE = ("SECURITY_TITLE", "TRANS_DATE", "TRANS_FORM_TYPE", "TRANS_CODE")
DV_COARSE = ("SECURITY_TITLE", "TRANS_DATE", "TRANS_FORM_TYPE", "TRANS_CODE", "UNDLYNG_SEC_TITLE")

ND_XML_MAP = {
    "SECURITY_TITLE": "securityTitle/value",
    "TRANS_DATE": "transactionDate/value",
    "DEEMED_EXECUTION_DATE": "deemedExecutionDate/value",
    "TRANS_FORM_TYPE": "transactionCoding/transactionFormType",
    "TRANS_CODE": "transactionCoding/transactionCode",
    "EQUITY_SWAP_INVOLVED": "transactionCoding/equitySwapInvolved",
    "TRANS_TIMELINESS": "transactionTimeliness",
    "TRANS_SHARES": "transactionAmounts/transactionShares/value",
    "TRANS_PRICEPERSHARE": "transactionAmounts/transactionPricePerShare/value",
    "TRANS_ACQUIRED_DISP_CD": "transactionAmounts/transactionAcquiredDisposedCode/value",
    "SHRS_OWND_FOLWNG_TRANS": "postTransactionAmounts/sharesOwnedFollowingTransaction/value",
    "VALU_OWND_FOLWNG_TRANS": "postTransactionAmounts/valueOwnedFollowingTransaction/value",
    "DIRECT_INDIRECT_OWNERSHIP": "ownershipNature/directOrIndirectOwnership/value",
    "NATURE_OF_OWNERSHIP": "ownershipNature/natureOfOwnership/value",
}
DV_XML_MAP = {
    "SECURITY_TITLE": "securityTitle/value",
    "CONV_EXERCISE_PRICE": "conversionOrExercisePrice/value",
    "TRANS_DATE": "transactionDate/value",
    "DEEMED_EXECUTION_DATE": "deemedExecutionDate/value",
    "TRANS_FORM_TYPE": "transactionCoding/transactionFormType",
    "TRANS_CODE": "transactionCoding/transactionCode",
    "EQUITY_SWAP_INVOLVED": "transactionCoding/equitySwapInvolved",
    "TRANS_TIMELINESS": "transactionTimeliness",
    "TRANS_SHARES": "transactionAmounts/transactionShares/value",
    "TRANS_TOTAL_VALUE": "transactionAmounts/transactionTotalValue/value",
    "TRANS_PRICEPERSHARE": "transactionAmounts/transactionPricePerShare/value",
    "TRANS_ACQUIRED_DISP_CD": "transactionAmounts/transactionAcquiredDisposedCode/value",
    "EXCERCISE_DATE": "exerciseDate/value",
    "EXPIRATION_DATE": "expirationDate/value",
    "UNDLYNG_SEC_TITLE": "underlyingSecurity/underlyingSecurityTitle/value",
    "UNDLYNG_SEC_SHARES": "underlyingSecurity/underlyingSecurityShares/value",
    "UNDLYNG_SEC_VALUE": "underlyingSecurity/underlyingSecurityValue/value",
    "SHRS_OWND_FOLWNG_TRANS": "postTransactionAmounts/sharesOwnedFollowingTransaction/value",
    "VALU_OWND_FOLWNG_TRANS": "postTransactionAmounts/valueOwnedFollowingTransaction/value",
    "DIRECT_INDIRECT_OWNERSHIP": "ownershipNature/directOrIndirectOwnership/value",
    "NATURE_OF_OWNERSHIP": "ownershipNature/natureOfOwnership/value",
}
ACC_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def norm_date(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.upper(), fmt).date().isoformat()
        except ValueError:
            pass
    return value.upper()


def norm_cik(value: str | None) -> str:
    value = (value or "").strip()
    return value.zfill(10) if value.isdigit() and len(value) <= 10 else ""


def norm_value(field: str, value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if field in NUMERIC:
        try:
            from decimal import Decimal
            number = Decimal(value.replace(",", ""))
            if number.is_finite():
                return format(number.normalize(), "f")
        except Exception:
            pass
    return " ".join(value.upper().split())


def read_table(zf: zipfile.ZipFile, suffix: str) -> list[dict[str, str]]:
    names = [name for name in zf.namelist() if name.rsplit("/", 1)[-1].upper() == suffix.upper()]
    if len(names) != 1:
        raise ValueError(f"expected_one_{suffix}:{names}")
    return list(csv.DictReader(io.StringIO(zf.read(names[0]).decode("utf-8-sig")), delimiter="\t"))


def load_period(path: Path, period: str) -> dict:
    payload = path.read_bytes()
    expected = INNER_HASHES[period]
    if sha256(payload) != expected:
        raise ValueError(f"inner_archive_hash_mismatch:{period}")
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        if zf.testzip():
            raise ValueError(f"zip_crc_failure:{period}")
        submissions = read_table(zf, "SUBMISSION.tsv")
        owners = read_table(zf, "REPORTINGOWNER.tsv")
        nd_rows = read_table(zf, "NONDERIV_TRANS.tsv")
        dv_rows = read_table(zf, "DERIV_TRANS.tsv")

    filings: dict[str, dict] = {}
    for row in submissions:
        doc = (row.get("DOCUMENT_TYPE") or "").strip().upper()
        if doc not in {"4", "4/A"}:
            continue
        accession = (row.get("ACCESSION_NUMBER") or "").strip()
        issuer = norm_cik(row.get("ISSUERCIK"))
        if not ACC_RE.fullmatch(accession) or not issuer:
            raise ValueError(f"invalid_accession_or_issuer:{period}:{accession}")
        filings[accession] = {
            "accession": accession, "period": period, "doc": doc,
            "issuer": issuer, "filing_date": norm_date(row.get("FILING_DATE")),
            "orig_date": norm_date(row.get("DATE_OF_ORIG_SUB")),
            "ticker": (row.get("ISSUERTRADINGSYMBOL") or "").strip(),
            "owners": set(), "nd": [], "dv": [],
        }
    for row in owners:
        accession = (row.get("ACCESSION_NUMBER") or "").strip()
        owner = norm_cik(row.get("RPTOWNERCIK"))
        if accession in filings and owner:
            filings[accession]["owners"].add(owner)
    for rows, key in ((nd_rows, "nd"), (dv_rows, "dv")):
        for row in rows:
            accession = (row.get("ACCESSION_NUMBER") or "").strip()
            if accession in filings:
                filings[accession][key].append(row)
    return {"sha256": sha256(payload), "filings": filings}


def signature(row: dict, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(norm_value(field, row.get(field)) for field in fields)


def diff_rows(parent: list[dict], child: list[dict], exact_fields: tuple[str, ...],
              coarse_fields: tuple[str, ...]) -> dict:
    parent_exact = Counter(signature(row, exact_fields) for row in parent)
    child_exact = Counter(signature(row, exact_fields) for row in child)
    repeated = sum((parent_exact & child_exact).values())
    parent_coarse = Counter(signature(row, coarse_fields) for row in parent)
    child_coarse = Counter(signature(row, coarse_fields) for row in child)
    matched_coarse = Counter()
    remaining_exact = parent_exact.copy()
    for row in child:
        sig = signature(row, exact_fields)
        if remaining_exact[sig] > 0:
            matched_coarse[signature(row, coarse_fields)] += 1
            remaining_exact[sig] -= 1
    parent_remaining = parent_coarse - matched_coarse
    child_remaining = child_coarse - matched_coarse
    same_coarse = sum(min(parent_coarse[key], child_remaining[key]) for key in child_remaining)
    distinct_added = sum(child_remaining.values()) - same_coarse
    parent_unmatched = sum(parent_remaining.values()) - sum(
        min(parent_remaining[key], child_remaining[key]) for key in parent_remaining
    )
    return {
        "parent_rows": len(parent), "amendment_rows": len(child),
        "exact_repeated": repeated, "same_coarse_unmatched": same_coarse,
        "distinct_coarse_added": distinct_added, "parent_unmatched": parent_unmatched,
    }


def diff_class(parent: dict, child: dict) -> str:
    nd = diff_rows(parent["nd"], child["nd"], ND_EXACT, ND_COARSE)
    dv = diff_rows(parent["dv"], child["dv"], DV_EXACT, DV_COARSE)
    same = nd["same_coarse_unmatched"] + dv["same_coarse_unmatched"] > 0
    distinct = nd["distinct_coarse_added"] + dv["distinct_coarse_added"] > 0
    if same and distinct:
        return "both"
    if same:
        return "same_coarse"
    if distinct:
        return "distinct_coarse"
    return "exact_only"


def build_candidate_pairs(periods: dict[str, dict]) -> list[dict]:
    index: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for period_data in periods.values():
        for filing in period_data["filings"].values():
            if filing["doc"] == "4" and filing["filing_date"]:
                index[(filing["issuer"], filing["filing_date"])].append(filing)

    pairs = []
    for target, search_periods in TARGET_PERIODS.items():
        for child in periods[target]["filings"].values():
            if child["doc"] != "4/A" or not child["orig_date"] or not child["owners"]:
                continue
            candidates = []
            for parent in index.get((child["issuer"], child["orig_date"]), []):
                if parent["accession"] == child["accession"] or parent["filing_date"] > child["filing_date"]:
                    continue
                shared = child["owners"] & parent["owners"]
                if shared:
                    candidates.append((parent, shared))
            if len(candidates) != 1:
                continue
            parent, shared = candidates[0]
            if parent["period"] not in search_periods:
                continue
            pairs.append({
                "target": target, "parent": parent, "child": child,
                "shared_owners": sorted(shared),
                "owner_sets_equal": child["owners"] == parent["owners"],
                "diff_class": diff_class(parent, child),
            })
    return pairs


def deterministic_rank(pair: dict) -> str:
    raw = pair["child"]["accession"] + "|" + pair["parent"]["accession"] + "|phase299-seed-1"
    return hashlib.sha256(raw.encode()).hexdigest()


def choose_sample(pairs: list[dict]) -> list[dict]:
    selected = []
    strata = ("exact_only", "same_coarse", "distinct_coarse", "both")
    for target, periods in TARGET_PERIODS.items():
        for parent_period in periods:
            for category in strata:
                pool = [
                    pair for pair in pairs
                    if pair["target"] == target
                    and pair["parent"]["period"] == parent_period
                    and pair["owner_sets_equal"]
                    and pair["diff_class"] == category
                ]
                pool.sort(key=deterministic_rank)
                selected.extend(pool[:2])
    # Include every partial-owner candidate: these are rare and directly test the
    # accession-level ownership limitation rather than hiding it through sampling.
    selected.extend(pair for pair in pairs if not pair["owner_sets_equal"])
    # Known positive control from the previous phase.
    known_child = "0001437749-26-029308"
    if not any(pair["child"]["accession"] == known_child for pair in selected):
        known = next((pair for pair in pairs if pair["child"]["accession"] == known_child), None)
        if known is None:
            raise ValueError("known_eton_positive_control_missing")
        selected.append(known)
    unique = {}
    for pair in selected:
        unique[pair["child"]["accession"]] = pair
    return sorted(unique.values(), key=lambda p: (p["target"], p["parent"]["period"], p["child"]["accession"]))


def doc_record(filing: dict) -> dict:
    owners = sorted(filing["owners"])
    path_ciks = list(owners)
    for candidate in (filing["issuer"], filing["accession"][:10]):
        if candidate and candidate not in path_ciks:
            path_ciks.append(candidate)
    return {
        "accession": filing["accession"], "period": filing["period"],
        "document_type": filing["doc"], "issuer_cik": filing["issuer"],
        "issuer_ticker_as_filed": filing["ticker"], "filing_date": filing["filing_date"],
        "owner_ciks": owners, "path_cik_candidates": path_ciks,
    }


def build_manifest(periods: dict[str, dict], pairs: list[dict], selected: list[dict]) -> dict:
    docs = {}
    pair_rows = []
    for i, pair in enumerate(selected, 1):
        parent, child = pair["parent"], pair["child"]
        docs[parent["accession"]] = doc_record(parent)
        docs[child["accession"]] = doc_record(child)
        pair_rows.append({
            "sample_id": f"P299-{i:03d}", "target_period": pair["target"],
            "parent_period": parent["period"],
            "parent_accession": parent["accession"],
            "amendment_accession": child["accession"],
            "issuer_cik": child["issuer"], "issuer_ticker_as_filed": child["ticker"],
            "parent_filing_date": parent["filing_date"],
            "amendment_filing_date": child["filing_date"],
            "amendment_date_of_orig_sub": child["orig_date"],
            "parent_owner_ciks": sorted(parent["owners"]),
            "amendment_owner_ciks": sorted(child["owners"]),
            "shared_owner_ciks": pair["shared_owners"],
            "owner_sets_equal": pair["owner_sets_equal"],
            "candidate_line_diff_class": pair["diff_class"],
            "bulk_parent_nonderivative_rows": len(parent["nd"]),
            "bulk_amendment_nonderivative_rows": len(child["nd"]),
            "bulk_parent_derivative_rows": len(parent["dv"]),
            "bulk_amendment_derivative_rows": len(child["dv"]),
            "sampling_rank_sha256": deterministic_rank(pair),
        })
    return {
        "phase": 299, "status": "STRATIFIED_SAMPLE_SELECTED",
        "selection_method": (
            "For each target quarter x parent quarter x candidate line-diff class, "
            "select the two exact-owner pairs with smallest SHA-256 rank; include all "
            "partial-owner pairs; include the known Eton positive control."
        ),
        "target_periods": TARGET_PERIODS,
        "source_archives": {
            period: {"sha256": periods[period]["sha256"], "form4_form4a_count": len(periods[period]["filings"])}
            for period in sorted(periods)
        },
        "candidate_pair_population": len(pairs),
        "sample_pair_count": len(pair_rows),
        "sample_document_count": len(docs),
        "sample_pairs": pair_rows,
        "documents": [docs[key] for key in sorted(docs)],
        "controls": {
            "all_partial_owner_pairs_included": True,
            "known_eton_pair_included": True,
            "returns_or_alpha_test": False,
            "strict_pit_admission": False,
            "holdout_used": False,
        },
    }


def child_text(element: ET.Element, path: str) -> str:
    found = element.find(path)
    return (found.text or "").strip() if found is not None else ""


def xml_transaction_rows(root: ET.Element, table: str) -> list[dict[str, str]]:
    if table == "nd":
        container = root.find("nonDerivativeTable")
        node_name = "nonDerivativeTransaction"
        mapping = ND_XML_MAP
    else:
        container = root.find("derivativeTable")
        node_name = "derivativeTransaction"
        mapping = DV_XML_MAP
    if container is None:
        return []
    rows = []
    for node in container.findall(node_name):
        rows.append({field: child_text(node, path) for field, path in mapping.items()})
    return rows


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_submission(payload: bytes) -> dict:
    text = payload.decode("utf-8", errors="replace")
    def header(pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""

    accession = header(r"^ACCESSION NUMBER:\s*(\S+)")
    form_type = header(r"^CONFORMED SUBMISSION TYPE:\s*(\S+)")
    filed_date = header(r"^FILED AS OF DATE:\s*(\d{8})")
    acceptance = header(r"<ACCEPTANCE-DATETIME>(\d{14})")
    xml_blocks = re.findall(r"<XML>\s*(.*?)\s*</XML>", text, re.IGNORECASE | re.DOTALL)
    root = None
    xml_error = ""
    for block in xml_blocks:
        if "ownershipDocument" not in block:
            continue
        try:
            candidate = ET.fromstring(block)
            if local_name(candidate.tag) == "ownershipDocument":
                root = candidate
                break
        except ET.ParseError as exc:
            xml_error = str(exc)
    if root is None:
        return {
            "accession": accession, "header_form_type": form_type,
            "filed_as_of_date": filed_date, "acceptance_datetime": acceptance,
            "xml_parse_ok": False, "xml_parse_error": xml_error or "ownershipDocument_not_found",
        }

    owners = sorted({
        norm_cik(child_text(node, "reportingOwnerId/rptOwnerCik"))
        for node in root.findall("reportingOwner")
        if child_text(node, "reportingOwnerId/rptOwnerCik")
    })
    return {
        "accession": accession, "header_form_type": form_type,
        "filed_as_of_date": filed_date, "acceptance_datetime": acceptance,
        "xml_parse_ok": True, "xml_document_type": child_text(root, "documentType"),
        "xml_issuer_cik": norm_cik(child_text(root, "issuer/issuerCik")),
        "xml_issuer_ticker": child_text(root, "issuer/issuerTradingSymbol"),
        "xml_owner_ciks": owners,
        "xml_period_of_report": child_text(root, "periodOfReport"),
        "xml_date_of_original_submission": child_text(root, "dateOfOriginalSubmission"),
        "xml_aff10b5_one": child_text(root, "aff10b5One"),
        "xml_nd_rows": xml_transaction_rows(root, "nd"),
        "xml_dv_rows": xml_transaction_rows(root, "dv"),
        "xml_remarks": child_text(root, "remarks"),
        "xml_footnote_count": len(root.findall("footnotes/footnote")),
    }


def compare_bulk_xml(doc: dict, parsed: dict, period_filings: dict) -> dict:
    filing = period_filings[doc["period"]]["filings"][doc["accession"]]
    bulk_nd, bulk_dv = filing["nd"], filing["dv"]
    xml_nd, xml_dv = parsed.get("xml_nd_rows", []), parsed.get("xml_dv_rows", [])
    nd_match = Counter(signature(row, ND_EXACT) for row in bulk_nd) == Counter(
        signature(row, ND_EXACT) for row in xml_nd
    )
    dv_match = Counter(signature(row, DV_EXACT) for row in bulk_dv) == Counter(
        signature(row, DV_EXACT) for row in xml_dv
    )
    return {
        "bulk_nd_rows": len(bulk_nd), "xml_nd_rows": len(xml_nd),
        "nd_exact_multiset_match": nd_match,
        "bulk_dv_rows": len(bulk_dv), "xml_dv_rows": len(xml_dv),
        "dv_exact_multiset_match": dv_match,
        "all_transaction_rows_exact_match": nd_match and dv_match,
    }


def metadata_check(expected: dict, parsed: dict, row_match: dict) -> dict:
    checks = {
        "accession_matches": parsed.get("accession") == expected["accession"],
        "header_form_matches": parsed.get("header_form_type", "").upper() == expected["document_type"],
        "xml_document_type_matches": parsed.get("xml_document_type", "").upper() == expected["document_type"],
        "filing_date_matches": parsed.get("filed_as_of_date") == expected["filing_date"].replace("-", ""),
        "issuer_cik_matches": parsed.get("xml_issuer_cik") == expected["issuer_cik"],
        "reporting_owner_set_matches": sorted(parsed.get("xml_owner_ciks", [])) == sorted(expected["owner_ciks"]),
        "xml_parsed": parsed.get("xml_parse_ok") is True,
    }
    checks["all_header_xml_identity_checks"] = all(checks.values())
    checks["bulk_xml_transaction_multisets_match"] = row_match["all_transaction_rows_exact_match"]
    return checks


def parse_acceptance(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S")
    except (ValueError, TypeError):
        return None


def download_document(expected: dict, output_dir: Path, user_agent: str) -> dict:
    accession = expected["accession"]
    acc_path = accession.replace("-", "")
    errors = []
    for cik in expected["path_cik_candidates"]:
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_path}/{accession}.txt"
        request = urllib.request.Request(
            url, headers={
                "User-Agent": user_agent,
                "Accept": "text/plain, application/octet-stream, */*",
                "Accept-Encoding": "identity",
            },
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    payload = response.read()
                    if not payload.startswith(b"<SEC-DOCUMENT>"):
                        raise ValueError("unexpected_sec_response_body")
                    path = output_dir / f"{acc_path}.txt"
                    path.write_bytes(payload)
                    time.sleep(0.16)
                    return {
                        "accession": accession, "downloaded": True,
                        "path_cik_used": cik, "url": url,
                        "bytes": len(payload), "sha256": sha256(payload),
                        "path": str(path),
                    }
            except urllib.error.HTTPError as exc:
                errors.append({"cik": cik, "status": exc.code})
                if exc.code in {403, 429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                errors.append({"cik": cik, "status": type(exc).__name__})
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                break
        time.sleep(0.16)
    return {"accession": accession, "downloaded": False, "attempts": errors}


def adjudicate_pairs(manifest: dict, parsed_docs: dict, doc_checks: dict,
                     bulk_periods: dict) -> list[dict]:
    results = []
    for pair in manifest["sample_pairs"]:
        parent = parsed_docs.get(pair["parent_accession"])
        child = parsed_docs.get(pair["amendment_accession"])
        parent_check = doc_checks.get(pair["parent_accession"], {})
        child_check = doc_checks.get(pair["amendment_accession"], {})
        parent_accept = parse_acceptance(parent.get("acceptance_datetime")) if parent else None
        child_accept = parse_acceptance(child.get("acceptance_datetime")) if child else None
        date_match = bool(
            child and child.get("xml_date_of_original_submission")
            and norm_date(child["xml_date_of_original_submission"]) == pair["parent_filing_date"]
        )
        issuer_match = bool(
            parent and child and parent.get("xml_issuer_cik") == child.get("xml_issuer_cik") == pair["issuer_cik"]
        )
        owner_overlap = bool(
            parent and child and set(parent.get("xml_owner_ciks", [])) & set(child.get("xml_owner_ciks", []))
        )
        chronological = bool(parent_accept and child_accept and parent_accept <= child_accept)
        parent_type = bool(parent and parent.get("xml_document_type") == "4")
        child_type = bool(child and child.get("xml_document_type") == "4/A")
        metadata_ok = all((
            parent_check.get("all_header_xml_identity_checks", False),
            child_check.get("all_header_xml_identity_checks", False),
            date_match, issuer_match, owner_overlap, chronological, parent_type, child_type,
        ))
        line_rows_ok = bool(
            parent_check.get("bulk_xml_transaction_multisets_match", False)
            and child_check.get("bulk_xml_transaction_multisets_match", False)
        )
        xml_diff = None
        if parent and child and parent.get("xml_parse_ok") and child.get("xml_parse_ok"):
            xml_diff = {
                "table_i_nonderivative": diff_rows(
                    parent["xml_nd_rows"], child["xml_nd_rows"], ND_EXACT, ND_COARSE
                ),
                "table_ii_derivative": diff_rows(
                    parent["xml_dv_rows"], child["xml_dv_rows"], DV_EXACT, DV_COARSE
                ),
            }
        results.append({
            "sample_id": pair["sample_id"], "parent_accession": pair["parent_accession"],
            "amendment_accession": pair["amendment_accession"],
            "candidate_link_metadata_corroborated": metadata_ok,
            "parent_header_xml_identity_ok": parent_check.get("all_header_xml_identity_checks", False),
            "amendment_header_xml_identity_ok": child_check.get("all_header_xml_identity_checks", False),
            "date_of_original_submission_matches_parent_filing_date": date_match,
            "issuer_identity_matches": issuer_match,
            "reporting_owner_overlap_matches": owner_overlap,
            "parent_acceptance_not_after_amendment": chronological,
            "parent_is_original_form4": parent_type,
            "child_is_form4a": child_type,
            "bulk_xml_transaction_rows_exact_match_both_filings": line_rows_ok,
            "xml_line_diff_candidate_only": xml_diff,
            "owner_attribution": (
                "single_owner_accession_level_only"
                if len(pair["parent_owner_ciks"]) == 1 and len(pair["amendment_owner_ciks"]) == 1
                and pair["owner_sets_equal"]
                else "multi_owner_or_partial_overlap_transaction_owner_unresolved"
            ),
            "authoritative_parent_accession_foreign_key": False,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase294-dir", type=Path, required=True)
    parser.add_argument("--phase298-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contact-email", required=True)
    args = parser.parse_args()
    if not args.contact_email.strip() or "@" not in args.contact_email:
        raise SystemExit("SEC_CONTACT_EMAIL_missing_or_invalid")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw_edgar"
    raw_dir.mkdir(parents=True, exist_ok=True)

    outer_payloads = {}
    # Outer artifacts are verified by the workflow before extraction; inner archives
    # are independently re-hashed here against the immutable Phase 294/298 manifests.
    archive_paths = {}
    for period, (source, relative) in ARCHIVE_PATHS.items():
        base = args.phase294_dir if source == "phase294" else args.phase298_dir
        path = base / relative
        if not path.is_file():
            raise SystemExit(f"missing_inner_archive:{period}:{path}")
        archive_paths[period] = path
    periods = {period: load_period(path, period) for period, path in archive_paths.items()}
    pairs = build_candidate_pairs(periods)
    selected = choose_sample(pairs)
    manifest = build_manifest(periods, pairs, selected)
    (args.output_dir / "phase299_sample_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    docs = manifest["documents"]
    user_agent = f"NuevaEstrategia SEC research {args.contact_email.strip()}"
    downloads = []
    for expected in docs:
        downloads.append(download_document(expected, raw_dir, user_agent))
    downloaded = {row["accession"]: row for row in downloads if row["downloaded"]}

    parsed_docs = {}
    doc_checks = {}
    for expected in docs:
        accession = expected["accession"]
        download = downloaded.get(accession)
        if not download:
            continue
        payload = Path(download["path"]).read_bytes()
        parsed = parse_submission(payload)
        row_match = compare_bulk_xml(expected, parsed, periods) if parsed.get("xml_parse_ok") else {
            "bulk_nd_rows": 0, "xml_nd_rows": 0, "nd_exact_multiset_match": False,
            "bulk_dv_rows": 0, "xml_dv_rows": 0, "dv_exact_multiset_match": False,
            "all_transaction_rows_exact_match": False,
        }
        parsed["download_bytes"] = len(payload)
        parsed["download_sha256"] = sha256(payload)
        parsed["path_cik_used"] = download["path_cik_used"]
        parsed["bulk_xml_row_comparison"] = row_match
        parsed_docs[accession] = parsed
        doc_checks[accession] = metadata_check(expected, parsed, row_match)

    pair_results = adjudicate_pairs(manifest, parsed_docs, doc_checks, periods)
    summary = {
        "expected_documents": len(docs),
        "downloaded_documents": len(downloaded),
        "xml_parse_success": sum(1 for value in parsed_docs.values() if value.get("xml_parse_ok")),
        "header_xml_identity_pass": sum(1 for value in doc_checks.values() if value.get("all_header_xml_identity_checks")),
        "bulk_xml_all_transaction_rows_match": sum(
            1 for value in doc_checks.values() if value.get("bulk_xml_transaction_multisets_match")
        ),
        "sample_pairs": len(pair_results),
        "metadata_corroborated_candidate_pairs": sum(
            1 for value in pair_results if value["candidate_link_metadata_corroborated"]
        ),
        "pairs_with_both_filings_bulk_xml_rows_exact": sum(
            1 for value in pair_results if value["bulk_xml_transaction_rows_exact_match_both_filings"]
        ),
        "single_owner_equal_set_pairs": sum(
            1 for row in manifest["sample_pairs"]
            if len(row["parent_owner_ciks"]) == 1 and len(row["amendment_owner_ciks"]) == 1 and row["owner_sets_equal"]
        ),
        "partial_or_multi_owner_pairs": sum(
            1 for row in manifest["sample_pairs"]
            if not (len(row["parent_owner_ciks"]) == 1 and len(row["amendment_owner_ciks"]) == 1 and row["owner_sets_equal"])
        ),
        "same_quarter_parent_pairs": sum(1 for row in manifest["sample_pairs"] if row["target_period"] == row["parent_period"]),
        "adjacent_quarter_parent_pairs": sum(1 for row in manifest["sample_pairs"] if row["target_period"] != row["parent_period"]),
    }
    result = {
        "phase": 299, "status": "COMPLETED" if len(downloaded) == len(docs) else "INCOMPLETE_DOWNLOAD",
        "source": {
            "provider": "SEC EDGAR",
            "phase294_artifact_id": 13884014630,
            "phase298_artifact_id": 13891901486,
            "inner_archive_sha256": {period: periods[period]["sha256"] for period in sorted(periods)},
        },
        "summary": summary,
        "downloads": downloads,
        "documents": {
            accession: {
                **{k: v for k, v in parsed_docs[accession].items() if k not in {"xml_nd_rows", "xml_dv_rows", "xml_remarks"}},
                "checks": doc_checks[accession],
            }
            for accession in sorted(parsed_docs)
        },
        "pairs": pair_results,
        "limitations": [
            "The SEC bulk archive has no authoritative parent-accession foreign key; corroborated links remain metadata candidates.",
            "DATE_OF_ORIG_SUB is date-only; same-day multiple originals may remain indistinguishable.",
            "The SEC complete-submission acceptance timestamp is a knowledge-clock field, not proof of exact first public availability.",
            "A transaction table in a joint/group filing is not mapped to an individual reporting owner; multi-owner transaction attribution remains unresolved.",
            "A line-level difference is a candidate addition or modification, not a confirmed new trade, deletion or reversal.",
            "This stratified sample is not a prevalence estimate and does not establish frozen-universe coverage.",
        ],
        "controls": {
            "strict_pit_admitted": False, "alpha_test": False, "return_test": False,
            "bootstrap_loo": False, "chronological_oos": False, "holdout_used": False,
            "f80_frozen": True, "production_changed": False, "universe_changed": False,
            "capital_changed": False, "parameters_changed": False, "data_purchase": False,
            "email_sent": False,
        },
    }
    (args.output_dir / "phase299_validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"phase": 299, "status": result["status"], "summary": summary}, indent=2))
    if len(downloaded) != len(docs):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

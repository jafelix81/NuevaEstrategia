#!/usr/bin/env python3
"""Targeted SEC Form 144 parent-link and acceptance-time audit; no return tests."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from research import phase401_form144a_full_parent_identity_census as p401

PHASE401_RUN_ID = 43626453375
PHASE401_ARTIFACT_ID = 14126667342
PHASE401_ARTIFACT_SHA256 = "6ce994213e507d6c0637162c520b003bb7e2a239b922f2a13cc24aaadd5d011c"
QUARTERS = ("2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2025Q4")
DAILY_DATES = ("2023-11-27", "2023-11-28", "2023-11-29", "2023-11-30", "2023-12-01", "2023-12-04", "2023-12-05", "2023-12-06", "2023-12-07", "2023-12-08", "2024-03-11", "2024-03-12", "2024-03-13")
EXPECTED_BOUNDARY_PAIRS = 4
EXPECTED_UNRESOLVED_PAIRS = 4
PHASE67_START = "2023-04-13"

def norm_acc(value):
    return p401.accession(value)

def path_cik_from_url(url):
    m = re.search(r"/data/(\d+)/", str(url or ""))
    return p401.norm_cik(m.group(1)) if m else None

def unique_ciks(*groups):
    out = []
    for group in groups:
        if isinstance(group, (str, int)):
            group = [group]
        for value in group or []:
            cik = p401.norm_cik(value)
            if cik and cik not in out:
                out.append(cik)
    return out

def parse_acceptance_html(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    visible = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    visible = re.sub(r"\s+", " ", visible)
    m = re.search(r"\bAccepted\b\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", visible, re.I)
    return m.group(1) if m else None

def parse_acceptance_submission(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    m = re.search(r"ACCEPTANCE-DATETIME\s*:\s*(\d{14})", raw, re.I)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")

def parse_filing_date_html(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    visible = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    visible = re.sub(r"\s+", " ", visible)
    m = re.search(r"\bFiling Date\b\s*(\d{4}-\d{2}-\d{2})", visible, re.I)
    return m.group(1) if m else None

def accepted_utc(accepted_et):
    if not accepted_et:
        return None
    dt = datetime.strptime(accepted_et, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("America/New_York"))
    return dt.astimezone(timezone.utc).isoformat()

def normalize_index_date(value):
    value = str(value or "").strip()
    if re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    return value or None

def parse_target_index(raw, target_accessions):
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    raw = raw.replace(
        "CIK|Company Name|Form Type|Date Filed|File Name",
        "CIK|Company Name|Form Type|Date Filed|Filename",
    )
    lines = raw.lstrip("\ufeff").splitlines()
    header = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("cik|company name|form type|date filed|filename"):
            header = i
            break
    if header is None:
        raise ValueError("SEC index header not found (daily/quarterly)")
    target_accessions = {norm_acc(x) for x in target_accessions}
    found = {}
    for line in lines[header + 1:]:
        if not line.strip() or line.startswith("---"):
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        master_cik, company, raw_form, filed, filename = [x.strip() for x in parts]
        m = re.search(r"(\d{10}-\d{2}-\d{6})\.txt$", filename, re.I)
        if not m:
            continue
        acc = norm_acc(m.group(1))
        if acc not in target_accessions:
            continue
        path_match = re.search(r"/data/(\d+)/", "/" + filename.lstrip("/"), re.I)
        item = {
            "accession": acc,
            "form": raw_form,
            "filing_date": normalize_index_date(filed),
            "master_index_ciks": [p401.norm_cik(master_cik)],
            "master_index_cik": p401.norm_cik(master_cik),
            "company_name": company,
            "archive_path_cik": p401.norm_cik(path_match.group(1)) if path_match else None,
            "filename": filename,
        }
        found[acc] = item
    return found

def load_target_indexes(target_accessions):
    by_accession, quarter_counts = {}, []
    for token in QUARTERS:
        year, qtr = p401.quarter(token)
        url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"
        raw = p401.fetch_bytes(url, sec=True, timeout=90, retries=5)
        found = parse_target_index(raw, target_accessions)
        for acc, row in found.items():
            row["index_quarter"] = token
        by_accession.update(found)
        quarter_counts.append({"quarter": token, "target_accession_hits": len(found),
                               "accessions_found": ";".join(sorted(found)),
                               "forms_found": ";".join(sorted({x["form"] for x in found.values()}))})
    return by_accession, quarter_counts

def parse_daily_master_index(raw, target_accessions):
    return parse_target_index(raw, target_accessions)
def load_target_daily_indexes(target_accessions):
    target_accessions = {norm_acc(x) for x in target_accessions}
    by_accession, daily_counts = {}, []
    for day in DAILY_DATES:
        dt = datetime.strptime(day, "%Y-%m-%d")
        qtr = (dt.month - 1) // 3 + 1
        compact = dt.strftime("%Y%m%d")
        url = f"https://www.sec.gov/Archives/edgar/daily-index/{dt.year}/QTR{qtr}/master.{compact}.idx"
        rows = parse_daily_master_index(p401.fetch_bytes(url, sec=True, timeout=60, retries=4), target_accessions)
        hits = []
        for acc, row in rows.items():
            item = dict(row)
            item["index_date"] = day
            item["index_type"] = "daily_master"
            by_accession[acc] = item
            hits.append(acc)
        daily_counts.append({"date": day, "daily_index_rows": len(rows),
                             "target_parent_hits": len(hits), "accessions_found": ";".join(sorted(hits))})
    return by_accession, daily_counts

def extract_edgar_xml_blocks(raw):
    if isinstance(raw, bytes):
        text = raw.decode("latin-1", "replace")
    else:
        text = str(raw)
    blocks = re.findall(r"<XML>\s*(.*?)\s*</XML>", text, flags=re.I | re.S)
    out = [block.encode("utf-8", "replace") for block in blocks if re.search(r"edgarSubmission", block, re.I)]
    if not out and re.search(r"edgarSubmission", text, re.I):
        out = [text.encode("utf-8", "replace")]
    return out

def fetch_xml(accession, index_row=None, direct_url=None, seed_ciks=()):
    accession = norm_acc(accession)
    candidates = unique_ciks(
        [path_cik_from_url(direct_url)] if direct_url else [],
        (index_row or {}).get("master_index_ciks", []),
        [(index_row or {}).get("archive_path_cik")],
        seed_ciks,
        [accession[:10] if accession else None],
    )
    acc_path = accession.replace("-", "")
    xml_urls = []
    if direct_url:
        xml_urls.append(direct_url)
    xml_urls.extend(f"{p401.SEC_ARCHIVES}/{int(cik)}/{acc_path}/primary_doc.xml" for cik in candidates)
    errors = []
    for url in dict.fromkeys(xml_urls):
        try:
            raw = p401.fetch_bytes(url, sec=True, timeout=45, retries=4)
            parsed = p401.parse_form144_xml(raw)
            root = ET.fromstring(raw)
            return {
                "ok": True, "parsed": parsed,
                "tranches": p401.tranche_sig(p401.extract_sale_tranches(root)),
                "url": url, "path_cik": path_cik_from_url(url),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "source": "primary_doc.xml", "errors_before_success": errors,
            }
        except HTTPError as exc:
            errors.append(f"{url}:HTTP{exc.code}")
        except Exception as exc:
            errors.append(f"{url}:{type(exc).__name__}:{str(exc)[:120]}")

    submission_urls = []
    filename = (index_row or {}).get("filename")
    if filename:
        submission_urls.append("https://www.sec.gov/Archives/" + filename.lstrip("/"))
    submission_urls.extend(
        f"{p401.SEC_ARCHIVES}/{int(cik)}/{acc_path}/{accession}.txt" for cik in candidates
    )
    for txt_url in dict.fromkeys(submission_urls):
        try:
            raw = p401.fetch_bytes(txt_url, sec=True, timeout=45, retries=3)
            blocks = extract_edgar_xml_blocks(raw)
            for block in blocks:
                try:
                    parsed = p401.parse_form144_xml(block)
                    root = ET.fromstring(block)
                    return {
                        "ok": True, "parsed": parsed,
                        "tranches": p401.tranche_sig(p401.extract_sale_tranches(root)),
                        "url": txt_url, "path_cik": path_cik_from_url(txt_url),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "source": "complete_submission_text_xml_block", "errors_before_success": errors,
                    }
                except Exception as exc:
                    errors.append(f"{txt_url}:XML_BLOCK:{type(exc).__name__}:{str(exc)[:100]}")
        except Exception as exc:
            errors.append(f"{txt_url}:{type(exc).__name__}:{str(exc)[:100]}")
    return {"ok": False, "url": None, "path_cik": None, "errors": errors}

def fetch_filing_detail(accession, doc, index_row=None):
    accession = norm_acc(accession)
    candidates = unique_ciks(
        [doc.get("path_cik")],
        (index_row or {}).get("master_index_ciks", []),
        [(index_row or {}).get("archive_path_cik")],
        [accession[:10] if accession else None],
    )
    acc_path = accession.replace("-", "")
    errors = []
    for cik in candidates:
        base = f"{p401.SEC_ARCHIVES}/{int(cik)}/{acc_path}"
        for page_name in (f"{accession}-index.htm", f"{accession}-index.html", f"{accession}-index-headers.html"):
            index_url = f"{base}/{page_name}"
            try:
                raw = p401.fetch_bytes(index_url, sec=True, timeout=35, retries=2)
                accepted = parse_acceptance_html(raw)
                filing_date = parse_filing_date_html(raw)
                if accepted:
                    return {"accepted_et": accepted, "accepted_utc": accepted_utc(accepted),
                            "filing_date": filing_date, "source": "SEC_filing_detail_index",
                            "url": index_url, "errors": errors}
                errors.append(f"{index_url}:accepted_not_found")
            except Exception as exc:
                errors.append(f"{index_url}:{type(exc).__name__}:{str(exc)[:100]}")
        txt_url = f"{base}/{accession}.txt"
        try:
            raw = p401.fetch_bytes(txt_url, sec=True, timeout=35, retries=2)
            accepted = parse_acceptance_submission(raw)
            if accepted:
                return {"accepted_et": accepted, "accepted_utc": accepted_utc(accepted),
                        "filing_date": (index_row or {}).get("filing_date"),
                        "source": "SEC_complete_submission_header",
                        "url": txt_url, "errors": errors}
            errors.append(f"{txt_url}:acceptance_not_found")
        except Exception as exc:
            errors.append(f"{txt_url}:{type(exc).__name__}:{str(exc)[:100]}")
    filename = (index_row or {}).get("filename")
    if filename:
        txt_url = "https://www.sec.gov/Archives/" + filename.lstrip("/")
        try:
            raw = p401.fetch_bytes(txt_url, sec=True, timeout=35, retries=2)
            accepted = parse_acceptance_submission(raw)
            if accepted:
                return {"accepted_et": accepted, "accepted_utc": accepted_utc(accepted),
                        "filing_date": (index_row or {}).get("filing_date"),
                        "source": "SEC_daily_index_complete_submission_header",
                        "url": txt_url, "errors": errors}
            errors.append(f"{txt_url}:acceptance_not_found")
        except Exception as exc:
            errors.append(f"{txt_url}:{type(exc).__name__}:{str(exc)[:100]}")
    return {"accepted_et": None, "accepted_utc": None,
            "filing_date": (index_row or {}).get("filing_date"),
            "source": None, "url": None, "errors": errors}


def parse_api_acceptance(value):
    if not value:
        return {"accepted_utc": None, "accepted_et": None}
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    et_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
    return {"accepted_utc": utc_dt.isoformat(),
            "accepted_et": et_dt.strftime("%Y-%m-%d %H:%M:%S")}

def find_submission_in_payload(payload, accession, cik):
    accession = norm_acc(accession)
    recent = (payload.get("filings") or {}).get("recent") or {}
    accessions = recent.get("accessionNumber") or []
    for i, value in enumerate(accessions):
        if norm_acc(value) != accession:
            continue
        def at(key):
            values = recent.get(key) or []
            return values[i] if i < len(values) else None
        accepted = parse_api_acceptance(at("acceptanceDateTime"))
        return {
            "found": True, "cik": p401.norm_cik(cik), "form": at("form"),
            "filing_date": normalize_index_date(at("filingDate")),
            "accepted_et": accepted["accepted_et"], "accepted_utc": accepted["accepted_utc"],
            "primary_document": at("primaryDocument"),
            "primary_document_description": at("primaryDocDescription"),
            "source": "SEC_submissions_API",
        }
    return {"found": False, "cik": p401.norm_cik(cik), "source": None}

def fetch_submission_api_metadata(accession, candidate_ciks):
    accession = norm_acc(accession)
    errors = []
    target_year = "20" + accession.split("-")[1]
    for cik in unique_ciks(candidate_ciks):
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            payload = json.loads(p401.fetch_bytes(url, sec=True, timeout=40, retries=2).decode("utf-8", "replace"))
            hit = find_submission_in_payload(payload, accession, cik)
            if hit.get("found"):
                hit["url"] = url
                hit["errors"] = errors
                return hit
            files = (payload.get("filings") or {}).get("files") or []
            for item in files:
                filing_from = str(item.get("filingFrom") or "")
                filing_to = str(item.get("filingTo") or "")
                if target_year not in filing_from and target_year not in filing_to:
                    continue
                name = item.get("name")
                if not name:
                    continue
                older_url = "https://data.sec.gov/submissions/" + name
                try:
                    older = json.loads(p401.fetch_bytes(older_url, sec=True, timeout=40, retries=2).decode("utf-8", "replace"))
                    hit = find_submission_in_payload(older, accession, cik)
                    if hit.get("found"):
                        hit["url"] = older_url
                        hit["errors"] = errors
                        return hit
                except Exception as exc:
                    errors.append(f"{older_url}:{type(exc).__name__}:{str(exc)[:100]}")
        except Exception as exc:
            errors.append(f"{url}:{type(exc).__name__}:{str(exc)[:100]}")
    return {"found": False, "cik": None, "source": None, "errors": errors}

def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def write_csv(path, rows):
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def build_pairs(manifest):
    if manifest.get("source_run_id") != PHASE401_RUN_ID:
        raise ValueError("Phase 401 source run mismatch")
    if manifest.get("source_artifact_id") != PHASE401_ARTIFACT_ID:
        raise ValueError("Phase 401 source artifact mismatch")
    if manifest.get("source_artifact_sha256") != PHASE401_ARTIFACT_SHA256:
        raise ValueError("Phase 401 source artifact digest mismatch")
    pairs = manifest.get("pairs") or []
    boundary = [x for x in pairs if x.get("pair_type") == "candidate_boundary"]
    unresolved = [x for x in pairs if x.get("pair_type") == "phase401_unresolved"]
    if len(boundary) != EXPECTED_BOUNDARY_PAIRS or len(unresolved) != EXPECTED_UNRESOLVED_PAIRS:
        raise ValueError(f"Expected 4 boundary and 4 unresolved pairs; got {len(boundary)} and {len(unresolved)}")
    return pairs

def audit(manifest_path, output_dir):
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    phase401_summary = manifest.get("phase401_summary", {})
    if phase401_summary.get("phase") != 401 or phase401_summary.get("all_market_144a_children") != 1446:
        raise ValueError("Phase 401 frozen manifest does not match the full-census result")
    if phase401_summary.get("resolved_parent_links") != 1442 or phase401_summary.get("unresolved_parent_links") != 4:
        raise ValueError("Phase 401 parent-link counts do not match the frozen result")
    pairs = build_pairs(manifest)
    target_accessions = {x["parent_accession"] for x in pairs} | {x["child_accession"] for x in pairs}
    index, quarter_counts = load_target_indexes(target_accessions)
    daily_index, daily_counts = load_target_daily_indexes(target_accessions)
    documents, pair_rows = [], []

    for pair in pairs:
        child_acc, parent_acc = pair["child_accession"], pair["parent_accession"]
        child_row = index.get(child_acc) or daily_index.get(child_acc)
        parent_quarter_row = index.get(parent_acc)
        parent_daily_row = daily_index.get(parent_acc)
        parent_row = parent_quarter_row or parent_daily_row
        child_seed = [pair.get("child_issuer_cik_expected")]
        child_doc = fetch_xml(child_acc, child_row, pair.get("child_xml_url"), child_seed)
        if child_doc.get("ok"):
            child_seed = unique_ciks(child_seed, [
                child_doc["parsed"].get("issuer_cik"),
                child_doc["parsed"].get("filer_cik"),
                path_cik_from_url(child_doc.get("url")),
            ])
        parent_seed = unique_ciks(
            child_seed,
            [(parent_row or {}).get("archive_path_cik")],
            (parent_row or {}).get("master_index_ciks", []),
            [parent_acc[:10]],
            [pair.get("parent_issuer_cik_expected")],
        )
        parent_doc = fetch_xml(parent_acc, parent_row, pair.get("parent_xml_url"), parent_seed)

        child_detail = fetch_filing_detail(child_acc, child_doc if child_doc.get("ok") else {"path_cik": (child_row or {}).get("archive_path_cik")}, child_row) if child_doc.get("ok") or child_row else {}
        parent_detail = fetch_filing_detail(parent_acc, parent_doc if parent_doc.get("ok") else {"path_cik": (parent_row or {}).get("archive_path_cik")}, parent_row) if parent_doc.get("ok") or parent_row else {}
        child_meta = {}
        parent_meta = {}
        if not child_detail.get("accepted_utc"):
            child_meta = fetch_submission_api_metadata(child_acc, unique_ciks(
                (child_row or {}).get("master_index_ciks", []),
                [(child_row or {}).get("archive_path_cik")],
                [child_parsed.get("issuer_cik") if child_doc.get("ok") else None],
                [child_parsed.get("filer_cik") if child_doc.get("ok") else None],
                [child_acc[:10]],
            ))
            if child_meta.get("found"):
                child_detail = {**child_detail, **child_meta}
        if not parent_detail.get("accepted_utc"):
            parent_meta = fetch_submission_api_metadata(parent_acc, unique_ciks(
                (parent_row or {}).get("master_index_ciks", []),
                [(parent_row or {}).get("archive_path_cik")],
                [child_parsed.get("issuer_cik") if child_doc.get("ok") else None],
                [child_parsed.get("filer_cik") if child_doc.get("ok") else None],
                [parent_acc[:10]],
            ))
            if parent_meta.get("found"):
                parent_detail = {**parent_detail, **parent_meta}

        for role, acc, row, doc, detail in (
            ("child", child_acc, child_row, child_doc, child_detail),
            ("parent", parent_acc, parent_row, parent_doc, parent_detail),
        ):
            parsed = doc.get("parsed", {})
            filing_date = (row or {}).get("filing_date") or detail.get("filing_date") or (
                pair.get(role + "_filing_date_expected") if role == "child" else None
            )
            documents.append({
                "pair_id": pair["pair_id"], "pair_type": pair["pair_type"], "role": role,
                "accession": acc, "master_index_found": bool((row or {}).get("index_quarter")),
                "daily_index_found": bool((row or {}).get("index_date")),
                "index_quarter": (row or {}).get("index_quarter"),
                "daily_index_date": (row or {}).get("index_date"),
                "filing_date": filing_date,
                "form": parsed.get("submission_type") or (row or {}).get("form") or detail.get("form"),
                "issuer_cik": parsed.get("issuer_cik"),
                "issuer_name": parsed.get("issuer_name"),
                "filer_cik": parsed.get("filer_cik"),
                "seller": parsed.get("seller_name"),
                "previous_accession": norm_acc(parsed.get("previous_accession")),
                "remarks": " | ".join(parsed.get("remarks") or []),
                "accepted_et": detail.get("accepted_et"),
                "accepted_utc": detail.get("accepted_utc"),
                "acceptance_source": detail.get("source"),
                "submission_api_found": bool(detail.get("source") == "SEC_submissions_API"),
                "submission_api_cik": detail.get("cik") if detail.get("source") == "SEC_submissions_API" else None,
                "submission_api_primary_document": detail.get("primary_document"),
                "archive_path_cik": doc.get("path_cik") or (row or {}).get("archive_path_cik"),
                "daily_index_filename": (row or {}).get("filename"),
                "daily_index_company_name": (row or {}).get("company_name"),
                "xml_url": doc.get("url"),
                "xml_source": doc.get("source"),
                "xml_sha256": doc.get("sha256"),
                "xml_status": "retrieved" if doc.get("ok") else "unresolved",
                "index_detail_url": detail.get("url"),
                "detail_errors": " || ".join(detail.get("errors") or []),
                "xml_errors": " || ".join(doc.get("errors") or []),
            })

        child_parsed = child_doc.get("parsed", {}) if child_doc.get("ok") else {}
        parent_parsed = parent_doc.get("parsed", {}) if parent_doc.get("ok") else {}
        child_date = (child_row or {}).get("filing_date") or child_detail.get("filing_date") or pair.get("child_filing_date_expected")
        parent_date = (parent_row or {}).get("filing_date") or parent_detail.get("filing_date") or pair.get("parent_filing_date_expected")
        c_accept = child_detail.get("accepted_utc")
        p_accept = parent_detail.get("accepted_utc")
        accepted_lag = None
        if c_accept and p_accept:
            accepted_lag = (datetime.fromisoformat(c_accept) - datetime.fromisoformat(p_accept)).total_seconds()
        previous_matches = bool(child_doc.get("ok") and norm_acc(child_parsed.get("previous_accession")) == parent_acc)
        pair_rows.append({
            **pair,
            "child_xml_status": "retrieved" if child_doc.get("ok") else "unresolved",
            "parent_xml_status": "retrieved" if parent_doc.get("ok") else "unresolved",
            "child_form": child_parsed.get("submission_type") or (child_row or {}).get("form") or child_detail.get("form"),
            "parent_form": parent_parsed.get("submission_type") or (parent_row or {}).get("form") or parent_detail.get("form"),
            "child_issuer_cik": child_parsed.get("issuer_cik"),
            "parent_issuer_cik": parent_parsed.get("issuer_cik"),
            "child_issuer_name": child_parsed.get("issuer_name"),
            "parent_issuer_name": parent_parsed.get("issuer_name"),
            "child_filer_cik": child_parsed.get("filer_cik"),
            "parent_filer_cik": parent_parsed.get("filer_cik"),
            "child_seller": child_parsed.get("seller_name"),
            "parent_seller": parent_parsed.get("seller_name"),
            "child_filing_date": child_date,
            "parent_filing_date": parent_date,
            "parent_in_phase67_window": None if not parent_date else parent_date >= PHASE67_START,
            "parent_index_found": bool(parent_quarter_row),
            "parent_daily_index_found": bool(parent_daily_row),
            "parent_daily_index_date": (parent_daily_row or {}).get("index_date"),
            "parent_daily_index_filename": (parent_daily_row or {}).get("filename"),
            "parent_daily_index_company_name": (parent_daily_row or {}).get("company_name"),
            "parent_daily_index_cik": (parent_daily_row or {}).get("master_index_cik"),
            "child_previous_accession_matches": previous_matches,
            "filing_date_order_ok": None if not child_date or not parent_date else parent_date <= child_date,
            "child_accepted_et": child_detail.get("accepted_et"),
            "parent_accepted_et": parent_detail.get("accepted_et"),
            "child_accepted_utc": c_accept,
            "parent_accepted_utc": p_accept,
            "accepted_order_ok": None if accepted_lag is None else accepted_lag >= 0,
            "accepted_lag_seconds": accepted_lag,
            "first_public_receipt_certified": False,
        })

    docs_ok = sum(x["xml_status"] == "retrieved" for x in documents)
    accepted_docs = sum(bool(x.get("accepted_utc")) for x in documents)
    resolved_parents = sum(x["parent_xml_status"] == "retrieved" for x in pair_rows)
    summary = {
        "phase": 402,
        "audit_date_utc": datetime.now(timezone.utc).isoformat(),
        "source": "SEC quarterly master.idx, EDGAR filing-detail index pages / complete submission headers, and Phase 401 immutable artifact",
        "phase401_source": {
            "run_id": PHASE401_RUN_ID,
            "artifact_id": PHASE401_ARTIFACT_ID,
            "artifact_sha256": PHASE401_ARTIFACT_SHA256,
            "all_market_144a_children": 1446,
            "resolved_parent_links": 1442,
            "unresolved_parent_links": 4,
        },
        "scope": {"candidate_boundary_pairs": EXPECTED_BOUNDARY_PAIRS,
                  "phase401_unresolved_pairs": EXPECTED_UNRESOLVED_PAIRS,
                  "pairs_audited": len(pair_rows), "documents_expected": len(pair_rows) * 2},
        "quarter_index_search": quarter_counts,
        "daily_index_search": daily_counts,
        "daily_index_parent_hits": sum(bool(x.get("parent_daily_index_found")) for x in pair_rows),
        "daily_index_parent_rows": [
            {"accession": acc, "index_date": row.get("index_date"), "filing_date": row.get("filing_date"),
             "form": row.get("form"), "company_name": row.get("company_name"),
             "master_index_cik": row.get("master_index_cik"), "archive_path_cik": row.get("archive_path_cik"),
             "filename": row.get("filename")}
            for acc, row in daily_index.items()
        ],
        "retrieval": {"documents_retrieved": docs_ok, "documents_expected": len(documents),
                      "parent_documents_retrieved": resolved_parents,
                      "parent_documents_expected": len(pair_rows),
                      "acceptance_timestamps_found": accepted_docs,
                      "acceptance_timestamps_expected": len(documents)},
        "quality_gates": {
            "four_candidate_boundary_pairs_audited": sum(x["pair_type"] == "candidate_boundary" for x in pair_rows) == 4,
            "four_phase401_unresolved_pairs_audited": sum(x["pair_type"] == "phase401_unresolved" for x in pair_rows) == 4,
            "all_child_documents_retrieved": all(x["child_xml_status"] == "retrieved" for x in pair_rows),
            "all_parent_documents_retrieved": all(x["parent_xml_status"] == "retrieved" for x in pair_rows),
            "all_parent_accessions_indexed_as_144_or_144a": all(
                (x.get("parent_form") or "").upper() in ("144", "144/A") for x in pair_rows
            ),
            "all_child_previous_accessions_match": all(x["child_previous_accession_matches"] for x in pair_rows),
            "no_parent_child_filing_date_inversions": not any(x["filing_date_order_ok"] is False for x in pair_rows),
            "no_parent_child_acceptance_order_inversions": not any(x["accepted_order_ok"] is False for x in pair_rows),
            "acceptance_time_coverage_ge_90pct": accepted_docs / len(documents) >= 0.90 if documents else False,
            "submission_api_used_only_for_missing_acceptance_times": True,
            "first_public_receipt_certified": False,
            "historical_f80_identity_gate": False,
            "economic_test_authorized": False,
        },
        "decision": {
            "acceptance_datetime_is_not_first_public_receipt": True,
            "same_day_intraday_use_authorized": False,
            "preserve_original_and_amendment_as_distinct_versions": True,
            "corrected_identity_may_be_backdated": False,
            "no_forward_returns_or_alpha_tests": True,
            "f80_changed": False,
        },
        "unresolved_parent_accessions_after_targeted_recovery": [
            x["parent_accession"] for x in pair_rows if x["parent_xml_status"] != "retrieved"
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "pair_audit.csv", pair_rows)
    write_csv(output_dir / "documents.csv", documents)
    write_csv(output_dir / "quarter_index_search.csv", quarter_counts)
    write_csv(output_dir / "daily_index_search.csv", daily_counts)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("phase402_form144_parent_acceptance_audit"))
    args = parser.parse_args()
    summary = audit(args.manifest, args.output_dir)
    if summary["scope"]["pairs_audited"] != 8:
        raise SystemExit("Phase 402 did not audit the frozen eight-pair scope")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Conservative SEC Form 144 feasibility pilot v2.

Searches the frozen candidate CIK set, but treats EFTS CIK matches as
candidate links only: the XML issuerCik is the authority for the subject issuer.
No forward returns or alpha tests are performed.
"""
import ast
import csv
import hashlib
import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
OUT_DIR = Path("phase50_form144_pilot_v2")
START_DATE = "2023-04-13"
END_DATE = os.environ.get("FORM144_END_DATE", "2026-11-03")
SAMPLE_SIZE = int(os.environ.get("FORM144_SAMPLE_SIZE", "50"))
MIN_MAPPED = 300
MIN_QUERY_ERROR_RATE = 0.0
MIN_SAMPLE_XML_RATE = 0.95
MIN_SUBJECT_MATCH_RATE = 0.95
MIN_ACCEPTED_TIMESTAMP_RATE = 0.95
REQUIRED_FIELDS = (
    "issuer_cik", "issuer_name", "seller_name", "security_class",
    "units_to_be_sold", "aggregate_market_value", "approx_sale_date",
    "notice_date",
)
HEADERS = {
    "User-Agent": "NuevaEstrategia quantitative research contact: research@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json,text/html,application/xml,*/*",
}

def norm_cik(value):
    if value in (None, ""):
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits.zfill(10) if digits else None

def cik_path(value):
    cik = norm_cik(value)
    return str(int(cik)) if cik else None

def normalize_accession(value):
    value = str(value or "").strip()
    match = re.search(r"(\d{10})-?(\d{2})-?(\d{6})", value)
    return "-".join(match.groups()) if match else None

def accession_nodash(value):
    normalized = normalize_accession(value)
    return normalized.replace("-", "") if normalized else None

def frozen_universe():
    tree = ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    names = sorted({str(x).strip().upper() for x in ast.literal_eval(node.value)})
                    if len(names) != 335:
                        raise RuntimeError(f"Expected 335 frozen names, got {len(names)}")
                    return names
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def sec_ticker_map():
    payload = get_json(SEC_TICKERS_URL)
    return {
        str(row.get("ticker", "")).strip().upper(): norm_cik(row.get("cik_str"))
        for row in payload.values() if row.get("ticker")
    }

def get_bytes(url, retries=6, timeout=45):
    last_error = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=timeout) as response:
                return response.read()
        except HTTPError as error:
            last_error = error
            if error.code in (429, 500, 502, 503, 504):
                time.sleep(min(30, 2 ** attempt))
                continue
            raise
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(min(20, 2 ** attempt))
    raise RuntimeError(f"GET failed after retries: {url}: {last_error}")

def get_json(url):
    return json.loads(get_bytes(url).decode("utf-8"))

def hit_source(hit):
    return (hit or {}).get("_source") or (hit or {}).get("source") or {}

def hit_accession(hit):
    source = hit_source(hit)
    for key in ("accession_no", "accession_number", "adsh", "accessionNo"):
        if source.get(key):
            value = normalize_accession(source[key])
            if value:
                return value
    for key in ("_id", "id"):
        value = normalize_accession(str((hit or {}).get(key, "")).split(":")[0])
        if value:
            return value
    return None

def hit_ciks(hit):
    value = hit_source(hit).get("ciks")
    if isinstance(value, str):
        value = re.split(r"[,; ]+", value)
    if not isinstance(value, list):
        return []
    output = []
    for item in value:
        cik = norm_cik(item)
        if cik and cik not in output:
            output.append(cik)
    return output

def hit_form(hit):
    source = hit_source(hit)
    value = source.get("form") or source.get("form_type") or source.get("root_forms") or ""
    if isinstance(value, list):
        value = value[0] if value else ""
    value = str(value).upper().strip()
    if "144/A" in value:
        return "144/A"
    if value == "144" or value.startswith("144 "):
        return "144"
    return value

def query_url(cik, start_date=START_DATE, end_date=END_DATE, offset=0):
    params = {
        "forms": "144,144/A",
        "ciks": norm_cik(cik),
        "startdt": start_date,
        "enddt": end_date,
        "from": str(offset),
    }
    return EFTS_URL + "?" + urlencode(params)

def parse_total(payload):
    total = (payload.get("hits") or {}).get("total", 0)
    if isinstance(total, dict):
        return int(total.get("value", 0) or 0), total.get("relation", "eq")
    return int(total or 0), "eq"

def search_issuer(cik):
    """Return all accessible 144/144-A hits for a candidate CIK.

    EFTS CIK matching is not treated as proof that the candidate is the subject.
    The primary XML issuerCik must verify the role.
    """
    hits = []
    first = get_json(query_url(cik, offset=0))
    total, relation = parse_total(first)
    hits.extend((first.get("hits") or {}).get("hits") or [])
    cap = 10000 if relation == "gte" or total >= 10000 else total
    offset = 100
    while offset < cap:
        payload = get_json(query_url(cik, offset=offset))
        page_hits = (payload.get("hits") or {}).get("hits") or []
        if not page_hits:
            break
        hits.extend(page_hits)
        offset += 100
        time.sleep(0.12)
    return hits, {"reported_total": total, "relation": relation, "retrieved_hits": len(hits),
                  "possibly_capped": relation == "gte" or total >= 10000}

def local_name(tag):
    return str(tag).split("}", 1)[-1].split(":", 1)[-1]

def descendants(root, name):
    wanted = name.lower()
    return [element for element in root.iter() if local_name(element.tag).lower() == wanted]

def first_text(root, name):
    for element in descendants(root, name):
        if element.text and element.text.strip():
            return element.text.strip()
    return None

def all_text(root, name):
    return [element.text.strip() for element in descendants(root, name)
            if element.text and element.text.strip()]

def parse_form144_xml(xml_text):
    root = ET.fromstring(xml_text)
    if local_name(root.tag).lower() != "edgarsubmission":
        raise ValueError(f"Unexpected XML root: {local_name(root.tag)}")
    submission_type = first_text(root, "submissionType")
    if submission_type not in ("144", "144/A"):
        raise ValueError(f"Unexpected submissionType: {submission_type}")
    tranches = []
    for node in descendants(root, "securitiesToBeSold"):
        tranches.append({
            "class_title": first_text(node, "securitiesClassTitle"),
            "acquired_date": first_text(node, "acquiredDate"),
            "acquisition_nature": first_text(node, "natureOfAcquisitionTransaction"),
            "amount_acquired": first_text(node, "amountOfSecuritiesAcquired"),
            "payment_date": first_text(node, "paymentDate"),
            "payment_nature": first_text(node, "natureOfPayment"),
            "is_gift": first_text(node, "isGiftTransaction"),
        })
    relationships = all_text(root, "relationshipToIssuer")
    issuer_cik = norm_cik(first_text(root, "issuerCik"))
    filer_cik = norm_cik(first_text(root, "cik"))
    result = {
        "submission_type": submission_type,
        "previous_accession": normalize_accession(first_text(root, "previousAccessionNumber")),
        "filer_cik": filer_cik,
        "issuer_cik": issuer_cik,
        "issuer_name": first_text(root, "issuerName"),
        "seller_name": first_text(root, "nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold"),
        "relationships": relationships,
        "security_class": all_text(root, "securitiesClassTitle"),
        "units_to_be_sold": first_text(root, "noOfUnitsSold"),
        "aggregate_market_value": first_text(root, "aggregateMarketValue"),
        "units_outstanding": first_text(root, "noOfUnitsOutstanding"),
        "approx_sale_date": first_text(root, "approxSaleDate"),
        "exchange": first_text(root, "securitiesExchangeName"),
        "notice_date": first_text(root, "noticeDate"),
        "prior_sales_flag": first_text(root, "nothingToReportFlagOnSecuritiesSoldInPast3Months"),
        "prior_sales": [
            {
                "sale_date": first_text(node, "saleDate"),
                "units_sold": first_text(node, "amountOfSecuritiesSold"),
                "gross_proceeds": first_text(node, "grossProceeds"),
            }
            for node in descendants(root, "securitiesSoldInPast3Months")
        ],
        "tranches": tranches,
    }
    result["field_presence"] = {
        "issuer_cik": bool(result["issuer_cik"]),
        "issuer_name": bool(result["issuer_name"]),
        "seller_name": bool(result["seller_name"]),
        "relationships": bool(relationships),
        "security_class": bool(result["security_class"]),
        "units_to_be_sold": bool(result["units_to_be_sold"]),
        "aggregate_market_value": bool(result["aggregate_market_value"]),
        "approx_sale_date": bool(result["approx_sale_date"]),
        "notice_date": bool(result["notice_date"]),
        "acquisition_tranche": bool(tranches),
        "previous_accession": bool(result["previous_accession"]),
    }
    return result

def archive_path_candidates(hit):
    """Try SEC CIKs in EFTS metadata before the accession prefix.

    The accession prefix is retained as a fallback only; it is not assumed to
    be the archive-directory CIK or the seller/issuer CIK.
    """
    candidates = []
    for cik in hit_ciks(hit):
        path_cik = cik_path(cik)
        if path_cik and path_cik not in candidates:
            candidates.append(path_cik)
    accession = hit_accession(hit)
    if accession:
        prefix = cik_path(accession[:10])
        if prefix and prefix not in candidates:
            candidates.append(prefix)
    return candidates

def xml_links(index_html):
    links = re.findall(r"""href\s*=\s*["']([^"']+\.xml(?:\?[^"']*)?)["']""",
                       index_html, flags=re.I)
    cleaned = []
    for link in links:
        link = html.unescape(link).split("?", 1)[0]
        if link not in cleaned:
            cleaned.append(link)
    cleaned.sort(key=lambda value: ("/xsl" in value.lower(), "primary_doc.xml" not in value.lower(), value))
    return cleaned

def parse_accepted_timestamp(index_html):
    patterns = (
        r"Accepted\s*</[^>]+>\s*<[^>]*>\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"Accepted.{0,250}?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, index_html, flags=re.I | re.S)
        if match:
            return match.group(1)
    return None

def download_form144(hit):
    accession = hit_accession(hit)
    nodash = accession_nodash(accession)
    if not accession or not nodash:
        return {"ok": False, "reason": "missing_accession"}
    errors = []
    for path_cik in archive_path_candidates(hit):
        base = f"{SEC_ARCHIVES}/{path_cik}/{nodash}"
        index_html = None
        index_url = None
        for suffix in (f"{accession}-index.htm", f"{accession}-index.html"):
            candidate = f"{base}/{suffix}"
            try:
                index_html = get_bytes(candidate).decode("utf-8", "replace")
                index_url = candidate
                break
            except Exception as error:
                errors.append({"url": candidate, "error": str(error)})
        candidate_urls = [f"{base}/primary_doc.xml"]
        if index_html:
            candidate_urls.extend(
                link if link.startswith("http") else f"{base}/{link.lstrip('./')}"
                for link in xml_links(index_html)
            )
        for xml_url in dict.fromkeys(candidate_urls):
            try:
                xml_text = get_bytes(xml_url).decode("utf-8", "replace")
                parsed = parse_form144_xml(xml_text)
                return {
                    "ok": True, "archive_path_cik": path_cik, "index_url": index_url,
                    "xml_url": xml_url, "accepted_at": parse_accepted_timestamp(index_html or ""),
                    "parsed": parsed, "accession": accession,
                }
            except Exception as error:
                errors.append({"url": xml_url, "error": str(error)})
    return {"ok": False, "reason": "archive_or_xml_resolution_failed",
            "accession": accession, "errors": errors[-12:]}

def classify_sale_date(approx_sale_date, filing_date):
    try:
        sale = date.fromisoformat(str(approx_sale_date)[:10])
        filed = date.fromisoformat(str(filing_date)[:10])
    except (TypeError, ValueError):
        return "unknown"
    return "sale_date_precedes_filing" if sale < filed else "not_before_filing"

def deterministic_sample(hits_by_accession, sample_size=SAMPLE_SIZE):
    pool = list(hits_by_accession.values())
    pool.sort(key=lambda hit: hashlib.sha256((hit_accession(hit) or "").encode()).hexdigest())
    chosen, counts = [], defaultdict(int)
    # First ensure both original notices and amendments are represented where available.
    for form in ("144", "144/A"):
        for hit in pool:
            if hit_form(hit) != form:
                continue
            query_ciks = hit.get("_research_query_ciks", [])
            if not query_ciks or not any(counts[cik] < 2 for cik in query_ciks):
                continue
            chosen.append(hit)
            for cik in query_ciks:
                counts[cik] += 1
            if len(chosen) >= sample_size:
                return chosen
    for hit in pool:
        if hit in chosen:
            continue
        query_ciks = hit.get("_research_query_ciks", [])
        if not query_ciks or not any(counts[cik] < 2 for cik in query_ciks):
            continue
        chosen.append(hit)
        for cik in query_ciks:
            counts[cik] += 1
        if len(chosen) >= sample_size:
            break
    return chosen

def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = frozen_universe()
    ticker_map = sec_ticker_map()
    mapping = [{"ticker": ticker, "cik": ticker_map.get(ticker)} for ticker in universe]
    mapped = [row for row in mapping if row["cik"]]
    unmapped = [row["ticker"] for row in mapping if not row["cik"]]
    query_rows, query_errors = [], []
    hits_by_accession = {}

    for index, row in enumerate(mapped, start=1):
        try:
            hits, meta = search_issuer(row["cik"])
            query_rows.append({"ticker": row["ticker"], "cik": row["cik"], **meta})
            for hit in hits:
                accession = hit_accession(hit)
                if not accession:
                    continue
                existing = hits_by_accession.get(accession)
                if existing is None:
                    hit["_research_query_ciks"] = [row["cik"]]
                    hits_by_accession[accession] = hit
                elif row["cik"] not in existing["_research_query_ciks"]:
                    existing["_research_query_ciks"].append(row["cik"])
        except Exception as error:
            query_errors.append({"ticker": row["ticker"], "cik": row["cik"], "error": str(error)})
        time.sleep(0.35)

    candidate_hit_ciks = {row["cik"] for row in query_rows if row["retrieved_hits"] > 0}
    sample_hits = deterministic_sample(hits_by_accession)
    sample_rows = []
    for hit in sample_hits:
        download = download_form144(hit)
        source = hit_source(hit)
        query_ciks = hit.get("_research_query_ciks", [])
        if download.get("ok"):
            parsed = download["parsed"]
            filing_date = source.get("file_date") or source.get("filing_date")
            issuer_cik = parsed.get("issuer_cik")
            sample_rows.append({
                "accession": download["accession"],
                "form_efts": hit_form(hit),
                "form_xml": parsed.get("submission_type"),
                "file_date": filing_date,
                "accepted_at": download.get("accepted_at"),
                "accepted_timestamp_verified": bool(download.get("accepted_at")),
                "query_ciks": query_ciks,
                "source_ciks": hit_ciks(hit),
                "archive_path_cik": download.get("archive_path_cik"),
                "filer_cik_xml": parsed.get("filer_cik"),
                "subject_issuer_cik_xml": issuer_cik,
                "subject_issuer_name_xml": parsed.get("issuer_name"),
                "subject_matches_query_cik": issuer_cik in query_ciks if issuer_cik else False,
                "form_matches": hit_form(hit) == parsed.get("submission_type"),
                "seller_name": parsed.get("seller_name"),
                "relationships": parsed.get("relationships"),
                "security_class": parsed.get("security_class"),
                "units_to_be_sold": parsed.get("units_to_be_sold"),
                "aggregate_market_value": parsed.get("aggregate_market_value"),
                "approx_sale_date": parsed.get("approx_sale_date"),
                "sale_date_classification": classify_sale_date(parsed.get("approx_sale_date"), filing_date),
                "notice_date": parsed.get("notice_date"),
                "previous_accession": parsed.get("previous_accession"),
                "tranche_count": len(parsed.get("tranches", [])),
                "field_presence": parsed.get("field_presence"),
                "xml_url": download.get("xml_url"),
                "index_url": download.get("index_url"),
            })
        else:
            sample_rows.append({
                "accession": hit_accession(hit), "form_efts": hit_form(hit),
                "file_date": source.get("file_date"), "query_ciks": query_ciks,
                "source_ciks": hit_ciks(hit), "download_ok": False,
                "download_reason": download.get("reason"), "download_errors": download.get("errors"),
            })

    downloaded = [row for row in sample_rows if row.get("subject_issuer_cik_xml")]
    xml_rate = len(downloaded) / len(sample_rows) if sample_rows else 0.0
    subject_matches = [row for row in downloaded if row.get("subject_matches_query_cik") is not None]
    subject_rate = (sum(bool(row["subject_matches_query_cik"]) for row in subject_matches) /
                    len(subject_matches)) if subject_matches else 0.0
    accepted_rate = (sum(bool(row.get("accepted_timestamp_verified")) for row in downloaded) /
                     len(downloaded)) if downloaded else 0.0
    form_rate = (sum(bool(row.get("form_matches")) for row in downloaded) / len(downloaded)
                 if downloaded else 0.0)
    field_rates = {}
    for field in REQUIRED_FIELDS:
        vals = [(row.get("field_presence") or {}).get(field) for row in downloaded]
        field_rates[field] = sum(bool(value) for value in vals) / len(vals) if vals else 0.0

    query_error_rate = len(query_errors) / len(mapped) if mapped else 1.0
    candidate_hit_rate = len(candidate_hit_ciks) / len(mapped) if mapped else 0.0
    gate_checks = {
        "at_least_300_current_cik_mappings": len(mapped) >= MIN_MAPPED,
        "zero_efts_query_errors": query_error_rate <= MIN_QUERY_ERROR_RATE,
        "sample_xml_parse_rate_at_least_95pct": xml_rate >= MIN_SAMPLE_XML_RATE,
        "sample_subject_cik_match_at_least_95pct": subject_rate >= MIN_SUBJECT_MATCH_RATE,
        "accepted_timestamp_coverage_at_least_95pct": accepted_rate >= MIN_ACCEPTED_TIMESTAMP_RATE,
        "form_type_agreement_at_least_95pct": form_rate >= 0.95,
        "required_xml_fields_at_least_95pct": all(rate >= 0.95 for rate in field_rates.values()),
    }
    gate = "PASS" if all(gate_checks.values()) else "FAIL"
    summary = {
        "phase": "50-v2", "source": "SEC EDGAR Form 144 and 144/A",
        "status": "COMPLETE", "start_date": START_DATE, "end_date": END_DATE,
        "frozen_universe_size": len(universe), "current_sec_cik_mapped": len(mapped),
        "current_sec_cik_unmapped": unmapped, "efts_query_count": len(mapped),
        "efts_query_errors": len(query_errors), "efts_query_error_rate": query_error_rate,
        "candidate_cik_hit_count": len(candidate_hit_ciks), "candidate_cik_hit_rate": candidate_hit_rate,
        "unique_accessions_retrieved": len(hits_by_accession),
        "unique_144_count": sum(hit_form(hit) == "144" for hit in hits_by_accession.values()),
        "unique_144a_count": sum(hit_form(hit) == "144/A" for hit in hits_by_accession.values()),
        "sample_size_requested": SAMPLE_SIZE, "sample_size_resolved": len(downloaded),
        "sample_xml_parse_rate": xml_rate, "sample_subject_cik_match_rate": subject_rate,
        "sample_accepted_timestamp_rate": accepted_rate, "sample_form_agreement_rate": form_rate,
        "required_field_presence_rates": field_rates,
        "sample_sale_date_precedes_filing_count": sum(
            row.get("sale_date_classification") == "sale_date_precedes_filing" for row in downloaded),
        "sample_previous_accession_count": sum(bool(row.get("previous_accession")) for row in downloaded),
        "gate_checks": gate_checks, "data_gate": gate,
        "historical_pit_universe_gate": "NOT_TESTED",
        "economic_test_authorized": False,
        "knowledge_date_rule": "SEC accepted timestamp where parsed; otherwise filing date and next-session use. ApproxSaleDate is never KnowledgeDate.",
        "amendment_rule": "144/A previousAccessionNumber is preserved as a reference to the filing being amended; do not count 144/A as an independent economic event without lineage consolidation.",
        "interpretation": "EFTS CIK matches are candidate links only. XML issuerCik is the subject-issuer authority; XML filer CIK and archive-path CIK remain separate.",
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "sample_filings.json").write_text(json.dumps(sample_rows, indent=2), encoding="utf-8")
    (OUT_DIR / "issuer_query_results.json").write_text(json.dumps(query_rows, indent=2), encoding="utf-8")
    (OUT_DIR / "query_errors.json").write_text(json.dumps(query_errors, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "issuer_query_results.csv", query_rows,
              ["ticker", "cik", "reported_total", "relation", "retrieved_hits", "possibly_capped"])
    write_csv(OUT_DIR / "sample_filings.csv", sample_rows, [
        "accession", "form_efts", "form_xml", "file_date", "accepted_at",
        "query_ciks", "source_ciks", "archive_path_cik", "filer_cik_xml",
        "subject_issuer_cik_xml", "subject_issuer_name_xml", "subject_matches_query_cik",
        "form_matches", "seller_name", "relationships", "security_class",
        "units_to_be_sold", "aggregate_market_value", "approx_sale_date",
        "sale_date_classification", "notice_date", "previous_accession", "tranche_count",
        "xml_url", "index_url", "download_reason",
    ])
    print(json.dumps(summary, indent=2))
    # A completed research gate failure is not a workflow execution failure.
    # Only unhandled technical exceptions should fail the Actions job.

if __name__ == "__main__":
    main()

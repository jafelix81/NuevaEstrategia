#!/usr/bin/env python3
"""Global SEC master-index Form 144/144-A feasibility pilot.

The SEC quarterly master index discovers every Form 144 accession in the quarter.
The filing-detail page supplies Subject/Reporting identity and acceptance time.
A stratified XML sample validates the structured document parser. This is a
source-feasibility audit only: it does not authorize forward-return testing.
"""
from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import hashlib
import html
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from threading import Lock

BASE_SOURCE = "Nueva_Estrategia_Fase0_Descubrimiento.py"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_MUTUAL_FUNDS_URL = "https://www.sec.gov/files/company_tickers_mf.json"
MAPPER_URL = "https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
SEC_INTERVAL = 0.20
SEC_WORKERS = 5
FORMS = {"144", "144/A"}
START_DATE = "2023-04-13"
OUT_DIR = Path("phase50_form144_global_index_pilot")
SEC_UA = "NuevaEstrategia quantitative research jose.felix@felixsarmiento.com"
_last_sec_request = 0.0
_sec_request_lock = Lock()
REQUIRED_FIELDS = (
    "issuer_cik", "issuer_name", "seller_name", "security_class",
    "units_to_be_sold", "aggregate_market_value", "approx_sale_date",
    "notice_date",
)


def norm_cik(value):
    if value in (None, ""):
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits.zfill(10) if digits else None


def cik_path(value):
    cik = norm_cik(value)
    return str(int(cik)) if cik else None


def normalize_form(value):
    value = " ".join(str(value or "").upper().split())
    value = value.replace("SCHEDULE ", "").replace("FORM ", "")
    if "144/A" in value:
        return "144/A"
    if re.search(r"(^|[^A-Z0-9])144([^A-Z0-9]|$)", value):
        return "144"
    return None


def decode_http_body(raw, content_encoding=""):
    encoding = (content_encoding or "").lower()
    if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    return raw


def fetch_bytes(url, sec=True, timeout=60, retries=6):
    global _last_sec_request
    last_error = None
    for attempt in range(retries):
        if sec:
            # Reserve globally spaced request slots before network I/O. Multiple
            # workers improve latency hiding without exceeding the SEC request rate.
            with _sec_request_lock:
                wait = SEC_INTERVAL - (time.monotonic() - _last_sec_request)
                if wait > 0:
                    time.sleep(wait)
                _last_sec_request = time.monotonic()
        request = Request(url, headers={
            "User-Agent": SEC_UA,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json,text/html,application/xml,*/*",
        })
        try:
            with urlopen(request, timeout=timeout) as response:
                return decode_http_body(
                    response.read(), response.headers.get("Content-Encoding", "")
                )
        except HTTPError as error:
            last_error = error
            if error.code == 404:
                raise
            if error.code not in (403, 408, 429, 500, 502, 503, 504):
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                delay = float(retry_after) if retry_after else min(45, 2 ** attempt)
            except (TypeError, ValueError):
                delay = min(45, 2 ** attempt)
            time.sleep(delay + random.uniform(0.1, 0.6))
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(min(30, 2 ** attempt) + random.uniform(0.1, 0.6))
    raise RuntimeError("GET failed after retries: {}: {}".format(url, last_error))


def fetch_json(url, sec=True):
    return json.loads(fetch_bytes(url, sec=sec).decode("utf-8"))


def records(payload):
    if isinstance(payload, dict):
        fields, rows = payload.get("fields"), payload.get("data")
        if isinstance(fields, list) and isinstance(rows, list):
            return [
                dict(zip(fields, row)) if isinstance(row, (list, tuple)) else row
                for row in rows if isinstance(row, (list, tuple, dict))
            ]
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        return [value for value in payload.values() if isinstance(value, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def ticker_variants(ticker):
    variants = [ticker]
    if "." in ticker:
        variants.append(ticker.replace(".", "-"))
    if "-" in ticker:
        variants.append(ticker.replace("-", "."))
    return list(dict.fromkeys(variants))


def load_universe():
    tree = ast.parse(Path(BASE_SOURCE).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    tickers = sorted({
                        str(value).strip().upper()
                        for value in ast.literal_eval(node.value)
                    })
                    if len(tickers) != 335:
                        raise RuntimeError("Expected 335 frozen tickers, got {}".format(len(tickers)))
                    return tickers
    raise RuntimeError("DEFAULT_UNIVERSE not found")


def current_cik_candidates(tickers):
    mapping = defaultdict(lambda: {"ciks": set(), "sources": set(), "fund_classes": []})
    source_errors = []

    def add(ticker, cik, source, fund_class=None):
        if not ticker or not cik:
            return
        ticker = str(ticker).strip().upper()
        cik = norm_cik(cik)
        if not ticker or not cik:
            return
        mapping[ticker]["ciks"].add(cik)
        mapping[ticker]["sources"].add(source)
        if fund_class:
            mapping[ticker]["fund_classes"].append(fund_class)

    for url, source in (
        (SEC_TICKERS_URL, "company_tickers"),
        (SEC_EXCHANGE_URL, "company_tickers_exchange"),
        (SEC_MUTUAL_FUNDS_URL, "company_tickers_mf"),
    ):
        try:
            for row in records(fetch_json(url, sec=True)):
                ticker = row.get("ticker") or row.get("classTicker") or row.get("class_ticker")
                cik = row.get("cik_str") or row.get("cik")
                fund = None
                if source == "company_tickers_mf":
                    fund = {
                        "series_id": row.get("seriesId") or row.get("series_id"),
                        "class_id": row.get("classId") or row.get("class_id"),
                        "series_name": row.get("seriesName") or row.get("series_name"),
                        "class_name": row.get("className") or row.get("class_name"),
                    }
                add(ticker, cik, source, fund)
        except Exception as error:
            source_errors.append({"source": source, "error": str(error)})

    try:
        mapper = fetch_json(MAPPER_URL, sec=False)
        for ticker, cik in mapper.items():
            add(ticker, cik, "sec_cik_mapper_fallback")
    except Exception as error:
        source_errors.append({"source": "sec_cik_mapper_fallback", "error": str(error)})

    ticker_details, cik_to_tickers, unresolved = {}, defaultdict(set), []
    for ticker in tickers:
        found = None
        for alias in ticker_variants(ticker):
            if mapping.get(alias) and mapping[alias]["ciks"]:
                found = (mapping[alias], alias)
                break
        if not found:
            unresolved.append(ticker)
            ticker_details[ticker] = {
                "ciks": [], "sources": [], "alias_used": None, "fund_classes": [],
            }
            continue
        item, alias = found
        ciks = sorted(item["ciks"])
        for cik in ciks:
            cik_to_tickers[cik].add(ticker)
        ticker_details[ticker] = {
            "ciks": ciks,
            "sources": sorted(item["sources"]),
            "alias_used": alias,
            "fund_classes": item["fund_classes"],
        }
    return (
        ticker_details,
        {cik: sorted(values) for cik, values in cik_to_tickers.items()},
        unresolved,
        source_errors,
    )


def parse_master_index(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    lines = raw.lstrip("\ufeff").splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if line.strip().lower().startswith(
            "cik|company name|form type|date filed|filename"
        ):
            header_index = index
            break
    if header_index is None:
        raise ValueError("SEC master.idx header not found")

    grouped = {}
    for line in lines[header_index + 1:]:
        if not line.strip() or line.startswith("---"):
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        master_cik, company, raw_form, filed, filename = [part.strip() for part in parts]
        form = normalize_form(raw_form)
        if form not in FORMS:
            continue
        accession_match = re.search(r"(\d{10}-\d{2}-\d{6})\.txt$", filename, re.I)
        if not accession_match:
            continue
        accession = accession_match.group(1)
        path_match = re.search(r"/data/(\d+)/", filename, re.I)
        archive_path_cik = path_match.group(1) if path_match else None
        item = grouped.setdefault(accession, {
            "accession": accession,
            "master_index_entities": {},
            "archive_path_ciks": set(),
            "forms": set(),
            "filing_dates": set(),
            "filenames": set(),
            "raw_rows": 0,
        })
        item["master_index_entities"][norm_cik(master_cik)] = company
        if archive_path_cik:
            item["archive_path_ciks"].add(cik_path(archive_path_cik))
        item["forms"].add(form)
        item["filing_dates"].add(filed)
        item["filenames"].add(filename)
        item["raw_rows"] += 1

    output = []
    for accession, item in grouped.items():
        forms = sorted(item["forms"])
        dates = sorted(item["filing_dates"])
        paths = sorted(item["archive_path_ciks"])
        entities = item["master_index_entities"]
        output.append({
            "accession": accession,
            "form": forms[0] if len(forms) == 1 else None,
            "filing_date": dates[0] if len(dates) == 1 else None,
            "master_index_ciks": sorted(entities),
            "master_index_names": entities,
            "archive_path_cik": paths[0] if len(paths) == 1 else None,
            "archive_path_cik_conflict": len(paths) > 1,
            "master_index_row_count": item["raw_rows"],
            "metadata_conflict": len(forms) != 1 or len(dates) != 1 or len(paths) > 1,
            "filenames": sorted(item["filenames"]),
        })
    return sorted(output, key=lambda row: (row["filing_date"] or "", row["accession"]))


def legacy_text(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    raw = re.sub(
        r"(?i)<\s*(?:br|/?p|/?tr|/?td|/?div|/?li)\b[^>]*>", "\n", raw
    )
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", raw)


def parse_index_page(raw):
    text = legacy_text(raw)
    flat = re.sub(r"\s+", " ", text).strip()
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    output = {
        "subject_name": None,
        "subject_cik": None,
        "reporting_name": None,
        "reporting_cik": None,
        "filed_by_name": None,
        "filed_by_cik": None,
        "accepted_at": None,
        "filing_date": None,
        "form": None,
        "accession": None,
    }
    for label, prefix in (("Subject", "subject"), ("Reporting", "reporting"), ("Filed by", "filed_by")):
        pattern = re.compile(
            r"(?i)^(.{1,220}?)\s*\(\s*" + re.escape(label) + r"\s*\)\s*CIK:\s*(\d{6,10})"
        )
        for line in lines:
            match = pattern.search(line)
            if match:
                output[prefix + "_name"] = match.group(1).strip(" |\t")
                output[prefix + "_cik"] = norm_cik(match.group(2))
                break
        if not output[prefix + "_cik"]:
            match = re.search(
                r"(?i)(.{1,220}?)\s*\(\s*" + re.escape(label) + r"\s*\)\s*CIK:\s*(\d{6,10})",
                flat,
            )
            if match:
                output[prefix + "_name"] = re.sub(r"\s+", " ", match.group(1)).strip(" |\t")
                output[prefix + "_cik"] = norm_cik(match.group(2))

    match = re.search(
        r"(?i)Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", flat
    )
    if match:
        output["accepted_at"] = match.group(1)
    match = re.search(r"(?i)Filing Date\s+(\d{4}-\d{2}-\d{2})", flat)
    if match:
        output["filing_date"] = match.group(1)
    match = re.search(r"(?i)\bForm\s+(144(?:/A)?)\b", flat)
    if match:
        output["form"] = normalize_form(match.group(1))
    match = re.search(r"(?i)SEC Accession No\.\s*(\d{10}-\d{2}-\d{6})", flat)
    if match:
        output["accession"] = match.group(1)
    return output


def archive_index_urls(group):
    accession = group["accession"]
    nodash = accession.replace("-", "")
    candidates = []
    if group.get("archive_path_cik"):
        candidates.append(group["archive_path_cik"])
    candidates.extend(group.get("master_index_ciks") or [])
    candidates.append(accession.split("-")[0])
    urls = []
    for cik in dict.fromkeys(candidates):
        path_cik = cik_path(cik)
        if not path_cik:
            continue
        base = "{}/{}/{}".format(SEC_ARCHIVES, str(int(path_cik)), nodash)
        urls.extend([base + "/" + accession + "-index.htm", base + "/" + accession + "-index.html"])
    return list(dict.fromkeys(urls))


def fetch_index_page(group):
    errors = []
    for url in archive_index_urls(group):
        try:
            raw = fetch_bytes(url, sec=True, timeout=45, retries=5)
            parsed = parse_index_page(raw)
            if parsed.get("accession") and parsed["accession"] != group["accession"]:
                errors.append("ACCESSION_MISMATCH")
                continue
            if not parsed.get("accession"):
                errors.append("ACCESSION_NOT_PARSED")
                continue
            path_match = re.search(r"/data/(\d+)/", url, re.I)
            parsed["archive_path_cik"] = norm_cik(path_match.group(1)) if path_match else None
            parsed["index_url"] = url
            return parsed, None
        except HTTPError as error:
            if error.code == 404:
                errors.append("404")
                continue
            return None, "HTTP{}".format(error.code)
        except Exception as error:
            errors.append("{}:{}".format(type(error).__name__, error))
    return None, ";".join(errors[-8:]) or "INDEX_NOT_FOUND"


def local_name(tag):
    return str(tag).split("}", 1)[-1].split(":")[-1].lower()


def descendants(root, name):
    wanted = name.lower()
    return [element for element in root.iter() if local_name(element.tag) == wanted]


def first_text(root, name):
    for element in descendants(root, name):
        if element.text and element.text.strip():
            return element.text.strip()
    return None


def all_text(root, name):
    return [
        element.text.strip()
        for element in descendants(root, name)
        if element.text and element.text.strip()
    ]


def parse_form144_xml(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    if local_name(root.tag) != "edgarsubmission":
        raise ValueError("Unexpected XML root: {}".format(local_name(root.tag)))
    submission_type = normalize_form(first_text(root, "submissionType"))
    if submission_type not in FORMS:
        raise ValueError("Unexpected submissionType: {}".format(submission_type))

    filer_nodes = descendants(root, "filerCredentials")
    filer_cik = None
    if filer_nodes:
        filer_cik = norm_cik(first_text(filer_nodes[0], "cik"))
    if not filer_cik:
        filer_cik = norm_cik(first_text(root, "cik"))

    relationships = all_text(root, "relationshipToIssuer")
    remarks = all_text(root, "remarks")
    plan_dates = all_text(root, "planAdoptionDate") + all_text(root, "dateOfPlanAdoption")
    result = {
        "submission_type": submission_type,
        "filer_cik": filer_cik,
        "previous_accession": first_text(root, "previousAccessionNumber"),
        "issuer_cik": norm_cik(first_text(root, "issuerCik")),
        "issuer_name": first_text(root, "issuerName"),
        "seller_name": first_text(root, "nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold"),
        "relationships": relationships,
        "security_class": all_text(root, "securitiesClassTitle"),
        "units_to_be_sold": first_text(root, "noOfUnitsSold"),
        "aggregate_market_value": first_text(root, "aggregateMarketValue"),
        "approx_sale_date": first_text(root, "approxSaleDate"),
        "notice_date": first_text(root, "noticeDate"),
        "plan_adoption_dates": plan_dates,
        "remarks": remarks,
        "mentions_10b5_1": any(re.search(r"10b5\s*[-–]?\s*1", value, re.I) for value in remarks),
        "tranche_count": len(descendants(root, "securitiesToBeSold")),
    }
    result["field_presence"] = {
        "issuer_cik": bool(result["issuer_cik"]),
        "issuer_name": bool(result["issuer_name"]),
        "seller_name": bool(result["seller_name"]),
        "security_class": bool(result["security_class"]),
        "units_to_be_sold": bool(result["units_to_be_sold"]),
        "aggregate_market_value": bool(result["aggregate_market_value"]),
        "approx_sale_date": bool(result["approx_sale_date"]),
        "notice_date": bool(result["notice_date"]),
    }
    return result


def xml_links(index_html):
    links = re.findall(
        r"""href\s*=\s*["']([^"']+\.xml(?:\?[^"']*)?)["']""",
        index_html,
        flags=re.I,
    )
    cleaned = []
    for link in links:
        link = html.unescape(link).split("?", 1)[0]
        if link not in cleaned:
            cleaned.append(link)
    cleaned.sort(key=lambda value: (
        "primary_doc.xml" not in value.lower(), "/xsl" in value.lower(), value
    ))
    return cleaned


def fetch_primary_xml(group, index_row):
    index_url = index_row.get("index_url") or ""
    match = re.search(r"(/Archives/edgar/data/\d+/\d+)/", index_url, re.I)
    if not match:
        return None, None, "ARCHIVE_PATH_NOT_RESOLVED"
    base = "https://www.sec.gov" + match.group(1)
    candidate_urls = [base + "/primary_doc.xml"]
    try:
        index_html = fetch_bytes(index_url, sec=True, timeout=45, retries=5).decode("utf-8", "replace")
        candidate_urls.extend(urljoin(index_url, link) for link in xml_links(index_html))
    except Exception:
        pass
    errors = []
    for url in dict.fromkeys(candidate_urls):
        try:
            raw = fetch_bytes(url, sec=True, timeout=45, retries=5)
            parsed = parse_form144_xml(raw)
            return parsed, url, None
        except HTTPError as error:
            errors.append("HTTP{}".format(error.code))
        except Exception as error:
            errors.append("{}:{}".format(type(error).__name__, error))
    return None, None, ";".join(errors[-8:]) or "PRIMARY_XML_NOT_FOUND"


def parse_edgar_date(value):
    if value in (None, ""):
        return None
    value = str(value).strip()
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def date_relation(event_date, filing_date):
    event = parse_edgar_date(event_date)
    filed = parse_edgar_date(filing_date)
    if event is None or filed is None:
        return "unknown"
    if event < filed:
        return "before_filing"
    if event == filed:
        return "same_day"
    return "after_filing"


def days_event_minus_filing(event_date, filing_date):
    event = parse_edgar_date(event_date)
    filed = parse_edgar_date(filing_date)
    return (event - filed).days if event and filed else None


def stable_key(row):
    return hashlib.sha256(row["accession"].encode("utf-8")).hexdigest()


def select_xml_sample(index_rows, target_ciks, sample_per_form=25):
    target = [row for row in index_rows if row.get("subject_cik") in target_ciks]
    non_target = [row for row in index_rows if row.get("subject_cik") not in target_ciks]
    selected = []
    for form in ("144", "144/A"):
        target_pool = sorted(
            [row for row in target
             if (row.get("master_index_form") or row.get("form")) == form],
            key=stable_key,
        )
        non_target_pool = sorted(
            [row for row in non_target
             if (row.get("master_index_form") or row.get("form")) == form],
            key=stable_key,
        )
        selected.extend(target_pool[:sample_per_form])
        selected.extend(non_target_pool[:sample_per_form])
    unique = {row["accession"]: row for row in selected}
    return sorted(unique.values(), key=lambda row: (row.get("master_index_form") or row.get("form") or "", row["accession"]))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else ["accession"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--quarter", type=int, default=1, choices=(1, 2, 3, 4))
    parser.add_argument("--sample-per-form", type=int, default=25)
    parser.add_argument("--output", default=str(OUT_DIR))
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    tickers = load_universe()
    ticker_details, cik_to_tickers, unresolved, mapping_errors = current_cik_candidates(tickers)
    target_ciks = set(cik_to_tickers)
    master_url = "https://www.sec.gov/Archives/edgar/full-index/{}/QTR{}/master.idx".format(
        args.year, args.quarter
    )
    master = fetch_bytes(master_url, sec=True, timeout=120)
    master_sha = hashlib.sha256(master).hexdigest()
    (output / "master.idx.gz").write_bytes(gzip.compress(master, compresslevel=9))

    groups = parse_master_index(master)
    form_counts = Counter(row["form"] for row in groups)
    index_rows_by_position = [None] * len(groups)
    index_errors = []

    def fetch_index_job(position, group):
        parsed, error = fetch_index_page(group)
        if error:
            return position, None, {
                "accession": group["accession"],
                "form": group["form"],
                "filing_date": group["filing_date"],
                "archive_path_cik": group.get("archive_path_cik"),
                "error": error,
            }
        row = {
            "accession": group["accession"],
            "master_index_form": group["form"],
            "master_index_filing_date": group["filing_date"],
            "master_index_ciks": ";".join(group["master_index_ciks"]),
            "master_index_names": json.dumps(group["master_index_names"], sort_keys=True),
            "archive_path_cik_from_master": group.get("archive_path_cik"),
            "archive_path_cik_from_url": parsed.get("archive_path_cik"),
            "master_index_row_count": group["master_index_row_count"],
            "metadata_conflict": group["metadata_conflict"],
            "index_form": parsed.get("form"),
            "index_form_match": parsed.get("form") == group["form"],
            "index_filing_date": parsed.get("filing_date"),
            "index_filing_date_match": parsed.get("filing_date") == group["filing_date"],
            "accepted_at": parsed.get("accepted_at"),
            "subject_name": parsed.get("subject_name"),
            "subject_cik": parsed.get("subject_cik"),
            "reporting_name": parsed.get("reporting_name"),
            "reporting_cik": parsed.get("reporting_cik") or parsed.get("filed_by_cik"),
            "filed_by_name": parsed.get("filed_by_name"),
            "filed_by_cik": parsed.get("filed_by_cik"),
            "submission_cik_accession_prefix": norm_cik(group["accession"].split("-")[0]),
            "index_url": parsed.get("index_url"),
            "subject_is_target_candidate": bool(parsed.get("subject_cik") in target_ciks),
            "subject_candidate_tickers": ";".join(
                cik_to_tickers.get(parsed.get("subject_cik"), [])
            ),
            "reporting_is_target_candidate": bool(
                (parsed.get("reporting_cik") or parsed.get("filed_by_cik")) in target_ciks
            ),
        }
        return position, row, None

    # SEC index pages are independent. A small worker pool hides network latency;
    # the shared lock still spaces all SEC requests at the configured global rate.
    with ThreadPoolExecutor(max_workers=SEC_WORKERS) as executor:
        futures = [
            executor.submit(fetch_index_job, position, group)
            for position, group in enumerate(groups)
        ]
        for completed, future in enumerate(as_completed(futures), 1):
            position, row, error_row = future.result()
            if row is not None:
                index_rows_by_position[position] = row
            if error_row is not None:
                index_errors.append(error_row)
            if completed % 500 == 0 or completed == len(groups):
                partial_rows = [item for item in index_rows_by_position if item is not None]
                write_csv(output / "global_index_census.partial.csv", partial_rows)
                write_csv(output / "index_fetch_errors.partial.csv", index_errors)
                print(json.dumps({
                    "stage": "INDEX_PROGRESS",
                    "completed": completed,
                    "total": len(groups),
                    "parsed": len(partial_rows),
                    "errors": len(index_errors),
                    "workers": SEC_WORKERS,
                    "sec_min_interval_seconds": SEC_INTERVAL,
                }), flush=True)

    index_rows = [item for item in index_rows_by_position if item is not None]
    index_errors.sort(key=lambda row: row["accession"])

    target_rows = [row for row in index_rows if row["subject_is_target_candidate"]]
    xml_sample = select_xml_sample(index_rows, target_ciks, args.sample_per_form)
    xml_rows, xml_errors = [], []
    for number, row in enumerate(xml_sample, 1):
        group = {
            "accession": row["accession"],
            "archive_path_cik": row.get("archive_path_cik_from_url"),
        }
        parsed, xml_url, error = fetch_primary_xml(group, row)
        if error:
            xml_errors.append({
                "accession": row["accession"],
                "form": row["master_index_form"],
                "target_subject": row["subject_is_target_candidate"],
                "error": error,
            })
            xml_rows.append({
                "accession": row["accession"],
                "form": row["master_index_form"],
                "target_subject": row["subject_is_target_candidate"],
                "xml_parse_ok": False,
                "xml_error": error,
            })
            continue
        filing_date = row["master_index_filing_date"]
        issuer_cik = parsed.get("issuer_cik")
        xml_rows.append({
            "accession": row["accession"],
            "form": row["master_index_form"],
            "target_subject": row["subject_is_target_candidate"],
            "subject_candidate_tickers": row["subject_candidate_tickers"],
            "index_subject_cik": row["subject_cik"],
            "xml_issuer_cik": issuer_cik,
            "xml_subject_matches_index": bool(issuer_cik and issuer_cik == row["subject_cik"]),
            "xml_filer_cik": parsed.get("filer_cik"),
            "reporting_cik_index": row["reporting_cik"],
            "xml_form": parsed.get("submission_type"),
            "xml_form_matches_index": parsed.get("submission_type") == row["master_index_form"],
            "file_date": filing_date,
            "accepted_at": row["accepted_at"],
            "accepted_timestamp_present": bool(row["accepted_at"]),
            "seller_name": parsed.get("seller_name"),
            "relationships": ";".join(parsed.get("relationships") or []),
            "security_class": ";".join(parsed.get("security_class") or []),
            "units_to_be_sold": parsed.get("units_to_be_sold"),
            "aggregate_market_value": parsed.get("aggregate_market_value"),
            "approx_sale_date": parsed.get("approx_sale_date"),
            "approx_sale_date_relation": date_relation(parsed.get("approx_sale_date"), filing_date),
            "approx_sale_days_minus_filing": days_event_minus_filing(
                parsed.get("approx_sale_date"), filing_date
            ),
            "notice_date": parsed.get("notice_date"),
            "notice_date_relation": date_relation(parsed.get("notice_date"), filing_date),
            "previous_accession": parsed.get("previous_accession"),
            "plan_adoption_dates": ";".join(parsed.get("plan_adoption_dates") or []),
            "mentions_10b5_1_in_remarks": parsed.get("mentions_10b5_1"),
            "tranche_count": parsed.get("tranche_count"),
            "field_presence": json.dumps(parsed.get("field_presence") or {}, sort_keys=True),
            "xml_url": xml_url,
            "xml_parse_ok": True,
        })
        if number % 25 == 0:
            print(json.dumps({
                "stage": "XML_SAMPLE_PROGRESS",
                "processed": number,
                "total": len(xml_sample),
                "parsed": sum(bool(item.get("xml_parse_ok")) for item in xml_rows),
                "errors": len(xml_errors),
            }), flush=True)

    parsed_xml = [row for row in xml_rows if row.get("xml_parse_ok")]
    by_form = {}
    for form in ("144", "144/A"):
        form_sample = [row for row in xml_rows if row["form"] == form]
        form_parsed = [row for row in form_sample if row.get("xml_parse_ok")]
        by_form[form] = {
            "sample_rows": len(form_sample),
            "target_subject_sample_rows": sum(bool(row.get("target_subject")) for row in form_sample),
            "non_target_sample_rows": sum(not bool(row.get("target_subject")) for row in form_sample),
            "xml_parse_rate": len(form_parsed) / len(form_sample) if form_sample else None,
            "xml_subject_match_rate": (
                sum(bool(row.get("xml_subject_matches_index")) for row in form_parsed) / len(form_parsed)
                if form_parsed else None
            ),
            "xml_form_match_rate": (
                sum(bool(row.get("xml_form_matches_index")) for row in form_parsed) / len(form_parsed)
                if form_parsed else None
            ),
            "approx_sale_date_relation": dict(Counter(
                row.get("approx_sale_date_relation") for row in form_parsed
            )),
            "notice_date_relation": dict(Counter(
                row.get("notice_date_relation") for row in form_parsed
            )),
            "previous_accession_count": sum(bool(row.get("previous_accession")) for row in form_parsed),
            "mentions_10b5_1_count": sum(bool(row.get("mentions_10b5_1_in_remarks")) for row in form_parsed),
        }

    field_rates = {}
    field_rates_by_form = {}
    for field in REQUIRED_FIELDS:
        values = []
        for row in parsed_xml:
            presence = json.loads(row.get("field_presence") or "{}")
            values.append(bool(presence.get(field)))
        field_rates[field] = sum(values) / len(values) if values else 0.0
    for form in ("144", "144/A"):
        form_parsed = [row for row in parsed_xml if row["form"] == form]
        field_rates_by_form[form] = {}
        for field in REQUIRED_FIELDS:
            values = [
                bool(json.loads(row.get("field_presence") or "{}").get(field))
                for row in form_parsed
            ]
            field_rates_by_form[form][field] = (
                sum(values) / len(values) if values else 0.0
            )

    index_success_rate = len(index_rows) / len(groups) if groups else 0.0
    subject_rate = (
        sum(bool(row.get("subject_cik")) for row in index_rows) / len(index_rows)
        if index_rows else 0.0
    )
    reporting_rate = (
        sum(bool(row.get("reporting_cik")) for row in index_rows) / len(index_rows)
        if index_rows else 0.0
    )
    accepted_rate = (
        sum(bool(row.get("accepted_at")) for row in index_rows) / len(index_rows)
        if index_rows else 0.0
    )
    index_form_rate = (
        sum(bool(row.get("index_form_match")) for row in index_rows) / len(index_rows)
        if index_rows else 0.0
    )
    index_date_rate = (
        sum(bool(row.get("index_filing_date_match")) for row in index_rows) / len(index_rows)
        if index_rows else 0.0
    )
    xml_parse_rate = len(parsed_xml) / len(xml_rows) if xml_rows else 0.0
    xml_subject_rate = (
        sum(bool(row.get("xml_subject_matches_index")) for row in parsed_xml) / len(parsed_xml)
        if parsed_xml else 0.0
    )
    xml_form_rate = (
        sum(bool(row.get("xml_form_matches_index")) for row in parsed_xml) / len(parsed_xml)
        if parsed_xml else 0.0
    )
    target_by_form = dict(Counter(row["master_index_form"] for row in target_rows))
    total_by_form = dict(form_counts)
    sample_by_form = {form: by_form[form]["sample_rows"] for form in ("144", "144/A")}
    gates = {
        "at_least_300_current_ticker_cik_mappings": len(cik_to_tickers) >= 300,
        "global_master_index_has_both_forms": all(total_by_form.get(form, 0) > 0 for form in FORMS),
        "at_least_25_global_sample_rows_per_form": all(
            sample_by_form.get(form, 0) >= min(25, total_by_form.get(form, 0))
            and sample_by_form.get(form, 0) > 0 for form in FORMS
        ),
        "index_page_fetch_rate_at_least_95pct": index_success_rate >= 0.95,
        "subject_cik_parse_rate_at_least_95pct": subject_rate >= 0.95,
        "accepted_timestamp_rate_at_least_95pct": accepted_rate >= 0.95,
        "index_form_agreement_at_least_95pct": index_form_rate >= 0.95,
        "index_filing_date_agreement_at_least_95pct": index_date_rate >= 0.95,
        "xml_parse_rate_at_least_95pct_each_form": all(
            by_form[form]["xml_parse_rate"] is not None
            and by_form[form]["xml_parse_rate"] >= 0.95
            for form in ("144", "144/A")
        ),
        "xml_subject_match_at_least_95pct_each_form": all(
            by_form[form]["xml_subject_match_rate"] is not None
            and by_form[form]["xml_subject_match_rate"] >= 0.95
            for form in ("144", "144/A")
        ),
        "xml_form_match_at_least_95pct_each_form": all(
            by_form[form]["xml_form_match_rate"] is not None
            and by_form[form]["xml_form_match_rate"] >= 0.95
            for form in ("144", "144/A")
        ),
        "required_xml_fields_at_least_95pct_each_form": all(
            rate >= 0.95
            for form_rates in field_rates_by_form.values()
            for rate in form_rates.values()
        ),
    }
    passed = all(gates.values())

    summary = {
        "phase": "50-global-index-form144-pilot",
        "status": "COMPLETE",
        "data_gate": "PASS" if passed else "FAIL",
        "quarter": "{}Q{}".format(args.year, args.quarter),
        "master_index_url": master_url,
        "master_index_sha256": master_sha,
        "master_index_bytes": len(master),
        "frozen_universe_size": len(tickers),
        "current_tickers_with_cik_mapping": sum(bool(item["ciks"]) for item in ticker_details.values()),
        "current_candidate_cik_count": len(cik_to_tickers),
        "unresolved_tickers": unresolved,
        "mapping_source_errors": mapping_errors,
        "global_form144_accessions": len(groups),
        "global_accessions_by_form": total_by_form,
        "global_accession_rows_by_form": dict(Counter(
            row["form"] for row in groups for _ in range(row["master_index_row_count"])
        )),
        "index_pages_requested": len(groups),
        "index_pages_parsed": len(index_rows),
        "index_page_errors": len(index_errors),
        "index_page_fetch_rate": index_success_rate,
        "subject_cik_parse_rate": subject_rate,
        "reporting_cik_parse_rate": reporting_rate,
        "accepted_timestamp_rate": accepted_rate,
        "index_form_agreement_rate": index_form_rate,
        "index_filing_date_agreement_rate": index_date_rate,
        "target_subject_accessions": len(target_rows),
        "target_subject_accessions_by_form": target_by_form,
        "target_subject_candidate_tickers": sorted({
            ticker for row in target_rows
            for ticker in (row.get("subject_candidate_tickers") or "").split(";") if ticker
        }),
        "xml_sample_requested_per_form_target_and_non_target": args.sample_per_form,
        "xml_sample_rows": len(xml_rows),
        "xml_sample_by_form": by_form,
        "xml_parse_rate": xml_parse_rate,
        "xml_subject_match_rate": xml_subject_rate,
        "xml_form_match_rate": xml_form_rate,
        "required_xml_field_presence_rates": field_rates,
        "required_xml_field_presence_rates_by_form": field_rates_by_form,
        "gate_checks": gates,
        "historical_pit_universe_gate": "NOT_TESTED",
        "economic_test_authorized": False,
        "knowledge_date_rule": (
            "SEC accepted timestamp retained; conservative signal use begins next trading session. "
            "Filing date is fallback only when accepted timestamp is absent."
        ),
        "approx_sale_date_rule": (
            "Parse EDGAR MM/DD/YYYY and ISO dates. Date relation is descriptive only; "
            "a past approximate sale date is not proof of execution and is never KnowledgeDate."
        ),
        "amendment_rule": (
            "144/A previousAccessionNumber is a prior-filing reference, not necessarily the "
            "immediately preceding amendment. Consolidate lineage before event counting."
        ),
        "mapping_limitation": (
            "Current SEC ticker/CIK maps are candidate mappings, not historical active-universe membership."
        ),
        "forward_returns_used": False,
        "index_errors_sample": index_errors[:50],
        "xml_errors_sample": xml_errors[:50],
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    write_csv(output / "ticker_cik_candidates.csv", [
        {
            "ticker": ticker,
            "candidate_ciks": ";".join(detail["ciks"]),
            "mapping_sources": ";".join(detail["sources"]),
            "alias_used": detail["alias_used"] or "",
            "fund_classes": json.dumps(detail["fund_classes"], sort_keys=True),
        }
        for ticker, detail in ticker_details.items()
    ])
    write_csv(output / "global_index_census.csv", index_rows)
    write_csv(output / "target_subject_filings.csv", target_rows)
    write_csv(output / "xml_validation_sample.csv", xml_rows)
    write_csv(output / "index_fetch_errors.csv", index_errors)
    write_csv(output / "xml_fetch_errors.csv", xml_errors)
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if not passed:
        raise RuntimeError("Form 144 global-index feasibility gate failed; inspect summary.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Diagnostic EFTS query semantics; bounded positive controls only."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, time
from pathlib import Path
import requests

EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
USER_AGENT = "NuevaEstrategia research contact jafelix81@gmail.com"
CONTROLS = [
    {"name": "Revance", "subject_cik": "0001479290", "filer_cik": "0000019617",
     "accession": "0000019617-25-000296", "form": "SC 13G/A", "filed": "2025-03-06"},
    {"name": "Osisko", "subject_cik": "0001431852", "filer_cik": "0002083861",
     "accession": "0001062993-25-015044", "form": "SC 13D", "filed": "2025-08-28"},
    {"name": "Fox", "subject_cik": "0001754301", "filer_cik": "0002080603",
     "accession": "0000950157-25-000788", "form": "SC 13D", "filed": "2025-09-12"},
    {"name": "Fox", "subject_cik": "0001754301", "filer_cik": "0002084288",
     "accession": "0000950170-25-114595", "form": "SC 13D", "filed": "2025-09-12"},
]


def normalize_accession(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}" if len(digits) >= 18 else ""


def build_queries():
    queries = [
        {"id": "generic_apple_10k", "q": "Apple", "forms": "10-K",
         "startdt": "2025-01-01", "enddt": "2025-12-31", "dateRange": "custom",
         "expected": []},
        {"id": "revance_name_root_form", "q": "Revance", "forms": "SC 13G",
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_name_amendment_form", "q": "Revance", "forms": "SC 13G/A",
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_name_no_form", "q": "Revance",
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_exact_name", "q": '"Revance Therapeutics"',
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_cik_unpadded", "q": "1479290", "forms": "SC 13G",
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_cik_padded", "q": "0001479290", "forms": "SC 13G",
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "revance_cik_quoted", "q": '"0001479290"',
         "startdt": "2025-03-05", "enddt": "2025-03-07", "dateRange": "custom",
         "expected": ["0000019617-25-000296"]},
        {"id": "osisko_name", "q": "Osisko", "forms": "SC 13D",
         "startdt": "2025-08-27", "enddt": "2025-08-29", "dateRange": "custom",
         "expected": ["0001062993-25-015044"]},
        {"id": "osisko_cik", "q": "1431852", "forms": "SC 13D",
         "startdt": "2025-08-27", "enddt": "2025-08-29", "dateRange": "custom",
         "expected": ["0001062993-25-015044"]},
        {"id": "fox_name", "q": "Fox", "forms": "SC 13D",
         "startdt": "2025-09-11", "enddt": "2025-09-13", "dateRange": "custom",
         "expected": ["0000950157-25-000788", "0000950170-25-114595"]},
        {"id": "fox_cik", "q": "1754301", "forms": "SC 13D",
         "startdt": "2025-09-11", "enddt": "2025-09-13", "dateRange": "custom",
         "expected": ["0000950157-25-000788", "0000950170-25-114595"]},
        {"id": "revance_name_ciks_subject", "q": "Revance", "forms": "SC 13G",
         "ciks": "0001479290", "startdt": "2025-03-05", "enddt": "2025-03-07",
         "dateRange": "custom", "expected": ["0000019617-25-000296"]},
        {"id": "revance_name_ciks_filer", "q": "Revance", "forms": "SC 13G",
         "ciks": "0000019617", "startdt": "2025-03-05", "enddt": "2025-03-07",
         "dateRange": "custom", "expected": ["0000019617-25-000296"]},
    ]
    return queries


def extract_total(payload):
    total = payload.get("hits", {}).get("total", 0)
    if isinstance(total, dict):
        return int(total.get("value", 0))
    try:
        return int(total)
    except (TypeError, ValueError):
        return 0


def parse_hit(hit):
    src = hit.get("_source") or {}
    adsh = src.get("adsh") or ""
    accession = normalize_accession(adsh)
    if not accession:
        m = re.search(r"(?<!\d)(\d{18})(?!\d)", str(hit.get("_id", "")))
        accession = normalize_accession(m.group(1)) if m else ""
    return {
        "accession": accession,
        "form": str(src.get("form") or src.get("root_forms") or ""),
        "file_date": str(src.get("file_date") or ""),
        "filename": str(src.get("filename") or ""),
        "document_type": str(src.get("document_type") or src.get("sequence") or ""),
        "description": str(src.get("description") or ""),
        "ciks": json.dumps(src.get("ciks", []), ensure_ascii=False),
        "display_names": json.dumps(src.get("display_names", []), ensure_ascii=False),
        "hit_id": str(hit.get("_id") or ""),
    }


class EftsClient:
    def __init__(self, sleep_seconds=0.6, timeout=60):
        self.sleep_seconds, self.timeout = sleep_seconds, timeout
        self.last_request, self.request_count = 0.0, 0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def search(self, query):
        delay = self.sleep_seconds - (time.monotonic() - self.last_request)
        if delay > 0: time.sleep(delay)
        params = {"from": 0, "size": 100}
        for key in ("q", "forms", "ciks", "startdt", "enddt", "dateRange"):
            if query.get(key):
                params[key] = query[key]
        self.last_request = time.monotonic()
        response = self.session.get(EFTS_URL, params=params, timeout=self.timeout)
        self.request_count += 1
        raw = response.content
        payload = {}
        error = ""
        try:
            payload = response.json()
        except Exception as exc:
            error = f"json_decode_error:{exc!r}"
        return {
            "status_code": response.status_code,
            "url": response.url,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_text": raw.decode("utf-8", errors="replace"),
            "payload": payload,
            "http_error": "" if response.ok else f"HTTP {response.status_code}",
            "body_error_type": payload.get("errorType", "") if isinstance(payload, dict) else "",
            "body_error_message": payload.get("errorMessage", "") if isinstance(payload, dict) else "",
            "json_error": error,
            "total": extract_total(payload) if isinstance(payload, dict) else 0,
            "documents": [parse_hit(h) for h in payload.get("hits", {}).get("hits", [])] if isinstance(payload, dict) else [],
            "query_echo": payload.get("query", {}) if isinstance(payload, dict) else {},
        }


def run_diagnostics(outdir: Path, sleep_seconds=0.6):
    outdir.mkdir(parents=True, exist_ok=True)
    raw_dir = outdir / "raw"
    raw_dir.mkdir(exist_ok=True)
    client, results, hits = EftsClient(sleep_seconds), [], []
    for query in build_queries():
        result = client.search(query)
        docs = result["documents"]
        expected = set(query["expected"])
        found = sorted(expected & {d["accession"] for d in docs if d["accession"]})
        raw_record = {
            "query": query, "url": result["url"], "status_code": result["status_code"],
            "response_sha256": result["response_sha256"], "query_echo": result["query_echo"],
            "total": result["total"], "documents": docs, "raw_text": result["raw_text"],
            "body_error_type": result["body_error_type"], "body_error_message": result["body_error_message"],
        }
        (raw_dir / f"{query['id']}.json").write_text(json.dumps(raw_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        results.append({
            "query_id": query["id"], "query": query["q"], "forms": query.get("forms", ""),
            "ciks": query.get("ciks", ""), "startdt": query.get("startdt", ""),
            "enddt": query.get("enddt", ""), "status_code": result["status_code"],
            "total": result["total"], "returned_hits": len(docs),
            "expected_accessions": json.dumps(query["expected"]),
            "expected_found": json.dumps(found), "expected_found_count": len(found),
            "response_sha256": result["response_sha256"],
            "body_error_type": result["body_error_type"],
            "body_error_message": result["body_error_message"],
            "http_error": result["http_error"], "json_error": result["json_error"],
            "query_echo": json.dumps(result["query_echo"], ensure_ascii=False),
        })
        for doc in docs:
            hits.append({"query_id": query["id"], **doc})
    generic = next(r for r in results if r["query_id"] == "generic_apple_10k")
    name_queries = [r for r in results if r["query_id"] in {
        "revance_name_root_form", "revance_name_amendment_form", "revance_name_no_form",
        "revance_exact_name", "osisko_name", "fox_name"}]
    name_found = set()
    for r in name_queries:
        name_found.update(json.loads(r["expected_found"]))
    expected = {normalize_accession(c["accession"]) for c in CONTROLS}
    summary = {
        "phase": "79-efts-query-semantics-diagnostic",
        "query_count": len(results),
        "request_count": client.request_count,
        "generic_baseline_hits": int(generic["total"]),
        "generic_endpoint_baseline_pass": int(generic["total"]) > 0 and not generic["http_error"] and not generic["body_error_type"],
        "company_name_queries_found_accessions": sorted(name_found),
        "company_name_queries_found_all_controls": expected.issubset(name_found),
        "all_expected_controls": sorted(expected),
        "exact_cik_text_queries_found": sorted({
            a for r in results if r["query_id"] in {"revance_cik_unpadded", "revance_cik_padded", "revance_cik_quoted", "osisko_cik", "fox_cik"}
            for a in json.loads(r["expected_found"])
        }),
        "ciks_filter_results": [r for r in results if r["ciks"]],
        "response_body_errors": sum(bool(r["body_error_type"] or r["json_error"]) for r in results),
        "http_errors": sum(bool(r["http_error"]) for r in results),
        "decision": (
            "EFTS_NAME_SEARCH_CANDIDATE" if expected.issubset(name_found)
            else ("EFTS_ENDPOINT_OR_QUERY_SYNTAX_UNRESOLVED" if int(generic["total"]) == 0
                  else "EFTS_SUBJECT_DISCOVERY_NOT_VALIDATED")
        ),
        "limitations": [
            "Small positive-control diagnostic only; no global recall or precision estimate.",
            "EFTS is not a documented stable API; query echo and raw response bodies are retained.",
            "Document-level results may include exhibits and must be deduplicated by accession.",
            "No full universe scan, forward returns or alpha tests.",
        ],
    }
    write_csv(outdir / "query_diagnostics.csv", results)
    write_csv(outdir / "document_hits.csv", hits)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("phase79_efts_query_diagnostics"))
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    args = parser.parse_args()
    run_diagnostics(args.outdir, args.sleep_seconds)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Small SEC EFTS subject-CIK positive-control pilot; no alpha or full-universe crawl."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import requests

EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
USER_AGENT = "NuevaEstrategia research contact jafelix81@gmail.com"
CONTROLS = [
    {"name": "Revance Therapeutics", "subject_cik": "0001479290", "filer_cik": "0000019617",
     "accession": "0000019617-25-000296", "form": "SC 13G/A", "filed": "2025-03-06"},
    {"name": "Osisko Development", "subject_cik": "0001431852", "filer_cik": "0002083861",
     "accession": "0001062993-25-015044", "form": "SC 13D", "filed": "2025-08-28"},
    {"name": "Fox Corporation", "subject_cik": "0001754301", "filer_cik": "0002080603",
     "accession": "0000950157-25-000788", "form": "SC 13D", "filed": "2025-09-12"},
    {"name": "Fox Corporation", "subject_cik": "0001754301", "filer_cik": "0002084288",
     "accession": "0000950170-25-114595", "form": "SC 13D", "filed": "2025-09-12"},
]


def normalize_accession(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}" if len(digits) >= 18 else ""


def date_window(value, days=1):
    d = date.fromisoformat(value)
    return (d - timedelta(days=days)).isoformat(), (d + timedelta(days=days)).isoformat()


def build_query_plan(controls=CONTROLS):
    grouped = defaultdict(list)
    for c in controls:
        grouped[(c["subject_cik"], c["form"], c["filed"])].append(c)
    plan = []
    for (subject, form, filed), items in sorted(grouped.items()):
        start, end = date_window(filed, 1)
        expected = sorted({normalize_accession(x["accession"]) for x in items})
        for kind, query in (("q_padded", f'"{subject}"'), ("q_unpadded", f'"{int(subject)}"')):
            plan.append({
                "query_type": kind, "query_value": query, "subject_cik": subject,
                "filer_cik": "", "form": form, "filed": filed, "startdt": start,
                "enddt": end, "expected_accessions": expected,
            })
        plan.append({
            "query_type": "ciks_subject", "query_value": subject, "subject_cik": subject,
            "filer_cik": "", "form": form, "filed": filed, "startdt": start,
            "enddt": end, "expected_accessions": expected,
        })
    filer_groups = defaultdict(list)
    for c in controls:
        filer_groups[(c["filer_cik"], c["form"], c["filed"])].append(c)
    for (filer, form, filed), items in sorted(filer_groups.items()):
        start, end = date_window(filed, 1)
        plan.append({
            "query_type": "ciks_filer", "query_value": filer, "subject_cik": "",
            "filer_cik": filer, "form": form, "filed": filed, "startdt": start,
            "enddt": end, "expected_accessions": sorted({normalize_accession(x["accession"]) for x in items}),
        })
    return plan


def extract_total(payload):
    total = payload.get("hits", {}).get("total", 0)
    if isinstance(total, dict):
        return int(total.get("value", 0))
    try:
        return int(total)
    except (TypeError, ValueError):
        return 0


def parse_hit(hit):
    source = hit.get("_source") or hit.get("source") or {}
    accession = normalize_accession(source.get("adsh") or source.get("accession") or "")
    if not accession:
        m = re.search(r"(?<!\d)(\d{18})(?!\d)", str(hit.get("_id", "")))
        accession = normalize_accession(m.group(1)) if m else ""
    return {
        "accession": accession,
        "form": str(source.get("form") or source.get("root_forms") or ""),
        "file_date": str(source.get("file_date") or source.get("filed") or ""),
        "filename": str(source.get("filename") or ""),
        "document_type": str(source.get("document_type") or source.get("sequence") or ""),
        "description": str(source.get("description") or ""),
        "display_names": json.dumps(source.get("display_names", []), ensure_ascii=False),
        "ciks": json.dumps(source.get("ciks", []), ensure_ascii=False),
        "document_url": str(source.get("url") or source.get("link") or ""),
        "hit_id": str(hit.get("_id") or ""),
    }


class EftsClient:
    def __init__(self, sleep_seconds=0.6, timeout=60, max_pages=10, page_size=100):
        self.sleep_seconds, self.timeout = sleep_seconds, timeout
        self.max_pages, self.page_size = max_pages, page_size
        self.last_request, self.request_count = 0.0, 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json,text/plain,*/*",
        })

    def search(self, query):
        docs, raw_pages, errors = [], [], []
        total, page_from, pages = None, 0, 0
        while pages < self.max_pages:
            delay = self.sleep_seconds - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            params = {
                "dateRange": "custom",
                "startdt": query["startdt"],
                "enddt": query["enddt"],
                "forms": query["form"],
                "from": page_from,
                "size": self.page_size,
            }
            if query["query_type"].startswith("q_"):
                params["q"] = query["query_value"]
            else:
                params["ciks"] = query["query_value"]
            self.last_request = time.monotonic()
            try:
                response = self.session.get(EFTS_URL, params=params, timeout=self.timeout)
                self.request_count += 1
                raw = response.content
                digest = hashlib.sha256(raw).hexdigest()
                status = response.status_code
                response.raise_for_status()
                payload = response.json()
                if total is None:
                    total = extract_total(payload)
                hits = payload.get("hits", {}).get("hits", [])
                parsed = [parse_hit(h) for h in hits]
                docs.extend(parsed)
                raw_pages.append({
                    "from": page_from, "size": self.page_size, "status_code": status,
                    "sha256": digest, "returned": len(hits),
                    "url": response.url,
                })
                pages += 1
                if not hits or len(docs) >= total or len(hits) < self.page_size:
                    break
                page_from += self.page_size
            except Exception as exc:
                errors.append({"from": page_from, "error": repr(exc)})
                break
        return {
            "total": total if total is not None else 0,
            "documents": docs,
            "pages": raw_pages,
            "errors": errors,
            "pagination_complete": bool(total is not None and (len(docs) >= total or total == 0)),
        }


def run_pilot(outdir: Path, sleep_seconds=0.6, page_size=100, max_pages=10):
    outdir.mkdir(parents=True, exist_ok=True)
    raw_dir = outdir / "raw_responses"
    raw_dir.mkdir(exist_ok=True)
    client = EftsClient(sleep_seconds=sleep_seconds, page_size=page_size, max_pages=max_pages)
    plan = build_query_plan()
    query_rows, hit_rows = [], []
    for index, query in enumerate(plan, 1):
        result = client.search(query)
        query_id = f"q{index:02d}_{query['query_type']}_{query['query_value'].replace(chr(34), '').replace(' ', '_')}"
        docs = result["documents"]
        accessions = sorted({d["accession"] for d in docs if d["accession"]})
        expected = query["expected_accessions"]
        found = sorted(set(expected) & set(accessions))
        expected_docs = [d for d in docs if d["accession"] in set(expected)]
        raw_record = {
            "query": query, "total": result["total"], "documents": docs,
            "pages": result["pages"], "errors": result["errors"],
        }
        raw_text = json.dumps(raw_record, indent=2, ensure_ascii=False)
        (raw_dir / f"{query_id}.json").write_text(raw_text + "\n", encoding="utf-8")
        query_rows.append({
            "query_id": query_id, "query_type": query["query_type"], "query_value": query["query_value"],
            "subject_cik": query["subject_cik"], "filer_cik": query["filer_cik"],
            "form": query["form"], "startdt": query["startdt"], "enddt": query["enddt"],
            "expected_accessions": json.dumps(expected), "expected_found": json.dumps(found),
            "expected_found_count": len(found), "expected_count": len(expected),
            "total_document_hits": result["total"], "returned_document_hits": len(docs),
            "unique_accessions": len(accessions), "pagination_complete": result["pagination_complete"],
            "pages": len(result["pages"]), "errors": json.dumps(result["errors"]),
            "response_sha256": hashlib.sha256(raw_text.encode()).hexdigest(),
        })
        for doc in docs:
            hit_rows.append({"query_id": query_id, "query_type": query["query_type"], **doc})

    # Evaluate positive controls only on exact-text CIK searches, not the undocumented ciks filter.
    q_results = [r for r in query_rows if r["query_type"] in {"q_padded", "q_unpadded"}]
    q_found = set()
    for row in q_results:
        q_found.update(json.loads(row["expected_found"]))
    expected_all = {normalize_accession(c["accession"]) for c in CONTROLS}
    q_positive = expected_all.issubset(q_found)
    form_date_matches = True
    for control in CONTROLS:
        accession = normalize_accession(control["accession"])
        candidates = [h for h in hit_rows if h["accession"] == accession and h["query_type"] in {"q_padded", "q_unpadded"}]
        if not candidates:
            form_date_matches = False
            continue
        if not any(
            normalize_form_value(h["form"]) == normalize_form_value(control["form"])
            and h["file_date"] == control["filed"]
            for h in candidates
        ):
            form_date_matches = False
    q_pagination_complete = all(r["pagination_complete"] for r in q_results)
    q_errors_absent = all(not json.loads(r["errors"]) for r in q_results)
    summary = {
        "phase": "78-efts-subject-cik-positive-control-pilot",
        "status": "COMPLETE",
        "query_count": len(query_rows),
        "request_count": client.request_count,
        "positive_control_count": len(CONTROLS),
        "positive_control_accessions": sorted(expected_all),
        "q_exact_subject_cik_found_all_controls": q_positive,
        "q_exact_subject_cik_form_and_date_match": form_date_matches,
        "q_query_pagination_complete": q_pagination_complete,
        "q_query_errors_absent": q_errors_absent,
        "ciks_subject_query_rows": sum(r["query_type"] == "ciks_subject" for r in query_rows),
        "ciks_filer_query_rows": sum(r["query_type"] == "ciks_filer" for r in query_rows),
        "ciks_parameter_semantics": "diagnostic only; not used as subject identity unless positive controls establish semantics",
        "data_gate": "PASS" if q_positive and form_date_matches and q_pagination_complete and q_errors_absent else "FAIL",
        "limitations": [
            "Only four known cross-filer positive controls were tested; recall/precision over the full 335-name universe is unknown.",
            "EFTS is a search index, not a documented complete subject-issuer API; document-level hits may include exhibits.",
            "Current CIKs are not historical F80 membership or PIT security lineage.",
            "No forward returns, alpha tests or production changes.",
        ],
    }
    write_csv(outdir / "query_results.csv", query_rows)
    write_csv(outdir / "document_hits.csv", hit_rows)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if summary["data_gate"] != "PASS":
        raise SystemExit(2)
    return summary


def normalize_form_value(value):
    return re.sub(r"\s+", " ", str(value or "").strip().upper())


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("phase78_efts_subject_cik_pilot"))
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()
    run_pilot(args.outdir, args.sleep_seconds, args.page_size, args.max_pages)


if __name__ == "__main__":
    main()

"""Global EDGAR Schedule 13D/G subject-issuer census pilot.

The quarterly master index enumerates filings by submitting CIK. The filing
index page supplies separate Filed-by and Subject CIK metadata. This pilot
scans all 13D/G submissions for one quarter and filters by Subject CIK, rather
than querying submissions for target tickers and assuming those filings are
about the queried company.

No forward returns or economic-group inference are performed.
"""
from __future__ import annotations
import argparse, ast, csv, gzip, hashlib, json, random, re, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from phase35_13dg_parser_v3 import parse_index, parse_master_index

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
MAPPER = "https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json"
SEC_UA = "NuevaEstrategia quantitative research jafelix@gmail.com"
SEC_INTERVAL = 0.16
_last_sec_request = 0.0

def fetch_bytes(url, *, sec=False, timeout=60, retries=6):
    global _last_sec_request
    last_error = None
    for attempt in range(retries):
        if sec:
            wait = SEC_INTERVAL - (time.monotonic() - _last_sec_request)
            if wait > 0:
                time.sleep(wait)
            _last_sec_request = time.monotonic()
        req = Request(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate", "Accept": "*/*"})
        try:
            with urlopen(req, timeout=timeout) as response:
                raw = response.read()
                if (response.headers.get("Content-Encoding") or "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw
        except HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                raise
            if exc.code not in (403, 408, 429, 500, 502, 503, 504):
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = float(retry_after) if retry_after else min(45, 2 ** attempt)
            except Exception:
                delay = min(45, 2 ** attempt)
            time.sleep(delay + random.uniform(0.1, 0.6))
        except Exception as exc:
            last_error = exc
            time.sleep(min(30, 2 ** attempt) + random.uniform(0.1, 0.6))
    raise RuntimeError(f"GET failed after retries: {url}: {last_error}")

def load_frozen_universe():
    source = Path("Nueva_Estrategia_Fase0_Descubrimiento.py")
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_UNIVERSE":
                    values = sorted({str(x).strip().upper() for x in ast.literal_eval(node.value)})
                    if len(values) != 335:
                        raise RuntimeError(f"Expected 335 frozen tickers; got {len(values)}")
                    return values
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def current_candidate_ciks(tickers):
    sec = json.loads(fetch_bytes(SEC_TICKERS, sec=True).decode("utf-8"))
    sec_map = {str(v.get("ticker", "")).strip().upper(): str(v.get("cik_str", "")).zfill(10)
               for v in sec.values() if v.get("ticker") and v.get("cik_str")}
    mapper = json.loads(fetch_bytes(MAPPER).decode("utf-8"))
    by_ticker, source = {}, {}
    for ticker in tickers:
        cik = sec_map.get(ticker)
        src = "sec_company_tickers_current"
        if not cik and mapper.get(ticker):
            cik, src = str(mapper[ticker]).zfill(10), "historical_mapper_fallback"
        if cik and not cik.isdigit():
            cik = None
        by_ticker[ticker] = cik
        source[ticker] = src if cik else "unresolved"
    cik_to_tickers = {}
    for ticker, cik in by_ticker.items():
        if cik:
            cik_to_tickers.setdefault(cik, []).append(ticker)
    return by_ticker, source, cik_to_tickers

def build_index_urls(row):
    parent = row["filename"].strip().lstrip("/").rsplit("/", 1)[0]
    base = f"https://www.sec.gov/Archives/{parent}/{row['accession']}-index"
    return [base + ".htm", base + ".html"]

def fetch_filing_index(row):
    errors = []
    for url in build_index_urls(row):
        try:
            raw = fetch_bytes(url, sec=True, timeout=45, retries=5)
            parsed = parse_index(raw)
            parsed["index_url"] = url
            return parsed, None
        except HTTPError as exc:
            if exc.code == 404:
                errors.append(f"404:{url.rsplit('.', 1)[-1]}")
                continue
            return None, f"HTTP{exc.code}:{url}"
        except Exception as exc:
            return None, f"{type(exc).__name__}:{exc}"
    return None, ";".join(errors) or "INDEX_NOT_FOUND"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--quarter", type=int, default=1, choices=(1, 2, 3, 4))
    parser.add_argument("--output", default="phase35_global_subject_census_pilot")
    args = parser.parse_args()

    tickers = load_frozen_universe()
    ticker_cik, mapping_source, cik_tickers = current_candidate_ciks(tickers)
    target_ciks = set(cik_tickers)
    unresolved = [t for t, c in ticker_cik.items() if not c]
    quarter = f"QTR{args.quarter}"
    master_url = f"https://www.sec.gov/Archives/edgar/full-index/{args.year}/{quarter}/master.idx"
    master_raw = fetch_bytes(master_url, sec=True, timeout=90)
    master_sha = hashlib.sha256(master_raw).hexdigest()
    candidates_raw = parse_master_index(master_raw)
    candidates_by_accession = {}
    duplicate_accessions = []
    for row in candidates_raw:
        if row["accession"] in candidates_by_accession:
            duplicate_accessions.append(row["accession"])
            continue
        candidates_by_accession[row["accession"]] = row
    candidates = list(candidates_by_accession.values())
    by_form = Counter(row["form"] for row in candidates)

    print(json.dumps({"stage": "MASTER_INDEX_FILTERED", "year": args.year, "quarter": quarter,
        "candidate_filings": len(candidates), "by_form": dict(by_form), "target_tickers": len(tickers),
        "target_candidate_ciks": len(target_ciks), "unresolved_tickers": len(unresolved),
        "master_sha256": master_sha}, indent=2), flush=True)

    results, errors = [], []
    for i, row in enumerate(candidates, 1):
        parsed, error = fetch_filing_index(row)
        if error:
            errors.append({"accession": row["accession"], "error": error})
            continue
        if parsed.get("accession") != row["accession"]:
            errors.append({"accession": row["accession"], "error": "INDEX_ACCESSION_MISMATCH", "index_accession": parsed.get("accession")})
            continue
        subject_cik, filed_by_cik = parsed.get("subject_cik"), parsed.get("filed_by_cik")
        results.append({
            **row,
            "subject_cik": subject_cik,
            "subject_name": parsed.get("subject_name"),
            "filed_by_cik_index": filed_by_cik,
            "filed_by_name": parsed.get("filed_by_name"),
            "accepted_at": parsed.get("accepted_at"),
            "index_filing_date": parsed.get("filing_date"),
            "index_form": parsed.get("form"),
            "subject_is_target_candidate": bool(subject_cik and subject_cik in target_ciks),
            "filer_is_target_candidate": bool(row["filer_cik"] in target_ciks),
            "filer_subject_same": bool(subject_cik and filed_by_cik and subject_cik == filed_by_cik),
            "index_url": parsed.get("index_url"),
        })
        if i % 500 == 0:
            print(json.dumps({"stage": "INDEX_PROGRESS", "processed": i, "total": len(candidates),
                "subject_parsed": sum(bool(x["subject_cik"]) for x in results),
                "target_subject": sum(x["subject_is_target_candidate"] for x in results),
                "errors": len(errors)}), flush=True)

    subject_parsed = sum(bool(x["subject_cik"]) for x in results)
    filed_by_parsed = sum(bool(x["filed_by_cik_index"]) for x in results)
    target_subject = [x for x in results if x["subject_is_target_candidate"]]
    target_filer = [x for x in results if x["filer_is_target_candidate"]]
    known_accession = "0000092230-25-000015"
    known = next((x for x in results if x["accession"] == known_accession), None)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    fields = ["filer_cik", "filer_company_name", "form", "filing_date", "accession", "filename",
        "subject_cik", "subject_name", "filed_by_cik_index", "filed_by_name", "accepted_at",
        "index_filing_date", "index_form", "subject_is_target_candidate", "filer_is_target_candidate",
        "filer_subject_same", "index_url"]
    for name, rows in (("global_13dg_index_census.csv", results), ("target_subject_filings.csv", target_subject)):
        with (out / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({k: x.get(k) for k in fields} for x in rows)
    with (out / "target_universe_cik_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["ticker", "candidate_cik", "mapping_source"])
        writer.writeheader()
        for ticker in tickers:
            writer.writerow({"ticker": ticker, "candidate_cik": ticker_cik[ticker], "mapping_source": mapping_source[ticker]})

    summary = {
        "phase": "35_global_subject_census_pilot",
        "status": "COMPLETE_WITH_ERRORS" if errors else "COMPLETE",
        "quarter": f"{args.year}Q{args.quarter}",
        "master_index_url": master_url,
        "master_index_sha256": master_sha,
        "frozen_tickers": len(tickers),
        "current_candidate_ciks": len(target_ciks),
        "unresolved_tickers": unresolved,
        "master_index_13dg_candidates_raw": len(candidates_raw),
        "master_index_13dg_candidates_unique_accession": len(candidates),
        "duplicate_accessions_in_master_index": len(duplicate_accessions),
        "duplicate_accession_sample": duplicate_accessions[:20],
        "candidate_forms": dict(by_form),
        "index_pages_parsed": len(results),
        "index_fetch_errors": len(errors),
        "subject_cik_coverage": subject_parsed / len(candidates) if candidates else None,
        "filed_by_cik_coverage": filed_by_parsed / len(candidates) if candidates else None,
        "target_subject_filings": len(target_subject),
        "target_filer_filings": len(target_filer),
        "same_filer_subject_count": sum(x["filer_subject_same"] for x in results),
        "target_subject_by_form": dict(Counter(x["form"] for x in target_subject)),
        "target_filer_by_form": dict(Counter(x["form"] for x in target_filer)),
        "known_truist_federated_accession": {
            "accession": known_accession, "found": known is not None,
            "filer_cik": known.get("filed_by_cik_index") if known else None,
            "subject_cik": known.get("subject_cik") if known else None,
            "subject_name": known.get("subject_name") if known else None,
            "expected_subject_cik": "0001849998",
            "pass": bool(known and known.get("subject_cik") == "0001849998"
                         and known.get("filed_by_cik_index") == "0000092230"),
        },
        "knowledge_date_rule": "master-index filing date / filing-index filing date; accepted timestamp retained separately; no same-day signal assumed",
        "mapping_limitation": "Current SEC ticker map plus historical mapper is a candidate issuer-CIK list only; not historical active-universe membership.",
        "economic_group_status": "NOT_TESTED; filer and reporting-person identity are not economic-group identity.",
        "forward_returns_used": False,
        "errors_sample": errors[:30],
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)

    if not summary["known_truist_federated_accession"]["pass"]:
        raise RuntimeError("Known Truist/Federated subject-vs-filer validation fixture failed")
    if summary["subject_cik_coverage"] is None or summary["subject_cik_coverage"] < 0.95:
        raise RuntimeError("Subject CIK coverage below 95% pilot gate")

if __name__ == "__main__":
    main()

"""Global EDGAR Schedule 13D/G subject-issuer census feasibility pilot."""
from __future__ import annotations
import argparse, ast, csv, gzip, hashlib, json, random, re, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from phase35_13dg_parser_v3 import parse_index, parse_master_index

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_EXCHANGE = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_MUTUAL_FUNDS = "https://www.sec.gov/files/company_tickers_mf.json"
MAPPER = "https://raw.githubusercontent.com/jadchaar/sec-cik-mapper/main/mappings/stocks/ticker_to_cik.json"
SEC_UA = "NuevaEstrategia quantitative research jose.felix@felixsarmiento.com"
SEC_INTERVAL = 0.16
FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
KNOWN_ACCESSION = "0000092230-25-000015"
_last_sec_request = 0.0

def fetch_bytes(url, sec=False, timeout=60, retries=6):
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
            try: delay = float(retry_after) if retry_after else min(45, 2 ** attempt)
            except Exception: delay = min(45, 2 ** attempt)
            time.sleep(delay + random.uniform(0.1, 0.6))
        except Exception as exc:
            last_error = exc
            time.sleep(min(30, 2 ** attempt) + random.uniform(0.1, 0.6))
    raise RuntimeError(f"GET failed after retries: {url}: {last_error}")

def records(data):
    if isinstance(data, dict):
        fields = data.get("fields")
        rows = data.get("data")
        if isinstance(fields, list) and isinstance(rows, list):
            return [dict(zip(fields, row)) if isinstance(row, (list, tuple)) else row
                    for row in rows if isinstance(row, (list, tuple, dict))]
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        return [v for v in data.values() if isinstance(v, dict)]
    return data if isinstance(data, list) and all(isinstance(x, dict) for x in data) else []

def cik_norm(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits else None

def variants(ticker):
    xs = [ticker]
    if "." in ticker: xs.append(ticker.replace(".", "-"))
    if "-" in ticker: xs.append(ticker.replace("-", "."))
    return list(dict.fromkeys(xs))

def load_universe():
    tree = ast.parse(Path("Nueva_Estrategia_Fase0_Descubrimiento.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DEFAULT_UNIVERSE" for t in node.targets):
            tickers = sorted({str(x).strip().upper() for x in ast.literal_eval(node.value)})
            if len(tickers) != 335: raise RuntimeError(f"Expected 335 frozen tickers, got {len(tickers)}")
            return tickers
    raise RuntimeError("DEFAULT_UNIVERSE not found")

def current_cik_candidates(tickers):
    sec_map = defaultdict(lambda: {"ciks": set(), "sources": set(), "fund_classes": []})
    def add(ticker, cik, source, fund=None):
        if not ticker or not cik: return
        ticker = str(ticker).strip().upper()
        cik = cik_norm(cik)
        if not ticker or not cik: return
        sec_map[ticker]["ciks"].add(cik)
        sec_map[ticker]["sources"].add(source)
        if fund: sec_map[ticker]["fund_classes"].append(fund)
    for row in records(json.loads(fetch_bytes(SEC_TICKERS, sec=True).decode())):
        add(row.get("ticker"), row.get("cik_str") or row.get("cik"), "company_tickers")
    for row in records(json.loads(fetch_bytes(SEC_EXCHANGE, sec=True).decode())):
        add(row.get("ticker"), row.get("cik") or row.get("cik_str"), "company_tickers_exchange")
    for row in records(json.loads(fetch_bytes(SEC_MUTUAL_FUNDS, sec=True).decode())):
        ticker = row.get("ticker") or row.get("classTicker") or row.get("class_ticker")
        add(ticker, row.get("cik") or row.get("cik_str"), "company_tickers_mf", {
            "seriesId": row.get("seriesId") or row.get("series_id"),
            "classId": row.get("classId") or row.get("class_id"),
            "seriesName": row.get("seriesName") or row.get("series_name"),
            "className": row.get("className") or row.get("class_name")})
    mapper = json.loads(fetch_bytes(MAPPER).decode())
    details, cik_to_tickers, unresolved = {}, defaultdict(set), []
    for ticker in tickers:
        found = None
        for alias in variants(ticker):
            if sec_map.get(alias) and sec_map[alias]["ciks"]:
                found = (sec_map[alias], alias)
                break
        if found is None:
            for alias in variants(ticker):
                if mapper.get(alias):
                    found = ({"ciks": {cik_norm(mapper[alias])}, "sources": {"sec_cik_mapper_fallback"}, "fund_classes": []}, alias)
                    break
        if found is None:
            unresolved.append(ticker)
            details[ticker] = {"ciks": [], "sources": [], "alias_used": None, "fund_classes": []}
            continue
        obj, alias = found
        ciks = sorted(x for x in obj["ciks"] if x)
        for cik in ciks: cik_to_tickers[cik].add(ticker)
        details[ticker] = {"ciks": ciks, "sources": sorted(obj["sources"]), "alias_used": alias, "fund_classes": obj["fund_classes"]}
    return details, {k: sorted(v) for k, v in cik_to_tickers.items()}, unresolved

def group_rows(rows):
    groups = {}
    for row in rows:
        a = row["accession"]
        g = groups.setdefault(a, {"accession": a, "entities": {}, "forms": set(), "dates": set(), "rows": 0, "filenames": []})
        g["entities"][row["master_index_cik"]] = row["master_index_company_name"]
        g["forms"].add(row["form"]); g["dates"].add(row["filing_date"])
        g["rows"] += 1; g["filenames"].append(row["filename"])
    out = []
    for a, g in groups.items():
        ciks, forms, dates = sorted(g["entities"]), sorted(g["forms"]), sorted(g["dates"])
        out.append({"accession": a, "master_index_ciks": ciks, "master_index_names": g["entities"],
                    "master_index_row_count": g["rows"], "master_index_filenames": sorted(set(g["filenames"])),
                    "form": forms[0] if len(forms)==1 else None, "filing_date": dates[0] if len(dates)==1 else None,
                    "metadata_conflict": len(forms)!=1 or len(dates)!=1, "single_cik_accession": len(ciks)==1})
    return sorted(out, key=lambda x: (x["filing_date"] or "", x["accession"]))

def select_groups(groups, target_ciks, per_form=50):
    relevant = [g for g in groups if set(g["master_index_ciks"]) & target_ciks]
    other = [g for g in groups if not (set(g["master_index_ciks"]) & target_ciks)]
    rng, sample = random.Random(20261103), []
    for form in sorted(FORMS):
        pool = [g for g in other if g["form"] == form]
        sample.extend(rng.sample(pool, min(per_form, len(pool))))
    sample.extend(g for g in other if g["single_cik_accession"])
    sample = list({g["accession"]: g for g in sample}.values())
    return relevant, sorted(sample, key=lambda x: x["accession"])

def index_urls(group):
    accession, nodash = group["accession"], group["accession"].replace("-", "")
    ciks = list(group["master_index_ciks"]) + [accession.split("-")[0]]
    urls = []
    for cik in dict.fromkeys(ciks):
        try: archive_cik = str(int(cik))
        except Exception: continue
        base = f"https://www.sec.gov/Archives/edgar/data/{archive_cik}/{nodash}/{accession}-index"
        urls.extend([base+".htm", base+".html"])
    return urls

def fetch_index(group):
    errors = []
    for url in index_urls(group):
        try:
            parsed = parse_index(fetch_bytes(url, sec=True, timeout=45, retries=5))
            if parsed.get("accession") != group["accession"]:
                errors.append("ACCESSION_MISMATCH"); continue
            parsed["index_url"] = url
            return parsed, None
        except HTTPError as exc:
            if exc.code == 404: errors.append("404"); continue
            return None, f"HTTP{exc.code}"
        except Exception as exc:
            return None, f"{type(exc).__name__}:{exc}"
    return None, ";".join(errors[-4:]) or "INDEX_NOT_FOUND"

def normalize_form(value):
    value = " ".join((value or "").upper().split())
    return "SC " + value[len("SCHEDULE "):] if value.startswith("SCHEDULE ") else value

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--quarter", type=int, default=1, choices=(1,2,3,4))
    ap.add_argument("--output", default="phase35_global_subject_census_pilot")
    ap.add_argument("--sample-per-form", type=int, default=50)
    args = ap.parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    tickers = load_universe()
    ticker_map, cik_to_tickers, unresolved = current_cik_candidates(tickers)
    target_ciks = set(cik_to_tickers)
    master_url = f"https://www.sec.gov/Archives/edgar/full-index/{args.year}/QTR{args.quarter}/master.idx"
    master = fetch_bytes(master_url, sec=True, timeout=120)
    master_sha = hashlib.sha256(master).hexdigest()
    (out/"master.idx.gz").write_bytes(gzip.compress(master, compresslevel=9))
    rows = parse_master_index(master)
    groups = group_rows(rows)
    relevant, sample = select_groups(groups, target_ciks, args.sample_per_form)
    fetch = {g["accession"]: {**g,"target_relevant":True,"validation_sample":False} for g in relevant}
    for g in sample: fetch.setdefault(g["accession"], {**g,"target_relevant":False,"validation_sample":True})
    known_group = next((g for g in groups if g["accession"] == KNOWN_ACCESSION), None)
    if known_group:
        fetch.setdefault(KNOWN_ACCESSION, {**known_group,"target_relevant":bool(set(known_group["master_index_ciks"])&target_ciks),
                                          "validation_sample":False,"known_fixture_extra":True})
    raw_text = master.decode("latin-1","replace")
    lines = raw_text.splitlines()
    form_counts = Counter()
    for line in lines:
        p = line.split("|",4)
        if len(p)==5: form_counts[" ".join(p[2].strip().upper().split())]+=1
    group_sizes = Counter(len(g["master_index_ciks"]) for g in groups)
    (out/"master_index_diagnostics.json").write_text(json.dumps({
        "bytes":len(master),"lines":len(lines),"raw_13dg_rows":len(rows),"unique_accessions":len(groups),
        "raw_form_counts":dict(form_counts),"group_size_distribution":dict(group_sizes),
        "single_cik_examples":[g for g in groups if g["single_cik_accession"]][:20]},indent=2),encoding="utf-8")
    with (out/"ticker_cik_candidates.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=["ticker","candidate_ciks","mapping_sources","alias_used","fund_classes"]);w.writeheader()
        for t,d in ticker_map.items():
            w.writerow({"ticker":t,"candidate_ciks":";".join(d["ciks"]),"mapping_sources":";".join(d["sources"]),
                        "alias_used":d["alias_used"] or "","fund_classes":json.dumps(d["fund_classes"],sort_keys=True)})
    results, errors = [], []
    for i,g in enumerate(sorted(fetch.values(),key=lambda x:x["accession"]),1):
        parsed,err=fetch_index(g)
        if err:
            errors.append({"accession":g["accession"],"error":err,"target_relevant":g["target_relevant"],"validation_sample":g["validation_sample"]})
            continue
        pair=set(g["master_index_ciks"]); sub=parsed.get("subject_cik"); filer=parsed.get("filed_by_cik")
        results.append({
            "accession":g["accession"],"form":g["form"],"filing_date":g["filing_date"],
            "master_index_ciks":";".join(g["master_index_ciks"]),
            "master_index_names":json.dumps(g["master_index_names"],sort_keys=True),
            "master_index_row_count":g["master_index_row_count"],"metadata_conflict":g["metadata_conflict"],
            "subject_cik":sub,"subject_name":parsed.get("subject_name"),
            "filed_by_cik":filer,"filed_by_name":parsed.get("filed_by_name"),
            "accepted_at":parsed.get("accepted_at"),"index_filing_date":parsed.get("filing_date"),
            "index_form":parsed.get("form"),"index_form_match":normalize_form(parsed.get("form"))==g["form"],
            "index_filing_date_match":parsed.get("filing_date")==g["filing_date"],
            "subject_in_master_pair":bool(sub and sub in pair),"filed_by_in_master_pair":bool(filer and filer in pair),
            "both_roles_in_master_pair":bool(sub and filer and sub in pair and filer in pair),
            "subject_is_target_candidate":bool(sub and sub in target_ciks),
            "filed_by_is_target_candidate":bool(filer and filer in target_ciks),
            "target_relevant":g["target_relevant"],"validation_sample_non_target":g["validation_sample"],
            "index_url":parsed.get("index_url")})
        if i%250==0:
            print(json.dumps({"stage":"INDEX_PROGRESS","processed":i,"total":len(fetch),
                "subject_parsed":sum(bool(x["subject_cik"]) for x in results),"errors":len(errors)}),flush=True)
    fields=list(results[0].keys()) if results else ["accession","form","filing_date","subject_cik","filed_by_cik"]
    outputs=[
        ("global_subject_census_fetched.csv",results),
        ("target_subject_filings.csv",[x for x in results if x["subject_is_target_candidate"]]),
        ("target_filer_filings.csv",[x for x in results if x["filed_by_is_target_candidate"]]),
        ("target_filer_only_cross_issuer.csv",[x for x in results if x["filed_by_is_target_candidate"] and not x["subject_is_target_candidate"]])]
    for name,subset in outputs:
        with (out/name).open("w",newline="",encoding="utf-8") as h:
            w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(subset)
    rel=[x for x in results if x["target_relevant"]]
    sam=[x for x in results if x["validation_sample_non_target"]]
    pair=[x for x in results if len(x["master_index_ciks"].split(";"))>=2 and x["subject_cik"] and x["filed_by_cik"]]
    cov=lambda xs,key,den: sum(bool(x[key]) for x in xs)/den if den else None
    subj_rel=cov(rel,"subject_cik",len(relevant)); filer_rel=cov(rel,"filed_by_cik",len(relevant))
    subj_sam=cov(sam,"subject_cik",len(sample)); filer_sam=cov(sam,"filed_by_cik",len(sample))
    pair_cov=sum(x["both_roles_in_master_pair"] for x in pair)/len(pair) if pair else None
    target_subject=[x for x in results if x["subject_is_target_candidate"]]
    target_filer=[x for x in results if x["filed_by_is_target_candidate"]]
    known=next((x for x in results if x["accession"]==KNOWN_ACCESSION),None)
    known_check={"found":known is not None,"filed_by_cik":known.get("filed_by_cik") if known else None,
                 "subject_cik":known.get("subject_cik") if known else None,
                 "pass":bool(known and known.get("filed_by_cik")=="0000092230" and known.get("subject_cik")=="0001849998")}
    error_rate=len(errors)/len(fetch) if fetch else 1.0
    passed=bool(len(relevant)>=100 and subj_rel is not None and subj_rel>=.95 and filer_rel is not None and filer_rel>=.95
                and subj_sam is not None and subj_sam>=.95 and filer_sam is not None and filer_sam>=.95
                and pair_cov is not None and pair_cov>=.95 and error_rate<=.05 and known_check["pass"])
    summary={
        "phase":"35_global_subject_census_pilot","status":"PASS" if passed else "FAILED_VALIDATION",
        "quarter":f"{args.year}Q{args.quarter}","master_index_url":master_url,"master_index_sha256":master_sha,
        "master_index_bytes":len(master),"master_index_lines":len(lines),"raw_13dg_rows":len(rows),
        "unique_13dg_accessions":len(groups),"group_size_distribution":dict(group_sizes),
        "unique_accessions_by_form":dict(Counter(g["form"] for g in groups if g["form"])),
        "frozen_tickers":len(tickers),"current_candidate_ciks":len(target_ciks),"unresolved_tickers":unresolved,
        "target_relevant_accessions":len(relevant),"validation_sample_non_target":len(sample),"pages_requested":len(fetch),
        "index_pages_parsed":len(results),"index_fetch_errors":len(errors),"index_fetch_error_rate":error_rate,
        "subject_cik_coverage_target_relevant":subj_rel,"filed_by_cik_coverage_target_relevant":filer_rel,
        "subject_cik_coverage_validation_sample":subj_sam,"filed_by_cik_coverage_validation_sample":filer_sam,
        "master_index_pair_both_roles_coverage":pair_cov,"target_subject_filings":len(target_subject),
        "target_filer_filings":len(target_filer),
        "target_filer_only_cross_issuer":sum(x["filed_by_is_target_candidate"] and not x["subject_is_target_candidate"] for x in results),
        "target_subject_by_form":dict(Counter(x["form"] for x in target_subject)),
        "target_filer_by_form":dict(Counter(x["form"] for x in target_filer)),
        "known_truist_federated_fixture":known_check,
        "knowledge_date_rule":"SEC filing date; Accepted timestamp retained separately; no same-day signal assumed.",
        "mapping_limitation":"Current SEC ticker/exchange/mutual-fund maps plus fallback are candidate mappings, not historical active-universe membership.",
        "economic_group_status":"NOT_TESTED; master-index CIK pairs are candidate entities, not economic groups.",
        "forward_returns_used":False,"errors_sample":errors[:50],"audit_timestamp_utc":datetime.now(timezone.utc).isoformat()}
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)
    if not passed: raise RuntimeError("Global subject-census pilot validation failed; inspect summary.json and master_index_diagnostics.json")

if __name__ == "__main__":
    main()

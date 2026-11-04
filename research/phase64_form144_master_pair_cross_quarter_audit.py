#!/usr/bin/env python3
"""Cross-quarter SEC Form 144 master-index CIK-pair identity audit.

A unique current-universe CIK in the accession's master-index pair is only a
candidate. The primary XML must confirm that it is issuerCik, not filer CIK.
This is a source/identity audit; it calculates no forward returns.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError
from research.phase50_form144_global_index_pilot import (
    SEC_ARCHIVES, current_cik_candidates, fetch_bytes, load_universe,
    norm_cik, parse_form144_xml, parse_master_index,
)

DEFAULT_QUARTERS = ("2023Q2", "2024Q1", "2024Q4", "2025Q1", "2025Q4", "2026Q1")
OUT_DIR = Path("phase64_form144_master_pair_audit")

def parse_quarter(value):
    m = re.fullmatch(r"(20\d{2})Q([1-4])", value.strip().upper())
    if not m:
        raise ValueError("Invalid quarter: " + value)
    return int(m.group(1)), int(m.group(2))

def stable_key(row):
    return hashlib.sha256((str(row["year"]) + "Q" + str(row["quarter"]) + ":" + row["accession"]).encode()).hexdigest()

def build_pair_rows(index_rows, candidate_ciks, cik_to_tickers, year, quarter):
    out = []
    for src in index_rows:
        row = dict(src)
        pair = sorted({norm_cik(x) for x in (row.get("master_index_ciks") or []) if norm_cik(x)})
        candidates = sorted(set(pair) & candidate_ciks)
        row.update({
            "year": year, "quarter": quarter, "master_index_ciks": pair,
            "pair_size": len(pair), "candidate_ciks_in_pair": candidates,
            "candidate_count_in_pair": len(candidates),
            "candidate_tickers": sorted({t for c in candidates for t in cik_to_tickers.get(c, [])}),
            "pair_class": "unique_candidate" if len(candidates) == 1 else ("ambiguous" if len(candidates) > 1 else "control"),
        })
        out.append(row)
    return out

def select_pair_sample(rows, target_per_form=25, control_per_form=25, ambiguous_per_form=5):
    out = []
    for form in ("144", "144/A"):
        pool = [r for r in rows if r.get("form") == form]
        for cls, limit in (("unique_candidate", target_per_form), ("control", control_per_form), ("ambiguous", ambiguous_per_form)):
            for row in sorted((r for r in pool if r["pair_class"] == cls), key=stable_key)[:limit]:
                item = dict(row)
                item["sample_stratum"] = cls
                out.append(item)
    return sorted(out, key=lambda r: (r["year"], r["quarter"], r.get("form") or "", r["accession"]))

def primary_xml_urls(row):
    no_dash = row["accession"].replace("-", "")
    return [f"{SEC_ARCHIVES}/{int(cik)}/{no_dash}/primary_doc.xml" for cik in sorted(row.get("master_index_ciks") or [])]

def fetch_pair_xml(row):
    errors = []
    for url in primary_xml_urls(row):
        try:
            return parse_form144_xml(fetch_bytes(url, sec=True, timeout=45, retries=4)), url, None
        except HTTPError as e:
            errors.append("HTTP" + str(e.code))
        except Exception as e:
            errors.append(type(e).__name__ + ":" + str(e))
    return None, None, ";".join(errors[-8:]) or "PRIMARY_XML_NOT_FOUND"

def classify_xml_identity(row, xml):
    pair = set(row.get("master_index_ciks") or [])
    issuer, filer = norm_cik(xml.get("issuer_cik")), norm_cik(xml.get("filer_cik"))
    candidates = row.get("candidate_ciks_in_pair") or []
    role = "none"
    if len(candidates) == 1:
        role = "issuer" if candidates[0] == issuer else ("filer" if candidates[0] == filer else "unresolved")
    elif len(candidates) > 1:
        role = "ambiguous"
    return {
        "xml_issuer_cik": issuer or "", "xml_filer_cik": filer or "",
        "issuer_in_master_pair": bool(issuer and issuer in pair),
        "filer_in_master_pair": bool(filer and filer in pair),
        "both_xml_ciks_in_pair": bool(issuer and filer and issuer != filer and issuer in pair and filer in pair),
        "xml_ciks_distinct": bool(issuer and filer and issuer != filer),
        "xml_form_matches_index": xml.get("submission_type") == row.get("form"),
        "unique_candidate_role": role,
        "xml_issuer_name": xml.get("issuer_name") or "",
        "xml_seller_name": xml.get("seller_name") or "",
    }

def wilson_lower_bound(successes, total, z=1.96):
    if total <= 0:
        return None
    p = successes / total
    d = 1 + z*z/total
    return max(0.0, (p + z*z/(2*total) - z*((p*(1-p)/total + z*z/(4*total*total))**0.5))/d)

def audit_quarter(year, quarter, candidate_ciks, cik_to_tickers, target_n, control_n, workers):
    url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
    rows = build_pair_rows(parse_master_index(fetch_bytes(url, sec=True, timeout=90, retries=5)),
                           candidate_ciks, cik_to_tickers, year, quarter)
    sample = select_pair_sample(rows, target_n, control_n)
    details, errors = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_pair_xml, r): r for r in sample}
        for future in as_completed(futures):
            r = futures[future]
            try:
                xml, xml_url, error = future.result()
            except Exception as e:
                xml, xml_url, error = None, None, type(e).__name__ + ":" + str(e)
            if xml is None:
                errors.append({"quarter": f"{year}Q{quarter}", "accession": r["accession"],
                               "form": r.get("form"), "sample_stratum": r["sample_stratum"], "error": error})
                continue
            d = {
                "quarter": f"{year}Q{quarter}", "accession": r["accession"], "form": r.get("form"),
                "filing_date": r.get("filing_date"), "master_index_ciks": ";".join(r["master_index_ciks"]),
                "pair_size": r["pair_size"], "candidate_ciks_in_pair": ";".join(r["candidate_ciks_in_pair"]),
                "candidate_count_in_pair": r["candidate_count_in_pair"],
                "candidate_tickers": ";".join(r["candidate_tickers"]),
                "sample_stratum": r["sample_stratum"], "xml_url": xml_url,
            }
            d.update(classify_xml_identity(r, xml))
            details.append(d)
    by_form = {}
    for form in ("144", "144/A"):
        sub = [r for r in details if r["form"] == form]
        targets = [r for r in sub if r["sample_stratum"] == "unique_candidate"]
        controls = [r for r in sub if r["sample_stratum"] == "control"]
        ok = sum(r["unique_candidate_role"] == "issuer" for r in targets)
        by_form[form] = {
            "xml_rows": len(sub), "target_unique_candidate_rows": len(targets),
            "target_candidate_is_issuer": ok,
            "target_candidate_is_filer": sum(r["unique_candidate_role"] == "filer" for r in targets),
            "target_candidate_unresolved": sum(r["unique_candidate_role"] == "unresolved" for r in targets),
            "target_issuer_rate": ok/len(targets) if targets else None,
            "target_issuer_wilson_95_lower": wilson_lower_bound(ok, len(targets)),
            "control_rows": len(controls),
            "control_both_xml_ciks_in_pair": sum(r["both_xml_ciks_in_pair"] for r in controls),
            "both_xml_ciks_in_pair_all_rows": sum(r["both_xml_ciks_in_pair"] for r in sub),
            "xml_form_matches_index": sum(r["xml_form_matches_index"] for r in sub),
        }
    summary = {
        "quarter": f"{year}Q{quarter}", "master_index_accessions": len(rows),
        "accessions_by_form": dict(Counter(r.get("form") for r in rows)),
        "pair_size_distribution": dict(Counter(str(r["pair_size"]) for r in rows)),
        "candidate_count_distribution_by_form": {
            f: dict(Counter(str(r["candidate_count_in_pair"]) for r in rows if r.get("form") == f))
            for f in ("144", "144/A")
        },
        "unique_candidate_pairs_by_form": {
            f: sum(r.get("form") == f and r["candidate_count_in_pair"] == 1 for r in rows)
            for f in ("144", "144/A")
        },
        "ambiguous_candidate_pairs_by_form": {
            f: sum(r.get("form") == f and r["candidate_count_in_pair"] > 1 for r in rows)
            for f in ("144", "144/A")
        },
        "xml_sample_requested": len(sample), "xml_sample_parsed": len(details),
        "xml_sample_errors": len(errors), "xml_sample_by_form": by_form,
    }
    return summary, details, errors

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0]), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quarters", default=",".join(DEFAULT_QUARTERS))
    p.add_argument("--target-per-form", type=int, default=25)
    p.add_argument("--control-per-form", type=int, default=25)
    p.add_argument("--workers", type=int, default=5)
    p.add_argument("--output", default=str(OUT_DIR))
    a = p.parse_args()
    tickers = load_universe()
    ticker_details, cik_to_tickers, unresolved, mapping_errors = current_cik_candidates(tickers)
    candidate_ciks = set(cik_to_tickers)
    q_summaries, all_details, all_errors = [], [], []
    for token in filter(None, (x.strip() for x in a.quarters.split(","))):
        year, quarter = parse_quarter(token)
        s, d, e = audit_quarter(year, quarter, candidate_ciks, cik_to_tickers,
                                a.target_per_form, a.control_per_form, a.workers)
        q_summaries.append(s); all_details.extend(d); all_errors.extend(e)
        print(json.dumps({"stage": "QUARTER_COMPLETE", "summary": s}, sort_keys=True), flush=True)
    overall = {}
    for form in ("144", "144/A"):
        sub = [r for r in all_details if r["form"] == form]
        targets = [r for r in sub if r["sample_stratum"] == "unique_candidate"]
        controls = [r for r in sub if r["sample_stratum"] == "control"]
        ok = sum(r["unique_candidate_role"] == "issuer" for r in targets)
        overall[form] = {
            "xml_rows": len(sub), "unique_candidate_target_rows": len(targets),
            "unique_candidate_is_issuer": ok,
            "unique_candidate_is_filer": sum(r["unique_candidate_role"] == "filer" for r in targets),
            "unique_candidate_unresolved": sum(r["unique_candidate_role"] == "unresolved" for r in targets),
            "issuer_rate": ok/len(targets) if targets else None,
            "issuer_wilson_95_lower": wilson_lower_bound(ok, len(targets)),
            "control_rows": len(controls),
            "control_pair_concordance": sum(r["both_xml_ciks_in_pair"] for r in controls)/len(controls) if controls else None,
            "both_xml_ciks_rate_all_rows": sum(r["both_xml_ciks_in_pair"] for r in sub)/len(sub) if sub else None,
            "xml_form_match_rate": sum(r["xml_form_matches_index"] for r in sub)/len(sub) if sub else None,
        }
    x, y = overall["144"], overall["144/A"]
    gates = {
        "at_least_300_current_candidate_ciks": len(candidate_ciks) >= 300,
        "at_least_100_form144_target_xml_rows": x["unique_candidate_target_rows"] >= 100,
        "form144_issuer_rate_ge_98pct": x["issuer_rate"] is not None and x["issuer_rate"] >= .98,
        "form144_wilson_lower_ge_95pct": x["issuer_wilson_95_lower"] is not None and x["issuer_wilson_95_lower"] >= .95,
        "at_least_20_form144a_target_xml_rows": y["unique_candidate_target_rows"] >= 20,
        "form144a_issuer_rate_ge_95pct": y["issuer_rate"] is not None and y["issuer_rate"] >= .95,
        "form144a_wilson_lower_ge_80pct": y["issuer_wilson_95_lower"] is not None and y["issuer_wilson_95_lower"] >= .80,
        "both_xml_ciks_in_pair_ge_98pct": all(overall[f]["both_xml_ciks_rate_all_rows"] is not None and overall[f]["both_xml_ciks_rate_all_rows"] >= .98 for f in ("144", "144/A")),
        "xml_form_match_ge_98pct": all(overall[f]["xml_form_match_rate"] is not None and overall[f]["xml_form_match_rate"] >= .98 for f in ("144", "144/A")),
        "no_xml_fetch_errors": len(all_errors) == 0,
    }
    passed = all(gates.values())
    summary = {
        "phase": "64-form144-master-pair-cross-quarter-audit", "status": "COMPLETE",
        "data_gate": "PASS" if passed else "FAIL",
        "quarters": [s["quarter"] for s in q_summaries],
        "frozen_universe_size": len(tickers),
        "current_tickers_with_cik_mapping": sum(bool(ticker_details[t]["ciks"]) for t in tickers),
        "current_candidate_cik_count": len(candidate_ciks), "unresolved_tickers": unresolved,
        "mapping_source_errors": mapping_errors, "overall_by_form": overall,
        "quarter_summaries": q_summaries, "gate_checks": gates,
        "historical_pit_universe_gate": "NOT_TESTED", "economic_test_authorized": False,
        "knowledge_date_rule": "Use the first full trading-session close after SEC filing_date; never same-date. This is conservative until accepted-time history is separately validated.",
        "identity_rule": "A unique current-universe CIK in the master-index pair is only a candidate; primary XML issuerCik confirms issuer role. XML filer CIK is not issuer identity.",
        "amendment_rule": "previousAccessionNumber is a prior-filing reference, not necessarily the immediately preceding amendment; event lineage remains separate.",
        "mapping_limitation": "Current ticker/CIK mappings are not historical active-universe membership; unresolved tickers and legacy/corporate identity cases remain uncovered.",
        "forward_returns_used": False, "xml_error_count": len(all_errors),
    }
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    write_csv(out/"xml_pair_validation.csv", all_details)
    write_csv(out/"xml_fetch_errors.csv", all_errors)
    print(json.dumps(summary, indent=2), flush=True)
    if not passed:
        raise RuntimeError("Phase 64 master-pair gate failed; inspect summary.json")

if __name__ == "__main__":
    main()

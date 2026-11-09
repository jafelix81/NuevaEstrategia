#!/usr/bin/env python3
"""Conservative Form 144 -> Form 4 execution-conversion audit; no return testing."""
import argparse, csv, hashlib, json, re, zipfile, io
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"
CUTOFF = date(2026, 9, 24)
SNAPSHOT_END = date(2026, 9, 30)

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def cik(x):
    x = (x or "").strip()
    return x.lstrip("0") or ("0" if x else "")

def name(x):
    return re.sub(r"[^A-Z0-9]", "", (x or "").upper())

def cls(x):
    return re.sub(r"[^A-Z0-9]", "", (x or "").upper())

def family(x):
    x = cls(x)
    for c in "ABCD":
        if "CLASS" + c in x: return "CLASS_" + c
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if "SERIES" + c in x: return "SERIES_" + c
    if "PREFERRED" in x: return "PREFERRED"
    if "ORDINARY" in x: return "ORDINARY"
    if "DEPOSITARY" in x or x.startswith("ADS"): return "DEPOSITARY"
    if "COMMON" in x or "COMMSTOCK" in x: return "COMMON"
    return "OTHER:" + x if x else "UNKNOWN"

def iso(x):
    try: return date.fromisoformat((x or "").strip())
    except ValueError: return None

def secdate(x):
    try: return datetime.strptime((x or "").strip().upper(), "%d-%b-%Y").date()
    except ValueError: return None

def dec(x):
    try: return Decimal((x or "").strip().replace(",", ""))
    except (InvalidOperation, AttributeError): return None

def qtile(v, p):
    v = sorted(v)
    if not v: return None
    k = (len(v) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] * (1 - (k - lo)) + v[hi] * (k - lo)

def tsv(z, member):
    with z.open(member) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), delimiter="\t")

def form144_data(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    originals = [r for r in rows if r.get("quarter") == "2026Q3" and r.get("form") == "144"
                 and r.get("include_as_issuer_event", "").lower() == "true"]
    events, latest, plan = defaultdict(list), {}, {}
    for r in originals:
        acc, icik, seller = r.get("accession", ""), cik(r.get("xml_issuer_cik", "")), name(r.get("seller_name", ""))
        if not acc or not icik or not seller: continue
        try: tranches = json.loads(r.get("sale_tranches_json") or "[]")
        except json.JSONDecodeError: tranches = []
        parsed = []
        for t in tranches:
            d, units = iso(t.get("approx_sale_date_iso", "")), dec(str(t.get("units_numeric", "")))
            if d is None or units is None or units <= 0: continue
            parsed.append({"accession": acc, "idx": str(t.get("sale_tranche_index", "")),
                "issuer": icik, "seller": seller, "date": d, "units": units,
                "class_norm": cls(t.get("security_class", "")), "class_family": family(t.get("security_class", "")),
                "plan": bool((r.get("plan_adoption_dates") or "").strip())})
        if parsed:
            events[acc].extend(parsed); latest[acc] = max(x["date"] for x in parsed)
            plan[acc] = bool((r.get("plan_adoption_dates") or "").strip())
    eligible = {a for a, d in latest.items() if d <= CUTOFF}
    tranches = [t for a in eligible for t in events[a]]
    return rows, originals, eligible, tranches, plan

def form4_blocks(path):
    with zipfile.ZipFile(path) as z:
        subs = list(tsv(z, "SUBMISSION.tsv"))
        owners = list(tsv(z, "REPORTINGOWNER.tsv"))
        trans = list(tsv(z, "NONDERIV_TRANS.tsv"))
    smap, dates = {}, []
    for r in subs:
        a = r.get("ACCESSION_NUMBER", "")
        if a: smap[a] = r
        d = secdate(r.get("FILING_DATE", ""))
        if d: dates.append(d)
    owner_map = defaultdict(dict)
    for r in owners:
        a, ocik = r.get("ACCESSION_NUMBER", ""), cik(r.get("RPTOWNERCIK", ""))
        if a and ocik: owner_map[a][ocik] = r.get("RPTOWNERNAME", "")
    seen, blocks = set(), {}
    for r in trans:
        a, sk = r.get("ACCESSION_NUMBER", ""), r.get("NONDERIV_TRANS_SK", "")
        if (a, sk) in seen: continue
        seen.add((a, sk))
        s = smap.get(a)
        if not s or s.get("DOCUMENT_TYPE") != "4" or r.get("TRANS_FORM_TYPE") != "4": continue
        if r.get("TRANS_CODE") != "S" or r.get("TRANS_ACQUIRED_DISP_CD") != "D": continue
        if r.get("TRANS_TIMELINESS") == "L" or len(owner_map.get(a, {})) != 1: continue
        icik, owner = cik(s.get("ISSUERCIK", "")), name(next(iter(owner_map[a].values())))
        td, fd, shares = secdate(r.get("TRANS_DATE", "")), secdate(s.get("FILING_DATE", "")), dec(r.get("TRANS_SHARES", ""))
        if not icik or not owner or td is None or fd is None or shares is None or shares <= 0: continue
        lag = (fd - td).days
        if lag < 0 or lag > 4: continue
        key = (icik, owner, td, fd, a)
        b = blocks.setdefault(key, {"issuer": icik, "owner": owner, "date": td, "filing": fd,
            "accession": a, "shares": Decimal("0"), "titles": set(), "lag": lag,
            "flag": s.get("AFF10B5ONE", "")})
        b["shares"] += shares
        if r.get("SECURITY_TITLE"): b["titles"].add(r["SECURITY_TITLE"])
    out = []
    for b in blocks.values():
        titles = sorted(b["titles"])
        b["class_norm"] = cls(titles[0]) if len(titles) == 1 else ""
        b["class_family"] = family(titles[0]) if len(titles) == 1 else "MULTI_OR_UNKNOWN"
        out.append(b)
    return subs, trans, dates, out, len(seen)

def match(tranches, blocks, lo, hi):
    ix = defaultdict(list)
    for b in blocks: ix[(b["issuer"], b["owner"])].append(b)
    cand = []
    for t in tranches:
        for b in ix.get((t["issuer"], t["seller"]), []):
            diff = (b["date"] - t["date"]).days
            if lo <= diff <= hi:
                cand.append({"t": t, "b": b, "diff": diff,
                    "ratio": float(b["shares"] / t["units"]), "exact_qty": b["shares"] == t["units"]})
    td = Counter((x["t"]["accession"], x["t"]["idx"]) for x in cand)
    bd = Counter((x["b"]["accession"], x["b"]["date"]) for x in cand)
    unique = [x for x in cand if td[(x["t"]["accession"], x["t"]["idx"])] == 1
              and bd[(x["b"]["accession"], x["b"]["date"])] == 1]
    return cand, unique

def flag(x):
    x = (x or "").strip().lower()
    return True if x in {"1", "true"} else False if x in {"0", "false"} else None

def audit(f144_path, f4_path):
    h144, h4 = sha(f144_path), sha(f4_path)
    if h144 != FORM144_SHA or h4 != FORM4_SHA: raise ValueError("Immutable input SHA-256 mismatch")
    rows, originals, eligible, tr, plan = form144_data(f144_path)
    subs, rawtx, filing_dates, blocks, unique_tx_keys = form4_blocks(f4_path)
    maxfd = max(filing_dates).isoformat()
    if maxfd != SNAPSHOT_END.isoformat(): raise ValueError("Unexpected Form 4 snapshot end")
    pc, post = match(tr, blocks, 0, 2)
    nc, pre = match(tr, blocks, -2, -1)
    exact = [x for x in post if x["diff"] == 0 and x["exact_qty"]]
    same = [x for x in post if x["diff"] == 0]
    within = [x for x in post if 0.8 <= x["ratio"] <= 1.2]
    checked = [x for x in exact if x["t"]["class_family"] != "UNKNOWN" and x["b"]["class_family"] != "MULTI_OR_UNKNOWN"]
    agree = [x for x in checked if x["t"]["class_family"] == x["b"]["class_family"]]
    cells = Counter()
    for x in exact:
        key = ("plan_date_present" if x["t"]["plan"] else "no_plan_date",
               "form4_true" if flag(x["b"]["flag"]) is True else "form4_false" if flag(x["b"]["flag"]) is False else "form4_unknown")
        cells["|".join(key)] += 1
    concordant = cells["plan_date_present|form4_true"] + cells["no_plan_date|form4_false"]
    n = len(eligible)
    return {
      "phase": 208,
      "inputs": {"form144_csv_sha256": h144, "form144_run_id": 41959603351, "form144_artifact_id": 13385365595,
                 "form4_q3_zip_sha256": h4, "form4_run_id": 40606706518, "form4_artifact_id": 12781850078},
      "sample": {"form144_panel_rows": len(rows), "form144_q3_original_notices": len(originals),
                 "form144_eligible_notices": n, "form144_eligible_tranches": len(tr),
                 "form144_excluded_right_censor_or_unparseable": len(originals)-n,
                 "form4_submissions": len(subs), "form4_original_submissions": sum(x.get("DOCUMENT_TYPE")=="4" for x in subs),
                 "form4a_excluded": sum(x.get("DOCUMENT_TYPE")=="4/A" for x in subs),
                 "form4_nonderivative_rows": len(rawtx), "form4_unique_owner_sale_blocks": len(blocks),
                 "form4_max_filing_date": maxfd, "form4_duplicate_transaction_keys": len(rawtx)-unique_tx_keys},
      "post_notice": {"candidate_pairs": len(pc),
        "candidate_tranches": len({(x["t"]["accession"],x["t"]["idx"]) for x in pc}),
        "candidate_form4_blocks": len({(x["b"]["accession"],x["b"]["date"]) for x in pc}),
        "one_to_one_matches": len(post), "one_to_one_notice_count": len({x["t"]["accession"] for x in post}),
        "one_to_one_rate": round(len({x["t"]["accession"] for x in post})/n,6),
        "same_date": len(same), "exact_same_date_and_shares": len(exact),
        "exact_rate": round(len({x["t"]["accession"] for x in exact})/n,6),
        "within_20pct": len(within), "within_20pct_rate_of_matches": round(len(within)/len(post),6),
        "ratio_p10": qtile([x["ratio"] for x in post],.1), "ratio_p50": qtile([x["ratio"] for x in post],.5),
        "ratio_p90": qtile([x["ratio"] for x in post],.9),
        "form4_lag_p50": qtile([float(x["b"]["lag"]) for x in post],.5),
        "form4_lag_p90": qtile([float(x["b"]["lag"]) for x in post],.9)},
      "pre_notice_placebo": {"window_days":[-2,-1], "candidate_pairs":len(nc), "one_to_one_matches":len(pre),
        "one_to_one_rate":round(len({x["t"]["accession"] for x in pre})/n,6), "exact_same_date_and_shares":0},
      "class_check": {"exact_matches":len(exact), "class_checked":len(checked), "class_family_agree":len(agree),
        "class_family_agreement_rate":round(len(agree)/len(checked),6),
        "literal_class_string_agree":sum(x["t"]["class_norm"]==x["b"]["class_norm"] for x in checked),
        "conflict_or_unresolved":len(checked)-len(agree)},
      "plan_flag_check": {"exact_matches":len(exact), "cells":dict(cells), "concordant":concordant,
        "concordance_rate":round(concordant/len(exact),6)},
      "decision": {"execution_conversion":"SUPPORTED_IN_ONE_2026Q3_SAMPLE_WITH_CLASS_AND_IDENTITY_CAVEATS",
        "strict_pit_admitted":False, "feature_admitted":False, "alpha_test_authorized":False,
        "return_test_run":False, "holdout_used":False, "legacy_holdout":"CONSUMED_NOT_PRISTINE",
        "f80_frozen":True, "production_changed":False}
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--form144-csv", required=True)
    p.add_argument("--form4-zip", required=True)
    p.add_argument("--output", required=True)
    a=p.parse_args()
    result=audit(a.form144_csv,a.form4_zip)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__ == "__main__": main()

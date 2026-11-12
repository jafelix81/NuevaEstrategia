#!/usr/bin/env python3
"""Phase 326: original Form 4 XML cross-check of Phase 325 same-day ticker collisions.

SEC transaction security-title labels are descriptive evidence, not permanent
security identifiers. This is an identity/source audit, not an alpha test.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, time, zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
from research.phase320_sec_bulk_daily_index_join import (
    _fetch_bytes, normalize_accession, normalize_cik, sha256_bytes, submission_url
)
from research.phase319_sec_daily_index_live_pilot import parse_filing_header

PHASE = 326
P321_SHA = "e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c"
P325_SHA = "6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3"
N_CENSUS, N_PAIRS, N_DATES, N_ACCESSIONS = 317267, 28, 42, 283
PLACEHOLDERS = {"", "NONE", "(NONE)", "[NONE]", "NO SYMBOL", "N/A", "NA", "NULL", "NAN", "NONE]"}
SINGLE = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,9}$")
EXCHANGE = re.compile(r"^([A-Z0-9.-]{1,8}):\s*([A-Z0-9.-]{1,10})$")


def classify_symbol(raw):
    value = (raw or "").strip().upper()
    if value in PLACEHOLDERS:
        return None
    m = EXCHANGE.fullmatch(value)
    if m:
        return m.group(2)
    return value if SINGLE.fullmatch(value) else None


def _csv(zf, suffix):
    names = [n for n in zf.namelist() if n.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"zip_member_count:{suffix}:{len(names)}")
    return list(csv.DictReader(io.TextIOWrapper(zf.open(names[0]), encoding="utf-8-sig")))


def _list(value):
    if isinstance(value, list):
        items = value
    else:
        try:
            items = json.loads(value or "[]")
        except (TypeError, json.JSONDecodeError):
            items = []
    return sorted({normalize_cik(v) for v in items if normalize_cik(v)})


def path_ciks_for(accession, issuer_cik, owners):
    # SEC archive path CIK is the accession prefix; it is a retrieval route,
    # not a substitute for issuer/reporting-owner identity in the filing XML.
    prefix = normalize_cik(str(accession).split("-")[0])
    return list(dict.fromkeys([prefix, normalize_cik(issuer_cik)] + [normalize_cik(x) for x in owners if normalize_cik(x)]))


def load_plan(p321: Path, p325: Path):
    b321, b325 = p321.read_bytes(), p325.read_bytes()
    if sha256_bytes(b321) != P321_SHA or sha256_bytes(b325) != P325_SHA:
        raise ValueError("immutable_source_sha256_mismatch")
    with zipfile.ZipFile(io.BytesIO(b321)) as z1, zipfile.ZipFile(io.BytesIO(b325)) as z5:
        census = _csv(z1, "phase321_bulk_daily_index_census.csv")
        p321j = [n for n in z1.namelist() if n.endswith("phase321_bulk_daily_index_census_result.json")]
        collisions = _csv(z5, "phase325_same_day_symbol_collisions.csv")
    if len(census) != N_CENSUS or len(p321j) != 1:
        raise ValueError("phase321_population_mismatch")
    if json.loads(zipfile.ZipFile(io.BytesIO(b321)).read(p321j[0])).get("bulk_census", {}).get("total_accessions") != N_CENSUS:
        raise ValueError("phase321_result_identity_mismatch")
    if len(collisions) != N_PAIRS:
        raise ValueError("phase325_collision_count_mismatch")
    shared_dates = sum(len((r.get("shared_filing_dates") or "").split(";")) for r in collisions)
    if shared_dates != N_DATES:
        raise ValueError("phase325_shared_date_count_mismatch")

    by_key = defaultdict(list)
    for r in census:
        form = (r.get("form_type") or "").upper().strip()
        accession = normalize_accession(r.get("accession"))
        cik = normalize_cik(r.get("issuer_cik"))
        day = (r.get("filing_date") or "").strip()
        symbol = classify_symbol(r.get("ticker_as_filed"))
        if form not in {"4", "4/A"} or not accession or not cik or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("invalid_phase321_census_row")
        if symbol:
            by_key[(cik, day, symbol)].append(r)

    selected, pairs, missing = {}, [], []
    for i, p in enumerate(collisions, 1):
        symbol = p["ticker_candidate"].strip().upper()
        a, b = normalize_cik(p["issuer_cik_a"]), normalize_cik(p["issuer_cik_b"])
        pair_id = f"P{i:02d}_{symbol}_{a}_{b}"
        dates = [d for d in p["shared_filing_dates"].split(";") if d]
        pairs.append({
            "pair_id": pair_id, "ticker_candidate": symbol,
            "issuer_cik_a": a, "issuer_name_a": p["issuer_name_a"],
            "issuer_cik_b": b, "issuer_name_b": p["issuer_name_b"],
            "shared_filing_dates": dates,
        })
        for day in dates:
            for side, cik in (("A", a), ("B", b)):
                hits = by_key.get((cik, day, symbol), [])
                if not hits:
                    missing.append((pair_id, side, cik, day))
                for r in hits:
                    acc = normalize_accession(r["accession"])
                    item = selected.setdefault(acc, {
                        **r, "accession": acc, "issuer_cik": cik,
                        "reporting_owner_ciks": _list(r.get("reporting_owner_ciks")),
                        "pair_memberships": []
                    })
                    item["pair_memberships"].append({
                        "pair_id": pair_id, "side": side, "date": day, "ticker_candidate": symbol
                    })
    if missing:
        raise ValueError("collision_side_missing_from_census:" + repr(missing[:5]))
    if len(selected) != N_ACCESSIONS:
        raise ValueError(f"selected_accession_count:{len(selected)}")
    for acc, r in selected.items():
        if r.get("index_status") != "MATCHED_ON_FILED_DATE":
            raise ValueError(f"selected_accession_not_index_matched:{acc}:{r.get('index_status')}")
        r["path_ciks"] = path_ciks_for(acc, r["issuer_cik"], r["reporting_owner_ciks"])
    return {
        "phase321_sha256": P321_SHA, "phase325_sha256": P325_SHA,
        "census_rows": len(census), "pair_count": len(pairs), "shared_dates": shared_dates,
        "selected": selected, "pairs": pairs
    }


def lname(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1]


def descendants(el, name):
    return [x for x in el.iter() if lname(x.tag) == name]


def value_of(el, name):
    nodes = descendants(el, name) if el is not None else []
    if not nodes:
        return ""
    vals = [x for x in list(nodes[0]) if lname(x.tag) == "value"]
    return (vals[0].text or "").strip() if vals else (nodes[0].text or "").strip()


def parse_ownership_xml(raw):
    text = raw.decode("latin-1", errors="replace")
    docs = re.findall(r"<DOCUMENT>\s*(.*?)\s*</DOCUMENT>", text, flags=re.I | re.S)
    candidates = []
    for doc in docs:
        typ = re.search(r"<TYPE>\s*([^\s<]+)", doc, flags=re.I)
        body = re.search(r"<TEXT>\s*(.*?)\s*</TEXT>", doc, flags=re.I | re.S)
        if not body:
            continue
        content = body.group(1).strip()
        xm = re.search(r"<XML>\s*(.*?)\s*</XML>", content, flags=re.I | re.S)
        content = xm.group(1).strip() if xm else content
        if (typ and typ.group(1).upper() in {"4", "4/A"}) or "ownershipdocument" in content.lower():
            candidates.append(content)
    if not candidates:
        candidates = [text]
    root = None
    for candidate in candidates:
        m = re.search(r"<ownershipDocument\b[\s\S]*?</ownershipDocument\s*>", candidate, flags=re.I)
        try:
            root = ET.fromstring((m.group(0) if m else candidate).encode("utf-8", errors="replace"))
            if lname(root.tag).lower() == "ownershipdocument":
                break
            root = None
        except ET.ParseError:
            root = None
    if root is None:
        return {"xml_status": "OWNERSHIP_XML_NOT_PARSED", "xml_issuer_cik": "",
                "xml_issuer_symbol": "", "xml_owner_ciks": [], "non_derivative_titles": [],
                "derivative_titles": [], "underlying_titles": [], "transaction_codes": [],
                "acquired_disposed_codes": [], "non_derivative_count": 0, "derivative_count": 0}
    issuers = descendants(root, "issuer")
    issuer = issuers[0] if issuers else None
    symbol_raw = value_of(issuer, "issuerTradingSymbol")
    nonder = descendants(root, "nonDerivativeTransaction")
    deriv = descendants(root, "derivativeTransaction")
    codes, acquired = [], []
    for tx in nonder + deriv:
        code, acq = value_of(tx, "transactionCode"), value_of(tx, "transactionAcquiredDisposedCode")
        if code: codes.append(code.upper())
        if acq: acquired.append(acq.upper())
    return {
        "xml_status": "PARSED",
        "xml_issuer_cik": normalize_cik(value_of(issuer, "issuerCik")),
        "xml_issuer_name": value_of(issuer, "issuerName"),
        "xml_issuer_symbol_raw": symbol_raw,
        "xml_issuer_symbol": classify_symbol(symbol_raw) or "",
        "xml_owner_ciks": sorted({normalize_cik(value_of(o, "rptOwnerCik")) for o in descendants(root, "reportingOwner") if normalize_cik(value_of(o, "rptOwnerCik"))}),
        "non_derivative_titles": sorted({value_of(tx, "securityTitle") for tx in nonder if value_of(tx, "securityTitle")}),
        "derivative_titles": sorted({value_of(tx, "securityTitle") for tx in deriv if value_of(tx, "securityTitle")}),
        "underlying_titles": sorted({value_of(tx, "underlyingSecurityTitle") for tx in deriv if value_of(tx, "underlyingSecurityTitle")}),
        "transaction_codes": sorted(set(codes)),
        "acquired_disposed_codes": sorted(set(acquired)),
        "non_derivative_count": len(nonder), "derivative_count": len(deriv),
    }


def submission_urls_for(accession, path_cik):
    """Return both SEC archive layouts; validate identity after every fetch."""
    cik = normalize_cik(path_cik)
    accession = normalize_accession(accession)
    flat_url = submission_url(accession, cik)
    accession_directory_url = (
        f"{flat_url.rsplit('/', 1)[0]}/{accession.replace('-', '')}/{accession}.txt"
    )
    return [("flat", flat_url), ("accession_directory", accession_directory_url)]


def retrieve_one(r, user_agent, total_bytes):
    errors = []
    for path_cik in r["path_ciks"]:
        for route, url in submission_urls_for(r["accession"], path_cik):
            try:
                raw, headers = _fetch_bytes(url, user_agent, total_bytes)
            except Exception as exc:
                errors.append(f"{path_cik}:{route}:{type(exc).__name__}:{str(exc)[:100]}")
                continue
            h = parse_filing_header(raw)
            expected_entities = {r["issuer_cik"], *r["reporting_owner_ciks"]}
            header_ok = (
                h.get("accession") == r["accession"] and h.get("form_type") == r["form_type"]
                and h.get("filed_date") == r["filing_date"] and normalize_cik(h.get("cik")) in expected_entities
            )
            if not header_ok:
                errors.append(f"{path_cik}:{route}:header_identity_mismatch")
                continue
            x = parse_ownership_xml(raw)
            expected_symbol = classify_symbol(r.get("ticker_as_filed"))
            return {
                "accession": r["accession"], "form_type": r["form_type"], "filing_date": r["filing_date"],
                "quarter": r["quarter"], "issuer_cik": r["issuer_cik"], "issuer_name_bulk": r["issuer_name"],
                "ticker_as_filed": r["ticker_as_filed"], "ticker_candidate": expected_symbol or "",
                "reporting_owner_ciks_bulk": r["reporting_owner_ciks"], "pair_memberships": r["pair_memberships"],
                "fetch_path_cik": path_cik, "fetch_path_route": route, "http_status": headers.get("http_status", ""),
                "bytes": len(raw), "submission_sha256": sha256_bytes(raw),
                "header_cik": normalize_cik(h.get("cik")), "header_filed_date": h.get("filed_date"),
                "acceptance_datetime": h.get("acceptance_datetime_et"), "header_identity_match": header_ok,
                **x,
                "xml_issuer_cik_match": x["xml_issuer_cik"] == r["issuer_cik"],
                "xml_issuer_symbol_match": bool(expected_symbol) and x["xml_issuer_symbol"] == expected_symbol,
                "xml_owner_ciks_match": bool(r["reporting_owner_ciks"]) and set(r["reporting_owner_ciks"]).issubset(set(x["xml_owner_ciks"])),
                "retrieval_status": "RETRIEVED", "prior_path_errors": errors,
            }
    return {
        "accession": r["accession"], "form_type": r["form_type"], "filing_date": r["filing_date"],
        "quarter": r["quarter"], "issuer_cik": r["issuer_cik"], "issuer_name_bulk": r["issuer_name"],
        "ticker_as_filed": r["ticker_as_filed"], "ticker_candidate": classify_symbol(r.get("ticker_as_filed")) or "",
        "reporting_owner_ciks_bulk": r["reporting_owner_ciks"], "pair_memberships": r["pair_memberships"],
        "retrieval_status": "FAILED", "prior_path_errors": errors, "header_identity_match": False,
        "xml_status": "NOT_RETRIEVED", "xml_issuer_cik_match": False, "xml_issuer_symbol_match": False,
        "xml_owner_ciks_match": False, "submission_sha256": "", "non_derivative_titles": [],
        "derivative_titles": [], "underlying_titles": [], "transaction_codes": [],
        "acquired_disposed_codes": [], "non_derivative_count": 0, "derivative_count": 0
    }


def pair_summary(pairs, filings):
    result = []
    for p in pairs:
        sides = {}
        for side in ("A", "B"):
            rows = [r for r in filings if r["issuer_cik"] == p[f"issuer_cik_{side.lower()}"]
                    and any(m["pair_id"] == p["pair_id"] and m["side"] == side for m in r.get("pair_memberships", []))]
            titles = {t for r in rows for t in r.get("non_derivative_titles", []) + r.get("derivative_titles", [])}
            sides[side] = (rows, titles)
        a, ta = sides["A"]; b, tb = sides["B"]
        overlap = sorted(ta & tb)
        if not a or not b or any(r.get("retrieval_status") != "RETRIEVED" for r in a+b):
            relation = "INCOMPLETE_RETRIEVAL"
        elif not ta or not tb:
            relation = "TITLE_LABEL_MISSING_ON_ONE_SIDE"
        elif overlap:
            relation = "OVERLAPPING_LABELS_NOT_SECURITY_IDENTITY"
        else:
            relation = "DISJOINT_LABELS_NOT_SHARE_CLASS_PROOF"
        result.append({
            "pair_id": p["pair_id"], "ticker_candidate": p["ticker_candidate"],
            "issuer_cik_a": p["issuer_cik_a"], "issuer_name_a": p["issuer_name_a"],
            "issuer_cik_b": p["issuer_cik_b"], "issuer_name_b": p["issuer_name_b"],
            "shared_filing_dates": p["shared_filing_dates"], "filings_a": len(a), "filings_b": len(b),
            "titles_a": sorted(ta), "titles_b": sorted(tb), "overlap": overlap,
            "title_relation": relation, "title_is_security_id": False
        })
    return result


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def run(plan, outdir, email):
    if not email or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required")
    outdir.mkdir(parents=True, exist_ok=True)
    ua = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total = [0]; filings = []
    for n, acc in enumerate(sorted(plan["selected"]), 1):
        filings.append(retrieve_one(plan["selected"][acc], ua, total))
        if n % 25 == 0: print(f"PHASE326_PROGRESS={n}/{N_ACCESSIONS}")
    pairs = pair_summary(plan["pairs"], filings)
    got = [r for r in filings if r["retrieval_status"] == "RETRIEVED"]
    titles = Counter(t for r in got for t in set(r["non_derivative_titles"] + r["derivative_titles"]))
    summary = {
        "source_accessions": plan["census_rows"], "collision_pairs": plan["pair_count"],
        "shared_dates": plan["shared_dates"], "selected_accessions": len(filings),
        "selected_forms": dict(sorted(Counter(r["form_type"] for r in filings).items())),
        "selected_issuer_ciks": len({r["issuer_cik"] for r in filings}),
        "retrieved": len(got), "retrieval_failures": len(filings)-len(got),
        "header_identity_matches": sum(bool(r.get("header_identity_match")) for r in got),
        "xml_parsed": sum(r.get("xml_status") == "PARSED" for r in got),
        "xml_issuer_cik_matches": sum(bool(r.get("xml_issuer_cik_match")) for r in got),
        "xml_symbol_matches": sum(bool(r.get("xml_issuer_symbol_match")) for r in got),
        "xml_owner_ciks_matches": sum(bool(r.get("xml_owner_ciks_match")) for r in got),
        "non_derivative_transactions": sum(r.get("non_derivative_count",0) for r in got),
        "derivative_transactions": sum(r.get("derivative_count",0) for r in got),
        "transaction_code_counts": dict(sorted(Counter(c for r in got for c in r.get("transaction_codes",[])).items())),
        "distinct_title_labels": len(titles), "title_label_filing_counts": dict(sorted(titles.items())),
        "pair_title_relations": dict(sorted(Counter(r["title_relation"] for r in pairs).items())),
        "sec_bytes_downloaded": total[0]
    }
    controls = {
        "strict_pit_admitted": False, "alpha_test_authorized": False, "return_test_run": False,
        "bootstrap_loo_run": False, "chronological_oos_run": False, "holdout_used": False,
        "f80_frozen": True, "production_changed": False, "universe_changed": False,
        "capital_changed": False, "parameters_changed": False, "raw_sec_bytes_uploaded": False,
        "vendor_contacted": False, "data_purchased": False, "email_sent": False
    }
    result = {
        "phase": PHASE, "status": "COMPLETED_WITH_SOURCE_LEVEL_RECONCILIATION" if summary["retrieved"] == N_ACCESSIONS and summary["header_identity_matches"] == N_ACCESSIONS else "COMPLETED_WITH_QUARANTINE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"phase321_artifact_sha256": plan["phase321_sha256"], "phase325_artifact_sha256": plan["phase325_sha256"]},
        "summary": summary,
        "interpretation": {
            "issuer_symbol_is_security_key": False, "transaction_title_is_permanent_security_id": False,
            "same_title_proves_same_security": False, "different_titles_prove_different_share_classes": False,
            "collision_is_corporate_relationship_adjudication": False, "strict_pit_admitted": False,
            "alpha_test_authorized": False
        },
        "controls": controls, "filings": filings, "pairs": pairs
    }
    (outdir/"phase326_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(outdir/"phase326_filing_audit.csv", filings)
    write_csv(outdir/"phase326_pair_summary.csv", pairs)
    write_csv(outdir/"phase326_title_counts.csv", [{"title":k,"filings":v} for k,v in sorted(titles.items())])
    print("PHASE326_STATUS="+result["status"])
    print("PHASE326_SUMMARY="+json.dumps(summary, sort_keys=True))
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase321-zip", type=Path, required=True)
    p.add_argument("--phase325-zip", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--email", default="")
    p.add_argument("--plan-only", action="store_true")
    a=p.parse_args(); plan=load_plan(a.phase321_zip,a.phase325_zip)
    if a.plan_only:
        print(json.dumps({
            "phase":PHASE,"phase321_census_rows":plan["census_rows"],
            "phase325_collision_pairs":plan["pair_count"],"shared_dates":plan["shared_dates"],
            "selected_accessions":len(plan["selected"]),
            "selected_forms":dict(sorted(Counter(r["form_type"] for r in plan["selected"].values()).items())),
            "selected_issuer_ciks":len({r["issuer_cik"] for r in plan["selected"].values()})
        },sort_keys=True)); return
    r=run(plan,a.output_dir,a.email)
    if r["summary"]["retrieval_failures"] or r["summary"]["header_identity_matches"] != N_ACCESSIONS:
        raise SystemExit("Phase 326 SEC retrieval/header identity incomplete; inspect artifact quarantine rows")


if __name__ == "__main__":
    main()
